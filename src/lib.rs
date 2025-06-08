use c2pa::{Reader, jumbf_io::load_jumbf_from_stream};
use log::debug;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use std::io::Cursor;

/// A Python module for fast C2PA reading
///
/// This module provides high-performance functions for reading Content Authenticity
/// Initiative (CAI) C2PA metadata from media files.
#[pymodule]
fn fast_c2pa_python(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read_c2pa_from_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(read_c2pa_from_file, m)?)?;
    m.add_function(wrap_pyfunction!(get_mime_type, m)?)?;
    Ok(())
}

/// Determine MIME type from file extension
///
/// This function uses Python's mimetypes module to determine the MIME type
/// based on the file extension.
///
/// Args:
///     file_path: Path to the file
///
/// Returns:
///     A string containing the MIME type if determinable, or None if not
#[pyfunction]
fn get_mime_type(py: Python, file_path: &str) -> PyResult<Option<String>> {
    // Import Python's mimetypes module
    let mimetypes = PyModule::import(py, "mimetypes")?;
    
    // Initialize mimetypes if needed
    if !mimetypes.getattr("inited")?.extract::<bool>()? {
        mimetypes.call_method0("init")?;
    }
    
    // Get MIME type from file path
    let result = mimetypes.call_method1("guess_type", (file_path,))?;
    let mime_type: Option<String> = result.get_item(0)?.extract()?;
    
    // If MIME type not found, try with common extensions fallback
    if mime_type.is_none() {
        let path = PyModule::import(py, "os.path")?;
        
        // Extract file extension
        let splitext = path.call_method1("splitext", (file_path,))?;
        let ext: String = splitext.get_item(1)?.extract::<String>()?.to_lowercase();
        
        // Fallbacks for common image types
        match ext.as_str() {
            ".jpg" | ".jpeg" => return Ok(Some("image/jpeg".to_string())),
            ".png" => return Ok(Some("image/png".to_string())),
            ".gif" => return Ok(Some("image/gif".to_string())),
            ".webp" => return Ok(Some("image/webp".to_string())),
            ".tiff" => return Ok(Some("image/tiff".to_string())),
            ".heic" => return Ok(Some("image/heic".to_string())),
            _ => {}
        }
    }
    
    Ok(mime_type)
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

/// Read C2PA metadata from a file
/// 
/// This function reads a file from disk and extracts C2PA metadata, returning a Python
/// dictionary containing the manifest if found.
///
/// Args:
///     file_path: Path to the file to read
///     mime_type: MIME type of the file (e.g., "image/jpeg"). If None or empty,
///                it will be automatically determined from the file extension.
///     allow_threads: Whether to release the Python GIL during processing (default: True)
///
/// Returns:
///     A dictionary containing the C2PA manifest data if found, or None if no 
///     C2PA metadata is present
///
/// Raises:
///     RuntimeError: If there is an error reading or parsing the C2PA data
#[pyfunction]
#[pyo3(signature = (file_path, mime_type=None, allow_threads=true))]
fn read_c2pa_from_file(py: Python, file_path: &str, mime_type: Option<&str>, allow_threads: bool) -> PyResult<Option<PyObject>> {
    // Determine the MIME type if not provided or empty
    let effective_mime_type = match mime_type {
        Some(mime) if !mime.trim().is_empty() => mime.to_string(),
        _ => match get_mime_type(py, file_path)? {
            Some(mime) => mime,
            None => return Err(PyRuntimeError::new_err(format!("Could not determine MIME type for file: {}", file_path)))
        }
    };

    // Read the file into memory
    match std::fs::read(file_path) {
        Ok(data) => {
            // Reuse the existing function to process the bytes
            read_c2pa_from_bytes(py, &data, &effective_mime_type, allow_threads)
        },
        Err(e) => {
            Err(PyRuntimeError::new_err(format!("Error reading file: {}", e)))
        }
    }
}