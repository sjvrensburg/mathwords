# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mathwords** is a high-performance Python library that converts LaTeX and MathML mathematical expressions into verbalized English text. It's a Rust/Python hybrid project using PyO3 for bindings.

**Architecture:** Rust backend (CPU-bound math conversion) + Python API + embedded MathCAT rulesets (compile-time)

**Key metric:** 88.4% success rate on real-world test ("Attention Is All You Need" paper, 130/147 expressions)

## Build & Development Commands

### Initial Setup
```bash
# Install Rust (if needed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dev dependencies
pip install maturin pytest
```

### Building
```bash
# Development build (with debug symbols, faster compilation)
maturin develop

# Release build (optimized, production-ready)
maturin develop --release

# Build distributable wheel
maturin build --release
# Output: target/wheels/mathwords-*.whl
```

### Testing
```bash
# Run unit tests only (11 tests)
pytest tests/ -v

# Run real-world test on "Attention Is All You Need" paper (88.4% coverage)
cd arxiv_test
python test_attention_paper.py

# Run demo of key formulas from the paper
python demo_attention_formulas.py

# Run all tests (configured in pytest.ini)
pytest -v
```

### Running Examples
```bash
# Basic examples
python example.py

# Specific formula verbalization
python -c "import mathwords; print(mathwords.verbalize('x^2 + y^2'))"
```

### Cleaning
```bash
# Remove build artifacts
rm -rf target build dist *.egg-info
rm -rf .pytest_cache __pycache__ **/__pycache__

# Clean compiled extensions
find . -name "*.so" -delete
find . -name "*.pyc" -delete
```

## Critical Architecture Concepts

### 1. Resource Bundling (Compile-Time Embedded MathCAT Rules)

**Problem:** MathCAT requires XML/YAML rulesets. How to distribute without external files?

**Solution:** Embed at compile time using `include_dir!` macro

**Key Code:** `src/lib.rs:10`
```rust
static RULES_DIR: Dir = include_dir!("$CARGO_MANIFEST_DIR/Rules");
```

**Runtime Behavior:**
1. First call: Extract embedded rules to `$TMPDIR/mathwords_rules/`
2. Subsequent calls: Use cached directory
3. Override for development: Set `MATHCAT_RULES_DIR` env var

**Why this matters:**
- Single-file distribution (wheel contains everything)
- Works in Docker, serverless, read-only filesystems
- No setup or configuration needed
- **Important fix applied:** Path deduplication in `extract_dir()` (lines 87-90) to prevent recursive path doubling

### 2. GIL Release for Concurrency

**Pattern:** CPU-bound Rust operations release Python's Global Interpreter Lock

**Key Code:** `src/lib.rs:217` (in `verbalize()` function)
```rust
Python::detach(py, || {
    // CPU-bound work here - GIL is released
    ensure_mathcat_initialized(speech_style)?;
    latex_to_mathml(input_str, display_mode)?;
    mathml_to_speech(&mathml)
})
```

**Implication:** Python threads can run concurrently during math conversion. Important for batch processing.

### 3. Panic Safety

**Pattern:** All Rust code that could panic is wrapped in `catch_unwind()`

**Key Code:** `src/lib.rs:107-118` and similar blocks

**Why:** Rust panics in a Python extension crash the Python interpreter. By catching them, we convert to Python exceptions.

**When modifying:** Any call to MathCAT or math-core must be wrapped in `catch_unwind()`.

### 4. Thread-Safe MathCAT Initialization

**Pattern:** Initialize MathCAT exactly once across all threads

**Key Code:** `src/lib.rs:13` and `ensure_mathcat_initialized()`
```rust
static MATHCAT_INITIALIZED: OnceLock<Mutex<bool>> = OnceLock::new();
```

**Why:** MathCAT state is global and not thread-safe. Uses `OnceLock` for lock-free reads after first initialization.

## Data Flow

```
User Input (LaTeX/MathML)
    ↓
verbalize() [Python function in Rust]
    ↓ [GIL released, CPU-bound]
ensure_mathcat_initialized() [thread-safe, once-per-process]
    ↓
latex_to_mathml() [math-core crate - LaTeX → MathML]
    ↓
mathml_to_speech() [mathcat crate - MathML → English]
    ↓
Result: English verbalization string
```

## File Structure (Key Files)

```
src/lib.rs                    # 297 lines - Complete Rust/PyO3 implementation
                              #   - Resource bundling logic
                              #   - GIL-releasing Python functions
                              #   - Error handling & panic safety

python/mathwords/
  __init__.py                 # Re-exports Rust bindings to Python
  __init__.pyi                # Type stubs for IDE support

tests/test_mathwords.py       # 114 lines - Unit tests (11 tests, 100% passing)

arxiv_test/                   # Real-world validation on research paper
  test_attention_paper.py     # 275 lines - Expression extraction & testing
  demo_attention_formulas.py  # 160 lines - Demo of key formulas
  ATTENTION_PAPER_TEST_REPORT.md  # Detailed analysis (88.4% success rate)

Rules/                        # Embedded MathCAT rulesets (compile-time)
  Languages/                  # Multilingual rules
  Braille/                    # Braille output rules
  Intent/                     # Domain-specific rules (calculus, geometry, etc)
```

