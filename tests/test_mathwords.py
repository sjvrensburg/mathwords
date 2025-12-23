"""
Test suite for mathwords library
"""

import pytest


def test_import():
    """Test that the module can be imported"""
    import mathwords
    assert hasattr(mathwords, 'verbalize')
    assert hasattr(mathwords, 'verbalize_batch')
    assert hasattr(mathwords, 'get_speech_styles')


def test_simple_latex():
    """Test simple LaTeX conversion"""
    import mathwords
    result = mathwords.verbalize("x^2")
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"x^2 -> {result}")


def test_equation():
    """Test equation conversion"""
    import mathwords
    result = mathwords.verbalize(r"x^2 + y^2 = z^2")
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"x^2 + y^2 = z^2 -> {result}")


def test_fraction():
    """Test fraction conversion"""
    import mathwords
    result = mathwords.verbalize(r"\frac{a}{b}")
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"\\frac{{a}}{{b}} -> {result}")


def test_display_mode():
    """Test display mode"""
    import mathwords
    inline = mathwords.verbalize(r"\sum_{i=1}^{n} i", display_mode=False)
    display = mathwords.verbalize(r"\sum_{i=1}^{n} i", display_mode=True)
    assert isinstance(inline, str)
    assert isinstance(display, str)
    print(f"Inline: {inline}")
    print(f"Display: {display}")


def test_speech_styles():
    """Test different speech styles"""
    import mathwords
    clear = mathwords.verbalize("x^2", speech_style="ClearSpeak")
    simple = mathwords.verbalize("x^2", speech_style="SimpleSpeak")
    assert isinstance(clear, str)
    assert isinstance(simple, str)
    print(f"ClearSpeak: {clear}")
    print(f"SimpleSpeak: {simple}")


def test_batch_conversion():
    """Test batch conversion"""
    import mathwords
    expressions = [
        ("x^2", None),
        (r"\frac{a}{b}", False),
        ("y + 2", None),
    ]
    results = mathwords.verbalize_batch(expressions)
    assert len(results) == 3
    assert all(isinstance(r, str) for r in results)
    for expr, result in zip(expressions, results):
        print(f"{expr[0]} -> {result}")


def test_empty_input_error():
    """Test that empty input raises ValueError"""
    import mathwords
    with pytest.raises(ValueError):
        mathwords.verbalize("")


def test_empty_batch_error():
    """Test that empty batch raises ValueError"""
    import mathwords
    with pytest.raises(ValueError):
        mathwords.verbalize_batch([])


def test_get_speech_styles():
    """Test getting available speech styles"""
    import mathwords
    styles = mathwords.get_speech_styles()
    assert isinstance(styles, list)
    assert len(styles) > 0
    assert "ClearSpeak" in styles
    print(f"Available styles: {styles}")


def test_version():
    """Test that version is available"""
    import mathwords
    assert hasattr(mathwords, '__version__')
    assert isinstance(mathwords.__version__, str)
    print(f"Version: {mathwords.__version__}")


if __name__ == "__main__":
    # Run tests with output
    pytest.main([__file__, "-v", "-s"])
