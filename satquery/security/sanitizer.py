"""
SatQuery AI — Input Sanitization and Security Guards.

Provides defense-in-depth protections:
1. Path traversal mitigation for user-supplied filenames and session paths.
2. File magic bytes verification (GeoTIFF, PNG, JPEG) and blocking of dangerous MIME types.
3. Prompt injection detection and neutralizer for autonomous agent queries.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityError(ValueError):
    """Raised when an operation violates security policy or input constraints."""
    pass


# Magic bytes signatures
MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "tiff": [b"II*\x00", b"MM\x00*"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpeg": [b"\xff\xd8\xff"],
}

# Blocked dangerous headers (executables, scripts, HTML)
BLOCKED_SIGNATURES: list[bytes] = [
    b"MZ",                 # Windows PE executable
    b"\x7fELF",            # Linux ELF executable
    b"#!/",                # Shell script
    b"<?php",              # PHP script
    b"<script",            # HTML/JS payload
    b"<!DOCTYPE html",     # HTML document
]

# Prompt injection patterns commonly used in adversarial LLM jailbreaks
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|system)\s+(instructions?|rules?|prompts?)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|unrestricted)", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?(system\s+prompt|developer\s+instructions|hidden\s+rules)", re.IGNORECASE),
    re.compile(r"system\s*:\s*override", re.IGNORECASE),
    re.compile(r"bypass\s+(safety|content)\s+filters?", re.IGNORECASE),
]


def validate_safe_path(filename_or_path: str | Path, base_dir: str | Path) -> Path:
    """
    Validates that a path is strictly contained within base_dir.
    Guards against directory traversal (../, ..\\, absolute paths, null bytes).
    """
    str_path = str(filename_or_path)

    # Check for null bytes
    if "\x00" in str_path:
        raise SecurityError("Null byte detected in file path.")

    # Check for suspicious traversal substrings
    if ".." in str_path.replace("\\", "/").split("/"):
        raise SecurityError(f"Directory traversal sequence detected in path: '{str_path}'")

    base_resolved = Path(base_dir).resolve()
    # Resolve relative to base_dir
    target_resolved = (base_resolved / Path(filename_or_path).name).resolve()

    try:
        target_resolved.relative_to(base_resolved)
    except ValueError as e:
        raise SecurityError(f"Path traversal violation: '{str_path}' escapes '{base_resolved}'") from e

    return target_resolved


def validate_file_magic(file_bytes: bytes, allowed_formats: list[str] | None = None) -> str:
    """
    Validates file content using binary magic signatures.
    Returns the detected format string (e.g. 'tiff', 'png', 'jpeg').
    """
    if not file_bytes:
        raise SecurityError("Uploaded file is empty (0 bytes).")

    # Check for blocked executable or script signatures
    for blocked in BLOCKED_SIGNATURES:
        if file_bytes.startswith(blocked):
            raise SecurityError(f"Prohibited executable or script file detected ({blocked!r}).")

    if allowed_formats is None:
        allowed_formats = ["tiff", "png", "jpeg"]

    detected_format: str | None = None
    for fmt, signatures in MAGIC_SIGNATURES.items():
        if fmt in allowed_formats:
            for sig in signatures:
                if file_bytes.startswith(sig):
                    detected_format = fmt
                    break
        if detected_format:
            break

    if not detected_format:
        raise SecurityError(
            f"Unsupported or invalid file format. File does not match allowed magic bytes for {allowed_formats}."
        )

    return detected_format


def sanitize_query(query: str, strict: bool = False) -> str:
    """
    Sanitizes user queries:
    1. Removes control characters and null bytes.
    2. Strips surrounding whitespace.
    3. Detects and neutralizes prompt injection patterns.
    """
    if not isinstance(query, str):
        raise SecurityError("Query must be a valid text string.")

    # Remove null bytes and control characters except basic newlines and tabs
    cleaned = "".join(ch for ch in query if ch == "\n" or ch == "\t" or (32 <= ord(ch) <= 126 or ord(ch) > 127))
    cleaned = cleaned.strip()

    if not cleaned:
        raise SecurityError("Query is empty after sanitization.")

    if len(cleaned) > 2000:
        raise SecurityError("Query exceeds maximum allowed length of 2000 characters.")

    # Check for prompt injection
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(cleaned):
            if strict:
                raise SecurityError(f"Prompt injection pattern detected: '{pattern.pattern}'")
            logger.warning("Sanitizing detected prompt injection attempt in query: %s", cleaned)
            # Neutralize matched jailbreak phrase
            cleaned = pattern.sub("[REDACTED_INJECTION_ATTEMPT]", cleaned)

    return cleaned.strip()
