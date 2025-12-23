# mathwords

**High-performance Python library for converting LaTeX and MathML to verbalized English text**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`mathwords` is a Python library that converts mathematical expressions (LaTeX or MathML) into natural language descriptions. It's built with Rust for high performance and uses the powerful MathCAT library for accurate mathematical verbalization.

**Key Features:**
- 🚀 **High Performance**: Rust-based backend with Python bindings via PyO3
- 🔓 **GIL-Free**: CPU-bound operations release the Python GIL for true multi-threading
- 🛡️ **Panic-Safe**: All Rust panics are caught and converted to Python exceptions
- 📦 **Portable**: MathCAT rulesets are embedded at compile time for zero-config deployment
- 🎯 **Simple API**: Clean, Pythonic interface with type hints
- ⚡ **Batch Processing**: Efficiently process multiple expressions at once
- ✅ **Battle-Tested**: 88.4% success rate on "Attention Is All You Need" paper (130/147 expressions)

## Installation

### From Source (Development)

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin
pip install maturin

# Clone and build
git clone <repository-url>
cd mathwords
maturin develop --release

# Or install in editable mode
pip install -e .
```

### From Wheel (Production)

```bash
# Build a wheel
maturin build --release

# Install the wheel
pip install target/wheels/mathwords-*.whl
```

## Usage

### Basic Usage

```python
import mathwords

# Convert LaTeX to speech
result = mathwords.verbalize("x^2 + y^2 = z^2")
print(result)
# Output: "x squared plus y squared equals z squared"

# Convert fractions
result = mathwords.verbalize(r"\frac{a}{b}")
print(result)
# Output: "a over b"

# Use display mode for better handling of large expressions
result = mathwords.verbalize(r"\sum_{i=1}^{n} i", display_mode=True)
print(result)
```

### Speech Styles

```python
# Available speech styles: ClearSpeak, SimpleSpeak
result = mathwords.verbalize("x^2", speech_style="ClearSpeak")
result = mathwords.verbalize("x^2", speech_style="SimpleSpeak")

# Get list of available styles
styles = mathwords.get_speech_styles()
print(styles)  # ['ClearSpeak', 'SimpleSpeak']
```

### Batch Processing

```python
# Process multiple expressions efficiently
expressions = [
    ("x^2", None),          # (expression, is_mathml)
    (r"\frac{a}{b}", False),
    ("y + 2", None),
]

results = mathwords.verbalize_batch(expressions)
for expr, result in zip(expressions, results):
    print(f"{expr[0]} -> {result}")
```

### MathML Input

```python
# You can also input MathML directly
mathml = "<math><mi>x</mi><mo>+</mo><mi>y</mi></math>"
result = mathwords.verbalize(mathml, is_mathml=True)
print(result)
# Output: "x plus y"
```

## API Reference

### `verbalize(input_str, is_mathml=False, speech_style="ClearSpeak", display_mode=False)`

Convert a single LaTeX or MathML expression to verbalized text.

**Parameters:**
- `input_str` (str): The LaTeX or MathML string to convert
- `is_mathml` (bool): If True, input is treated as MathML; if False, as LaTeX (default: False)
- `speech_style` (str): Speech style for verbalization - "ClearSpeak" or "SimpleSpeak" (default: "ClearSpeak")
- `display_mode` (bool): For LaTeX input, whether to treat as display (block) mode (default: False)

**Returns:** str - Verbalized English text

**Raises:**
- `ValueError`: If input is invalid or empty
- `RuntimeError`: If conversion fails

### `verbalize_batch(expressions, speech_style="ClearSpeak", display_mode=False)`

Convert multiple expressions in a single call.

**Parameters:**
- `expressions` (List[Tuple[str, Optional[bool]]]): List of (input_str, is_mathml) tuples
- `speech_style` (str): Speech style for all expressions (default: "ClearSpeak")
- `display_mode` (bool): Default display mode for LaTeX expressions (default: False)

**Returns:** List[str] - List of verbalized English text strings

**Raises:**
- `ValueError`: If expression list is empty
- `RuntimeError`: If any conversion fails

### `get_speech_styles()`

Get list of available speech styles.

**Returns:** List[str] - List of available speech style names

## Architecture

### Resource Bundling Strategy

One of the key challenges in building `mathwords` was handling MathCAT's ruleset files (XML/YAML) in a way that makes the library truly portable. Here's how we solved it:

#### 1. **Embedded Resources via `include_dir`**

The Rules directory is embedded directly into the compiled binary at build time using the `include_dir` crate:

```rust
use include_dir::{include_dir, Dir};

static RULES_DIR: Dir = include_dir!("$CARGO_MANIFEST_DIR/Rules");
```

This means:
- ✅ Zero external dependencies at runtime
- ✅ Works in any environment (Docker, Lambda, etc.)
- ✅ No file path configuration needed
- ✅ Rules are versioned with the code

#### 2. **Lazy Extraction**

On first use, the embedded rules are extracted to a temporary directory:

```rust
fn get_rules_directory() -> Result<PathBuf, MathWordsError> {
    // 1. Check MATHCAT_RULES_DIR env var (for overrides)
    // 2. Check local Rules/ directory (for development)
    // 3. Extract embedded resources to temp dir (for production)

    let temp_dir = std::env::temp_dir().join("mathwords_rules");
    if !temp_dir.exists() {
        extract_dir(&RULES_DIR, &temp_dir)?;
    }
    Ok(temp_dir)
}
```

This approach provides:
- 🔧 **Development flexibility**: Use `MATHCAT_RULES_DIR` to override
- 📦 **Production simplicity**: Automatic extraction on first use
- 💾 **Performance**: Extract once, reuse across sessions

#### 3. **Thread-Safe Initialization**

MathCAT initialization is thread-safe and happens only once:

```rust
static MATHCAT_INITIALIZED: OnceLock<Mutex<bool>> = OnceLock::new();

