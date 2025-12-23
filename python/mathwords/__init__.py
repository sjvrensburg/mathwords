"""
mathwords - High-performance Python library for converting LaTeX and MathML to verbalized English text

This library provides a fast, Rust-based backend for converting mathematical expressions
to natural language descriptions.
"""

from .mathwords import verbalize, verbalize_batch, get_speech_styles, __version__

__all__ = [
    "verbalize",
    "verbalize_batch",
    "get_speech_styles",
    "__version__",
]
