"""
XDFclier — Vercel Python Serverless Function

使用 Mangum 适配 FastAPI ASGI → Vercel WSGI 运行时。
Vercel Python runtime 通过 `app` 变量自动识别 WSGI handler。
"""
import sys
import os

# 将 cli/ 加入 Python 路径以便导入 main.py
_cli_dir = os.path.join(os.path.dirname(__file__), "..", "cli")
_cli_dir = os.path.normpath(_cli_dir)
if _cli_dir not in sys.path:
    sys.path.insert(0, _cli_dir)

# 导入 FastAPI 应用实例
from main import app as fastapi_app

# Mangum 适配器：FastAPI ASGI → Vercel WSGI
from mangum import Mangum
app = Mangum(fastapi_app)
