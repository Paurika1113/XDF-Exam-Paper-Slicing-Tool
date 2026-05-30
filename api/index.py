"""
XDFclier — Vercel Python Serverless Function

直接导出 FastAPI ASGI app，让 Vercel Python runtime 原生处理。
不再使用 Mangum（可能对文件上传兼容性有问题）。
"""
import sys
import os

# 将 cli/ 加入 Python 路径以便导入 main.py
_cli_dir = os.path.join(os.path.dirname(__file__), "..", "cli")
_cli_dir = os.path.normpath(_cli_dir)
if _cli_dir not in sys.path:
    sys.path.insert(0, _cli_dir)

# 直接导出 FastAPI app（Vercel Python 3+ 原生支持 ASGI）
from main import app
