"""
Excel/CSV 資料解析模組

負責將上傳的問卷資料解析為結構化 DataFrame，
並進行分數文字轉數值、角色分群等前處理。
"""
import pandas as pd
import io
import re
from ..config import SCORE_MAP, ROLE_COLUMN_KEYWORD, SELF_ROLE_KEYWORD


def parse_uploaded_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """
    解析上傳的 Excel 或 CSV 檔案為 DataFrame。

    Args:
        file_content: 檔案二進位內容
        filename: 原始檔名（用於判斷格式）

    Returns:
        解析後的 DataFrame
    """
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(file_content), engine="openpyxl")
    elif filename.endswith(".csv"):
        # 嘗試不同編碼
        for encoding in ["utf-8", "utf-8-sig", "big5", "cp950"]:
            try:
                df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("無法解析 CSV 檔案編碼，請確認檔案格式。")
    else:
        raise ValueError(f"不支援的檔案格式：{filename}，請上傳 .xlsx 或 .csv 檔案。")

    # 清理欄位名稱中的換行與不間斷空格
    df.columns = [_clean_column_name(col) for col in df.columns]

    return df


def _clean_column_name(name: str) -> str:
    """清理欄位名稱中的特殊字元"""
    if not isinstance(name, str):
        return str(name)
    # 移除換行、不間斷空格，並去除首尾空白
    name = name.replace("\n", "").replace("\xa0", " ").strip()
    # 壓縮連續空格
    name = re.sub(r"\s+", " ", name)
    return name


def find_role_column(df: pd.DataFrame) -> str:
    """
    找到「填寫者的角色」欄位名稱。

    Returns:
        匹配到的欄位名稱
    """
    for col in df.columns:
        if ROLE_COLUMN_KEYWORD in col:
            return col
    raise ValueError(f"找不到角色欄位（包含「{ROLE_COLUMN_KEYWORD}」的欄位）。")


def split_by_role(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    根據角色欄位將資料分為自評與他評。

    Returns:
        (自評 DataFrame, 他評 DataFrame)
    """
    role_col = find_role_column(df)

    # 清理角色欄位的值
    df[role_col] = df[role_col].apply(
        lambda x: x.replace("\n", "").replace("\xa0", "").strip()
        if isinstance(x, str) else x
    )

    self_df = df[df[role_col].str.contains(SELF_ROLE_KEYWORD, na=False)]
    others_df = df[~df[role_col].str.contains(SELF_ROLE_KEYWORD, na=False)]

    if self_df.empty:
        raise ValueError("找不到自評資料（角色為「受評者自己」的填答）。")

    return self_df, others_df


def convert_score_value(value) -> float | None:
    """
    將問卷分數文字轉換為數值。

    支援格式：
    - "4分(佳)" → 4.0
    - 數字 → 直接轉換
    - None / NaN / 空字串 → None

    Returns:
        數值分數或 None
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    value_str = str(value).strip()
    if not value_str:
        return None

    # 先嘗試完全匹配
    if value_str in SCORE_MAP:
        return SCORE_MAP[value_str]

    # 嘗試提取數字部分（例如 "4分(佳)" → 4）
    match = re.match(r"(\d+)", value_str)
    if match:
        num = float(match.group(1))
        if 1.0 <= num <= 5.0:
            return num

    # 嘗試直接轉為數字
    try:
        num = float(value_str)
        return num
    except (ValueError, TypeError):
        return None


def find_column_by_keyword(df: pd.DataFrame, keyword: str) -> str | None:
    """
    根據關鍵字模糊匹配欄位名稱。

    Returns:
        匹配到的欄位名稱，若無則回傳 None
    """
    for col in df.columns:
        if keyword in col:
            return col
    return None
