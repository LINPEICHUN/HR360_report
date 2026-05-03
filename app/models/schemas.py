"""
Pydantic 資料模型定義
"""
from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class ReportRequest(BaseModel):
    """報告產生請求參數"""
    name: str                                           # 受評者姓名
    grade: Literal["L0", "L1"]                          # 職級
    purpose: str                                        # 管理目的
    api_key: str                                        # LLM API Key
    api_provider: Literal["gemini", "openai"]           # API 提供者


class QuestionScore(BaseModel):
    """單一題目的分數資料"""
    question_keyword: str                               # 題目關鍵字（如「組建團隊」）
    question_full: str                                  # 完整題目名稱
    question_en: str                                    # 英文名稱
    dimension: str                                      # 所屬面向
    self_score: float | None = None                     # 自評分數
    others_average: float | None = None                 # 他評平均分
    individual_scores: list[float | None] = []          # 隨機化個別分數


class DimensionSummary(BaseModel):
    """面向摘要"""
    dimension: str                                      # 面向名稱
    dimension_en: str                                   # 面向英文名稱
    self_average: float | None = None                   # 該面向自評平均
    others_average: float | None = None                 # 該面向他評平均
    questions: list[QuestionScore] = []                 # 該面向所有題目


class QualitativeFeedback(BaseModel):
    """質性回饋"""
    dimension: str                                      # 所屬面向
    positive_self: str = ""                             # 自評 - 做得好的
    positive_others: list[str] = []                     # 他評 - 做得好的
    improve_self: str = ""                              # 自評 - 建議改善的
    improve_others: list[str] = []                      # 他評 - 建議改善的


class ReportData(BaseModel):
    """完整報告資料"""
    # 基本資訊
    name: str
    grade: str
    purpose: str
    generated_at: str                                   # 報告生成日期

    # 分數資料
    dimensions: list[DimensionSummary] = []             # 各面向分數摘要

    # 質性回饋
    qualitative: list[QualitativeFeedback] = []         # 各面向質性回饋
    other_feedback_self: str = ""                        # 自評其他回饋
    other_feedback_others: list[str] = []                # 他評其他回饋

    # 繼續共事意願
    collaboration_self: int | None = None                # 自評共事意願
    collaboration_others: list[int] = []                 # 他評共事意願
    collaboration_average: float | None = None           # 他評共事意願平均

    # LLM 分析結果
    llm_analysis: str = ""                               # LLM 生成的管理建議
