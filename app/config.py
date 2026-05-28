"""
系統設定與常數定義
"""

# 分數轉換映射表（問卷文字 → 數值）
SCORE_MAP: dict[str, float] = {
    "1分(差)": 1.0,
    "2分(需強化)": 2.0,
    "3分(一般)": 3.0,
    "4分(佳)": 4.0,
    "5分(極佳)": 5.0,
}

# 評分等級說明（報告中顯示用）
RATING_SCALE = [
    {"score": 1, "label_zh": "差", "label_en": "Poor"},
    {"score": 2, "label_zh": "需強化", "label_en": "Need Improvement"},
    {"score": 3, "label_zh": "一般", "label_en": "Average"},
    {"score": 4, "label_zh": "佳", "label_en": "Good"},
    {"score": 5, "label_zh": "極佳", "label_en": "Role Model"},
]

# 自評角色關鍵字
SELF_ROLE_KEYWORD = "受評者自己"

# 角色欄位名稱（含可能的空白字元）
ROLE_COLUMN_KEYWORD = "填寫者的角色"

# 三大面向與對應題目定義（區分 L0 / L1）
DIMENSIONS_L0: dict[str, dict] = {
    "帶領團隊": {
        "label_en": "Leading Team",
        "questions": [
            {
                "keyword": "組建團隊",
                "full_name": "組建團隊：組建團隊以承接任務",
                "name_en": "Team Building",
            },
            {
                "keyword": "目標衡量",
                "full_name": "目標衡量：清楚定義承接任務，並訂定團隊到個人的目標與衡量標準",
                "name_en": "Goal Setting & Measurement",
            },
            {
                "keyword": "團隊文化",
                "full_name": "團隊文化：理解與傳遞公司理念，並以行動支持",
                "name_en": "Team Culture",
            },
            {
                "keyword": "部門合作",
                "full_name": "部門合作：促進團隊合作，主動提出困難並協調解方或尋求協助",
                "name_en": "Cross-team Collaboration",
            },
        ],
        "qualitative_positive_keyword": "在「帶領團隊」面向，你認為受評者做得最好的地方",
        "qualitative_improve_keyword": "在「帶領團隊」面向，為了讓團隊運作更順暢",
    },
    "發展個人": {
        "label_en": "Developing People",
        "questions": [
            {
                "keyword": "以身作則",
                "full_name": "以身作則：續落實發展自己，並學習自我覺察",
                "name_en": "Leading by Example",
            },
            {
                "keyword": "理解支持",
                "full_name": "理解支持：辨識成員強弱項與狀態，尊重個人差異，使其發揮所長",
                "name_en": "Understanding & Support",
            },
            {
                "keyword": "發展連結",
                "full_name": "發展連結：任務安排考量個人發展，並與成員和利害關係人溝通其目的",
                "name_en": "Development Alignment",
            },
            {
                "keyword": "回饋對話",
                "full_name": "回饋對話：收集客觀事實，給予具體發展回饋",
                "name_en": "Feedback & Dialogue",
            },
        ],
        "qualitative_positive_keyword": "在「發展個人」面向，你認為受評者做得最好的地方",
        "qualitative_improve_keyword": "在「發展個人」面向，為了更好地支持人才成長",
    },
    "完成任務": {
        "label_en": "Accomplishing Tasks",
        "questions": [
            {
                "keyword": "任務目標",
                "full_name": "任務目標：明確團隊任務、共同目標與期望成果",
                "name_en": "Task Objectives",
            },
            {
                "keyword": "資源整合",
                "full_name": "資源整合：盤點並管理團隊資源",
                "name_en": "Resource Integration",
            },
            {
                "keyword": "進度衡量",
                "full_name": "進度衡量：監督並追蹤任務執行進度",
                "name_en": "Progress Tracking",
            },
            {
                "keyword": "風險管理",
                "full_name": "風險管理：具備風險意識能辨識異常，釐清問題，主動處理並適時提報",
                "name_en": "Risk Management",
            },
            {
                "keyword": "回顧優化",
                "full_name": "回顧優化：定期檢視任務成果，回饋並持續改善執行方式",
                "name_en": "Review & Optimization",
            },
        ],
        "qualitative_positive_keyword": "在「完成任務」面向，你認為受評者做得最好的地方",
        "qualitative_improve_keyword": "在「完成任務」面向，為了更好地推動任務與目標",
    },
}

