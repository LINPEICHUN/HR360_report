"""
分數計算與聚合模組

負責從解析後的資料中：
1. 提取各題自評分數
2. 計算他評平均分（L0）以及主管、同儕、部屬細分平均分（L1）
3. 產生隨機排列的個別分數列表（保護匿名性）
4. 按面向聚合計算
"""
import random
import pandas as pd
from ..config import get_dimensions, COLLABORATION_KEYWORD, OTHER_FEEDBACK_KEYWORD
from ..models.schemas import QuestionScore, DimensionSummary, QualitativeFeedback
from .data_parser import convert_score_value, find_column_by_keyword, find_role_column


def calculate_all_scores(
    self_df: pd.DataFrame,
    others_df: pd.DataFrame,
    grade: str = "L0",
) -> list[DimensionSummary]:
    """
    計算所有面向、所有題目的分數摘要。

    Args:
        self_df: 自評 DataFrame（通常只有 1 筆）
        others_df: 他評 DataFrame（多筆）
        grade: 職級 ("L0" 或 "L1")

    Returns:
        各面向的分數摘要列表
    """
    dimension_summaries = []

    dimensions = get_dimensions(grade)
    for dim_name, dim_config in dimensions.items():
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

            # --- L0：他評總體分數 ---
            individual_scores = []
            if not others_df.empty:
                for _, row in others_df.iterrows():
                    score = convert_score_value(row.get(col))
                    individual_scores.append(score)

            random.shuffle(individual_scores)
            valid_scores = [s for s in individual_scores if s is not None]
            others_avg = (
                round(sum(valid_scores) / len(valid_scores), 2)
                if valid_scores else None
            )

            # --- L1：細分評分 (主管、同儕、部屬) ---
            manager_score = None
            peer_avg = None
            subordinate_avg = None
            peer_scores = []
            subordinate_scores = []

            if grade == "L1" and not others_df.empty:
                role_col = find_role_column(others_df)
                manager_df = others_df[others_df[role_col].str.contains("主管", na=False)]
                peers_df = others_df[others_df[role_col].str.contains("同儕|合作夥伴", na=False)]
                subordinates_df = others_df[others_df[role_col].str.contains("部屬", na=False)]

                # 主管評分 (通常為 1 筆)
                if not manager_df.empty:
                    m_val = manager_df.iloc[0].get(col)
                    manager_score = convert_score_value(m_val)

                # 同儕評分平均
                if not peers_df.empty:
                    for _, row in peers_df.iterrows():
                        s = convert_score_value(row.get(col))
                        peer_scores.append(s)
                    random.shuffle(peer_scores)
                    valid_peer = [s for s in peer_scores if s is not None]
                    peer_avg = round(sum(valid_peer) / len(valid_peer), 2) if valid_peer else None

                # 部屬評分平均
                if not subordinates_df.empty:
                    for _, row in subordinates_df.iterrows():
                        s = convert_score_value(row.get(col))
                        subordinate_scores.append(s)
                    random.shuffle(subordinate_scores)
                    valid_sub = [s for s in subordinate_scores if s is not None]
                    subordinate_avg = round(sum(valid_sub) / len(valid_sub), 2) if valid_sub else None

            questions.append(QuestionScore(
                question_keyword=q["keyword"],
                question_full=q["full_name"],
                question_en=q["name_en"],
                dimension=dim_name,
                self_score=self_score,
                others_average=others_avg,
                individual_scores=individual_scores,
                manager_score=manager_score,
                peer_average=peer_avg,
                subordinate_average=subordinate_avg,
                peer_scores=peer_scores,
                subordinate_scores=subordinate_scores,
            ))

        # --- 計算面向平均 ---
        self_scores = [q.self_score for q in questions if q.self_score is not None]
        others_avgs = [q.others_average for q in questions if q.others_average is not None]

        dim_self_avg = (
            round(sum(self_scores) / len(self_scores), 2) if self_scores else None
        )
        dim_others_avg = (
            round(sum(others_avgs) / len(others_avgs), 2) if others_avgs else None
        )

        # L1 專用面向平均
        dim_manager_avg = None
        dim_peer_avg = None
        dim_subordinate_avg = None

        if grade == "L1":
            m_scores = [q.manager_score for q in questions if q.manager_score is not None]
            p_avgs = [q.peer_average for q in questions if q.peer_average is not None]
            s_avgs = [q.subordinate_average for q in questions if q.subordinate_average is not None]

            dim_manager_avg = round(sum(m_scores) / len(m_scores), 2) if m_scores else None
            dim_peer_avg = round(sum(p_avgs) / len(p_avgs), 2) if p_avgs else None
            dim_subordinate_avg = round(sum(s_avgs) / len(s_avgs), 2) if s_avgs else None

        dimension_summaries.append(DimensionSummary(
            dimension=dim_name,
            dimension_en=dim_config["label_en"],
            self_average=dim_self_avg,
            others_average=dim_others_avg,
            questions=questions,
            manager_average=dim_manager_avg,
            peer_average=dim_peer_avg,
            subordinate_average=dim_subordinate_avg,
        ))

    return dimension_summaries


