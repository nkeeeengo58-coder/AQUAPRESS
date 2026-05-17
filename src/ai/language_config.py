"""Language configuration for AQUA PRESS multi-language support (Phase 10)."""

from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_LANGUAGES = {"ja", "en", "zh", "th"}


@dataclass
class LanguageConfig:
    """Configuration for each language."""

    code: str  # Language code: ja, en, zh, th
    name: str  # Language name
    name_native: str  # Native name
    
    # Google News search queries (aquarium-related)
    google_news_queries: list[str]
    
    # Gemini prompt instructions
    system_prompt: str
    
    # VOICEVOX speaker ID (if supported, else None)
    voicevox_speaker: int | None
    
    # TTS (Text-to-Speech) configuration (Phase 11)
    tts_engine: str | None  # "voicevox", "google", None
    tts_language_code: str  # e.g., "ja-JP", "en-US", "zh-CN", "th-TH"
    tts_voice_id: str | None  # e.g., "en-US-Neural2-A"
    
    # Video style customization (if needed)
    font_name: str | None = None
    
    # Language-specific UI text
    ui_text: dict[str, str] = None


LANGUAGE_CONFIGS = {
    "ja": LanguageConfig(
        code="ja",
        name_native="日本語",
        name="Japanese",
        google_news_queries=[
            "アクアリウム",
            "熱帯魚",
            "観賞魚",
            "水草",
            "アクアリウムセール",
            "熱帯魚入荷",
            "海水魚",
            "メダカ",
            "シュリンプ",
        ],
        system_prompt="""You are AQUA PRESS, an automated aquarium news generator. 
Generate a concise, engaging Japanese news script about aquarium topics.
Output format: JSON with 'title' and 'narration_lines' fields.
Keep lines short (max 30 chars) for readability in vertical video format.""",
        voicevox_speaker=3,  # Japanese narrator
        tts_engine="voicevox",
        tts_language_code="ja-JP",
        tts_voice_id=None,
        font_name="arial",
        ui_text={
            "loading": "読込中...",
            "generating": "生成中...",
            "uploading": "アップロード中...",
            "error": "エラーが発生しました",
        },
    ),
    "en": LanguageConfig(
        code="en",
        name_native="English",
        name="English (Global)",
        google_news_queries=[
            "aquarium",
            "tropical fish",
            "ornamental fish",
            "aquascape",
            "freshwater aquarium",
            "saltwater fish",
            "aquarium sale",
            "fish care",
            "planted tank",
        ],
        system_prompt="""You are AQUA PRESS, an automated aquarium news generator.
Generate a concise, engaging English news script about aquarium topics.
Output format: JSON with 'title' and 'narration_lines' fields.
Keep lines short (max 30 chars) for readability in vertical video format.
Use simple English suitable for global audience.""",
        voicevox_speaker=None,  # Not supported by VOICEVOX
        tts_engine="google",
        tts_language_code="en-US",
        tts_voice_id="en-US-Neural2-A",
        font_name="arial",
        ui_text={
            "loading": "Loading...",
            "generating": "Generating...",
            "uploading": "Uploading...",
            "error": "An error occurred",
        },
    ),
    "zh": LanguageConfig(
        code="zh",
        name_native="中文",
        name="Chinese (Simplified)",
        google_news_queries=[
            "水族箱",
            "热带鱼",
            "观赏鱼",
            "水草",
            "鱼缸",
            "养鱼",
            "水族馆",
            "鱼类养殖",
            "水族爱好",
        ],
        system_prompt="""你是 AQUA PRESS，一个自动化的水族馆新闻生成器。
生成关于水族馆话题的简洁、引人入胜的中文新闻脚本。
输出格式：JSON，包含 'title' 和 'narration_lines' 字段。
保持行短（最多30个字符），便于竖屏视频格式阅读。
使用简体中文。""",
        voicevox_speaker=None,  # Not supported by VOICEVOX
        tts_engine=None,  # TBD in Phase 12
        tts_language_code="zh-CN",
        tts_voice_id=None,
        font_name=None,  # Chinese fonts need special handling
        ui_text={
            "loading": "加载中...",
            "generating": "生成中...",
            "uploading": "上传中...",
            "error": "发生错误",
        },
    ),
    "th": LanguageConfig(
        code="th",
        name_native="ไทย",
        name="Thai",
        google_news_queries=[
            "ตัวอักษรปลา",
            "สัตว์เลี้ยงน้ำ",
            "ปลาสวยงาม",
            "พืชน้ำ",
            "บ่อปลา",
            "เลี้ยงปลา",
            "ตัวอักษร",
            "ปลาน้ำจืด",
            "ปลาทะเล",
        ],
        system_prompt="""คุณคือ AQUA PRESS ผู้สร้างข่าวตัวอักษรอัตโนมัติ
สร้างสคริปต์ข่าวเกี่ยวกับหัวข้อตัวอักษรที่กระชับและน่าสนใจ
รูปแบบเอาต์พุต: JSON พร้อมฟิลด์ 'title' และ 'narration_lines'
เก็บบรรทัดให้สั้น (สูงสุด 30 ตัวอักษร) เพื่อให้อ่านง่ายในรูปแบบวิดีโอแนวตั้ง
ใช้ภาษาไทยที่เรียบง่าย""",
        voicevox_speaker=None,  # Not supported by VOICEVOX
        tts_engine=None,  # TBD in Phase 12
        tts_language_code="th-TH",
        tts_voice_id=None,
        font_name=None,  # Thai fonts need special handling
        ui_text={
            "loading": "กำลังโหลด...",
            "generating": "กำลังสร้าง...",
            "uploading": "กำลังอัพโหลด...",
            "error": "เกิดข้อผิดพลาด",
        },
    ),
}


def get_language_config(language: str = "ja") -> LanguageConfig:
    """Get configuration for specified language."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}. Supported: {SUPPORTED_LANGUAGES}")
    return LANGUAGE_CONFIGS[language]


def get_google_news_queries(language: str = "ja") -> list[str]:
    """Get Google News search queries for language."""
    config = get_language_config(language)
    return config.google_news_queries


def get_system_prompt(language: str = "ja") -> str:
    """Get Gemini system prompt for language."""
    config = get_language_config(language)
    return config.system_prompt
