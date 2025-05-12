use c2pa::Reader;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use std::io::Cursor;

/// A Python module for fast C2PA reading
///
/// This module provides high-performance functions for reading Content Authenticity
/// Initiative (CAI) C2PA metadata from media files.
#[pymodule]
fn fast_c2pa_reader(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read_c2pa_from_bytes, m)?)?;
    Ok(())
}

/// Read C2PA metadata from a byte array
/// 
/// This function parses binary data to extract C2PA metadata, returning a Python 
/// dictionary containing the manifest if found.
///
/// Args:
///     data: Binary data of the file (bytes-like object)
///     mime_type: MIME type of the data (e.g., "image/jpeg")
///     allow_threads: Whether to release the Python GIL during processing (default: True)
///
/// Returns:
///     A dictionary containing the C2PA manifest data if found, or None if no 
///     C2PA metadata is present
///
/// Raises:
///     RuntimeError: If there is an error reading or parsing the C2PA data
#[pyfunction]
#[pyo3(signature = (data, mime_type, allow_threads=true))]
fn read_c2pa_from_bytes(py: Python, data: &[u8], mime_type: &str, allow_threads: bool) -> PyResult<Option<PyObject>> {
    let reader = if allow_threads {
        let cursor = Cursor::new(data);
        py.allow_threads(|| Reader::from_stream(mime_type, cursor))
    } else {
        let cursor = Cursor::new(data);
        Reader::from_stream(mime_type, cursor)
    };
    match reader {
        Ok(reader) => {
            // Get the active manifest
            if let Some(manifest) = reader.active_manifest() {
                let json_str = serde_json::to_string(&manifest)
                    .unwrap_or_else(|_| String::from("{}"));

                // Convert to Python object
                let json_module = PyModule::import(py, "json")?;
                let py_json = json_module.getattr("loads")?.call1((json_str,))?;
                
                Ok(Some(py_json.to_object(py)))
            } else {
                // No active manifest found
                Ok(None)
            }
        },
        Err(e) => {
            // Ok if Error is missing JUMBF data
            if e.to_string().contains("no JUMBF data found") {
                // TODO: rely on error message is fragile
                Ok(None)
            } else {
                // Error reading C2PA data
                Err(PyRuntimeError::new_err(format!("Error reading C2PA data: {}", e)))
            }
        }
    }
}