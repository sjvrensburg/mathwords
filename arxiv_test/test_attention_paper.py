#!/usr/bin/env python3
"""
Comprehensive test of mathwords on the "Attention Is All You Need" paper.
Extracts all math expressions and tests verbalization.
"""

import re
import sys
import os
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Dict

# Add parent directory to path to import mathwords
sys.path.insert(0, str(Path(__file__).parent.parent))

import mathwords


class MathExpressionExtractor:
    """Extract math expressions from LaTeX files"""

    def __init__(self):
        # Patterns for different math environments
        self.patterns = {
            'inline_dollar': r'\$([^\$]+)\$',
            'inline_paren': r'\\\((.+?)\\\)',
            'inline_bracket': r'\\\[(.+?)\\\]',
            'equation': r'\\begin\{equation\}(.+?)\\end\{equation\}',
            'equation_star': r'\\begin\{equation\*\}(.+?)\\end\{equation\*\}',
            'align': r'\\begin\{align\}(.+?)\\end\{align\}',
            'align_star': r'\\begin\{align\*\}(.+?)\\end\{align\*\}',
            'eqnarray': r'\\begin\{eqnarray\}(.+?)\\end\{eqnarray\}',
            'multline': r'\\begin\{multline\}(.+?)\\end\{multline\}',
        }

    def extract_from_text(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Extract math expressions from text.
        Returns list of (expression, environment_type, cleaned_expression)
        """
        results = []

        for env_type, pattern in self.patterns.items():
            flags = re.DOTALL if 'begin' in env_type else 0
            matches = re.finditer(pattern, text, flags)

            for match in matches:
                expr = match.group(1).strip()

                # Clean up expression
                cleaned = self.clean_expression(expr)

                if cleaned and len(cleaned) > 0:
                    # Determine if display mode
                    display_mode = env_type not in ['inline_dollar', 'inline_paren']
                    results.append((expr, env_type, cleaned, display_mode))

        return results

    def clean_expression(self, expr: str) -> str:
        """Clean up extracted expression"""
        # Remove excessive whitespace
        expr = re.sub(r'\s+', ' ', expr)

        # Remove comments
        expr = re.sub(r'%.*?$', '', expr, flags=re.MULTILINE)

        # Remove alignment characters for multi-line equations
        expr = expr.replace('&', '')
        expr = expr.replace('\\\\', ' ')

        # Remove labels
        expr = re.sub(r'\\label\{[^}]+\}', '', expr)

        return expr.strip()

    def extract_from_file(self, filepath: Path) -> List[Tuple[str, str, str]]:
        """Extract all math expressions from a LaTeX file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return self.extract_from_text(text)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return []


def test_expression(expr: str, display_mode: bool = False) -> Tuple[bool, str, str]:
    """
    Test a single expression with mathwords.
    Returns (success, verbalized_text, error_message)
    """
    try:
        result = mathwords.verbalize(expr, display_mode=display_mode)
        return (True, result, "")
    except Exception as e:
        return (False, "", str(e))


def main():
    print("=" * 80)
    print("Testing mathwords on 'Attention Is All You Need' Paper")
    print("=" * 80)
    print()

    # Find all .tex files
    test_dir = Path(__file__).parent
    tex_files = list(test_dir.glob("*.tex"))

    print(f"Found {len(tex_files)} LaTeX files:")
    for f in tex_files:
        print(f"  - {f.name}")
    print()

    # Extract all math expressions
    extractor = MathExpressionExtractor()
    all_expressions = []

    print("Extracting math expressions...")
    for tex_file in tex_files:
        exprs = extractor.extract_from_file(tex_file)
        for expr_data in exprs:
            all_expressions.append((tex_file.name, *expr_data))

    print(f"Found {len(all_expressions)} math expressions total")
    print()

    # Remove duplicates (keep first occurrence)
    seen = set()
    unique_expressions = []
    for file, orig, env, cleaned, display in all_expressions:
        if cleaned not in seen:
            seen.add(cleaned)
            unique_expressions.append((file, orig, env, cleaned, display))

    print(f"Unique expressions: {len(unique_expressions)}")
    print()

    # Test each expression
    print("=" * 80)
    print("Testing expressions with mathwords...")
    print("=" * 80)
    print()

    results = {
        'success': [],
        'failure': [],
    }

    for i, (file, orig, env, cleaned, display) in enumerate(unique_expressions, 1):
        success, verbalized, error = test_expression(cleaned, display)

        if success:
            results['success'].append({
                'file': file,
                'expr': cleaned,
                'env': env,
                'verbalized': verbalized,
                'display_mode': display
            })
        else:
            results['failure'].append({
                'file': file,
                'expr': cleaned,
                'env': env,
                'error': error,
                'display_mode': display
            })

        # Progress indicator
        if i % 10 == 0:
            print(f"Processed {i}/{len(unique_expressions)} expressions...")

    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print(f"Total unique expressions: {len(unique_expressions)}")
    print(f"Successful conversions:   {len(results['success'])} ({len(results['success'])*100/len(unique_expressions):.1f}%)")
    print(f"Failed conversions:       {len(results['failure'])} ({len(results['failure'])*100/len(unique_expressions):.1f}%)")
    print()

    # Show successful examples
    if results['success']:
        print("=" * 80)
        print("SUCCESSFUL CONVERSIONS (Sample)")
        print("=" * 80)
        print()

        # Show first 20 successful conversions
        for i, item in enumerate(results['success'][:20], 1):
            print(f"{i}. [{item['file']}] ({item['env']})")
            print(f"   LaTeX: {item['expr'][:80]}{'...' if len(item['expr']) > 80 else ''}")
            print(f"   Verbalized: {item['verbalized']}")
            print()

    # Show all failures
    if results['failure']:
        print("=" * 80)
        print("FAILED CONVERSIONS")
        print("=" * 80)
        print()

        # Group failures by error type
        errors_by_type = defaultdict(list)
        for item in results['failure']:
            error_type = item['error'].split(':')[0] if ':' in item['error'] else item['error']
            errors_by_type[error_type].append(item)

        for error_type, items in errors_by_type.items():
            print(f"\nError Type: {error_type} ({len(items)} occurrences)")
            print("-" * 80)
            for i, item in enumerate(items[:5], 1):  # Show first 5 of each type
                print(f"  {i}. [{item['file']}]")
                print(f"     LaTeX: {item['expr'][:70]}{'...' if len(item['expr']) > 70 else ''}")
                print(f"     Error: {item['error']}")
                print()
            if len(items) > 5:
                print(f"     ... and {len(items) - 5} more")
                print()

    # Show some interesting examples
    if results['success']:
        print("=" * 80)
        print("INTERESTING EXAMPLES FROM THE PAPER")
        print("=" * 80)
        print()

        # Find specific interesting patterns
        interesting = []
        for item in results['success']:
            expr_lower = item['expr'].lower()
            if any(keyword in expr_lower for keyword in ['attention', 'softmax', 'sqrt', 'mathrm']):
                interesting.append(item)

        for i, item in enumerate(interesting[:10], 1):
            print(f"{i}. Key Formula from {item['file']}")
            print(f"   LaTeX: {item['expr']}")
            print(f"   Verbalized: {item['verbalized']}")
            print()

    # Statistics by environment type
    print("=" * 80)
    print("STATISTICS BY ENVIRONMENT TYPE")
    print("=" * 80)
    print()

    env_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0})

    for item in results['success']:
        env_stats[item['env']]['total'] += 1
        env_stats[item['env']]['success'] += 1

    for item in results['failure']:
        env_stats[item['env']]['total'] += 1
        env_stats[item['env']]['failure'] += 1

    print(f"{'Environment':<20} {'Total':<8} {'Success':<8} {'Failure':<8} {'Rate':<8}")
    print("-" * 60)
    for env, stats in sorted(env_stats.items()):
        rate = stats['success'] * 100 / stats['total'] if stats['total'] > 0 else 0
        print(f"{env:<20} {stats['total']:<8} {stats['success']:<8} {stats['failure']:<8} {rate:.1f}%")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return results


if __name__ == "__main__":
    results = main()
