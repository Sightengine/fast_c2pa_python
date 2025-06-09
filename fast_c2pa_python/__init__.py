import mimetypes
from fast_c2pa_core import read_c2pa_from_bytes

def get_mime_type(file_path):
    """Get MIME type of file"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"

def read_c2pa_from_file(file_path, mime_type=None, allow_threads=True, verify_trust=None):
    """Read C2PA data from file using Rust core"""
    # Determine MIME type if not provided
    effective_mime_type = mime_type if mime_type else get_mime_type(file_path)
    
    with open(file_path, 'rb') as f:
        return read_c2pa_from_bytes(f.read(), effective_mime_type, allow_threads, verify_trust)

__all__ = ["read_c2pa_from_file", "read_c2pa_from_bytes", "get_mime_type"]