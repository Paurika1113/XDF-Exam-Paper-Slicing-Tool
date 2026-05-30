"""XDFclier — minimal test"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/ping")
async def ping():
    return {"status": "ok", "version": "minimal"}

@app.exception_handler(Exception)
async def handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)[:300]})
