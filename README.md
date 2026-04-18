# Academic Pulse (学术脉动) 

Academic Pulse 是一款专为科研人员（特别是浙江大学学子）设计的学术情报自动化工具。它能够自动通过 WebVPN 访问顶级学术期刊，利用大语言模型（LLM）对最新文献进行多维度研读，并生成图文并茂的 Markdown 简报。

## 核心特性
- **自动化导航**：集成 Playwright 自动化引擎，支持 ZJU WebVPN 自动登录及异地登录冲突处理。
- **多刊联动**：支持 Science, Nature, Cell 等主流顶刊的定向采集，具备智能分类算法（识别 Research Article 与 News）。
- **AI 智能研读**：
  - **Skim (泛读)**：快速生成全面综述，不含原文，适合高效筛选。
  - **Deep (精读)**：深度解析方法论与结论，提取高阶学术词汇表。
- **多模态归档**：自动抓取文章高清配图，支持 Markdown 排版美化（自动缩进、标题识别）及按日期分层归档。
- **可视化操作**：提供基于 Tkinter 的 GUI 界面，支持独立配置各期刊的采集频率与阅读深度。

## 技术架构
- **语言**：Python 3.10+
- **自动化**：Playwright (Chromium/Edge)
- **正文提取**：Trafilatura
- **AI 引擎**：LLM API (Ollama/OpenAI compatible)
- **界面**：Tkinter & Threading (异步执行)

## 项目结构
```text
Academic_Pulse/
├── core/                # 核心逻辑 (Scraper基类、AI引擎)
├── scrapers/            # 期刊适配器 (Science, Nature, Cell)
├── config/              # 配置文件 (YAML)
├── gui.py               # 图形界面入口
├── main.py              # 程序主逻辑与调度器
└── requirements.txt     # 项目依赖
```

## 快速开始
1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   playwright install msedge
   ```
2. **配置信息**：
   在 `main.py` 中配置 ZJU 凭证，并在 `config/settings.yaml` 中设置 AI API 地址。
3. **启动程序**：
   ```bash
   python gui.py
   ```

## 免责声明 (Disclaimer)
本项目仅供学术交流与个人研究使用。请遵循各期刊网站的 Robots 协议及版权规定，严禁用于任何商业用途。

---

## 演示与成果展示 (Showcase)

### 演示视频
你可以通过下面的链接观看 Academic Pulse 的完整运行过程（包括 WebVPN 自动登录及 UI 操作演示）：

[![Academic Pulse Demo](【学校买的期刊,你不看看吗?】 https://www.bilibili.com/video/BV1Zsz9BVEh5/?share_source=copy_web&vd_source=e778e99289cda8e95b5b052ca255f7d1)]
> *注：视频展示了如何一键完成从 ZJU 门户登录到生成 AI 综述的全流程。*

### 生成文档示例 (Sample Outputs)
点击下方链接查看程序自动生成的学术简报样张：

| 来源期刊 | 文章标题 | 阅读模式 | 预览链接 |
| :--- | :--- | :--- | :--- |
| **Nature** | 48 hours without lungs: artificial organ kept man alive until transplant | 深度研读 (Deep) | [查看文档](./examples/2026-02-01_48_hours_without_lungs.md) |
| **Science** | How tumours trick the brain into shutting down cancer-fighting cells | 快速泛读 (Skim) | [查看文档](./examples/2026-02-01_China_biotech.md) |

### 🖼️ 界面截图
| 配置界面 | 运行日志 |
| :--- | :--- |
| ![GUI](./output/assets/gui_screenshot.png) |
