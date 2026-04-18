import time
import traceback
from core.base_scraper import BaseScraper

class NatureScraper(BaseScraper):
    def __init__(self, page, config):
        super().__init__(page, config)
        self.journal_name = "Nature"
        self.content_type = config.get('content_type', 'research')

    # === 🛡️ Nature 专属视觉净化 ===
    def nuke_distractions(self):
        try:
            # Nature 的广告和弹窗 ID 和 Science 不太一样
            css = """
                #c-cookie-banner, .c-banner, .cc-banner, .privacy-banner,
                footer, .c-site-footer, .c-footer-main, 
                .c-ad, .advertisement, [data-test="google-ad"],
                .c-header-plugin, .c-popup
                { display: none !important; visibility: hidden !important; }
            """
            self.target_page.add_style_tag(content=css)
        except: pass

    def get_article_links(self) -> list:
        page = self.target_page 
        urls = []

        try:
            print("\n   🌿 [Nature] 启动抓取流程...")
            page.set_viewport_size({"width": 1920, "height": 1080})
            time.sleep(2)
            self.nuke_distractions()

            # === 步骤 1: 寻找并点击 "Current Issue" (当期目录) ===
            print("      🖱️ 步骤1: 寻找当期目录 (Current Issue)...")
            
            current_issue_btn = page.locator("a").filter(has_text="Current Issue").first
            
            if not current_issue_btn.is_visible():
                print("      ⚠️ 未找到文字入口，尝试点击封面图...")
                current_issue_btn = page.locator(".c-card__image, .c-cover-image").first

            # 强制点击
            if current_issue_btn.is_visible():
                print(f"      👉 点击进入目录页...")
                current_issue_btn.click(force=True)
                page.wait_for_load_state("domcontentloaded")
            else:
                print("      ⚠️ 没找到目录入口，尝试直接在当前页抓取 (可能是直达目录)...")

            time.sleep(3)
            self.nuke_distractions()

            # === 步骤 2: 智能分类抓取 ===
            print(f"      👀 步骤2: 提取链接 (模式: {self.content_type.upper()})...")
            
            page.wait_for_selector("a[href*='/articles/']", timeout=10000)
            
            articles = page.locator("article, li.c-article-list__item").all()
            
            keywords_research = ["Research", "Article", "Letter", "Analysis", "Resource"]
            keywords_news = ["News", "Feature", "Comment", "Books", "Arts", "Editorial", "Correspondence"]

            print(f"      🔍 扫描到 {len(articles)} 个条目，开始过滤...")
            
            # 👇👇👇 之前漏掉了这一行！ 👇👇👇
            seen = set()  
            # 👆👆👆 补全了初始化集合 👆👆👆

            for art in articles:
                try:
                    text_content = art.inner_text()
                    
                    link_el = art.locator("a[href*='/articles/']").first
                    if not link_el.is_visible(): continue
                    
                    href = link_el.get_attribute("href")
                    if not href or href in seen: continue

                    # === 过滤逻辑 ===
                    is_match = False
                    
                    if self.content_type == 'all':
                        is_match = True
                        
                    elif self.content_type == 'research':
                        if any(kw in text_content for kw in keywords_research):
                            is_match = True
                        elif "s41586" in href: 
                             if not any(kw in text_content for kw in keywords_news):
                                 is_match = True

                    elif self.content_type == 'news':
                        if any(kw in text_content for kw in keywords_news):
                            is_match = True
                        elif "d41586" in href: 
                            is_match = True

                    if is_match:
                        seen.add(href)
                        urls.append(href)
                        
                except: continue

            # === 兜底模式 (防止上面没抓到) ===
            if len(urls) == 0:
                print("      ⚠️ 精细抓取未命中，启动暴力链接提取...")
                all_links = page.locator("h3 a[href*='/articles/']").all()
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and href not in seen:
                        # 简单的 URL 规则过滤
                        if self.content_type == 'research' and 'd41586' in href: continue 
                        if self.content_type == 'news' and 's41586' in href: continue 
                        
                        seen.add(href)
                        urls.append(href)

            print(f"      ✅ 筛选后剩余 {len(urls)} 篇")

        except Exception as e:
            print(f"\n❌ [Nature] 出错: {e}")
            traceback.print_exc()
        
        return urls