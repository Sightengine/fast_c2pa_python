//TODO: Check better way to handle mime

use pyo3::prelude::*;

mod c2pa_reader;
use c2pa_reader::{
    read_c2pa_from_bytes
};

/// A Python module for fast C2PA reading
///
/// This module provides high-performance functions for reading Content Authenticity
/// Initiative (CAI) C2PA metadata from media files.
#[pymodule]
fn fast_c2pa_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read_c2pa_from_bytes, m)?)?;
    Ok(())
}