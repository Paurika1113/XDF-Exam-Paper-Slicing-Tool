"""XDFclier — step 3: diagnose import"""
import sys, os, traceback

_cli_dir = os.path.join(os.path.dirname(__file__), "..", "cli")
_cli_dir = os.path.normpath(_cli_dir)
if _cli_dir not in sys.path:
    sys.path.insert(0, _cli_dir)

# Try import
_cli_ok = False
_import_detail = ""
try:
    from main import app as fastapi_app
    _cli_ok = True
    _import_detail = "ok"
    # Check routes
    _routes = [r.path for r in fastapi_app.routes]
    _import_detail = "routes: " + ", ".join(_routes[:10])
except Exception as e:
    _import_detail = traceback.format_exc()[-500:]

from fastapi import FastAPI
from fastapi.responses import JSONResponse

if _cli_ok:
    app = fastapi_app
else:
    app = FastAPI()

# Always add a diagnostic endpoint
@app.get("/api/diag")
async def diag():
    return {
        "cli_import_ok": _cli_ok,
        "detail": _import_detail
    }

@app.exception_handler(Exception)
async def handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)[:300]})
