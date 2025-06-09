//TODO: Check better way to handle mime

use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;

mod c2pa_reader;
use c2pa_reader::{
    read_c2pa_from_bytes
};

#[pyfunction]
pub fn load_c2pa_settings(settings_json: &str) -> PyResult<()> {
    match c2pa::settings::load_settings_from_str(settings_json, "json") {
        Ok(_) => Ok(()),
        Err(e) => Err(PyRuntimeError::new_err(format!("Error loading C2PA settings: {}", e)))
    }
}

/// A Python module for fast C2PA reading
///
/// This module provides high-performance functions for reading Content Authenticity
/// Initiative (CAI) C2PA metadata from media files.
#[pymodule]
fn fast_c2pa_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read_c2pa_from_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(load_c2pa_settings, m)?)?; 

    Ok(())
}