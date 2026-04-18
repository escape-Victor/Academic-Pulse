import requests
import json

class LLMEngine:
    def __init__(self, config: dict):
        self.api_url = config['api_url']
        self.model = config['model']

    def analyze(self, article_data: dict):
        title = article_data['title']
        content = article_data['content']
        mode = article_data['mode']
        
        print(f"      🧠 AI 正在分析 ({mode}): {title[:20]}...")
        prompt = self._build_prompt(title, content, mode)
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_ctx": 8192}
                },
                timeout=120
            )
            return response.json().get('response', "AI 响应解析失败")
        except Exception as e:
            return f"⚠️ AI 调用异常: {e}"

    def _build_prompt(self, title, text, mode):
        # === 核心逻辑修改：区分泛读和精读的详细程度 ===
        if mode == "deep":
            task_desc = "请进行【深度研读】，提供核心简报、方法论细节、以及高阶研读词汇表。"
            output_format = """
        > **📖 核心简报 (Deep Dive)**
        * (Point 1: Context & Problem)
        * (Point 2: Methodology & Innovation)
        * (Point 3: Key Results)
        
        > **🧪 研读词汇**
        | Word | Phonetic | Chinese | Context |
        |---|---|---|---|
        | ... | ... | ... | ... |
            """
        else:
            # 泛读模式：虽然叫 Skim，但内容要全面 (Comprehensive)，只是不摘录单词
            task_desc = "请进行【全面综述】，详细概括文章的背景、核心发现和意义。不要遗漏关键数据。🚫 严禁提供词汇表。"
            output_format = """
        > **📖 全面综述 (Comprehensive Summary)**
        * **背景**: ...
        * **核心发现**: ... (包含关键数据)
        * **结论与意义**: ...
            """

        return f"""
        CRITICAL INSTRUCTIONS:
            1. **NO HTML TAGS**: Use standard Markdown only.
            2. **LANGUAGE**: Summary MUST be in CHINESE (简体中文).
            3. **FORMATTING**: Use bolding for key concepts.
            
        ROLE: 学术编辑
        TASK: {task_desc}
        
        TITLE: {title}
        CONTENT: {text[:7500]} 

        OUTPUT FORMAT:
        {output_format}
        """