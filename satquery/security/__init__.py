"""
SatQuery AI — Security & Input Sanitization Framework.
Protects against path traversal, malicious file uploads, and prompt injection attacks.
"""

from .sanitizer import (
    SecurityError,
    sanitize_query,
    validate_file_magic,
    validate_safe_path,
)

__all__ = [
    "SecurityError",
    "sanitize_query",
    "validate_file_magic",
    "validate_safe_path",
]
