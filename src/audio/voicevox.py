from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import parse, request
from urllib.error import HTTPError, URLError

from utils.paths import get_project_root


DEFAULT_VOICEVOX_ENGINE_URL = os.getenv("VOICEVOX_ENGINE_URL", "http://127.0.0.1:50021")
DEFAULT_SPEAKER = 3


def synthesize_voicevox(
    text: str,
    output_path: str | Path | None,
    speaker: int = DEFAULT_SPEAKER,
    engine_url: str = DEFAULT_VOICEVOX_ENGINE_URL,
    speed_scale: float = 1.0,
    pitch_scale: float = 0.0,
    intonation_scale: float = 1.0,
    volume_scale: float = 1.0,
    pre_phoneme_length: float = 0.1,
    post_phoneme_length: float = 0.1,
    silence_length: float = 0.0,
) -> Path | None:
    if not text or not text.strip():
        return None

    if output_path is None:
        output_path = get_project_root() / "output" / "audio" / "voicevox_narration.wav"

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        query = _build_audio_query(
            text=text,
            speaker=speaker,
            engine_url=engine_url,
            speed_scale=speed_scale,
            pitch_scale=pitch_scale,
            intonation_scale=intonation_scale,
            volume_scale=volume_scale,
            pre_phoneme_length=pre_phoneme_length,
            post_phoneme_length=post_phoneme_length,
            silence_length=silence_length,
        )
        wav_bytes = _request_synthesis(query=query, speaker=speaker, engine_url=engine_url)
        output_file.write_bytes(wav_bytes)
        return output_file
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[WARN] VOICEVOX synthesis failed: {exc}")
        return None


def _build_audio_query(
    text: str,
    speaker: int,
    engine_url: str,
    speed_scale: float,
    pitch_scale: float,
    intonation_scale: float,
    volume_scale: float,
    pre_phoneme_length: float,
    post_phoneme_length: float,
    silence_length: float,
) -> dict:
    url = f"{engine_url.rstrip('/')}/audio_query"
    params = parse.urlencode({"text": text, "speaker": speaker})
    req = request.Request(f"{url}?{params}", data=b"", method="POST")
    with request.urlopen(req, timeout=30) as response:
        query = json.loads(response.read().decode("utf-8"))

    query["speedScale"] = speed_scale
    query["pitchScale"] = pitch_scale
    query["intonationScale"] = intonation_scale
    query["volumeScale"] = volume_scale
    query["prePhonemeLength"] = pre_phoneme_length
    query["postPhonemeLength"] = post_phoneme_length
    query["outputSamplingRate"] = int(query.get("outputSamplingRate", 24000))
    query["outputStereo"] = bool(query.get("outputStereo", False))
    query["kana"] = query.get("kana", "")
    query["silenceLength"] = silence_length
    return query


def _request_synthesis(query: dict, speaker: int, engine_url: str) -> bytes:
    url = f"{engine_url.rstrip('/')}/synthesis?speaker={speaker}"
    data = json.dumps(query).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = request.Request(url, data=data, headers=headers, method="POST")
    with request.urlopen(req, timeout=60) as response:
        return response.read()
