"""
LLM 分析服務

支援 Google Gemini API 與 OpenAI API，
根據結構化分數資料與質性回饋生成管理建議。
"""
import httpx
import json
from ..models.schemas import ReportData

# 達哥 (DaVinci) 官方模型與 api_version 映射表
DAVINCI_MODEL_VERSION_MAPPING = {
    "gpt-4o": "2025-03-01-preview",
    "gpt-4o-mini": "2024-10-21",
    "gpt-5": "2025-04-01-preview",
    "gpt-5-mini": "2025-04-01-preview",
    "gpt-o3-mini": "2024-12-01-preview",
    "gpt-o3": "2024-12-01-preview",
    "gemini-3-flash": "2024-10-21",
    "deepseek-r1-0528": "2024-10-21",
    "deepseek-v3-2": "2024-05-01-preview",
    "grok-4-1-fast-reasoning": "2024-05-01-preview",
    "kimi-k2-thinking": "2024-10-21"
}


# 管理目的對應的分析焦點
PURPOSE_PROMPTS = {
    "IDP 發展": (
        "請以「個人發展計畫 (IDP)」為分析焦點。"
        "著重在如何改善自評與他評落差最大的維度，深入剖析「盲點（自評高他評低）」與「痛點（得分最低項）」，提出具體、可執行的短期與中期發展行動計畫。"
    ),
    "績效校準": (
        "請以「績效校準 (Performance Calibration)」為分析焦點。"
        "著重將受評者的實際表現與當前職級 KRA 的期待進行對照，"
        "明確標示出受評者有哪些具體行為得分偏低、尚未達標，評估其現職符合度並給出改善建議。"
    ),
    "晉升評估": (
        "請以「晉升評估 (Promotion Review)」為分析焦點。"
        "評估受評者當前表現與下一職級 KRA 的期待落差，衡量其晉升準備度 (Readiness)，"
        "明確指出其與下一階行為要求的 Gap Area (能力差距)，並提出晉升前優先強化的建議。"
    ),
    "團隊文化": (
        "請以「團隊文化 (Team Culture)」為分析焦點。"
        "特別篩選並聚焦於特定 Key Elements（即問卷中的：第3題 - 團隊文化、第6題 - 理解支持、第8題 - 回饋對話）的分數與文字回饋，"
        "深入剖析受評者的領導風格、團隊氛圍（包含心理安全感的建立），以及在文化傳遞上的感受與期待。"
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
    is_l1 = report_data.grade == "L1"

    # 組裝分數資料摘要
    score_summary = []
    for dim in report_data.dimensions:
        score_summary.append(f"\n### {dim.dimension} ({dim.dimension_en})")
        if is_l1:
            score_summary.append(
                f"面向平均 — 自評: {dim.self_average}, 主管評: {dim.manager_average}, 同儕平均: {dim.peer_average}, 部屬平均: {dim.subordinate_average}"
            )
            for q in dim.questions:
                score_summary.append(
                    f"  - {q.question_full}: 自評 {q.self_score}, 主管評 {q.manager_score}, 同儕平均 {q.peer_average}, 部屬平均 {q.subordinate_average}"
                )
        else:
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
        
        if is_l1:
            if qf.positive_manager:
                qual_summary.append(f"【做得好 - 主管回饋】")
                for fb in qf.positive_manager:
                    qual_summary.append(f"  - {fb}")
            if qf.positive_peer:
                qual_summary.append(f"【做得好 - 同儕回饋】")
                for fb in qf.positive_peer:
                    qual_summary.append(f"  - {fb}")
            if qf.positive_subordinate:
                qual_summary.append(f"【做得好 - 部屬回饋】")
                for fb in qf.positive_subordinate:
                    qual_summary.append(f"  - {fb}")
        else:
            qual_summary.append(f"【做得好 - 他人回饋】")
            for fb in qf.positive_others:
                qual_summary.append(f"  - {fb}")

        qual_summary.append(f"【建議改善 - 自評】{qf.improve_self}")
        
        if is_l1:
            if qf.improve_manager:
                qual_summary.append(f"【建議改善 - 主管回饋】")
                for fb in qf.improve_manager:
                    qual_summary.append(f"  - {fb}")
            if qf.improve_peer:
                qual_summary.append(f"【建議改善 - 同儕回饋】")
                for fb in qf.improve_peer:
                    qual_summary.append(f"  - {fb}")
            if qf.improve_subordinate:
                qual_summary.append(f"【建議改善 - 部屬回饋】")
                for fb in qf.improve_subordinate:
                    qual_summary.append(f"  - {fb}")
        else:
            qual_summary.append(f"【建議改善 - 他人回饋】")
            for fb in qf.improve_others:
                qual_summary.append(f"  - {fb}")

    # 額外回饋
    if is_l1:
        if report_data.other_feedback_manager or report_data.other_feedback_peer or report_data.other_feedback_subordinate:
            qual_summary.append("\n### 其他回饋")
            if report_data.other_feedback_manager:
                qual_summary.append(f"【其他回饋 - 主管】")
                for fb in report_data.other_feedback_manager:
                    qual_summary.append(f"  - {fb}")
            if report_data.other_feedback_peer:
                qual_summary.append(f"【其他回饋 - 同儕】")
                for fb in report_data.other_feedback_peer:
                    qual_summary.append(f"  - {fb}")
            if report_data.other_feedback_subordinate:
                qual_summary.append(f"【其他回饋 - 部屬】")
                for fb in report_data.other_feedback_subordinate:
                    qual_summary.append(f"  - {fb}")
    else:
        if report_data.other_feedback_others:
            qual_summary.append("\n### 其他回饋")
            for fb in report_data.other_feedback_others:
                qual_summary.append(f"  - {fb}")

    current_grade = report_data.grade
    if current_grade == "L0":
        current_kra_desc = "當前 L0 職級 KRA 面向（任務執行、溝通協作、問題解決）"
        next_kra_desc = "下一階 L1 職級 KRA 面向（組建團隊、引領績效、流程變革、形塑氛圍）"
    else:
        current_kra_desc = "當前 L1 職級 KRA 面向（組建團隊、引領績效、流程變革、形塑氛圍）"
        next_kra_desc = "下一階（高階管理與跨組織戰略影響力）"

    # 動態產生目的提示詞，完美融合專業的 KRA 落差與準備度衡量思維
    if report_data.purpose == "IDP 發展":
        purpose_focus = (
            "請以「個人發展計畫 (IDP)」為分析焦點。\n"
            "著重分析該受評者的「自評與他評分數落差」，找出其最突出的「盲點（自評高於他評最多、落差最大的題目）」與當前最需克服的「痛點（他評或主管評分最低的題目）」。\n"
            "請深入探討造成此盲點與痛點的可能原因，並提出具體、具備操作性且分階段的短期（1-3個月）與中期（3-6個月）個人發展計畫。"
        )
    elif report_data.purpose == "績效校準":
        purpose_focus = (
            f"請以「績效校準 (Performance Calibration)」為分析焦點。\n"
            f"著重分析該受評者的「各項實際回饋結果」與其「{current_kra_desc}」的落差與達成度。\n"
            f"指出其在日常交付與行為表現上，是否已穩健達成該職級 KRA 的期待，並「明確標示出有哪些具體現職行為/題目得分偏低（如低於 3.5 分或顯著低於同儕平均）而尚未達標」，以此評估其現職符合度並提出績效校準與具體改善行動。"
        )
    elif report_data.purpose == "晉升評估":
        purpose_focus = (
            f"請以「晉升評估 (Promotion Review)」為分析焦點。\n"
            f"著重評估受評者當前的各面向表現與「{next_kra_desc}」要求的落差，衡量其晉升準備度 (Readiness)。\n"
            f"明確指出其是否已具備或展現下一階 KRA 所需的核心潛力與能力，並「精確標示出受評者當前表現與下一階期待之間的 Gap Area (能力差距項目)」，給出晉升前建議優先強化的面向與能力。"
        )
    elif report_data.purpose == "團隊文化":
        purpose_focus = (
            "請以「團隊文化 (Team Culture)」為分析焦點。\n"
            "請特別聚焦並篩選特定 Key Elements（即問卷中的：第 3 題『團隊文化：理解與傳遞公司理念』、第 6 題『理解支持：辨識成員強弱與尊重個人差異』、第 8 題『回饋對話：給予具體發展回饋』）的量化與質性回饋進行深度剖析。\n"
            "聚焦分析受評者在這些核心題目上的表現、與他人的共事互動方式，進而探討其形塑的「領導風格與團隊氛圍」（尤其是如何建立團隊心理安全感，以及如何傳遞公司核心文化價值），並整理團隊成員在文化塑造上對其的感受與期待。"
        )
    else:
        purpose_focus = ""

    collab_info = f"- 繼續共事意願（他評平均）：{report_data.collaboration_average}/10"
    if is_l1:
        collab_info = (
            f"- 繼續共事意願：\n"
            f"  * 主管意願：{report_data.collaboration_manager if report_data.collaboration_manager is not None else 'N/A'}/10\n"
            f"  * 同儕平均意願：{report_data.collaboration_peer_average if report_data.collaboration_peer_average is not None else 'N/A'}/10\n"
            f"  * 部屬平均意願：{report_data.collaboration_subordinate_average if report_data.collaboration_subordinate_average is not None else 'N/A'}/10"
        )

    # 針對 L1 和 L0 的 AI 分析分析焦點說明
    analysis_focus = "找出自評與他評落差最大的項目，分析可能原因"
    if is_l1:
        analysis_focus = "對比自評、主管、同儕及部屬評分的落差與期待盲點，重點分析受評者在『向上管理、平級協作、向下帶領』三種關係中的互動盲區，並推導背後可能原因。"

    prompt = f"""你是一位專業的組織發展顧問與 HRBP 顧問。
以下是一份 360 度回饋報告的結構化資料，請根據這些資料為 HRBP 產出一段專業、客觀的分析建議。

## 受評者資訊
- 姓名：{report_data.name}
- 職級：{report_data.grade}
- 管理目的：{report_data.purpose}
{collab_info}

## 量化分數摘要
{''.join(score_summary)}

## 質性回饋
{''.join(qual_summary)}

## 分析要求
{purpose_focus}

請產出一段 **400-600 字**的客觀分析，內容需包含：
1. **強項總結**：明確指出受評者在哪些面向/題目表現突出（以他評/主管/同儕/部屬分數為依據）
2. **盲點分析**：{analysis_focus}
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


async def analyze_with_davinci(api_key: str, prompt: str, model: str) -> str:
    """
    使用 Moxa 達哥 (DaVinci) GAISF API 進行分析（繞過內網 SSL 憑證驗證與 API 閘道 JWT 認證）。

    Args:
        api_key: 達哥平台 JWT 認證金鑰
        prompt: 分析 Prompt
        model: 使用的大模型名稱

    Returns:
        LLM 生成的分析文字
    """
    import httpx
    import urllib3

    # 關閉內網測試時的 SSL 警告
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    endpoint = "https://moxaingress-gaisf-ingress.azurewebsites.net"
    api_version = DAVINCI_MODEL_VERSION_MAPPING.get(model, "2024-10-21")

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [
            {"role": "system", "content": "你是一位專業的組織發展與人力資源管理顧問。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    url = f"{endpoint}/openai/deployments/{model}/chat/completions?api-version={api_version}"

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(url, headers=headers, json=payload, timeout=60.0)

        if response.status_code == 200:
            data = response.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                raise Exception(f"達哥 API 回傳格式不符: {data}")
        else:
            raise Exception(f"達哥 API 呼叫失敗 ({response.status_code}): {response.text}")


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
    model: str = "gemini-1.5-flash",
) -> str:
    """
    執行 LLM 分析的主入口。

    Args:
        api_key: API Key
        api_provider: "gemini"、"openai" 或 "davinci"
        report_data: 完整報告資料
        model: 使用的大模型名稱

    Returns:
        LLM 生成的管理建議
    """
    prompt = _build_analysis_prompt(report_data)

    try:
        if api_provider == "gemini":
            result = await analyze_with_gemini(api_key, prompt)
        elif api_provider == "openai":
            result = await analyze_with_openai(api_key, prompt)
        elif api_provider == "davinci":
            result = await analyze_with_davinci(api_key, prompt, model)
        else:
            result = f"不支援的 API 提供者：{api_provider}"
        return result
    except Exception as e:
        return f"⚠️ LLM 分析失敗：{str(e)}\n\n請確認 API Key 是否正確，以及是否有足夠的配額。"
