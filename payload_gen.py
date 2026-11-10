import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import yaml
import base64
from urllib.parse import quote


# ==================== 引擎核心 ====================
class PayloadEngine:
    def __init__(self, rules_file="rules.yaml"):
        self.rules_file = rules_file
        self.rules = []
        self.load_rules()

    def load_rules(self):
        # rules.yaml 必定存在，直接读取
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.rules = data.get('rules', [])

    def _json_style_to_url_style(self, payload):
        """将 JSON 键值对风格转换为 url/form 键值对风格"""
        # 去掉最外层花括号（如果有）
        payload = payload.replace('{', '').replace('}', '')
        # 冒号替换为等号
        payload = payload.replace(':', '=')
        # 删除所有双引号和单引号
        payload = payload.replace('"', '').replace("'", '')
        return payload

    def generate(self, param, value, format_choice, hpp_mode=False, extra=""):
        results = []
        for rule in self.rules:
            if not rule.get('enabled', True):
                continue
            if format_choice not in rule.get('formats', []):
                continue
            if hpp_mode and not rule.get('hpp', False):
                continue
            if not hpp_mode and rule.get('hpp', False):
                continue

            template = rule['template']
            payload = template
            payload = payload.replace('{param}', param)
            payload = payload.replace('{param_upper}', param.upper())
            payload = payload.replace('{param_lower}', param.lower())
            payload = payload.replace('{value}', value)
            if '{extra}' in template:
                payload = payload.replace('{extra}', extra)

            # URL / Form 格式自动转为 id=value 风格
            if format_choice in ('url', 'form'):
                payload = self._json_style_to_url_style(payload)

            encode_type = rule.get('encode', 'none')
            if encode_type == 'url_encode':
                payload = quote(payload)
            elif encode_type == 'json_escape':
                payload = payload.replace('"', '\\"')
            elif encode_type == 'base64':
                payload = base64.b64encode(payload.encode()).decode()

            results.append(payload)
        return results


