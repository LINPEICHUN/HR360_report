"""
分數計算與聚合模組

負責從解析後的資料中：
1. 提取各題自評分數
2. 計算他評平均分
3. 產生隨機排列的個別分數列表（保護匿名性）
4. 按面向聚合計算
"""
import random
import pandas as pd
from ..config import DIMENSIONS, COLLABORATION_KEYWORD, OTHER_FEEDBACK_KEYWORD
from ..models.schemas import QuestionScore, DimensionSummary, QualitativeFeedback
from .data_parser import convert_score_value, find_column_by_keyword


def calculate_all_scores(
    self_df: pd.DataFrame,
    others_df: pd.DataFrame,
) -> list[DimensionSummary]:
    """
    計算所有面向、所有題目的分數摘要。

    Args:
        self_df: 自評 DataFrame（通常只有 1 筆）
        others_df: 他評 DataFrame（多筆）

    Returns:
        各面向的分數摘要列表
    """
    dimension_summaries = []

    for dim_name, dim_config in DIMENSIONS.items():
        questions = []

        for q in dim_config["questions"]:
            # 找到對應欄位
            col = find_column_by_keyword(self_df, q["keyword"])
            if col is None:
                continue

            # 自評分數
            self_score = None
            if not self_df.empty:
                raw = self_df.iloc[0].get(col)
                self_score = convert_score_value(raw)

            # 他評個別分數
            individual_scores = []
            if not others_df.empty:
                for _, row in others_df.iterrows():
                    score = convert_score_value(row.get(col))
                    individual_scores.append(score)

            # 隨機打亂順序（保護匿名性）
            random.shuffle(individual_scores)

            # 計算他評平均（排除 None）
            valid_scores = [s for s in individual_scores if s is not None]
            others_avg = (
                round(sum(valid_scores) / len(valid_scores), 2)
                if valid_scores else None
            )

            questions.append(QuestionScore(
                question_keyword=q["keyword"],
                question_full=q["full_name"],
                question_en=q["name_en"],
                dimension=dim_name,
                self_score=self_score,
                others_average=others_avg,
                individual_scores=individual_scores,
            ))

        # 計算面向平均
        self_scores = [q.self_score for q in questions if q.self_score is not None]
        others_avgs = [q.others_average for q in questions if q.others_average is not None]

        dim_self_avg = (
            round(sum(self_scores) / len(self_scores), 2) if self_scores else None
        )
        dim_others_avg = (
            round(sum(others_avgs) / len(others_avgs), 2) if others_avgs else None
        )

        dimension_summaries.append(DimensionSummary(
            dimension=dim_name,
            dimension_en=dim_config["label_en"],
            self_average=dim_self_avg,
            others_average=dim_others_avg,
            questions=questions,
        ))

    return dimension_summaries


def extract_qualitative_feedback(
    self_df: pd.DataFrame,
    others_df: pd.DataFrame,
) -> list[QualitativeFeedback]:
    """
    提取各面向的質性回饋。

    Returns:
        各面向的質性回饋列表
    """
    feedbacks = []

    for dim_name, dim_config in DIMENSIONS.items():
        pos_keyword = dim_config["qualitative_positive_keyword"]
        imp_keyword = dim_config["qualitative_improve_keyword"]

        # 找到對應欄位
        pos_col = find_column_by_keyword(self_df, pos_keyword)
        imp_col = find_column_by_keyword(self_df, imp_keyword)

        # 自評質性回饋
        positive_self = ""
        improve_self = ""
        if not self_df.empty:
            if pos_col:
                val = self_df.iloc[0].get(pos_col)
                positive_self = str(val).strip() if pd.notna(val) else ""
            if imp_col:
                val = self_df.iloc[0].get(imp_col)
                improve_self = str(val).strip() if pd.notna(val) else ""

        # 他評質性回饋（收集後隨機打亂）
        positive_others = []
        improve_others = []
        if not others_df.empty:
            if pos_col:
                for _, row in others_df.iterrows():
                    val = row.get(pos_col)
                    if pd.notna(val) and str(val).strip():
                        positive_others.append(str(val).strip())
            if imp_col:
                for _, row in others_df.iterrows():
                    val = row.get(imp_col)
                    if pd.notna(val) and str(val).strip():
                        improve_others.append(str(val).strip())

        # 隨機打亂順序保護匿名
        random.shuffle(positive_others)
        random.shuffle(improve_others)

        feedbacks.append(QualitativeFeedback(
            dimension=dim_name,
            positive_self=positive_self,
            positive_others=positive_others,
            improve_self=improve_self,
            improve_others=improve_others,
        ))

    return feedbacks


def extract_other_feedback(
    self_df: pd.DataFrame,
    others_df: pd.DataFrame,
) -> tuple[str, list[str]]:
    """
    提取「其他回饋與建議」欄位。

    Returns:
        (自評其他回饋, 他評其他回饋列表)
    """
    col = find_column_by_keyword(self_df, OTHER_FEEDBACK_KEYWORD)

    self_feedback = ""
    others_feedback = []

    if col:
        if not self_df.empty:
            val = self_df.iloc[0].get(col)
            self_feedback = str(val).strip() if pd.notna(val) else ""

        if not others_df.empty:
            for _, row in others_df.iterrows():
                val = row.get(col)
                if pd.notna(val) and str(val).strip():
                    others_feedback.append(str(val).strip())

    random.shuffle(others_feedback)
    return self_feedback, others_feedback


def extract_collaboration_scores(
    self_df: pd.DataFrame,
    others_df: pd.DataFrame,
) -> tuple[int | None, list[int], float | None]:
    """
    提取「繼續共事意願」分數。

    Returns:
        (自評分數, 他評分數列表, 他評平均)
    """
    col = find_column_by_keyword(self_df, COLLABORATION_KEYWORD)

    self_score = None
    others_scores = []

    if col:
        if not self_df.empty:
            val = self_df.iloc[0].get(col)
            try:
                self_score = int(val) if pd.notna(val) else None
            except (ValueError, TypeError):
                self_score = None

        if not others_df.empty:
            for _, row in others_df.iterrows():
                val = row.get(col)
                try:
                    if pd.notna(val):
                        others_scores.append(int(val))
                except (ValueError, TypeError):
                    pass

    random.shuffle(others_scores)
    avg = (
        round(sum(others_scores) / len(others_scores), 2)
        if others_scores else None
    )

    return self_score, others_scores, avg
