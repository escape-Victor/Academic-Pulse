import time
import os
import trafilatura
from abc import ABC, abstractmethod
from playwright.sync_api import Page

# === 🌍 期刊导航配置表 ===
JOURNAL_META = {
    "Science": {
        "search_key": "Science",
        "db_marker": "AAAS",
        "site_marker": "science.org"
    },
    "Nature": {
        "search_key": "Nature",
        "db_marker": "Nature期刊",
        "site_marker": "nature.com"
    },
    "Cell": {
        "search_key": "cell",
        "db_marker": "Cell Press",  # 图书馆通常显示 Cell Press
        "site_marker": "cell.com"
    },
    "ACM": {
        "search_key": "ACM Digital Library",
        "db_marker": "ACM",
        "site_marker": "dl.acm.org"
    }
}

class BaseScraper(ABC):
    def __init__(self, page: Page, config: dict):
        self.page = page
        self.config = config
        self.journal_name = "Unknown"

    def navigate_to_database(self, journal_name):
        print(f"🗺️ 2. 正在通过图书馆导航至 {journal_name}...")
        
        meta = JOURNAL_META.get(journal_name)
        if not meta:
            print(f"   ⚠️ 未知期刊 '{journal_name}'，使用通用模式...")
            meta = {"search_key": journal_name, "db_marker": journal_name, "site_marker": "http"}

        context = self.page.context
        
        try:
            # === 步骤 1: 进搜索页 & 搜索 ===
            # (尝试点击常见的数据库入口，不同学校可能不同，这里保留通用逻辑)
            db_link = self.page.locator("a").filter(has_text="图书馆数据库").first
            if db_link.is_visible():
                with context.expect_page() as new_page_info: 
                    db_link.click()
                lib_page = new_page_info.value
            else:
                lib_page = self.page
            
            lib_page.wait_for_load_state('domcontentloaded')
            
            search_box = lib_page.locator("input[placeholder*='数据库'], #searchName").first
            if not search_box.is_visible():
                print("   ⚠️ 找不到搜索框，尝试直接在当前页面查找...")
            else:
                print(f"   🔍 搜索关键词: {meta['search_key']}")
                search_box.fill(meta['search_key'])
                lib_page.keyboard.press("Enter")
                time.sleep(2) 

            # === 步骤 2: 从列表进详情页 ===
            print(f"      🕵️ 正在筛选包含 '{meta['db_marker']}' 的入口...")
            
            # 优先找同时包含“搜索词”和“标记词”的
            target_link = lib_page.locator("a").filter(has_text=meta['db_marker']).first
            
            if not target_link.is_visible():
                # 兜底：只找搜索词
                target_link = lib_page.locator(f"a:has-text('{meta['search_key']}')").first

            if not target_link.is_visible():
                 raise Exception(f"未找到符合 '{meta['db_marker']}' 的数据库入口")

            try:
                with context.expect_page(timeout=10000) as detail_info:
                    target_link.click()
                detail_page = detail_info.value
                print("      ✅ 详情页在新窗口打开")
            except:
                print("      ℹ️ 详情页在当前窗口打开")
                detail_page = lib_page
            
            detail_page.bring_to_front()
            detail_page.wait_for_load_state('domcontentloaded')

            # === 步骤 3: 从详情页进官网 ===
            print(f"      🔗 正在寻找官网链接...")
            
            official_link = detail_page.locator("a").filter(has_text=meta['site_marker']).first
            
            if not official_link.is_visible():
                # 兜底：找任何 HTTP 链接
                official_link = detail_page.locator("td.e_url a, a[href^='http']").first

            with context.expect_page(timeout=60000) as final_info:
                official_link.click()
            
            self.target_page = final_info.value
            self.target_page.wait_for_load_state('domcontentloaded')
            print(f"   ✅ 成功抵达 {journal_name} 官网！")

        except Exception as e:
            print(f"❌ 导航失败: {e}")
            # 不死循环，直接抛出让上层处理或重试
            raise e

    def run(self):
        self.navigate_to_database(self.journal_name)
        self.nuke_distractions()
        links = self.get_article_links()
        print(f"   🔍 发现 {len(links)} 个候选文章，将处理前 {self.config['count']} 篇")
        
        results = []
        for i, link in enumerate(links[:self.config['count']]):
            print(f"   📄 处理 ({i+1}/{self.config['count']}): {link}")
            data = self.process_single_article(link, i)
            if data: results.append(data)
        return results

    def process_single_article(self, url, index=0):
        try:
            full_url = url if url.startswith("http") else self.get_base_url() + url
            self.target_page.goto(full_url, timeout=60000)
            self.nuke_distractions()
            time.sleep(2)

            # === 📸 图片抓取 ===
            captured_images = []
            try:
                assets_dir = os.path.join("output", "assets")
                if not os.path.exists(assets_dir): os.makedirs(assets_dir)
                
                # 增加了 Cell 常见的图片容器选择器
                candidates = self.target_page.locator("""
                    article img, figure img, [role='main'] img, .c-article-body img,
                    .article-content img, .figures-tables img
                """).all()
                
                seen_src = set()
                img_count = 0
                for img in candidates:
                    if not img.is_visible(): continue
                    box = img.bounding_box()
                    if box and ((box['width'] > 150 and box['height'] > 150) or box['width'] > 300):
                        src = img.get_attribute("src")
                        if src in seen_src: continue
                        seen_src.add(src)
                        
                        safe_name = f"{self.journal_name}_{index}_img{img_count}_{int(time.time())}.png"
                        img.screenshot(path=os.path.join(assets_dir, safe_name))
                        captured_images.append(f"assets/{safe_name}")
                        img_count += 1
            except: pass
            
            html = self.target_page.content()
            content = trafilatura.extract(html, include_tables=True, include_comments=False) or "提取失败"
            
            return {
                "title": self.target_page.title(),
                "url": full_url,
                "content": content,
                "mode": self.config['mode'], # 这里的 mode 是从 GUI 传进来的独立配置
                "images": captured_images
            }
        except Exception as e:
            print(f"   ❌ 单篇处理失败: {e}")
            return None

    def nuke_distractions(self):
        try:
            css = """
                #cookie-banner, .c-cookie-banner, .banner, .cc-banner, .cc-window,
                footer, .c-site-footer, .advertisement, .c-ad, .ad-banner, 
                [data-test="related-content"]
                { display: none !important; visibility: hidden !important; }
            """
            self.target_page.add_style_tag(content=css)
        except: pass

    @abstractmethod
    def get_article_links(self) -> list:
        pass

    def get_base_url(self):
        if hasattr(self, 'target_page'):
            return "/".join(self.target_page.url.split("/")[:3])
        return ""