## Key Dependencies & Why

| Dependency | Version | Purpose | Notes |
|-----------|---------|---------|-------|
| pyo3 | 0.27 | Rust-Python bindings | Must support Python 3.8-3.14 |
| math-core | 0.1.1 | LaTeX → MathML conversion | Core math logic |
| mathcat | 0.7.6-beta.1 | MathML → English speech | Verbalization engine |
| include_dir | 0.7 | Compile-time resource embedding | Enables portable rules |
| thiserror | 1.0 | Error type derivation | Panic-safe error mapping |

## Testing Strategy

### Unit Tests (`tests/test_mathwords.py`)
- **11 tests, 100% passing**
- Test basic API: simple expressions, fractions, equations, error handling
- Test features: speech styles, batch processing, display modes
- **How to add:** Add `test_*()` function to `tests/test_mathwords.py`, runs via pytest

### Real-World Test (`arxiv_test/`)
- **88.4% success rate (130/147 unique expressions)**
- Tests on actual research paper: "Attention Is All You Need" (arXiv:1706.03762)
- Validates core attention mechanism formula, complex nested expressions, summations
- **Failures:** Custom LaTeX macros (expected limitation, not a bug)
- **How to run:** `cd arxiv_test && python test_attention_paper.py`

### Known Limitations Tested
- ✅ Standard LaTeX notation (works well)
- ✅ Complex nested expressions (works well)
- ❌ Custom LaTeX macros like `\dmodel` (requires preprocessing - user responsibility)

## Common Modifications & Patterns

### Adding a New Python Function (Exposed from Rust)

1. Write function in `src/lib.rs` with `#[pyfunction]` attribute
2. Use `py.allow_threads()` (now `Python::detach()`) for CPU-bound work
3. Wrap potentially panicking code in `catch_unwind()`
4. Add to `#[pymodule]` registration
5. Add type stubs to `python/mathwords/__init__.pyi`

Example:
```rust
#[pyfunction]
fn my_new_function(py: Python, input: &str) -> PyResult<String> {
    py.allow_threads(|| {
        // your implementation
        Ok("result".to_string())
    }).map_err(Into::into)
}
```

### Debugging MathCAT Issues

MathCAT initialization can be sensitive. Debugging steps:

1. Check rule extraction: `ls -la $TMPDIR/mathwords_rules/Languages/en/`
2. Override rules directory: `export MATHCAT_RULES_DIR=/path/to/rules && python`
3. Enable verbose output: Check environment variables in `get_rules_directory()`

## Performance Characteristics

- **Per-expression latency:** ~3.4ms (includes LaTeX→MathML→Speech)
- **Batch processing:** Amortizes initialization cost
- **GIL behavior:** Released during conversion (use threading for parallelism)
- **Build time:** ~30 seconds release build (LTO enabled)
- **Binary size:** ~10.5 MB .so file (includes embedded MathCAT rules)

## Bug History & Important Fixes

### Resource Extraction Path Duplication (Fixed Dec 23, 2025)

**Bug:** `extract_dir()` was creating nested paths like `/tmp/mathwords_rules/Languages/Languages/en/Languages/en/...`

**Root Cause:** Recursive call was joining already-relative paths again

**Fix:** Changed line 89 from `extract_dir(subdir, &subdir_path)?` to `extract_dir(subdir, target)?`

**How it was found:** Real-world test on academic paper failed because MathCAT couldn't find rules

**How to verify fix:** Run `find /tmp/mathwords_rules -type d | head -10` after first call - should be flat, not nested

## Important Notes for Development

1. **Python version compatibility:** Target Python 3.8+ (supports 3.14 via PyO3 0.27)

2. **Release builds matter:** Always test with `--release` flag. Debug builds may have different behavior.

3. **Custom macros aren't supported:** Users must preprocess LaTeX to expand `\newcommand` before calling mathwords. This is documented and intentional.

4. **Rules directory is critical:** If embedded rules extraction fails, the entire library fails. Keep `Rules/` directory clean.

5. **Thread safety:** MathCAT global state is protected by `OnceLock`. Don't try to reinitialize or reset it - trust the once-initialization.

6. **Error messages are important:** Rust panic-wrapping provides clear error messages. Preserve error context when modifying error handling.

## Documentation References

- **README.md** - User-facing feature overview and API docs
- **TECHNICAL_SUMMARY.md** - Deep architecture dive with resource bundling explanation
- **CHANGELOG.md** - All features, fixes, and changes for this release
- **arxiv_test/ATTENTION_PAPER_TEST_REPORT.md** - Real-world test validation and analysis
- **src/lib.rs** - Inline comments explain key sections
