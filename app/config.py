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

# 三大面向與對應題目定義
# 鍵 = 面向名稱，值 = 該面向下的量化題目欄位關鍵字列表
DIMENSIONS: dict[str, dict] = {
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

# 額外題目：繼續共事意願
COLLABORATION_KEYWORD = "若有選擇機會"

# 額外題目：其他回饋
OTHER_FEEDBACK_KEYWORD = "你還有什麼其他回饋"

# 管理目的選項
MANAGEMENT_PURPOSES = [
    {"value": "個人發展", "label": "個人發展 (IDP)"},
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
