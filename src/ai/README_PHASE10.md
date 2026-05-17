# Phase 10: Multi-Language Support

## Overview

Phase 10 implements multi-language support for AQUA PRESS, enabling video generation in multiple languages: Japanese (日本語), English, Chinese (中文), and Thai (ไทย).

## Architecture

### 1. Language Configuration Module (`src/ai/language_config.py`)

New module that centralizes all language-specific settings:

```python
LanguageConfig:
  - code: Language identifier (ja, en, zh, th)
  - name & name_native: Display names
  - google_news_queries: List of search queries for each language
  - system_prompt: Language-specific Gemini prompt
  - voicevox_speaker: Speaker ID (if supported)
  - font_name: Font configuration
  - ui_text: Translated UI text
```

### 2. Crawler Language Support (`src/crawler/__init__.py`)

- `run_crawler(language="ja")`: Now accepts language parameter
- `_get_language_specific_rss_feeds()`: Generates language-specific Google News feeds
- Dynamically creates RSS feed URLs based on language-specific search queries

### 3. Gemini Script Generation (`src/ai/gemini_script.py`)

- `generate_script_from_text(info_text, language="ja")`: Added language parameter
- `_build_prompt(info_text, language="ja")`: Uses language-specific system prompt
- Language-aware script generation for title, narration, and captions

### 4. Main Workflow (`src/main.py`)

- Added `--language` CLI parameter (choices: ja, en, zh, th)
- Passes language parameter through entire pipeline:
  - Crawler → Gemini → Video Generation

### 5. Comprehensive Tests (`tests/test_language_support.py`)

19 new tests covering:
- ✅ Language configuration completeness
- ✅ Query generation per language
- ✅ System prompt validation
- ✅ Language-specific content
- ✅ Voiceover configuration
- ✅ Translation completeness

## Supported Languages

### Japanese (日本語) - `ja`
- **Status**: ✅ Fully Supported
- **Queries**: アクアリウム, 熱帯魚, 観賞魚, 水草, etc. (9 queries)
- **VOICEVOX**: Speaker ID 3 (Supported)
- **Font**: Arial

### English (Global) - `en`
- **Status**: 🔄 Partial (Voice TBD)
- **Queries**: aquarium, tropical fish, ornamental fish, aquascape, etc. (9 queries)
- **VOICEVOX**: TBD (Future enhancement)
- **Font**: Arial

### Chinese (中文) - `zh`
- **Status**: 🔄 Partial (Voice & Fonts TBD)
- **Queries**: 水族箱, 热带鱼, 观赏鱼, 水草, etc. (9 queries)
- **VOICEVOX**: TBD
- **Font**: TBD (needs CJK font support)

### Thai (ไทย) - `th`
- **Status**: 🔄 Partial (Voice & Fonts TBD)
- **Queries**: ตัวอักษรปลา, สัตว์เลี้ยงน้ำ, ปลาสวยงาม, etc. (9 queries)
- **VOICEVOX**: TBD
- **Font**: TBD (needs Thai font support)

## Usage

### Command Line

```bash
# Generate video in Japanese (default)
python -m src.main --crawler

# Generate video in English
python -m src.main --crawler --language en

# Generate video in Chinese
python -m src.main --crawler --language zh

# Generate video in Thai
python -m src.main --crawler --language th

# Generate from text (English)
python -m src.main --info "Aquarium news text" --language en

# Use saved crawler data (Japanese)
python -m src.main --crawler-date 2025-01-21 --language ja
```

### Python API

```python
from crawler import run_crawler
from ai.gemini_script import generate_script_from_text

# Fetch language-specific news
crawler_result = run_crawler(language="en")

# Generate English script
script = generate_script_from_text(
    info_text="Latest aquarium information",
    language="en"
)
```

## Implementation Details

### Language Configuration Approach

Each language has:
- **Multiple search queries** (5-9 per language) for diverse news coverage
- **Language-specific Gemini prompts** that provide context-appropriate generation
- **Translated UI text** for user interface messages
- **Placeholder support** for future voiceover and font configurations

### Google News RSS Integration

- Generates language-specific Google News RSS URLs:
  ```
  https://news.google.com/rss/search?q={query}
  ```
