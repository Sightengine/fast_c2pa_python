use c2pa::Reader;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use std::io::Cursor;

/// A Python module for fast C2PA reading
#[pymodule]
fn fast_c2pa_reader(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read_c2pa_from_bytes, m)?)?;
    Ok(())
}

/// Read C2PA metadata from a byte array - full manifest version
#[pyfunction]
fn read_c2pa_from_bytes(py: Python, data: &[u8], mime_type: &str) -> PyResult<Option<PyObject>> {
    // Release the GIL during parsing to allow other Python threads to run
    let reader = py.allow_threads(|| {
        // Create a cursor for the data
        let cursor = Cursor::new(data);
        
        // Create a reader for the data
        Reader::from_stream(mime_type, cursor)
    });

    match reader {
        Ok(reader) => {
            // Get the active manifest
            if let Some(manifest) = reader.active_manifest() {
                let json_str = py.allow_threads(|| {
                    // Convert the manifest to JSON in Rust for efficiency
                    serde_json::to_string(&manifest)
                        .unwrap_or_else(|_| String::from("{}"))
                });
                
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
            // Error reading C2PA data
            Err(PyRuntimeError::new_err(format!("Error reading C2PA data: {}", e)))
        }
    }
}