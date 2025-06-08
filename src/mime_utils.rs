use pyo3::prelude::*;

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
pub fn get_mime_type(py: Python, file_path: &str) -> PyResult<Option<String>> {
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