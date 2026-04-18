import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import yaml
import os
import threading
import sys
import datetime
from main import main as run_scraper_logic

CONFIG_PATH = os.path.join("config", "settings.yaml")

class RedirectText(object):
    def __init__(self, text_ctrl):
        self.output = text_ctrl
    def write(self, string):
        self.output.insert(tk.END, string)
        self.output.see(tk.END)
    def flush(self): pass

class AcademicPulseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Academic Pulse v3.0 - 科研情报工作台")
        self.root.geometry("900x700")
        self.config = self.load_config()
        self.create_widgets()

    def load_config(self):
        if not os.path.exists(CONFIG_PATH): return {}
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            conf = yaml.safe_load(f)
            # 确保所有期刊的默认结构存在
            for j in ['science', 'nature', 'cell', 'acm']:
                if j not in conf['journals']:
                    conf['journals'][j] = {'enabled': False, 'mode': 'skim', 'count': 3, 'content_type': 'research'}
            return conf

    def save_config(self):
        # 遍历所有 Tab，保存各自的配置
        for journal, vars in self.journal_vars.items():
            self.config['journals'][journal]['enabled'] = vars['enabled'].get()
            self.config['journals'][journal]['mode'] = vars['mode'].get()
            self.config['journals'][journal]['count'] = int(vars['count'].get())
            
            # 映射回 content_type 代码
            disp_type = vars['type'].get()
            type_map = {"仅抓取论文": "research", "仅抓取新闻": "news", "全部抓取": "all"}
            self.config['journals'][journal]['content_type'] = type_map.get(disp_type, "research")

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, allow_unicode=True)
        print("💾 全局配置已保存！")

    def create_widgets(self):
        # 使用 Notebook 实现 Tab 标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="x", padx=10, pady=10)

        # 存储每个期刊的变量控件，方便保存时读取
        self.journal_vars = {}

        # 创建四个期刊的 Tab
        self.create_journal_tab("Science", "science")
        self.create_journal_tab("Nature", "nature")
        self.create_journal_tab("Cell", "cell")
        self.create_journal_tab("ACM", "acm")

        # === 按钮区 ===
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="💾 保存所有配置", command=self.save_config).pack(side="left", padx=5)
        self.btn_run = ttk.Button(btn_frame, text="🚀 开始采集", command=self.start_thread)
        self.btn_run.pack(side="right", padx=5)

        # === 日志区 ===
        log_frame = ttk.LabelFrame(self.root, text=" 📜 运行日志 ", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)
        sys.stdout = RedirectText(self.log_text)
        sys.stderr = RedirectText(self.log_text)

    def create_journal_tab(self, label, key):
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text=f"  {label}  ")
        
        conf = self.config['journals'].get(key, {})
        
        # 1. 启用开关
        var_enabled = tk.BooleanVar(value=conf.get('enabled', False))
        ttk.Checkbutton(frame, text=f"启用 {label} 抓取任务", variable=var_enabled).pack(anchor="w", pady=5)
        
        # 2. 抓取内容
        f_type = ttk.Frame(frame); f_type.pack(fill="x", pady=2)
        ttk.Label(f_type, text="抓取内容:", width=10).pack(side="left")
        combo_type = ttk.Combobox(f_type, values=["仅抓取论文", "仅抓取新闻", "全部抓取"], state="readonly", width=15)
        
        curr_type = conf.get('content_type', 'research')
        rev_map = {"research": "仅抓取论文", "news": "仅抓取新闻", "all": "全部抓取"}
        combo_type.set(rev_map.get(curr_type, "仅抓取论文"))
        combo_type.pack(side="left")

        # 3. 阅读深度
        f_mode = ttk.Frame(frame); f_mode.pack(fill="x", pady=2)
        ttk.Label(f_mode, text="阅读深度:", width=10).pack(side="left")
        var_mode = tk.StringVar(value=conf.get('mode', 'skim'))
        ttk.Radiobutton(f_mode, text="深度研读 (Deep)", variable=var_mode, value="deep").pack(side="left", padx=5)
        ttk.Radiobutton(f_mode, text="快速泛读 (Skim)", variable=var_mode, value="skim").pack(side="left", padx=5)

        # 4. 数量
        f_count = ttk.Frame(frame); f_count.pack(fill="x", pady=2)
        ttk.Label(f_count, text="摘取数量:", width=10).pack(side="left")
        spin_count = ttk.Spinbox(f_count, from_=1, to=50, width=5)
        spin_count.set(conf.get('count', 3))
        spin_count.pack(side="left")

        # 保存引用
        self.journal_vars[key] = {
            'enabled': var_enabled,
            'type': combo_type,
            'mode': var_mode,
            'count': spin_count
        }

    def start_thread(self):
        self.save_config()
        self.btn_run.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        t = threading.Thread(target=self.run_task)
        t.daemon = True
        t.start()

    def run_task(self):
        try:
            print(f"[{datetime.datetime.now().time()}] 🚀 任务启动...")
            run_scraper_logic()
            print(f"\n✨ 任务完成！")
            messagebox.showinfo("成功", "采集完成，请查看 output 文件夹。")
        except Exception as e:
            print(f"❌ 错误: {e}")
            messagebox.showerror("错误", str(e))
        finally:
            self.root.after(0, lambda: self.btn_run.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = AcademicPulseGUI(root)
    root.mainloop()