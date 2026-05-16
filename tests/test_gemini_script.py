from __future__ import annotations

import json

import pytest

from ai.gemini_script import generate_script_from_text, merge_script_into_video_data, validate_script_schema


def test_validate_script_schema_accepts_minimum_payload() -> None:
    payload = {
        "title": "速報: 新着個体",
        "description": "説明",
        "hook": "速報\n新着",
        "sections": [{"caption": "1つ目"}, {"caption": "2つ目"}],
        "narration_text": "ナレーション",
        "cta": "保存してチェック",
    }
    validate_script_schema(payload)


def test_validate_script_schema_rejects_missing_sections() -> None:
    payload = {
        "title": "速報",
        "hook": "導入",
        "sections": [],
        "narration_text": "本文",
    }
    with pytest.raises(ValueError):
        validate_script_schema(payload)


def test_merge_script_into_video_data_preserves_images() -> None:
    base_data = {
        "title": "old",
        "hook": "old",
        "sections": [
            {"image": "input/images/sample1.jpg", "caption": "old1"},
            {"image": "input/images/sample2.jpg", "caption": "old2"},
        ],
        "narration_text": "old",
    }
    script_data = {
        "title": "new title",
        "description": "new desc",
        "hook": "new hook",
        "sections": [{"caption": "cap1"}, {"caption": "cap2"}],
        "narration_text": "new narration",
        "cta": "save",
    }

    merged = merge_script_into_video_data(base_data, script_data)

    assert merged["title"] == "new title"
    assert merged["hook"] == "new hook"
    assert merged["narration_text"] == "new narration"
    assert merged["sections"][0]["image"] == "input/images/sample1.jpg"
    assert merged["sections"][1]["image"] == "input/images/sample2.jpg"
    assert merged["sections"][0]["caption"] == "cap1"


def test_generate_script_from_text_uses_mocked_api(monkeypatch: pytest.MonkeyPatch) -> None:
    class _DummyResponse:
        def __init__(self, body: dict):
            self._body = body

        def read(self) -> bytes:
            return json.dumps(self._body).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(_req, timeout=30):
        del timeout
        body = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"title":"T","description":"D","hook":"H","sections":[{"caption":"C1"}],"narration_text":"N","cta":"CTA"}'
                            }
                        ]
                    }
                }
            ]
        }
        return _DummyResponse(body)

    monkeypatch.setattr("ai.gemini_script.request.urlopen", _fake_urlopen)
    result = generate_script_from_text("入荷情報", api_key="dummy")

    assert result["title"] == "T"
    assert result["sections"][0]["caption"] == "C1"


def test_generate_script_from_text_requires_api_key() -> None:
    with pytest.raises(ValueError):
        generate_script_from_text("入荷情報", api_key="")