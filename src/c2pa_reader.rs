use pyo3::prelude::*;
use std::io::Cursor;
use c2pa::{
    Reader,
    jumbf_io::load_jumbf_from_stream,
};
use log::debug;
use pyo3::exceptions::PyRuntimeError;

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
#[pyo3(signature = (data, mime_type, allow_threads=true, verify_trust=None))]
pub fn read_c2pa_from_bytes(
    py: Python,
    data: &[u8],
    mime_type: &str,
    allow_threads: bool,
    verify_trust: Option<bool>
) -> PyResult<Option<PyObject>> {
    // First check if JUMBF data exists before trying to create a Reader
    let has_jumbf = {
        let mut cursor = Cursor::new(data);
        load_jumbf_from_stream(mime_type, &mut cursor).is_ok()
    };

    if !has_jumbf {
        // No JUMBF data found
        debug!("No JUMBF data found in the provided data");
        return Ok(None);
    }

    // JUMBF data exists, proceed with Reader creation
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
            Err(PyRuntimeError::new_err(format!("Error reading C2PA data: {}", e)))
        }
    }
}