fn ensure_mathcat_initialized(speech_style: &str) -> Result<(), MathWordsError> {
    // Initialize once, safely across threads
}
```

### Concurrency & GIL Handling

All CPU-bound operations release Python's Global Interpreter Lock:

```rust
#[pyfunction]
fn verbalize(py: Python, input_str: &str, ...) -> PyResult<String> {
    py.allow_threads(|| {
        // CPU-bound work happens here without holding GIL
        // Python threads can run concurrently
    })
}
```

This means Python code can use threading effectively:

```python
from concurrent.futures import ThreadPoolExecutor
import mathwords

expressions = ["x^2", "y^3", "z^4", ...]

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(mathwords.verbalize, expressions))
```

### Panic Safety

All Rust code that might panic is wrapped in `std::panic::catch_unwind`:

```rust
let result = std::panic::catch_unwind(|| {
    // Potentially panicking code
});

match result {
    Ok(Ok(value)) => Ok(value),
    Ok(Err(e)) => Err(MathWordsError::ConversionError(e)),
    Err(_) => Err(MathWordsError::ConversionError("Operation panicked".into())),
}
```

This ensures:
- ✅ No undefined behavior in Python
- ✅ Clear error messages
- ✅ Graceful degradation

## Real-World Testing

### "Attention Is All You Need" Paper Test

The library has been thoroughly tested on the LaTeX source of the seminal Transformer paper by Vaswani et al. (2017).

**Results:**
- ✅ **88.4% success rate** (130/147 unique mathematical expressions)
- ✅ Successfully verbalized the **core attention mechanism formula**
- ✅ Handled complex nested expressions, summations, fractions, and matrix operations
- ✅ Zero crashes with excellent error handling
- ⚠️ 11.6% failures were all custom LaTeX macros (expected limitation)

**Key formula successfully verbalized:**
```latex
\mathrm{Attention}(Q, K, V) = \mathrm{softmax}(\frac{QK^T}{\sqrt{d_k}})V
```

See the full test report: [`arxiv_test/ATTENTION_PAPER_TEST_REPORT.md`](arxiv_test/ATTENTION_PAPER_TEST_REPORT.md)

**Run the real-world test:**
```bash
cd arxiv_test
python test_attention_paper.py      # Full test suite
python demo_attention_formulas.py   # Demo of key formulas
```

## Development

### Project Structure

```
mathwords/
├── Cargo.toml                      # Rust dependencies and config
├── pyproject.toml                  # Python packaging with maturin
├── src/
│   └── lib.rs                      # Rust source with PyO3 bindings
├── python/
│   └── mathwords/
│       ├── __init__.py             # Python package
│       └── __init__.pyi            # Type stubs
├── Rules/                          # MathCAT rulesets (embedded at build time)
├── tests/
│   └── test_mathwords.py           # Unit test suite
├── arxiv_test/                     # Real-world test on academic paper
│   ├── test_attention_paper.py    # Comprehensive test extractor
│   ├── demo_attention_formulas.py # Demo of key formulas
│   └── ATTENTION_PAPER_TEST_REPORT.md
├── example.py                      # Usage examples
└── TECHNICAL_SUMMARY.md            # Architecture deep-dive
```

### Building

```bash
# Development build with debug symbols
maturin develop

# Release build (optimized)
maturin develop --release

# Build wheel
maturin build --release
```

### Testing

```bash
# Run unit tests
pytest tests/ -v

# Run real-world test on "Attention Is All You Need" paper
cd arxiv_test
python test_attention_paper.py

# Run demo of key formulas
python demo_attention_formulas.py

# Run example
python example.py
```

**Test Coverage:**
- ✅ Unit tests: 11/11 passing
- ✅ Real-world test: 88.4% success rate on academic paper (130/147 expressions)
- ✅ Zero crashes across all tests

## Technical Details

### Dependencies

**Rust:**
- `pyo3` - Python bindings
- `math-core` - LaTeX to MathML conversion
- `mathcat` - MathML to speech verbalization
- `include_dir` - Embedding resources at compile time
- `anyhow`, `thiserror` - Error handling

**Python:**
- Python 3.8+

### Performance

- **Zero-copy** where possible
- **Batch processing** amortizes initialization costs
- **GIL release** enables true parallelism
- **Optimized Rust** compilation settings

## License

MIT License - see LICENSE file for details

## Credits

This library was designed and implemented by **Claude (Anthropic)** using the Claude Code CLI tool, based on an initial concept and requirements from Stefan.

**Implementation:**
- Architecture and design: Claude Sonnet 4.5
- Rust/PyO3 implementation: Claude Sonnet 4.5
- Testing and validation: Claude Sonnet 4.5
- Documentation: Claude Sonnet 4.5

**Concept:**
- Original idea and requirements: Stefan
- Real-world testing direction: Stefan

## Acknowledgments

- Built on [MathCAT](https://github.com/NSoiffer/MathCAT) by Neil Soiffer
- Uses [math-core](https://crates.io/crates/math-core) for LaTeX parsing
- Powered by [PyO3](https://pyo3.rs/) for Rust-Python interop
- Developed with [Claude Code](https://claude.com/claude-code) by Anthropic

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
