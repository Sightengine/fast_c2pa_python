use std::io::Cursor;
use c2pa::jumbf_io::{load_jumbf_from_stream, save_jumbf_to_stream};
use pyo3::prelude::*;
use pyo3::pyfunction;
use pyo3::exceptions::PyRuntimeError;

#[pyfunction]
pub fn convert_to_gray_keep_c2pa(
    input_path: &str, 
    output_path: &str,
    format: &str,
) -> PyResult<()> {
    // 1. Read and extract JUMBF (C2PA data)
    let mut source = std::fs::File::open(input_path)
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to open file: {}", e)))?;

    let jumbf = load_jumbf_from_stream(format, &mut source)
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to load JUMBF: {}", e)))?;

    // 2. Convert to grayscale
    let input_img = image::open(input_path)
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to open input path: {}", e)))?;

    let output_img = input_img.grayscale();
    output_img.save(output_path)
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to save output file: {}", e)))?;


    // 3. Write back JUMBF
    let image = std::fs::read(output_path)?;
    let mut dest = std::fs::File::create(output_path)?;
    save_jumbf_to_stream(
        format,
        &mut Cursor::new(image),
        &mut dest,
        &jumbf
    )
    .map_err(|e| PyRuntimeError::new_err(format!("Failed to save output with jumbf: {}", e)))?;

    Ok(())
}