def extract_qualitative_feedback(
    self_df: pd.DataFrame,
    others_df: pd.DataFrame,
    grade: str = "L0",
) -> list[QualitativeFeedback]:
    """
    提取各面向的質性回饋。

    Returns:
        各面向的質性回饋列表
    """
    feedbacks = []

    dimensions = get_dimensions(grade)
    for dim_name, dim_config in dimensions.items():
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

        # --- L0 他評質性回饋（收集後隨機打亂） ---
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

        random.shuffle(positive_others)
        random.shuffle(improve_others)

        # --- L1 細分質性回饋 ---
        positive_manager = []
        positive_peer = []
        positive_subordinate = []
        improve_manager = []
        improve_peer = []
        improve_subordinate = []

        if grade == "L1" and not others_df.empty:
            role_col = find_role_column(others_df)
            manager_df = others_df[others_df[role_col].str.contains("主管", na=False)]
            peers_df = others_df[others_df[role_col].str.contains("同儕|合作夥伴", na=False)]
            subordinates_df = others_df[others_df[role_col].str.contains("部屬", na=False)]

            # 主管
            if pos_col and not manager_df.empty:
                for _, row in manager_df.iterrows():
                    val = row.get(pos_col)
                    if pd.notna(val) and str(val).strip():
                        positive_manager.append(str(val).strip())
            if imp_col and not manager_df.empty:
                for _, row in manager_df.iterrows():
                    val = row.get(imp_col)
                    if pd.notna(val) and str(val).strip():
                        improve_manager.append(str(val).strip())

            # 同儕
            if pos_col and not peers_df.empty:
                for _, row in peers_df.iterrows():
                    val = row.get(pos_col)
                    if pd.notna(val) and str(val).strip():
                        positive_peer.append(str(val).strip())
            if imp_col and not peers_df.empty:
                for _, row in peers_df.iterrows():
                    val = row.get(imp_col)
                    if pd.notna(val) and str(val).strip():
                        improve_peer.append(str(val).strip())

            # 部屬
            if pos_col and not subordinates_df.empty:
                for _, row in subordinates_df.iterrows():
                    val = row.get(pos_col)
                    if pd.notna(val) and str(val).strip():
                        positive_subordinate.append(str(val).strip())
            if imp_col and not subordinates_df.empty:
                for _, row in subordinates_df.iterrows():
                    val = row.get(imp_col)
                    if pd.notna(val) and str(val).strip():
                        improve_subordinate.append(str(val).strip())

            random.shuffle(positive_peer)
            random.shuffle(improve_peer)
            random.shuffle(positive_subordinate)
            random.shuffle(improve_subordinate)

        feedbacks.append(QualitativeFeedback(
            dimension=dim_name,
            positive_self=positive_self,
            positive_others=positive_others,
            improve_self=improve_self,
            improve_others=improve_others,
            positive_manager=positive_manager,
            positive_peer=positive_peer,
            positive_subordinate=positive_subordinate,
            improve_manager=improve_manager,
            improve_peer=improve_peer,
            improve_subordinate=improve_subordinate,
        ))

    return feedbacks


