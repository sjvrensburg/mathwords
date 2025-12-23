"""Type stubs for mathwords"""

from typing import List, Tuple, Optional

__version__: str

def verbalize(
    input_str: str,
    is_mathml: bool = False,
    speech_style: str = "ClearSpeak",
    display_mode: bool = False,
) -> str:
    """
    Convert LaTeX or MathML input to English verbalized text.

    Args:
        input_str: The LaTeX or MathML string to convert
        is_mathml: If True, input is treated as MathML; if False, as LaTeX (default: False)
        speech_style: Speech style for verbalization - "ClearSpeak", "SimpleSpeak", etc. (default: "ClearSpeak")
        display_mode: For LaTeX input, whether to treat as display (block) mode (default: False)

    Returns:
        Verbalized English text string

    Raises:
        ValueError: If input is invalid or empty
        RuntimeError: If conversion fails

    Example:
        >>> import mathwords
        >>> mathwords.verbalize("x^2 + y^2 = z^2")
        'x squared plus y squared equals z squared'
        >>> mathwords.verbalize("<math><mi>x</mi></math>", is_mathml=True)
        'x'
    """
    ...

def verbalize_batch(
    expressions: List[Tuple[str, Optional[bool]]],
    speech_style: str = "ClearSpeak",
    display_mode: bool = False,
) -> List[str]:
    """
    Batch verbalize multiple expressions.

    Args:
        expressions: List of (input_str, is_mathml) tuples. is_mathml can be None (defaults to False)
        speech_style: Speech style for verbalization (default: "ClearSpeak")
        display_mode: For LaTeX inputs, default display mode (default: False)

    Returns:
        List of verbalized English text strings

    Raises:
        ValueError: If expression list is empty
        RuntimeError: If any conversion fails

    Example:
        >>> import mathwords
        >>> mathwords.verbalize_batch([
        ...     ("x^2", None),
        ...     ("\\frac{a}{b}", None),
        ... ])
        ['x squared', 'a over b']
    """
    ...

def get_speech_styles() -> List[str]:
    """
    Get list of available speech styles.

    Returns:
        List of available speech style names

    Example:
        >>> import mathwords
        >>> mathwords.get_speech_styles()
        ['ClearSpeak', 'SimpleSpeak']
    """
    ...
