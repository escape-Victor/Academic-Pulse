import time
import traceback
from core.base_scraper import BaseScraper

class CellScraper(BaseScraper):
    def __init__(self, page, config):
        super().__init__(page, config)
        self.journal_name = "Cell"
        self.content_type = config.get('content_type', 'research')

    def get_article_links(self) -> list:
        page = self.target_page 
        urls = []
        try:
            print("\n   🧬 [Cell] 启动抓取...")
            page.set_viewport_size({"width": 1920, "height": 1080})
            time.sleep(3)
            self.nuke_distractions()

            # Cell 官网比较特殊，有时需要点一下 Issues 或者 Current Issue
            # 通常首页就是最新的 Highlight
            
            print("      👀 正在扫描首页文章...")
            # Cell 的文章链接通常包含 /cell/fulltext/ 或 /cell/pdf/
            # 或者是 ScienceDirect 风格的 /science/article/pii/
            
            # 等待文章列表加载
            page.wait_for_selector("a", timeout=10000)
            
            # 针对 Cell 官网改版，尝试找主要的文章标题
            # 常见类名：article-title, c-card__title
            candidates = page.locator("h3 a, h2 a, .article-title a").all()
            
            seen = set()
            print(f"      🔍 扫描到 {len(candidates)} 个潜在链接...")
            
            for link in candidates:
                href = link.get_attribute("href")
                text = link.inner_text()
                
                if not href: continue
                
                # 过滤逻辑
                is_match = False
                
                # Cell 的链接特征
                if "/cell/fulltext/" in href or "/article/pii/" in href:
                    if self.content_type == 'research':
                        # 简单的长度判断，论文标题通常较长
                        if len(text) > 30: is_match = True
                    else:
                        is_match = True # 全抓
                
                if is_match and href not in seen:
                    seen.add(href)
                    urls.append(href)
            
            print(f"      ✅ 筛选后剩余 {len(urls)} 篇")

        except Exception as e:
            print(f"❌ [Cell] 出错: {e}")
            traceback.print_exc()
        
        return urls