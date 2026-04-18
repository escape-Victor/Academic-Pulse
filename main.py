import yaml
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from core.llm_engine import LLMEngine

# 导入所有插件
from scrapers.nature import NatureScraper 
from scrapers.science import ScienceScraper
from scrapers.cell import CellScraper 
# from scrapers.acm import ACMScraper

# === 配置区 ===
ZJU_ID = "YOUR_ID"
ZJU_PWD = "YOUR_PASSWORD"

def load_config():
    config_path = os.path.join("config", "settings.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def format_original_text(text):
    """
    🎨 原文排版美化引擎
    """
    if not text: return ""
    
    formatted_lines = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for line in lines:
        # 识别小标题
        if len(line) < 80 and line[-1] not in ['.', '?', '!', ':', ';', '。', '？', '！', '”', '"']:
            formatted_lines.append(f"\n### **{line}**\n")
        else:
            # 普通段落首行缩进
            formatted_lines.append(f"　　{line}\n")
            
    return "\n".join(formatted_lines)

def save_to_markdown(article_data, ai_analysis):
    """保存 Markdown，支持按日期归档和相对路径修复"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 📂 归档逻辑：创建日期文件夹 (例如 output/2026-02-01/)
    output_dir = os.path.join("output", date_str)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    safe_title = "".join([c for c in article_data['title'] if c.isalnum() or c in " _-"])[:50]
    filename = f"{output_dir}/{article_data.get('journal_name', 'Doc')}_{safe_title}.md"
    
    content = f"# {article_data['title']}\n\n"
    content += f"**URL:** {article_data['url']}\n"
    content += f"**Mode:** {article_data['mode'].upper()}\n\n"
    
    # === 🖼️ 图片插入区 (路径修复) ===
    if article_data.get('images'):
        content += "### 📊 文章配图\n\n"
        for i, img_path in enumerate(article_data['images']):
            # 🛠️ 关键修复：添加 ../ 前缀，因为 Markdown 文件在子文件夹里
            # 原始 img_path 是 "assets/xxx.png"
            # 修正后是 "../assets/xxx.png"
            content += f"![Fig {i+1}](../{img_path})\n\n"
        content += "---\n\n"

    # AI 分析
    content += f"{ai_analysis}\n\n"
    
    # 🚫 泛读模式下，不保存原文
    if article_data['mode'] == 'skim':
        content += "\n*(注：当前为泛读模式，未收录原文全文)*\n"
    else:
        content += "---\n\n### 📜 原文全文\n\n"
        pretty_content = format_original_text(article_data['content'])
        content += f"{pretty_content}\n" 
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"      💾 已保存至: {filename}")

def main():
    config = load_config()
    ai_engine = LLMEngine(config['ai'])
    
    print("🚀 启动 Academic Pulse (Anti-Bot Pro)...")

    # 打印配置预览
    for name, conf in config['journals'].items():
        if conf.get('enabled'):
            print(f"   🔹 {name.capitalize()}: [启用] | {conf['mode']} | {conf['count']}篇 | {conf.get('content_type', 'all')}")

    with sync_playwright() as p:
        # === 🛠️ 浏览器启动参数增强 (解决 Cell 卡死问题) ===
        browser = p.chromium.launch(
            channel="msedge", 
            headless=False, 
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled' # 关键：禁用自动化特征
            ]
        )
        
        # 创建上下文时指定 User Agent，伪装成真实用户
        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        )
        page = context.new_page()
        
        # 注入反检测脚本 (双重保险)
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)

        # === 登录 WebVPN ===
        print("🔐 连接 WebVPN...")
        try:
            page.goto("https://webvpn.zju.edu.cn/", timeout=60000)
            if "login" in page.url:
                page.wait_for_selector("input[type='password']", timeout=10000)
                if page.locator("input[name='username']").count() > 0:
                    page.fill("input[name='username']", ZJU_ID)
                else:
                    page.locator("input[type='text']").first.fill(ZJU_ID)
                page.fill("input[type='password']", ZJU_PWD)
                
                if page.locator("#dl").count() > 0: page.click("#dl")
                else: page.press("input[type='password']", "Enter")

                start_time = time.time()
                while time.time() - start_time < 60:
                    if "index" in page.url or ("webvpn" in page.url and "login" not in page.url):
                        break
                    confirm_btn = page.locator(".layui-layer-btn0, a:has-text('继续')").first
                    if confirm_btn.is_visible():
                        confirm_btn.click()
                        time.sleep(2)
                    time.sleep(1)
            page.wait_for_load_state('domcontentloaded')
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return

        # === 调度逻辑 ===
        for journal_name, j_config in config['journals'].items():
            if not j_config['enabled']: continue
            
            print(f"\n📚 处理期刊: {journal_name}")
            
            scraper = None
            if journal_name == "science": scraper = ScienceScraper(page, j_config)
            elif journal_name == "nature": scraper = NatureScraper(page, j_config)
            elif journal_name == "cell": scraper = CellScraper(page, j_config)
            # elif journal_name == "acm": scraper = ACMScraper(page, j_config)

            if scraper:
                try:
                    articles = scraper.run()
                    if not articles: continue
                    for art in articles:
                        art['journal_name'] = journal_name.capitalize()
                        art['mode'] = j_config['mode']
                        
                        analysis = ai_engine.analyze(art)
                        save_to_markdown(art, analysis)
                        print(f"   ✅ [完成] {art['title'][:30]}...")
                except Exception as e:
                    print(f"   ❌ {journal_name} 出错: {e}")
                    # import traceback
                    # traceback.print_exc()

    print("\n👋 任务结束")

if __name__ == "__main__":
    main()