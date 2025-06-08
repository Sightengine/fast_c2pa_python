//TODO: Add Makefile

use pyo3::prelude::*;
mod mime_utils;
use mime_utils::get_mime_type;

mod c2pa_reader;
use c2pa_reader::{
    read_c2pa_from_bytes,
    read_c2pa_from_file
};

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