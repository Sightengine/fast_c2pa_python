import mimetypes
from fast_c2pa_core import read_c2pa_from_bytes, load_c2pa_settings, convert_to_gray_keep_c2pa
import json
from pathlib import Path

__all__ = ["read_c2pa_from_file", "read_c2pa_from_bytes", "get_mime_type", "setup_trust_verification", "convert_to_gray_keep_c2pa"]

def get_mime_type(file_path):
    """Get MIME type of file"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"

def read_c2pa_from_file(file_path, mime_type=None, allow_threads=True):
    """Read C2PA data from file using Rust core"""
    # Determine MIME type if not provided
    effective_mime_type = mime_type if mime_type else get_mime_type(file_path)
    
    with open(file_path, 'rb') as f:
        return read_c2pa_from_bytes(f.read(), effective_mime_type, allow_threads)

def build_trust_settings_from_files(anchors_path, allowed_path, config_path):
    """Build trust settings from three config files"""
    try:
        anchors = Path(anchors_path).read_text()
        allowed = Path(allowed_path).read_text() 
        config = Path(config_path).read_text()
        
        settings = {
            "verify": {
                "verify_trust": True
            },
            "trust": {
                "trust_anchors": anchors,
                "allowed_list": allowed,
                "trust_config": config
            }
        }
        
        return json.dumps(settings)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Trust config file not found: {e}")
    except Exception as e:
        raise RuntimeError(f"Error building trust settings: {e}")
    
def setup_trust_verification(anchors_path, allowed_path, config_path):
    """Setup global C2PA trust settings"""
    settings = build_trust_settings_from_files(anchors_path, allowed_path, config_path)
    load_c2pa_settings(settings)