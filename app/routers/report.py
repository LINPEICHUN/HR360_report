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

# 各平台支援大模型清單
MODELS = {
    "davinci": [
        {"value": "gpt-4o-mini", "label": "GPT-4o Mini (最推薦)"},
        {"value": "gpt-4o", "label": "GPT-4o 旗艦模型"},
        {"value": "gemini-3-flash", "label": "Gemini 3.0 Flash"},
        {"value": "deepseek-r1-0528", "label": "DeepSeek R1 推理模型"},
        {"value": "deepseek-v3-2", "label": "DeepSeek V3 旗艦模型"},
        {"value": "gpt-o3-mini", "label": "GPT-o3 Mini 推理模型"},
        {"value": "gpt-5", "label": "GPT-5 (搶先體驗)"}
    ],
    "gemini": [
        {"value": "gemini-1.5-flash", "label": "Gemini 1.5 Flash (預設)"},
        {"value": "gemini-2.0-flash", "label": "Gemini 2.0 Flash"},
        {"value": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
        {"value": "gemini-1.5-pro", "label": "Gemini 1.5 Pro"}
    ],
    "openai": [
        {"value": "gpt-4o-mini", "label": "GPT-4o Mini (預設)"},
        {"value": "gpt-4o", "label": "GPT-4o"}
    ]
}
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
    api_provider: str = Form(""),
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


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理員後台設定頁面"""
    config = {
        "api_provider": "gemini",
        "api_key": "",
        "model": "gemini-1.5-flash"
    }
    config_path = BASE_DIR / "admin_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

    # 將 API_PROVIDERS 加入 "Moxa DaVinci" 的標籤供管理員選取
    extended_providers = API_PROVIDERS.copy()
    if not any(p["value"] == "davinci" for p in extended_providers):
        extended_providers.append({"value": "davinci", "label": "Moxa DaVinci 達哥"})

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "config": config,
            "purposes": MANAGEMENT_PURPOSES,
            "grades": GRADES,
            "api_providers": extended_providers,
            "models_json": json.dumps(MODELS, ensure_ascii=False)
        },
    )


@router.post("/api/admin/config", response_class=HTMLResponse)
async def save_admin_config(
    request: Request,
    api_provider: str = Form(...),
    api_key: str = Form(""),
    model: str = Form(...),
):
    """儲存管理員後台設定"""
    config = {
        "api_provider": api_provider,
        "api_key": api_key,
        "model": model
    }
    config_path = BASE_DIR / "admin_config.json"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        success = "設定已成功儲存！"
        error = None
    except Exception as e:
        success = None
        error = f"設定儲存失敗：{str(e)}"

    extended_providers = API_PROVIDERS.copy()
    if not any(p["value"] == "davinci" for p in extended_providers):
        extended_providers.append({"value": "davinci", "label": "Moxa DaVinci 達哥"})

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "config": config,
            "purposes": MANAGEMENT_PURPOSES,
            "grades": GRADES,
            "api_providers": extended_providers,
            "models_json": json.dumps(MODELS, ensure_ascii=False),
            "success": success,
            "error": error
        },
    )
