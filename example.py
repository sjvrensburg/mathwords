#!/usr/bin/env python3
"""
Example usage of mathwords library
"""

import mathwords


def main():
    print("=" * 70)
    print("mathwords - LaTeX/MathML to English Text Verbalization")
    print("=" * 70)
    print()

    # Example 1: Simple expressions
    print("1. Simple Expressions")
    print("-" * 70)
    examples = [
        "x^2",
        "a + b",
        r"\sqrt{2}",
        r"x^2 + y^2 = z^2",
    ]

    for latex in examples:
        speech = mathwords.verbalize(latex)
        print(f"  {latex:30s} -> {speech}")
    print()

    # Example 2: Fractions
    print("2. Fractions")
    print("-" * 70)
    fractions = [
        r"\frac{1}{2}",
        r"\frac{a}{b}",
        r"\frac{x^2 + 1}{x - 1}",
    ]

    for latex in fractions:
        speech = mathwords.verbalize(latex)
        print(f"  {latex:30s} -> {speech}")
    print()

    # Example 3: Summations and Integrals
    print("3. Summations and Integrals (Display Mode)")
    print("-" * 70)
    calculus = [
        r"\sum_{i=1}^{n} i",
        r"\int_{0}^{1} x^2 dx",
        r"\prod_{i=1}^{n} x_i",
    ]

    for latex in calculus:
        speech = mathwords.verbalize(latex, display_mode=True)
        print(f"  {latex:30s} -> {speech}")
    print()

    # Example 4: Speech Styles
    print("4. Different Speech Styles")
    print("-" * 70)
    test_expr = r"\frac{x^2}{y}"

    for style in mathwords.get_speech_styles():
        speech = mathwords.verbalize(test_expr, speech_style=style)
        print(f"  {style:15s}: {speech}")
    print()

    # Example 5: Batch Processing
    print("5. Batch Processing")
    print("-" * 70)
    batch = [
        ("x + y", None),
        ("a^2 + b^2", False),
        (r"\sin(x)", None),
    ]

    results = mathwords.verbalize_batch(batch)
    for (expr, _), result in zip(batch, results):
        print(f"  {expr:30s} -> {result}")
    print()

    # Example 6: Matrix
    print("6. Matrix")
    print("-" * 70)
    matrix = r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}"
    speech = mathwords.verbalize(matrix, display_mode=True)
    print(f"  {matrix}")
    print(f"  -> {speech}")
    print()

    print("=" * 70)
    print(f"mathwords version: {mathwords.__version__}")
    print("=" * 70)


if __name__ == "__main__":
    main()
