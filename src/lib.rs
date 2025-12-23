use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PyRuntimeError};
use pyo3::types::PyModule;
use math_core::{LatexToMathML, MathCoreConfig, MathDisplay};
use std::sync::{Mutex, OnceLock};
use std::path::PathBuf;
use include_dir::{include_dir, Dir};

// Embed the Rules directory at compile time
static RULES_DIR: Dir = include_dir!("$CARGO_MANIFEST_DIR/Rules");

// Global state for MathCAT initialization
static MATHCAT_INITIALIZED: OnceLock<Mutex<bool>> = OnceLock::new();

/// Custom error type for mathwords operations
#[derive(Debug, thiserror::Error)]
enum MathWordsError {
    #[error("Failed to initialize MathCAT: {0}")]
    InitializationError(String),

    #[error("Failed to convert LaTeX to MathML: {0}")]
    LatexConversionError(String),

    #[error("Failed to convert MathML to speech: {0}")]
    MathMLConversionError(String),

    #[error("Invalid input: {0}")]
    ValidationError(String),

    #[error("Resource error: {0}")]
    ResourceError(String),
}

impl From<MathWordsError> for PyErr {
    fn from(err: MathWordsError) -> PyErr {
        match err {
            MathWordsError::ValidationError(msg) => PyValueError::new_err(msg),
            _ => PyRuntimeError::new_err(err.to_string()),
        }
    }
}

/// Extract embedded Rules directory to a temporary location
/// This is called once on first use and cached
fn get_rules_directory() -> Result<PathBuf, MathWordsError> {
    // Try environment variable first (allows override for development/testing)
    if let Ok(dir) = std::env::var("MATHCAT_RULES_DIR") {
        let path = PathBuf::from(dir);
        if path.exists() {
            return Ok(path);
        }
    }

    // Check if Rules directory exists alongside the module (for development)
    let local_rules = PathBuf::from("Rules");
    if local_rules.exists() {
        return Ok(local_rules);
    }

    // For installed wheels, try to find it relative to the Python package
    // This requires extracting embedded resources to a temp location
    let temp_dir = std::env::temp_dir().join("mathwords_rules");

    // Only extract if not already present
    if !temp_dir.exists() {
        std::fs::create_dir_all(&temp_dir)
            .map_err(|e| MathWordsError::ResourceError(format!("Failed to create temp directory: {}", e)))?;

        // Extract all embedded files
        extract_dir(&RULES_DIR, &temp_dir)
            .map_err(|e| MathWordsError::ResourceError(format!("Failed to extract rules: {}", e)))?;
    }

    Ok(temp_dir)
}

/// Recursively extract embedded directory to filesystem
fn extract_dir(dir: &Dir, target: &PathBuf) -> std::io::Result<()> {
    for file in dir.files() {
        let file_path = target.join(file.path());
        if let Some(parent) = file_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(file_path, file.contents())?;
    }

    for subdir in dir.dirs() {
        // Don't join the path again - file.path() already includes the full relative path
        extract_dir(subdir, target)?;
    }

    Ok(())
}

/// Initialize MathCAT with rules directory
/// This is thread-safe and will only initialize once
fn ensure_mathcat_initialized(speech_style: &str) -> Result<(), MathWordsError> {
    let initialized = MATHCAT_INITIALIZED.get_or_init(|| Mutex::new(false));
    let mut init_guard = initialized.lock()
        .map_err(|e| MathWordsError::InitializationError(format!("Mutex lock failed: {}", e)))?;

    if !*init_guard {
        let rules_dir = get_rules_directory()?;

        // Initialize MathCAT - wrap in catch_unwind to prevent panics
        let init_result = std::panic::catch_unwind(|| {
            libmathcat::interface::set_rules_dir(rules_dir.to_string_lossy().to_string())
                .map_err(|e| format!("Failed to set rules directory: {:?}", e))?;

            libmathcat::interface::set_preference("Language".to_string(), "en".to_string())
                .map_err(|e| format!("Failed to set language: {:?}", e))?;

            libmathcat::interface::set_preference("SpeechStyle".to_string(), speech_style.to_string())
                .map_err(|e| format!("Failed to set speech style: {:?}", e))?;

            Ok::<(), String>(())
        });

        match init_result {
            Ok(Ok(())) => {
                *init_guard = true;
                Ok(())
            }
            Ok(Err(e)) => Err(MathWordsError::InitializationError(e)),
            Err(_) => Err(MathWordsError::InitializationError(
                "MathCAT initialization panicked".to_string()
            )),
        }
    } else {
        // Already initialized, just update speech style if needed
        libmathcat::interface::set_preference("SpeechStyle".to_string(), speech_style.to_string())
            .map_err(|e| MathWordsError::InitializationError(format!("Failed to update speech style: {:?}", e)))?;
        Ok(())
    }
}

