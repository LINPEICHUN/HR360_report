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
    api_key: str,
    api_provider: str,
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

    Returns:
        完整的 ReportData
    """
    # 1. 解析檔案
    df = parse_uploaded_file(file_content, filename)

    # 2. 分群
    self_df, others_df = split_by_role(df)

    # 3. 計算分數
    dimensions = calculate_all_scores(self_df, others_df)

    # 4. 提取質性回饋
    qualitative = extract_qualitative_feedback(self_df, others_df)

    # 5. 提取其他回饋
    other_self, other_others = extract_other_feedback(self_df, others_df)

    # 6. 提取共事意願
    collab_self, collab_others, collab_avg = extract_collaboration_scores(
        self_df, others_df
    )

    # 7. 組裝初始報告資料（不含 LLM 分析）
    report_data = ReportData(
        name=name,
        grade=grade,
        purpose=purpose,
        generated_at=datetime.now().strftime("%Y 年 %m 月 %d 日"),
        dimensions=dimensions,
        qualitative=qualitative,
        other_feedback_self=other_self,
        other_feedback_others=other_others,
        collaboration_self=collab_self,
        collaboration_others=collab_others,
        collaboration_average=collab_avg,
    )

    # 8. LLM 分析
    if api_key and api_key.strip():
        import markdown
        llm_result = await run_llm_analysis(api_key, api_provider, report_data)
        # 將 Markdown 轉為 HTML
        report_data.llm_analysis = markdown.markdown(llm_result)

    return report_data