def extract_other_feedback(
    self_df: pd.DataFrame,
    others_df: pd.DataFrame,
    grade: str = "L0",
) -> dict:
    """
    提取「其他回饋與建議」欄位。

    Returns:
        包含各角色其他回饋的 dict
    """
    col = find_column_by_keyword(self_df, OTHER_FEEDBACK_KEYWORD)

    res = {
        "self": "",
        "others": [],
        "manager": [],
        "peer": [],
        "subordinate": [],
    }

    if not col:
        return res

    if not self_df.empty:
        val = self_df.iloc[0].get(col)
        res["self"] = str(val).strip() if pd.notna(val) else ""

    if others_df.empty:
        return res

    # L0 他評
    for _, row in others_df.iterrows():
        val = row.get(col)
        if pd.notna(val) and str(val).strip():
            res["others"].append(str(val).strip())
    random.shuffle(res["others"])

    # L1 細分
    if grade == "L1":
        role_col = find_role_column(others_df)
        manager_df = others_df[others_df[role_col].str.contains("主管", na=False)]
        peers_df = others_df[others_df[role_col].str.contains("同儕|合作夥伴", na=False)]
        subordinates_df = others_df[others_df[role_col].str.contains("部屬", na=False)]

        for _, row in manager_df.iterrows():
            val = row.get(col)
            if pd.notna(val) and str(val).strip():
                res["manager"].append(str(val).strip())

        for _, row in peers_df.iterrows():
            val = row.get(col)
            if pd.notna(val) and str(val).strip():
                res["peer"].append(str(val).strip())
        random.shuffle(res["peer"])

        for _, row in subordinates_df.iterrows():
            val = row.get(col)
            if pd.notna(val) and str(val).strip():
                res["subordinate"].append(str(val).strip())
        random.shuffle(res["subordinate"])

    return res


def extract_collaboration_scores(
    self_df: pd.DataFrame,
    others_df: pd.DataFrame,
    grade: str = "L0",
) -> dict:
    """
    提取「繼續共事意願」分數。

    Returns:
        包含各角色共事意願分數與平均的 dict
    """
    col = find_column_by_keyword(self_df, COLLABORATION_KEYWORD)

    res = {
        "self": None,
        "others": [],
        "others_avg": None,
        "manager": None,
        "peer": [],
        "peer_avg": None,
        "subordinate": [],
        "subordinate_avg": None,
    }

    if not col:
        return res

    if not self_df.empty:
        val = self_df.iloc[0].get(col)
        try:
            res["self"] = int(val) if pd.notna(val) else None
        except (ValueError, TypeError):
            res["self"] = None

    if others_df.empty:
        return res

    # L0 他評
    for _, row in others_df.iterrows():
        val = row.get(col)
        try:
            if pd.notna(val):
                res["others"].append(int(val))
        except (ValueError, TypeError):
            pass
    random.shuffle(res["others"])
    if res["others"]:
        res["others_avg"] = round(sum(res["others"]) / len(res["others"]), 2)

    # L1 細分
    if grade == "L1":
        role_col = find_role_column(others_df)
        manager_df = others_df[others_df[role_col].str.contains("主管", na=False)]
        peers_df = others_df[others_df[role_col].str.contains("同儕|合作夥伴", na=False)]
        subordinates_df = others_df[others_df[role_col].str.contains("部屬", na=False)]

        # 主管
        for _, row in manager_df.iterrows():
            val = row.get(col)
            try:
                if pd.notna(val):
                    res["manager"] = int(val)
            except (ValueError, TypeError):
                pass

        # 同儕
        for _, row in peers_df.iterrows():
            val = row.get(col)
            try:
                if pd.notna(val):
                    res["peer"].append(int(val))
            except (ValueError, TypeError):
                pass
        random.shuffle(res["peer"])
        if res["peer"]:
            res["peer_avg"] = round(sum(res["peer"]) / len(res["peer"]), 2)

        # 部屬
        for _, row in subordinates_df.iterrows():
            val = row.get(col)
            try:
                if pd.notna(val):
                    res["subordinate"].append(int(val))
            except (ValueError, TypeError):
                pass
        random.shuffle(res["subordinate"])
        if res["subordinate"]:
            res["subordinate_avg"] = round(sum(res["subordinate"]) / len(res["subordinate"]), 2)

    return res