/// Convert LaTeX to MathML
fn latex_to_mathml(latex: &str, display_mode: bool) -> Result<String, MathWordsError> {
    let config = MathCoreConfig::default();

    let display = if display_mode {
        MathDisplay::Block
    } else {
        MathDisplay::Inline
    };

    // Wrap in catch_unwind to prevent panics
    let result = std::panic::catch_unwind(|| {
        let converter = LatexToMathML::new(&config)
            .map_err(|e| format!("Failed to create converter: {:?}", e))?;

        converter.convert_with_local_counter(latex, display)
            .map_err(|e| format!("Conversion failed: {:?}", e))
    });

    match result {
        Ok(Ok(mathml)) => Ok(mathml),
        Ok(Err(e)) => Err(MathWordsError::LatexConversionError(e)),
        Err(_) => Err(MathWordsError::LatexConversionError(
            "LaTeX conversion panicked".to_string()
        )),
    }
}

/// Convert MathML to speech text
fn mathml_to_speech(mathml: &str) -> Result<String, MathWordsError> {
    // Wrap in catch_unwind to prevent panics
    let result = std::panic::catch_unwind(|| {
        libmathcat::interface::set_mathml(mathml.to_string())
            .map_err(|e| format!("Failed to set MathML: {:?}", e))?;

        libmathcat::interface::get_spoken_text()
            .map_err(|e| format!("Failed to get speech: {:?}", e))
    });

    match result {
        Ok(Ok(speech)) => Ok(speech),
        Ok(Err(e)) => Err(MathWordsError::MathMLConversionError(e)),
        Err(_) => Err(MathWordsError::MathMLConversionError(
            "MathML to speech conversion panicked".to_string()
        )),
    }
}

/// Main verbalize function exposed to Python
///
/// Converts LaTeX or MathML input to English verbalized text.
///
/// Args:
///     input_str: The LaTeX or MathML string to convert
///     is_mathml: If True, input is treated as MathML; if False, as LaTeX (default: False)
///     speech_style: Speech style for verbalization - "ClearSpeak", "SimpleSpeak", etc. (default: "ClearSpeak")
///     display_mode: For LaTeX input, whether to treat as display (block) mode (default: False)
///
/// Returns:
///     Verbalized English text string
///
/// Raises:
///     ValueError: If input is invalid or empty
///     RuntimeError: If conversion fails
#[pyfunction]
#[pyo3(signature = (input_str, is_mathml=false, speech_style="ClearSpeak", display_mode=false))]
fn verbalize(
    py: Python,
    input_str: &str,
    is_mathml: bool,
    speech_style: &str,
    display_mode: bool,
) -> PyResult<String> {
    // Validate input
    if input_str.trim().is_empty() {
        return Err(MathWordsError::ValidationError("Input string is empty".to_string()).into());
    }

    // Release GIL for CPU-bound work
    Python::detach(py, || {
        // Ensure MathCAT is initialized
        ensure_mathcat_initialized(speech_style)?;

        // Convert to MathML if needed
        let mathml = if is_mathml {
            input_str.to_string()
        } else {
            latex_to_mathml(input_str, display_mode)?
        };

        // Convert MathML to speech
        mathml_to_speech(&mathml)
    }).map_err(|e: MathWordsError| e.into())
}

/// Batch verbalize multiple expressions
///
/// Args:
///     expressions: List of (input_str, is_mathml) tuples
///     speech_style: Speech style for verbalization (default: "ClearSpeak")
///     display_mode: For LaTeX inputs, default display mode (default: False)
///
/// Returns:
///     List of verbalized English text strings
#[pyfunction]
#[pyo3(signature = (expressions, speech_style="ClearSpeak", display_mode=false))]
fn verbalize_batch(
    py: Python,
    expressions: Vec<(String, Option<bool>)>,
    speech_style: &str,
    display_mode: bool,
) -> PyResult<Vec<String>> {
    if expressions.is_empty() {
        return Err(MathWordsError::ValidationError("Expression list is empty".to_string()).into());
    }

    Python::detach(py, || {
        // Initialize once for the batch
        ensure_mathcat_initialized(speech_style)?;

        let mut results = Vec::with_capacity(expressions.len());

        for (input_str, is_mathml_opt) in expressions {
            let is_mathml = is_mathml_opt.unwrap_or(false);

            let mathml = if is_mathml {
                input_str
            } else {
                latex_to_mathml(&input_str, display_mode)?
            };

            let speech = mathml_to_speech(&mathml)?;
            results.push(speech);
        }

        Ok(results)
    }).map_err(|e: MathWordsError| e.into())
}

/// Get information about available speech styles
#[pyfunction]
fn get_speech_styles() -> PyResult<Vec<String>> {
    Ok(vec![
        "ClearSpeak".to_string(),
        "SimpleSpeak".to_string(),
    ])
}

/// Python module definition
#[pymodule]
fn mathwords(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(verbalize, m)?)?;
    m.add_function(wrap_pyfunction!(verbalize_batch, m)?)?;
    m.add_function(wrap_pyfunction!(get_speech_styles, m)?)?;

    // Add module metadata
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__doc__", "High-performance Python library for converting LaTeX and MathML to verbalized English text")?;

    Ok(())
}
