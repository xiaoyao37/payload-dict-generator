#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心引擎模块（与 GUI 解耦，方便在无 tkinter 环境下单独测试和复用）
"""

import os
import base64
import html
import urllib.parse

import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_FILE = os.path.join(BASE_DIR, "rules.yaml")


def load_rules(path=RULES_FILE):
    """加载规则文件，返回启用且字段完整的规则列表"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到规则文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    rules = data.get("rules", [])
    valid = []
    for r in rules:
        if not r.get("enabled", True):
            continue
        if "id" not in r or "template" not in r:
            print(f"[!] 跳过无效规则（缺少 id 或 template）: {r}")
            continue
        valid.append(r)
    return valid


def apply_template(rule, param, value, extra):
    """占位符替换（注意顺序，避免二次替换）"""
    tpl = rule["template"]
    replacements = [
        ("{param_upper}", param.upper()),
        ("{param_lower}", param.lower()),
        ("{param_camel}", param[:1].upper() + param[1:].lower() if param else ""),
        ("{extra}", extra if extra else ""),
        ("{value}", value if value else ""),
        ("{param}", param if param else ""),
    ]
    for placeholder, real in replacements:
        tpl = tpl.replace(placeholder, real)
    return tpl


def apply_encoding(text, encode_type):
    """按规则指定的编码方式做二次处理"""
    if encode_type == "url_encode":
        return urllib.parse.quote(text, safe="=&:;,[]/(){}")
    elif encode_type == "url_all":
        return urllib.parse.quote(text, safe="")
    elif encode_type == "json_escape":
        return text.replace("\\", "\\\\").replace('"', '\\"')
    elif encode_type == "html_escape":
        return html.escape(text, quote=True)
    elif encode_type == "base64":
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")
    else:
        return text


def generate(rule, param, value, extra):
    """对单条规则：占位符替换 -> 编码"""
    result = apply_template(rule, param, value, extra)
    result = apply_encoding(result, rule.get("encode", "none"))
    return result
