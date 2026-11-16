"""Conservative, deterministic cleaning that never overwrites source evidence."""

import re
from html import unescape

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"[^\S\n]+")
_BOILERPLATE_RE = re.compile(
    r"(?im)^\s*(?:apply now|share this job|cookie(?:s)?(?: policy)?|"
    r"privacy policy|back to search|sign in)\s*$"
)


def clean_description(text: str) -> str:
    """Remove obvious presentation boilerplate while retaining job text and line breaks."""
    text = unescape(_TAG_RE.sub(" ", text)).replace("\r\n", "\n").replace("\r", "\n")
    text = _BOILERPLATE_RE.sub("", text)
    lines = [_SPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def normalize_title(value: str) -> str:
    return normalize_text(value)


def normalize_company(value: str) -> str:
    normalized = normalize_text(value)
    return re.sub(r"\b(incorporated|inc|ltd|limited|ag|gmbh|sa)\b", "", normalized).strip()


def normalize_location(value: str | None) -> str:
    return normalize_text(value)
