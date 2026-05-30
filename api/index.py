"""XDFclier — step 2: test cli import"""
import sys, os, traceback

_cli_import_error = None

# Try to import cli/main
_cli_dir = os.path.join(os.path.dirname(__file__), "..", "cli")
_cli_dir = os.path.normpath(_cli_dir)
if _cli_dir not in sys.path:
    sys.path.insert(0, _cli_dir)

try:
    from main import app as fastapi_app
    _cli_ok = True
except Exception as e:
    _cli_ok = False
    _cli_import_error = traceback.format_exc()

from fastapi import FastAPI
from fastapi.responses import JSONResponse

if _cli_ok:
    app = fastapi_app
else:
    app = FastAPI()

    @app.get("/api/ping")
    async def ping():
        return {
            "status": "error",
            "cli_import": False,
            "error": _cli_import_error[-500:] if _cli_import_error else "unknown"
        }

    @app.exception_handler(Exception)
    async def handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": str(exc)[:300]})
