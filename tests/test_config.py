import sys
from pathlib import Path
from typing import Iterable

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings


def _load_settings(monkeypatch: pytest.MonkeyPatch, value: str):
    monkeypatch.setenv("CORS_ORIGINS", value)
    settings = Settings()
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    return settings


@pytest.mark.parametrize(
    "raw_value,expected",
    [
        ("", []),
        ("https://example.com", ["https://example.com"]),
        (
            "https://example.com, https://another.example",
            ["https://example.com", "https://another.example"],
        ),
    ],
)
def test_cors_origins_from_env(raw_value: str, expected: Iterable[str], monkeypatch):
    settings = _load_settings(monkeypatch, raw_value)
    assert settings.cors_origins == list(expected)