- Each language supports 5-9 curated search queries
- Queries are optimized for aquarium-related content in each language

### System Prompts

Each language has a specialized Gemini prompt that:
1. Specifies the language for output
2. Provides format instructions (JSON output)
3. Includes length guidance (max 30 chars per line for vertical video)
4. Emphasizes clarity and brevity

Example:
- **Japanese**: Includes cultural context and natural Japanese phrasing
- **English**: Emphasizes global audience accessibility
- **Chinese**: Uses simplified characters
- **Thai**: Adapted to Thai grammar and syntax

## Test Coverage

**File**: `tests/test_language_support.py`

**Test Classes**:
1. `TestLanguageConfiguration` - Validates config completeness
2. `TestLanguageConfigAccess` - Tests helper functions
3. `TestLanguageSpecificContent` - Validates language-specific queries and prompts
4. `TestLanguageVoiceover` - Tests voiceover configuration
5. `TestLanguagePrompts` - Tests AI generation prompts
6. `TestLanguageConfigCompleteness` - Tests overall configuration quality

**Test Results**: 19/19 passing ✅

## Future Enhancements

### Phase 11 (Recommended Next Steps):

1. **Voiceover Support for Non-Japanese Languages**
   - Integrate Google Cloud Text-to-Speech API
   - Add support for en, zh, th voice synthesis
   - Configuration per language

2. **Dynamic Font Support**
   - Implement CJK (Chinese, Japanese, Korean) font fallback
   - Add Thai font support for video captions
   - Font selection based on language

3. **Multi-Language Video Batching**
   - Generate multiple language versions in single run
   - Parallel processing capability
   - Metadata tracking for each language variant

4. **Translation Service Integration**
   - Automatic crawled content translation
   - Multi-language output from single source
   - Google Translate API integration

5. **Language-Specific Formatting**
   - Adapt typography for each language (RTL support)
   - Regional number/date formatting
   - Cultural adaptation of visuals

## Files Modified

1. ✅ `src/ai/language_config.py` - NEW
2. ✅ `src/ai/gemini_script.py` - Modified (added language parameter)
3. ✅ `src/crawler/__init__.py` - Modified (language support)
4. ✅ `src/main.py` - Modified (CLI parameter + language flow)
5. ✅ `tests/test_language_support.py` - NEW (19 tests)

## Test Statistics

Before Phase 10:
- 44 tests passing
- 8 tests skipped

After Phase 10:
- **63 tests passing** ✅
- **8 tests skipped** (YouTube uploader tests)
- **19 new language tests** ✅

## Configuration Examples

### Adding a New Language

To add a new language (e.g., Korean), modify `src/ai/language_config.py`:

```python
"ko": LanguageConfig(
    code="ko",
    name_native="한국어",
    name="Korean",
    google_news_queries=[
        "수족관",
        "열대어",
        "관상어",
        # ... more queries
    ],
    system_prompt="Korean-specific Gemini prompt...",
    voicevox_speaker=None,  # TBD
    font_name=None,  # TBD
    ui_text={
        "loading": "로드 중...",
        "generating": "생성 중...",
        "uploading": "업로드 중...",
        "error": "오류가 발생했습니다",
    },
)
```

## Troubleshooting

### Issue: Language configuration not found
```
ValueError: Unsupported language: xx. Supported: {'ja', 'en', 'zh', 'th'}
```
**Solution**: Ensure language code is one of supported values.

### Issue: Google News RSS feed returns no results
**Solution**: Check that search queries are valid and relevant to the language.

### Issue: Gemini generates content in wrong language
**Solution**: Verify language parameter is passed to `generate_script_from_text()`.

## Performance Notes

- Crawler with language support: ~5-10 queries per language
- Average crawler runtime: 10-30 seconds per language
- Gemini script generation: 5-15 seconds per request
- No significant performance impact from language parameter

## Quality Assurance

✅ All 19 language tests passing
✅ All 44 existing tests still passing
✅ No breaking changes to existing functionality
✅ Backward compatible (default language = Japanese)
✅ Code properly documented with docstrings
✅ Language-specific test coverage for all supported languages
