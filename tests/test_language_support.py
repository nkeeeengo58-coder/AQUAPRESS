"""Tests for multi-language support (Phase 10)."""

import pytest

from ai.language_config import (
    LANGUAGE_CONFIGS,
    SUPPORTED_LANGUAGES,
    get_google_news_queries,
    get_language_config,
    get_system_prompt,
)


class TestLanguageConfiguration:
    """Test language configuration."""

    def test_supported_languages(self):
        """Test supported languages list."""
        assert SUPPORTED_LANGUAGES == {"ja", "en", "zh", "th"}

    def test_language_configs_complete(self):
        """Test all languages have complete configuration."""
        for lang in SUPPORTED_LANGUAGES:
            assert lang in LANGUAGE_CONFIGS
            config = LANGUAGE_CONFIGS[lang]

            # Verify required fields
            assert config.code == lang
            assert config.name
            assert config.name_native
            assert isinstance(config.google_news_queries, list)
            assert len(config.google_news_queries) > 0
            assert config.system_prompt
            assert config.ui_text is not None

    def test_google_news_queries_per_language(self):
        """Test Google News queries for each language."""
        queries = {
            "ja": get_google_news_queries("ja"),
            "en": get_google_news_queries("en"),
            "zh": get_google_news_queries("zh"),
            "th": get_google_news_queries("th"),
        }

        for lang, q_list in queries.items():
            assert len(q_list) > 5, f"Language {lang} should have multiple queries"
            assert all(isinstance(q, str) for q in q_list), f"Language {lang} queries must be strings"

    def test_system_prompt_per_language(self):
        """Test Gemini system prompts for each language."""
        for lang in SUPPORTED_LANGUAGES:
            prompt = get_system_prompt(lang)
            assert len(prompt) > 50, f"Prompt for {lang} too short"
            assert "JSON" in prompt or "json" in prompt, f"Prompt for {lang} should mention JSON format"


class TestLanguageConfigAccess:
    """Test language configuration access methods."""

    def test_get_language_config_valid(self):
        """Test get_language_config with valid languages."""
        for lang in SUPPORTED_LANGUAGES:
            config = get_language_config(lang)
            assert config.code == lang

    def test_get_language_config_invalid(self):
        """Test get_language_config with invalid language."""
        with pytest.raises(ValueError):
            get_language_config("invalid")

    def test_get_language_config_default(self):
        """Test get_language_config default (Japanese)."""
        config = get_language_config()
        assert config.code == "ja"

    def test_get_google_news_queries_default(self):
        """Test get_google_news_queries default (Japanese)."""
        queries = get_google_news_queries()
        assert len(queries) > 0
        assert "アクアリウム" in queries

    def test_get_system_prompt_default(self):
        """Test get_system_prompt default (Japanese)."""
        prompt = get_system_prompt()
        assert "日本語" in prompt or "Japanese" in prompt


class TestLanguageSpecificContent:
    """Test language-specific content."""

    def test_japanese_queries_contain_japanese(self):
        """Test Japanese queries are in Japanese."""
        ja_config = get_language_config("ja")
        # At least some queries should be in Japanese
        ja_chars = sum(1 for q in ja_config.google_news_queries if any(ord(c) > 0x3000 for c in q))
        assert ja_chars > 0, "Japanese config should have Japanese queries"

    def test_english_queries_contain_english(self):
        """Test English queries are in English."""
        en_config = get_language_config("en")
        # All queries should contain English words
        assert all(
            any(c.isalpha() for c in q) for q in en_config.google_news_queries
        ), "English queries should contain English letters"

    def test_ui_text_translations(self):
        """Test UI text is translated for each language."""
        ui_keys = {"loading", "generating", "uploading", "error"}

        for lang in SUPPORTED_LANGUAGES:
            config = get_language_config(lang)
            for key in ui_keys:
                assert key in config.ui_text, f"Missing UI text key '{key}' for {lang}"
                assert isinstance(config.ui_text[key], str), f"UI text for '{key}' in {lang} should be string"
                assert len(config.ui_text[key]) > 0, f"UI text for '{key}' in {lang} should not be empty"


class TestLanguageVoiceover:
    """Test language voiceover configuration."""

    def test_japanese_voiceover_supported(self):
        """Test Japanese has VOICEVOX speaker assigned."""
        ja_config = get_language_config("ja")
        assert ja_config.voicevox_speaker is not None
        assert isinstance(ja_config.voicevox_speaker, int)

    def test_other_languages_voiceover_tbd(self):
        """Test other languages are marked as TBD."""
        for lang in ["en", "zh", "th"]:
            config = get_language_config(lang)
            assert config.voicevox_speaker is None, f"{lang} should have voicevox_speaker=None (TBD)"


class TestLanguagePrompts:
    """Test language prompts for AI generation."""

    def test_prompt_includes_output_format(self):
        """Test prompts specify JSON output format."""
        for lang in SUPPORTED_LANGUAGES:
            prompt = get_system_prompt(lang)
            # Should mention JSON format in some way
            assert (
                "json" in prompt.lower() or "JSON" in prompt
            ), f"Prompt for {lang} should specify JSON format"

    def test_prompt_includes_length_guidance(self):
        """Test prompts include line length guidance."""
        for lang in SUPPORTED_LANGUAGES:
            prompt = get_system_prompt(lang)
            # Should mention character or length constraints
            assert (
                "30" in prompt or "short" in prompt.lower() or "brief" in prompt.lower()
            ), f"Prompt for {lang} should include length guidance"


class TestLanguageConfigCompleteness:
    """Test language configuration completeness."""

    def test_all_languages_have_names(self):
        """Test all languages have both native and English names."""
        for lang in SUPPORTED_LANGUAGES:
            config = get_language_config(lang)
            assert config.name, f"{lang} missing 'name' field"
            assert config.name_native, f"{lang} missing 'name_native' field"
            # Names should be different
            assert (
                config.name.lower() != config.name_native.lower()
            ), f"{lang} name fields should differ"

    def test_queries_are_reasonable_length(self):
        """Test all queries are reasonable length."""
        for lang in SUPPORTED_LANGUAGES:
            queries = get_google_news_queries(lang)
            for query in queries:
                assert (
                    1 < len(query) < 100
                ), f"Query '{query}' in {lang} has unreasonable length"

    def test_prompts_are_substantial(self):
        """Test all prompts are substantial."""
        for lang in SUPPORTED_LANGUAGES:
            prompt = get_system_prompt(lang)
            assert len(prompt) > 100, f"Prompt for {lang} is too short"
            assert len(prompt) < 5000, f"Prompt for {lang} is too long"
