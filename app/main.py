"""
FastAPI 應用入口

掛載靜態檔案、模板引擎與路由。
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .routers import report

# 取得專案根目錄
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="360 度回饋分析系統",
    description="HRBP 360 度回饋分析與自動化報告生成",
    version="1.0.0",
)

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 設定模板引擎
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 註冊路由
app.include_router(report.router)
