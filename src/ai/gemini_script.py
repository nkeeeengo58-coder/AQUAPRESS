from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any
from urllib import error, parse, request

from dotenv import load_dotenv

from ai.language_config import get_system_prompt

load_dotenv()


DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"


def generate_script_from_text(
    info_text: str,
    *,
    language: str = "ja",
    api_key: str | None = None,
    model: str | None = None,
    endpoint: str | None = None,
    temperature: float = 0.7,
    timeout: int = 30,
) -> dict[str, Any]:
    """Generate script from text using Gemini API.
    
    Args:
        info_text: Input information text.
        language: Target language (ja, en, zh, th). Defaults to 'ja'.
        api_key: Gemini API key. If not provided, uses GEMINI_API_KEY env var.
        model: Gemini model to use. If not provided, uses default.
        endpoint: Gemini API endpoint. If not provided, uses default.
        temperature: Temperature for generation.
        timeout: Request timeout in seconds.
        
    Returns:
        Generated script data as dictionary.
    """
    if not info_text or not info_text.strip():
        raise ValueError("info_text must not be empty")

    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")

    chosen_model = model or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    chosen_endpoint = endpoint or os.getenv("GEMINI_API_ENDPOINT") or DEFAULT_GEMINI_ENDPOINT
    prompt = _build_prompt(info_text, language=language)

    response_json = _request_gemini(
        api_key=key,
        model=chosen_model,
        endpoint=chosen_endpoint,
        prompt=prompt,
        temperature=temperature,
        timeout=timeout,
    )
    script_data = _parse_response_script(response_json)
    validate_script_schema(script_data)
    return script_data


def validate_script_schema(script_data: dict[str, Any]) -> None:
    required_text_fields = ["title", "hook", "narration_text"]
    for key in required_text_fields:
        value = script_data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"script field '{key}' must be a non-empty string")

    sections = script_data.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("script field 'sections' must be a non-empty list")

    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"script section[{idx}] must be an object")
        caption = section.get("caption")
        if not isinstance(caption, str) or not caption.strip():
            raise ValueError(f"script section[{idx}].caption must be a non-empty string")


def merge_script_into_video_data(base_data: dict[str, Any], script_data: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base_data)
    merged["title"] = script_data["title"].strip()
    merged["hook"] = script_data["hook"].strip()
    merged["narration_text"] = script_data["narration_text"].strip()

    if isinstance(script_data.get("description"), str) and script_data["description"].strip():
        merged["description"] = script_data["description"].strip()

    base_sections = merged.get("sections") if isinstance(merged.get("sections"), list) else []
    generated_sections = script_data.get("sections", [])
    sections: list[dict[str, Any]] = []
    for idx, generated in enumerate(generated_sections):
        section: dict[str, Any] = {"image": None, "caption": generated["caption"].strip()}
        if idx < len(base_sections) and isinstance(base_sections[idx], dict):
            section["image"] = base_sections[idx].get("image")
        sections.append(section)
    merged["sections"] = sections
    return merged


def _build_prompt(info_text: str, language: str = "ja") -> str:
    """Build Gemini prompt for script generation in specified language.
    
    Args:
        info_text: Input information text.
        language: Target language (ja, en, zh, th).
        
    Returns:
        Prompt string for Gemini API.
    """
    system_prompt = get_system_prompt(language)
    
    return (
        f"{system_prompt}\n\n"
        "必須キーは title, description, hook, sections, narration_text, cta。\n"
        "sections は2-4件で、各要素は {\"caption\": \"...\"} を返してください。\n"
        "hook は改行を含めて短く強い導入にしてください。\n"
        "narration_text は自然なニュース読み上げ文にしてください。\n"
        "入力情報:\n"
        f"{info_text.strip()}"
    )


def _request_gemini(
    *,
    api_key: str,
    model: str,
    endpoint: str,
    prompt: str,
    temperature: float,
    timeout: int,
) -> dict[str, Any]:
    base = endpoint.rstrip("/")
    safe_model = parse.quote(model, safe="")
    url = f"{base}/{safe_model}:generateContent?key={parse.quote(api_key, safe='')}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": float(temperature),
            "responseMimeType": "application/json",
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
        raise ValueError(f"Gemini API HTTP error: {exc.code} {body}") from exc
    except error.URLError as exc:
        raise ValueError(f"Gemini API connection error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini API returned invalid JSON: {exc}") from exc


def _parse_response_script(response_json: dict[str, Any]) -> dict[str, Any]:
    text_chunks: list[str] = []
    for candidate in response_json.get("candidates", []):
        content = candidate.get("content", {}) if isinstance(candidate, dict) else {}
        for part in content.get("parts", []) if isinstance(content, dict) else []:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                text_chunks.append(part["text"])

    raw_text = "\n".join(text_chunks).strip()
    if not raw_text:
        raise ValueError("Gemini API returned no text content")

    json_text = _extract_json(raw_text)
    parsed = json.loads(json_text)
    if not isinstance(parsed, dict):
        raise ValueError("Gemini output must be a JSON object")
    return parsed


def _extract_json(raw_text: str) -> str:
    stripped = raw_text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Gemini output does not contain JSON object")
    return stripped[start : end + 1]