DIMENSIONS_L1: dict[str, dict] = {
    "帶領團隊": {
        "label_en": "Leading Team",
        "questions": [
            {
                "keyword": "組建團隊",
                "full_name": "組建團隊：部門組織規劃與工作設計",
                "name_en": "Team Building",
            },
            {
                "keyword": "目標衡量",
                "full_name": "目標衡量：連結公司或組織目標，建立部門與個人的衡量指標",
                "name_en": "Goal Setting & Measurement",
            },
            {
                "keyword": "團隊文化",
                "full_name": "團隊文化：實踐公司理念，凝聚團隊向心力",
                "name_en": "Team Culture",
            },
            {
                "keyword": "部門合作",
                "full_name": "部門合作：推動跨部門協作，辨識難點(流程/組織)，並提出可行協作計畫",
                "name_en": "Cross-team Collaboration",
            },
        ],
        "qualitative_positive_keyword": "在「帶領團隊」面向，你認為受評者做得最好的地方",
        "qualitative_improve_keyword": "在「帶領團隊」面向，為了讓團隊運作更順暢",
    },
    "發展個人": {
        "label_en": "Developing People",
        "questions": [
            {
                "keyword": "以身作則",
                "full_name": "以身作則：以身作則發展自我，於工作中開始展現自我覺察與反思",
                "name_en": "Leading by Example",
            },
            {
                "keyword": "理解支持",
                "full_name": "理解支持：透過職涯對話(Career Talk)，激勵與支持個人的發展",
                "name_en": "Understanding & Support",
            },
            {
                "keyword": "發展連結",
                "full_name": "發展連結：運用組織內外部資源，拓展成員學習發展平台",
                "name_en": "Development Alignment",
            },
            {
                "keyword": "回饋對話",
                "full_name": "回饋對話：給予真誠發展回饋，面對困難對話，在對話過程中心相互學習",
                "name_en": "Feedback & Dialogue",
            },
        ],
        "qualitative_positive_keyword": "在「發展個人」面向，你認為受評者做得最好的地方",
        "qualitative_improve_keyword": "在「發展個人」面向，為了更好地支持人才成長",
    },
    "完成任務": {
        "label_en": "Accomplishing Tasks",
        "questions": [
            {
                "keyword": "任務目標",
                "full_name": "任務目標：連結公司或組織目標，規劃部門短中長期目標",
                "name_en": "Task Objectives",
            },
            {
                "keyword": "資源整合",
                "full_name": "資源整合：盤點橫向協作資源，建立上下游跨單位協作機制",
                "name_en": "Resource Integration",
            },
            {
                "keyword": "進度衡量",
                "full_name": "進度衡量：設計有效衡量指標，追蹤團隊成果並適時調整",
                "name_en": "Progress Tracking",
            },
            {
                "keyword": "風險管理",
                "full_name": "風險管理：評估風險與可能衝擊，提出因應對策及備案規劃並介入處理",
                "name_en": "Risk Management",
            },
            {
                "keyword": "回顧優化",
                "full_name": "回顧優化：建立任務回顧機制(Retro)，優化部門營運與跨部門協作效能",
                "name_en": "Review & Optimization",
            },
        ],
        "qualitative_positive_keyword": "在「完成任務」面向，你認為受評者做得最好的地方",
        "qualitative_improve_keyword": "在「完成任務」面向，為了更好地推動任務與目標",
    },
}

def get_dimensions(grade: str = "L0") -> dict:
    """根據職級獲取面向與題目設定"""
    if grade == "L1":
        return DIMENSIONS_L1
    return DIMENSIONS_L0

# 相容預設值
DIMENSIONS = DIMENSIONS_L0


# 額外題目：繼續共事意願
COLLABORATION_KEYWORD = "若有選擇機會"

# 額外題目：其他回饋
OTHER_FEEDBACK_KEYWORD = "你還有什麼其他回饋"

# 管理目的選項
MANAGEMENT_PURPOSES = [
    {"value": "IDP 發展", "label": "IDP 發展 (IDP)"},
    {"value": "績效校準", "label": "績效校準 (Performance Calibration)"},
    {"value": "晉升評估", "label": "晉升評估 (Promotion Review)"},
    {"value": "團隊文化", "label": "團隊文化 (Team Culture)"},
]

# 職級選項
GRADES = ["L0", "L1"]

# LLM API 提供者
API_PROVIDERS = [
    {"value": "gemini", "label": "Google Gemini"},
    {"value": "openai", "label": "OpenAI"},
]
