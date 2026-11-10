# Payload Dict Generator

规则驱动的 Web 安全测试 Payload 字典生成器，支持 URL / Form / JSON 三种输出格式与 HPP（HTTP 参数污染）专项场景，可直出 Burp Intruder 可用字典。

## 功能特性

- **规则外置**：35+ 条变异策略以 YAML 配置管理，新增测试向量零代码改动
- **三维过滤**：输出格式 × HPP 模式 × 启用状态，自动筛选适用规则
- **占位符模板引擎**：`{param}` `{param_upper}` `{param_lower}` `{value}` `{extra}` 动态渲染
- **双模式**：GUI 交互生成 / 命令行直接调用
- **一键导出**：TXT 文件、Burp Intruder 列表

## 环境要求

- Python 3.8+
- tkinter（Python 标准库自带，Linux 需 `sudo apt install python3-tk`）

## 使用

直接运行 `main.py` 即可启动 GUI 界面：

生成的字典直接使用bp的intruder模块进行爆破使用

![dd55c70d-8787-4276-bcdd-3181111e301b](file:///C:/Users/%E5%88%98%E6%AF%85%E8%B1%AA/Pictures/Typedown/dd55c70d-8787-4276-bcdd-3181111e301b.png)