# ==================== GUI 界面 ====================
class PayloadGenGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("参数化 Payload 字典生成器 v1.0")
        self.root.geometry("800x650")
        self.root.resizable(True, True)

        self.engine = PayloadEngine()
        self._build_ui()
        self._refresh_rule_list()

    def _build_ui(self):
        # 顶部输入区
        frm_top = ttk.LabelFrame(self.root, text="输入参数", padding=10)
        frm_top.pack(fill="x", padx=10, pady=5)

        ttk.Label(frm_top, text="参数名:").grid(row=0, column=0, sticky="w")
        self.param_var = tk.StringVar(value="id")
        ttk.Entry(frm_top, textvariable=self.param_var, width=20).grid(row=0, column=1, padx=5)

        ttk.Label(frm_top, text="参数值:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.value_var = tk.StringVar(value="123")
        ttk.Entry(frm_top, textvariable=self.value_var, width=20).grid(row=0, column=3, padx=5)

        ttk.Label(frm_top, text="额外值(HPP/拼接):").grid(row=1, column=0, sticky="w", pady=5)
        self.extra_var = tk.StringVar(value="124")
        self.extra_entry = ttk.Entry(frm_top, textvariable=self.extra_var, width=20)
        self.extra_entry.grid(row=1, column=1, padx=5, pady=5)

        # 选项区
        frm_opt = ttk.LabelFrame(self.root, text="生成选项", padding=10)
        frm_opt.pack(fill="x", padx=10, pady=5)

        ttk.Label(frm_opt, text="格式:").grid(row=0, column=0, sticky="w")
        self.format_var = tk.StringVar(value="json")
        self.format_combo = ttk.Combobox(frm_opt, textvariable=self.format_var, width=15,
                                         values=["url", "form", "json"], state="readonly")
        self.format_combo.grid(row=0, column=1, padx=5)
        self.format_combo.bind("<<ComboboxSelected>>",
                               lambda e: (self._refresh_rule_list(), self._update_json_quote_state()))

        self.hpp_var = tk.BooleanVar()
        self.hpp_check = ttk.Checkbutton(frm_opt, text="开启 HPP 参数污染模式", variable=self.hpp_var,
                                         command=self._on_hpp_toggle)
        self.hpp_check.grid(row=0, column=2, padx=20)

        ttk.Button(frm_opt, text="🔄 重新加载规则文件", command=self._refresh_rule_list).grid(row=0, column=3, padx=10)
        ttk.Button(frm_opt, text="📝 打开 rules.yaml 编辑", command=self._open_rules).grid(row=0, column=4, padx=10)

        # JSON引号选项
        self.json_quote_var = tk.BooleanVar(value=True)
        self.json_quote_check = ttk.Checkbutton(frm_opt, text="JSON值带引号", variable=self.json_quote_var)
        self.json_quote_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # 规则列表
        frm_rules = ttk.LabelFrame(self.root, text="可用规则", padding=5)
        frm_rules.pack(fill="both", expand=False, padx=10, pady=5)

        columns = ("enabled", "name", "hpp", "formats")
        self.tree = ttk.Treeview(frm_rules, columns=columns, show="headings", height=8)
        self.tree.heading("enabled", text="启用")
        self.tree.heading("name", text="规则名称")
        self.tree.heading("hpp", text="HPP")
        self.tree.heading("formats", text="适用格式")
        self.tree.column("enabled", width=50, anchor="center")
        self.tree.column("name", width=300)
        self.tree.column("hpp", width=60, anchor="center")
        self.tree.column("formats", width=150)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # 按钮区
        frm_btn = ttk.Frame(self.root)
        frm_btn.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btn, text="🚀 开始生成字典", command=self._generate).pack(side="left", padx=5)
        ttk.Button(frm_btn, text="📋 复制全部结果", command=self._copy).pack(side="left", padx=5)
        ttk.Button(frm_btn, text="💾 导出为 TXT", command=self._export).pack(side="left", padx=5)
        ttk.Button(frm_btn, text="📤 导出 Burp 列表", command=self._export_burp).pack(side="left", padx=5)

        # 输出区
        frm_out = ttk.LabelFrame(self.root, text="生成结果", padding=5)
        frm_out.pack(fill="both", expand=True, padx=10, pady=5)
        self.output = scrolledtext.ScrolledText(frm_out, wrap=tk.WORD, font=("Consolas", 10))
        self.output.pack(fill="both", expand=True)

        self._on_hpp_toggle()
        self._update_json_quote_state()

    def _update_json_quote_state(self):
        if self.format_var.get() == 'json':
            self.json_quote_check.config(state='normal')
        else:
            self.json_quote_check.config(state='disabled')

    def _on_hpp_toggle(self):
        state = "normal" if self.hpp_var.get() else "disabled"
        self.extra_entry.config(state=state)
        self._refresh_rule_list()

    def _refresh_rule_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        fmt = self.format_var.get()
        hpp = self.hpp_var.get()
        for rule in self.engine.rules:
            if fmt not in rule.get('formats', []):
                continue
            if hpp and not rule.get('hpp', False):
                continue
            if not hpp and rule.get('hpp', False):
                continue
            enabled = "✅" if rule.get('enabled', True) else "❌"
            hpp_tag = "✅" if rule.get('hpp', False) else ""
            self.tree.insert("", "end", iid=rule['id'],
                             values=(enabled, rule['name'], hpp_tag, ", ".join(rule.get('formats', []))))

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            col = self.tree.identify_column(event.x)
            if col == "#1":
                item = self.tree.identify_row(event.y)
                if item:
                    for rule in self.engine.rules:
                        if rule['id'] == item:
                            rule['enabled'] = not rule.get('enabled', True)
                            break
                    self._refresh_rule_list()

    def _remove_json_value_quotes(self, text):
        """删除 JSON 值引号，支持简单值和数组值"""
        out = []
        i = 0
        n = len(text)
        while i < n:
            c = text[i]
            if c == ':':
                out.append(c)
                i += 1
                # 跳过冒号后的空白
                while i < n and text[i] in ' \t':
                    i += 1

                # 简单字符串值："value"
                if i < n and text[i] == '"':
                    j = i + 1
                    while j < n:
                        if text[j] == '\\':
                            j += 2
                            continue
                        if text[j] == '"':
                            break
                        j += 1
                    if j < n:
                        out.extend(text[i+1:j])  # 去掉两端引号
                        i = j + 1
                        continue
                    else:
                        out.extend(text[i:])
                        i = n
                        continue

                # 数组值：[ "value1", "value2" ]
                elif i < n and text[i] == '[':
                    out.append('[')
                    i += 1
                    while i < n:
                        # 跳过数组内空白
                        while i < n and text[i] in ' \t':
                            i += 1

                        if i < n and text[i] == '"':
                            j = i + 1
                            while j < n:
                                if text[j] == '\\':
                                    j += 2
                                    continue
                                if text[j] == '"':
                                    break
                                j += 1
                            if j < n:
                                out.extend(text[i+1:j])  # 去掉元素引号
                                i = j + 1
                                continue
                            else:
                                out.extend(text[i:])
                                i = n
                                break

                        elif i < n and text[i] == ',':
                            out.append(',')
                            i += 1

                        elif i < n and text[i] == ']':
                            out.append(']')
                            i += 1
                            break

                        else:
                            # 数字、null、true 等直接保留
                            out.append(text[i])
                            i += 1
                    continue

                else:
                    # 非字符串非数组值，继续正常扫描
                    continue

            else:
                out.append(c)
                i += 1

        return ''.join(out)

    def _generate(self):
        param = self.param_var.get().strip()
        value = self.value_var.get().strip()
        extra = self.extra_var.get().strip()
        fmt = self.format_var.get()
        hpp = self.hpp_var.get()
        json_quote = self.json_quote_var.get()

        if not param or not value:
            messagebox.showwarning("提示", "参数名和参数值不能为空！")
            return

        # 1. 引擎正常生成带引号的结果
        results = self.engine.generate(param, value, fmt, hpp, extra)

        # 2. JSON 格式时统一处理后输出
        if fmt == 'json':
            processed_results = []
            for r in results:
                # 还原 json_escape 的转义引号
                r = r.replace('\\"', '"')
                # 取消“JSON值带引号”时，删除值引号
                if not json_quote:
                    r = self._remove_json_value_quotes(r)
                processed_results.append(r)
            results = processed_results

        # 3. 输出
        self.output.delete("1.0", tk.END)
        if results:
            self.output.insert(tk.END, f"# 共生成 {len(results)} 条 payload\n")
            self.output.insert(tk.END, "# " + "=" * 50 + "\n")
            for r in results:
                self.output.insert(tk.END, r + "\n")
        else:
            self.output.insert(tk.END, "没有匹配的规则，请检查格式和 HPP 设置。")

    def _copy(self):
        text = self.output.get("1.0", tk.END).strip()
        if not text:
            return
        payload_lines = [l for l in text.split('\n') if not l.startswith('#') and l.strip()]
        if not payload_lines:
            messagebox.showwarning("提示", "没有可复制的 payload！")
            return
        payload_text = '\n'.join(payload_lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(payload_text)
        messagebox.showinfo("成功", f"已复制 {len(payload_lines)} 条 payload 到剪贴板！")

    def _export(self):
        text = self.output.get("1.0", tk.END).strip()
        if not text:
            return
        payload_lines = [l for l in text.split('\n') if not l.startswith('#') and l.strip()]
        if not payload_lines:
            messagebox.showwarning("提示", "没有可导出的 payload！")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                for line in payload_lines:
                    f.write(line + '\n')
            messagebox.showinfo("成功", f"已导出 {len(payload_lines)} 条 payload 到 {path}")

    def _export_burp(self):
        text = self.output.get("1.0", tk.END).strip()
        lines = [l for l in text.split('\n') if not l.startswith('#') and l.strip()]
        if not lines:
            messagebox.showwarning("提示", "没有可导出的 payload！")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Burp Payload List", "*.txt")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                for line in lines:
                    f.write(line + '\n')
            messagebox.showinfo("成功", f"已导出 {len(lines)} 条 payload 到 {path}\n可直接在 Burp Intruder 中 Load 此文件")

    def _open_rules(self):
        if os.path.exists(self.engine.rules_file):
            os.startfile(self.engine.rules_file)
        else:
            messagebox.showerror("错误", "rules.yaml 不存在！")


# ==================== 主入口 ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = PayloadGenGUI(root)
    root.mainloop()