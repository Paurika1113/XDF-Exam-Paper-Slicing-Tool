"""XDFclier — test cli import"""
import sys, os, traceback

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# Set up path
_cli_dir = os.path.join(os.path.dirname(__file__), "..", "cli")
_cli_dir = os.path.normpath(_cli_dir)
if _cli_dir not in sys.path:
    sys.path.insert(0, _cli_dir)

# Try import
_cli_ok = False
_import_err = ""
try:
    from main import app as fastapi_app
    _cli_ok = True
except Exception as e:
    _import_err = str(e)[:200]

if _cli_ok:
    app = fastapi_app

@app.get("/api/t2")
async def t2():
    return {"cli_ok": _cli_ok, "import_err": _import_err, "cli_dir": _cli_dir}

@app.exception_handler(Exception)
async def handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)[:300]})
