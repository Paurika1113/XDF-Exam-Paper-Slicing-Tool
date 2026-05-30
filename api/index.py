"""XDFclier — diagnose import with minimal deps"""
import sys, os, traceback

# Try importing from cli (will fail if deps missing, that's ok)
_cli_ok = False
_import_detail = "not attempted"

_cli_dir = os.path.join(os.path.dirname(__file__), "..", "cli")
_cli_dir = os.path.normpath(_cli_dir)
if _cli_dir not in sys.path:
    sys.path.insert(0, _cli_dir)

try:
    from main import app as fastapi_app
    _cli_ok = True
    _routes = [r.path for r in fastapi_app.routes]
    _import_detail = "routes: " + ", ".join(_routes[:15])
except Exception as e:
    _import_detail = traceback.format_exc()[-500:]

from fastapi import FastAPI
from fastapi.responses import JSONResponse

if _cli_ok:
    app = fastapi_app
else:
    app = FastAPI()

@app.get("/api/diag")
async def diag():
    return {"cli_import_ok": _cli_ok, "detail": _import_detail}

@app.exception_handler(Exception)
async def handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)[:300]})
