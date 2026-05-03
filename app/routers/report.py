"""
報告相關 API 路由

提供首頁渲染與報告生成 API。
"""
import json
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from ..config import MANAGEMENT_PURPOSES, GRADES, API_PROVIDERS, RATING_SCALE
from ..services.report_generator import generate_report

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首頁：設定面板"""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "purposes": MANAGEMENT_PURPOSES,
            "grades": GRADES,
            "api_providers": API_PROVIDERS,
        },
    )


@router.post("/api/generate-report", response_class=HTMLResponse)
async def generate_report_api(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    grade: str = Form(...),
    purpose: str = Form(...),
    api_key: str = Form(""),
    api_provider: str = Form("gemini"),
):
    """
    產生 360 回饋報告。

    接收表單參數與上傳檔案，執行完整的報告生成 Pipeline，
    回傳渲染完成的報告 HTML。
    """
    # 讀取上傳檔案
    file_content = await file.read()
    filename = file.filename or "uploaded.xlsx"

    try:
        # 執行報告生成
        report_data = await generate_report(
            file_content=file_content,
            filename=filename,
            name=name,
            grade=grade,
            purpose=purpose,
            api_key=api_key,
            api_provider=api_provider,
        )

        # 將 Pydantic model 序列化為純 Python dict，供 Jinja2 tojson 使用
        # （避免 numpy.float64 等型別導致 JSON serializable 錯誤）
        report_dict = json.loads(report_data.model_dump_json())

        # 渲染報告模板
        return templates.TemplateResponse(
            request=request,
            name="report.html",
            context={
                "report": report_data,
                "report_dict": report_dict,
                "rating_scale": RATING_SCALE,
            },
        )

    except Exception as e:
        # 錯誤處理：回傳錯誤頁面
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "purposes": MANAGEMENT_PURPOSES,
                "grades": GRADES,
                "api_providers": API_PROVIDERS,
                "error": f"報告生成失敗：{str(e)}",
            },
        )
