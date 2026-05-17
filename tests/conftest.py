from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Mock google-cloud-texttospeech if not installed
try:
    from google.cloud import texttospeech  # noqa: F401
except ImportError:
    # Create mock module
    mock_texttospeech = mock.MagicMock()
    sys.modules["google"] = mock.MagicMock()
    sys.modules["google.cloud"] = mock.MagicMock()
    sys.modules["google.cloud.texttospeech"] = mock_texttospeech
