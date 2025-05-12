"""
API compatibility tests for fast_c2pa_reader.

These tests verify that our implementation correctly reads C2PA metadata
and maintains compatibility with expected output formats.
"""

import os
import pytest
import json
import mimetypes
from pathlib import Path

# Import the implementation
from fast_c2pa_reader import read_c2pa_from_bytes

# Test image path - update this to point to a test image with C2PA metadata
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"
# TEST_IMAGE = str(TEST_IMAGES_DIR / "adobe_firefly_image.jpg")
TEST_IMAGE = str(TEST_IMAGES_DIR / "chatgpt_image.png")
TEST_IMAGE_NOT_C2PA = str(TEST_IMAGES_DIR / "screenshot_noc2pa.png")

def get_mime_type(file_path):
    """
    Determine MIME type from file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MIME type or None if it cannot be determined
    """
    # Initialize mimetypes if needed
    if not mimetypes.inited:
        mimetypes.init()
    
    mime_type, _ = mimetypes.guess_type(file_path)
    
    # Fallbacks for common image types if mime_type is None
    if mime_type is None:
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.tiff': 'image/tiff',
            '.heic': 'image/heic',
        }
        mime_type = mime_map.get(ext)
    
    return mime_type

@pytest.fixture(scope="session")
def setup_test_image_bytes():
    """Ensure test images directory exists and return image bytes."""
    TEST_IMAGES_DIR.mkdir(exist_ok=True)
    if not os.path.exists(TEST_IMAGE):
        pytest.skip(f"Test image not found: {TEST_IMAGE}")
    
    # Read file into bytes
    with open(TEST_IMAGE, "rb") as f:
        image_bytes_firefly = f.read()
    
    return image_bytes_firefly, get_mime_type(TEST_IMAGE)

def test_read_c2pa_from_bytes(setup_test_image_bytes):
    """Test reading C2PA metadata from bytes."""
    image_bytes, mime_type = setup_test_image_bytes
    
    # Read metadata from bytes
    metadata = read_c2pa_from_bytes(image_bytes, mime_type)
    
    # Basic validation
    assert metadata is not None
    assert "title" in metadata or "generator" in metadata or "claim_generator" in metadata
    
    # Verify signature info exists if the file has valid C2PA data
    if "signature_info" in metadata:
        assert "issuer" in metadata["signature_info"]

def test_mime_type_handling(setup_test_image_bytes):
    """Test handling of different MIME types."""
    image_bytes, correct_mime_type = setup_test_image_bytes
    
    # Test with correct MIME type
    result_correct = read_c2pa_from_bytes(image_bytes, correct_mime_type)
    assert result_correct is not None
    
    # Test with incorrect but valid MIME type (should fail gracefully)
    wrong_mime_type = "image/png" if correct_mime_type == "image/jpeg" else "image/jpeg"
    try:
        result_wrong = read_c2pa_from_bytes(image_bytes, wrong_mime_type)
        # Either it returns None/empty or it still works (some parsers are forgiving)
        assert result_wrong is None or result_wrong == {} or isinstance(result_wrong, dict)
    except Exception:
        # Or it raises an exception, which is also acceptable
        pass

def test_error_handling_invalid_bytes():
    """Test error handling with invalid data."""
    # Test with invalid bytes
    with pytest.raises(Exception):
        read_c2pa_from_bytes(b"invalid data", "image/jpeg")

def test_error_handling_no_c2pa():
    """Test with data that has no C2PA metadata."""
    if not os.path.exists(TEST_IMAGE_NOT_C2PA):
        pytest.skip(f"Test image without C2PA not found: {TEST_IMAGE_NOT_C2PA}")
    
    # Read a real image without C2PA metadata
    with open(TEST_IMAGE_NOT_C2PA, "rb") as f:
        image_bytes = f.read()
    
    # Get MIME type
    mime_type = get_mime_type(TEST_IMAGE_NOT_C2PA)
    if not mime_type:
        pytest.skip(f"Could not determine MIME type for {TEST_IMAGE_NOT_C2PA}")
    
    # Should not raise exception but return None
    result = read_c2pa_from_bytes(image_bytes, mime_type)
    assert result is None

def test_thread_safety():
    """Test thread safety option."""
    if not os.path.exists(TEST_IMAGE):
        pytest.skip(f"Test image not found: {TEST_IMAGE}")
    
    # Read test image
    with open(TEST_IMAGE, "rb") as f:
        image_bytes = f.read()
    
    # Get MIME type
    mime_type = get_mime_type(TEST_IMAGE)
    if not mime_type:
        pytest.skip(f"Could not determine MIME type for {TEST_IMAGE}")
    
    # Test with allow_threads=True (default)
    result_threaded = read_c2pa_from_bytes(image_bytes, mime_type, allow_threads=True)
    
    # Test with allow_threads=False
    result_unthreaded = read_c2pa_from_bytes(image_bytes, mime_type, allow_threads=False)
    
    # Results should be the same
    assert type(result_threaded) == type(result_unthreaded)
    if result_threaded is not None and result_unthreaded is not None:
        # Both should contain the same keys if they returned data
        assert result_threaded.keys() == result_unthreaded.keys() 