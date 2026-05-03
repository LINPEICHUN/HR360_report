"""
LLM 分析服務

支援 Google Gemini API 與 OpenAI API，
根據結構化分數資料與質性回饋生成管理建議。
"""
import httpx
import json
from ..models.schemas import ReportData


# 管理目的對應的分析焦點
PURPOSE_PROMPTS = {
    "個人發展": (
        "請以「個人發展計畫 (IDP)」為分析焦點。"
        "著重在如何改善自評與他評落差最大的維度，提出具體、可執行的行動計畫。"
        "建議應涵蓋短期（1-3個月）與中期（3-6個月）的發展目標。"
    ),
    "績效校準": (
        "請以「績效校準 (Performance Calibration)」為分析焦點。"
        "著重在日常交付的穩定度與跨部門合作效能，"
        "指出受評者的表現是否符合當前職級的期待，並標示出高於或低於該職級水準的面向。"
    ),
    "晉升評估": (
        "請以「晉升評估 (Promotion Review)」為分析焦點。"
        "評估受評者是否已具備更高階職務所需的領導力與前瞻思維，"
        "明確指出強項與待準備的差距，以及在晉升前建議優先強化的能力。"
    ),
    "團隊文化": (
        "請以「團隊文化 (Team Culture)」為分析焦點。"
        "聚焦在團隊溝通品質、心理安全感建立、是否能有效傳遞公司願景，"
        "以及團隊成員對受評者在文化塑造上的感受與期待。"
    ),
}


def _build_analysis_prompt(report_data: ReportData) -> str:
    """
    建構 LLM 分析的完整 Prompt。

    Args:
        report_data: 完整報告資料

    Returns:
        結構化的 Prompt 字串
    """
    # 組裝分數資料摘要
    score_summary = []
    for dim in report_data.dimensions:
        score_summary.append(f"\n### {dim.dimension} ({dim.dimension_en})")
        score_summary.append(
            f"面向平均 — 自評: {dim.self_average}, 他評: {dim.others_average}"
        )
        for q in dim.questions:
            score_summary.append(
                f"  - {q.question_full}: 自評 {q.self_score}, 他評平均 {q.others_average}"
            )

    # 組裝質性回饋
    qual_summary = []
    for qf in report_data.qualitative:
        qual_summary.append(f"\n### {qf.dimension}")
        qual_summary.append(f"【做得好 - 自評】{qf.positive_self}")
        qual_summary.append(f"【做得好 - 他人回饋】")
        for fb in qf.positive_others:
            qual_summary.append(f"  - {fb}")
        qual_summary.append(f"【建議改善 - 自評】{qf.improve_self}")
        qual_summary.append(f"【建議改善 - 他人回饋】")
        for fb in qf.improve_others:
            qual_summary.append(f"  - {fb}")

    # 額外回饋
    if report_data.other_feedback_others:
        qual_summary.append("\n### 其他回饋")
        for fb in report_data.other_feedback_others:
            qual_summary.append(f"  - {fb}")

    purpose_focus = PURPOSE_PROMPTS.get(report_data.purpose, "")

    prompt = f"""你是一位專業的組織發展顧問與 HRBP 顧問。
以下是一份 360 度回饋報告的結構化資料，請根據這些資料為 HRBP 產出一段專業、客觀的分析建議。

## 受評者資訊
- 姓名：{report_data.name}
- 職級：{report_data.grade}
- 管理目的：{report_data.purpose}
- 繼續共事意願（他評平均）：{report_data.collaboration_average}/10

## 量化分數摘要
{''.join(score_summary)}

## 質性回饋
{''.join(qual_summary)}

## 分析要求
{purpose_focus}

請產出一段 **300-500 字**的客觀分析，內容需包含：
1. **強項總結**：明確指出受評者在哪些面向/題目表現突出（以他評分數為依據）
2. **盲點分析**：找出自評與他評落差最大的項目，分析可能原因
3. **管理建議**：針對「{report_data.purpose}」的管理情境，提出具體、可落地的建議
4. **發展優先序**：建議優先改善的 2-3 個面向

要求：
- 使用繁體中文
- 以第三人稱書寫（「該受評者」而非「你」）
- 保持客觀專業，避免過度正面或負面
- 引用具體分數佐證你的分析
"""
    return prompt


async def analyze_with_gemini(api_key: str, prompt: str) -> str:
    """
    使用 Google Gemini API 進行分析。

    Args:
        api_key: Gemini API Key
        prompt: 分析 Prompt

    Returns:
        LLM 生成的分析文字
    """
    import httpx
    
    # 使用 REST API 避免 SDK 在 Windows 環境下的編碼問題
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-1.5-pro",
    ]
    
    last_error_text = ""
    last_status_code = 0
    
    async with httpx.AsyncClient() as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            
            if response.status_code == 200:
                data = response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    raise Exception(f"Unexpected API response format: {data}")
            elif response.status_code in [404, 429, 403, 500, 503]:
                # 若模型找不到、配額用盡或伺服器錯誤，則記錄並嘗試下一個模型
                last_status_code = response.status_code
                last_error_text = response.text
                continue
            else:
                # 其他錯誤（如 API Key 錯誤）直接拋出
                raise Exception(f"API Error ({response.status_code}): {response.text}")
                
        # 如果所有模型都失敗，拋出最後一次錯誤
        raise Exception(f"API Error ({last_status_code}): 所有嘗試的模型皆無效。最後錯誤: {last_error_text}")


async def analyze_with_openai(api_key: str, prompt: str) -> str:
    """
    使用 OpenAI API 進行分析。

    Args:
        api_key: OpenAI API Key
        prompt: 分析 Prompt

    Returns:
        LLM 生成的分析文字
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一位專業的組織發展與人力資源管理顧問。"},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
        temperature=0.7,
    )
    return response.choices[0].message.content


async def analyze_feedback(report_data: ReportData) -> str:
    """
    根據報告資料呼叫 LLM 進行分析。

    Args:
        report_data: 完整報告資料（需包含 api_key 與 api_provider 資訊）

    Returns:
        LLM 生成的管理建議文字
    """
    prompt = _build_analysis_prompt(report_data)

    # 從 report_data 中暫時無法取得 api_key，需透過外部傳入
    # 此函式的實際呼叫將由 report_generator 傳遞 key
    return prompt  # 預設回傳 prompt，供外部使用


async def run_llm_analysis(
    api_key: str,
    api_provider: str,
    report_data: ReportData,
) -> str:
    """
    執行 LLM 分析的主入口。

    Args:
        api_key: API Key
        api_provider: "gemini" 或 "openai"
        report_data: 完整報告資料

    Returns:
        LLM 生成的管理建議
    """
    prompt = _build_analysis_prompt(report_data)

    try:
        if api_provider == "gemini":
            result = await analyze_with_gemini(api_key, prompt)
        elif api_provider == "openai":
            result = await analyze_with_openai(api_key, prompt)
        else:
            result = f"不支援的 API 提供者：{api_provider}"
        return result
    except Exception as e:
        return f"⚠️ LLM 分析失敗：{str(e)}\n\n請確認 API Key 是否正確，以及是否有足夠的配額。"
