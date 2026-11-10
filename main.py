#!/usr/bin/env python3
"""启动入口"""

import sys
import os

# 确保能找到同目录下的主模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ↓ 把这里的 payload_gen 改成你主文件的名字（不带 .py）
from payload_gen import PayloadGenGUI
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = PayloadGenGUI(root)
    root.mainloop()