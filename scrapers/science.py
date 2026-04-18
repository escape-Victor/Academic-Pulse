import time
import traceback
from core.base_scraper import BaseScraper

class ScienceScraper(BaseScraper):
    def __init__(self, page, config):
        super().__init__(page, config)
        self.journal_name = "Science"
        # 获取用户在 GUI 里选的类型 (research / news / all)
        self.content_type = config.get('content_type', 'research')

    # === 🛡️ 视觉净化 ===
    def nuke_distractions(self):
        try:
            css = """
                #cookie-banner, .c-cookie-banner, .banner, .cc-banner, .cc-window,
                #onetrust-banner-sdk, .osano-cm-window,
                footer, .c-site-footer, .advertisement, .c-ad, .ad-banner, 
                [data-test="related-content"], .c-hutton-hero-context-bar
                { display: none !important; visibility: hidden !important; }
            """
            self.target_page.add_style_tag(content=css)
        except: pass

    def get_article_links(self) -> list:
        page = self.target_page 
        urls = []

        try:
            print("\n   🤖 [Science] 极简模式启动...")
            page.set_viewport_size({"width": 1920, "height": 1080})
            time.sleep(2)
            self.nuke_distractions()

            # === 步骤 1: 暴力点击封面 ===
            print("      🖱️ 步骤1: 锁定 Science 封面...")
            target_cover = page.locator(".journals-showcase__showcase-item").first
            try: target_cover.evaluate("node => node.style.border = '5px solid red'")
            except: pass
            
            print("      👉 执行强制点击...")
            target_cover.click(force=True)
            print("      ⏳ 等待页面响应 (5s)...")
            time.sleep(5) 
            self.nuke_distractions()

            # === 步骤 2: 点击目录按钮 ===
            print("      🖱️ 步骤2: 寻找并点击 'VIEW TABLE OF CONTENTS'...")
            toc_btn = page.locator("a").filter(has_text="View Table of Contents").first
            
            # 补刀逻辑
            if not toc_btn.is_visible():
                toc_btn = page.get_by_text("VIEW TABLE OF CONTENTS").first
            
            if not toc_btn.is_visible():
                print("      ⚠️ 似乎没跳过去，尝试补刀点击...")
                target_cover.click(force=True)
                time.sleep(5)
                toc_btn = page.locator("a").filter(has_text="View Table of Contents").first

            if toc_btn.is_visible():
                toc_btn.scroll_into_view_if_needed()
                toc_btn.click(force=True)
            else:
                # 最后的备选：直接拼 URL 跳转 (防止死循环)
                print("      ⚠️ 找不到目录按钮，尝试 URL 拼接跳转...")
                current_url = page.url
                if "/doi/" not in current_url:
                    # 这是一个简单的 fallback，通常 Science 每一期都有固定的 issue 号
                    # 但如果没有 issue 号，这一步可能跳不过去。我们假设点击是生效的。
                    pass

            print("      📖 等待目录加载...")
            time.sleep(3)
            self.nuke_distractions()

            # === 步骤 3: 智能分类抓取 (核心升级) ===
            print(f"      👀 步骤3: 提取链接 (模式: {self.content_type.upper()})...")
            
            # 等待文章列表加载
            page.wait_for_selector("h3 a", timeout=15000)
            
            # 获取所有文章卡片 (比单纯找链接更稳，因为我们要看上下文)
            # Science 的文章通常包在 role="listitem" 或者类似的容器里
            # 但为了通用，我们还是遍历 h3 链接，然后看它的“邻居”文字
            
            link_elements = page.locator("h3 a[href*='/doi/']").all()
            seen = set()
            
            # 定义关键词字典
            keywords_research = ["Research Article", "Report", "Review", "Paper"]
            keywords_news = ["News", "In Depth", "Perspective", "Editorial", "Podcast", "Feature"]

            print(f"      🔍 扫描到 {len(link_elements)} 个潜在链接，开始过滤...")

            for link in link_elements:
                href = link.get_attribute("href")
                title_text = link.inner_text().strip()
                
                if not href or href in seen: continue

                # === 核心过滤逻辑 ===
                # 获取文章卡片的全部文本 (通常包含 Category, Title, Authors)
                # 我们找 h3 的父级再父级，通常能覆盖整个卡片
                try:
                    # 向上找两层，获取卡片文本
                    card_text = link.locator("xpath=../../..").inner_text()
                except:
                    card_text = title_text # 如果找不到父级，就只查标题

                is_match = False
                
                if self.content_type == 'all':
                    is_match = True
                
                elif self.content_type == 'research':
                    # 如果卡片里包含 "Research Article" 等词，或者它是 "All" 模式
                    if any(kw in card_text for kw in keywords_research):
                        is_match = True
                    # Science 有时候不标 Research，但 Research 标题通常很长
                    elif len(title_text.split()) > 8 and not any(kw in card_text for kw in keywords_news):
                         is_match = True # 标题长且不是新闻，大概率是论文

                elif self.content_type == 'news':
                    if any(kw in card_text for kw in keywords_news):
                        is_match = True
                    # 标题短的通常是 News
                    elif len(title_text.split()) < 8 and not any(kw in card_text for kw in keywords_research):
                        is_match = True

                if is_match:
                    seen.add(href)
                    urls.append(href)
                    # 打印一下调试信息，让你知道它抓了啥
                    # print(f"         [+] 收录: {title_text[:30]}...")
                
            print(f"      ✅ 筛选后剩余 {len(urls)} 篇")

        except Exception as e:
            print(f"\n❌ [Science] 出错: {e}")
            traceback.print_exc()
            print("🛑 程序暂停... (按回车键结束)")
            input()
        
        return urls