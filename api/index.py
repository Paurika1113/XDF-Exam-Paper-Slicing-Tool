"""XDFclier — test sys.path only"""
import sys, os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# Just set up the path, don't import from cli yet
_cli_dir = os.path.join(os.path.dirname(__file__), "..", "cli")
_cli_dir = os.path.normpath(_cli_dir)

@app.get("/api/t1")
async def t1():
    return {"status": "ok", "cli_dir": _cli_dir}

@app.exception_handler(Exception)
async def handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)[:300]})
