"""
報告資料組裝模組

將解析後的資料組裝為完整的 ReportData，
供模板渲染使用。
"""
from datetime import datetime
from ..models.schemas import ReportData
from .data_parser import parse_uploaded_file, split_by_role
from .score_calculator import (
    calculate_all_scores,
    extract_qualitative_feedback,
    extract_other_feedback,
    extract_collaboration_scores,
)
from .llm_analyzer import run_llm_analysis


async def generate_report(
    file_content: bytes,
    filename: str,
    name: str,
    grade: str,
    purpose: str,
    api_key: str = "",
    api_provider: str = "gemini",
    model: str = "gemini-1.5-flash",
    focus_keywords: str = "",
) -> ReportData:
    """
    完整的報告生成 Pipeline。

    流程：
    1. 解析上傳檔案
    2. 分群（自評 vs 他評）
    3. 計算所有分數
    4. 提取質性回饋
    5. 呼叫 LLM 分析
    6. 組裝 ReportData

    Args:
        file_content: 上傳檔案二進位內容
        filename: 原始檔名
        name: 受評者姓名
        grade: 職級
        purpose: 管理目的
        api_key: LLM API Key
        api_provider: LLM API 提供者
        focus_keywords: HRBP 指定的質性焦點關鍵字

    Returns:
        完整的 ReportData
    """
    # 1. 解析檔案
    df = parse_uploaded_file(file_content, filename)

    # 2. 分群
    self_df, others_df = split_by_role(df)

    # 3. 計算分數
    dimensions = calculate_all_scores(self_df, others_df, grade)

    # 4. 提取質性回饋
    qualitative = extract_qualitative_feedback(self_df, others_df, grade)

    # 5. 提取其他回饋
    other_data = extract_other_feedback(self_df, others_df, grade)

    # 6. 提取共事意願
    collab_data = extract_collaboration_scores(self_df, others_df, grade)

    # 7. 組裝初始報告資料（不含 LLM 分析）
    report_data = ReportData(
        name=name,
        grade=grade,
        purpose=purpose,
        generated_at=datetime.now().strftime("%Y 年 %m 月 %d 日"),
        dimensions=dimensions,
        qualitative=qualitative,
        other_feedback_self=other_data["self"],
        other_feedback_others=other_data["others"],
        other_feedback_manager=other_data["manager"],
        other_feedback_peer=other_data["peer"],
        other_feedback_subordinate=other_data["subordinate"],
        collaboration_self=collab_data["self"],
        collaboration_others=collab_data["others"],
        collaboration_average=collab_data["others_avg"],
        collaboration_manager=collab_data["manager"],
        collaboration_peer=collab_data["peer"],
        collaboration_peer_average=collab_data["peer_avg"],
        collaboration_subordinate=collab_data["subordinate"],
        collaboration_subordinate_average=collab_data["subordinate_avg"],
        focus_keywords=focus_keywords,
    )

    # 7.5. 如果 api_key 為空，嘗試載入全域管理員配置
    if not api_key or not api_key.strip():
        import json
        from pathlib import Path
        config_path = Path(__file__).resolve().parent.parent / "admin_config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    api_key = config.get("api_key", "")
                    api_provider = config.get("api_provider", "gemini")
                    model = config.get("model", "gemini-1.5-flash")
            except Exception:
                pass

    # 8. LLM 分析
    if api_key and api_key.strip():
        import markdown
        llm_result = await run_llm_analysis(api_key, api_provider, report_data, model)
        # 將 Markdown 轉為 HTML
        report_data.llm_analysis = markdown.markdown(llm_result)

    return report_data
