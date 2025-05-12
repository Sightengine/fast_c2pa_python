"""
API compatibility tests for fast_c2pa_reader.

These tests verify that our implementation correctly reads C2PA metadata
and maintains compatibility with expected output formats.
"""

import os
import pytest
import json
from pathlib import Path

# Import both implementations to compare results
from fast_c2pa_reader import read_c2pa_from_file, read_c2pa_from_bytes

# Test image path - update this to point to a test image with C2PA metadata
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"
TEST_IMAGE = str(TEST_IMAGES_DIR / "sample_firefly.jpg")

@pytest.fixture(scope="session")
def setup_test_images():
    """Ensure test images directory exists."""
    TEST_IMAGES_DIR.mkdir(exist_ok=True)
    if not os.path.exists(TEST_IMAGE):
        pytest.skip(f"Test image not found: {TEST_IMAGE}")
    return TEST_IMAGE

def test_read_c2pa_from_file(setup_test_images):
    """Test reading C2PA metadata from file."""
    test_image = setup_test_images
    
    # Read full metadata
    metadata = read_c2pa_from_file(test_image)
    
    # Basic validation
    assert metadata is not None
    assert "title" in metadata or "generator" in metadata
    
    # Verify signature info exists if the file has valid C2PA data
    if "signature_info" in metadata:
        assert "issuer" in metadata["signature_info"]
        assert "time" in metadata["signature_info"]

def test_read_c2pa_from_file_minimal(setup_test_images):
    """Test reading minimal C2PA metadata from file."""
    test_image = setup_test_images
    
    # Read minimal metadata
    metadata = read_c2pa_from_file(test_image, minimal=True)
    
    # Basic validation
    assert metadata is not None
    
    # Minimal mode should be more efficient with less data
    assert len(json.dumps(metadata)) < len(json.dumps(read_c2pa_from_file(test_image)))

def test_read_c2pa_from_bytes(setup_test_images):
    """Test reading C2PA metadata from bytes."""
    test_image = setup_test_images
    
    # Read file into bytes
    with open(test_image, "rb") as f:
        image_bytes = f.read()
    
    # Read metadata from bytes
    metadata = read_c2pa_from_bytes(image_bytes, "image/jpeg")
    
    # Basic validation
    assert metadata is not None
    assert "title" in metadata or "generator" in metadata
    
    # Verify results match file-based reading
    file_metadata = read_c2pa_from_file(test_image)
    assert metadata.keys() == file_metadata.keys()

def test_error_handling_invalid_file():
    """Test error handling with invalid files."""
    # Test with non-existent file
    with pytest.raises(Exception):
        read_c2pa_from_file("non_existent_file.jpg")
    
    # Test with invalid bytes
    with pytest.raises(Exception):
        read_c2pa_from_bytes(b"invalid data", "image/jpeg")

def test_error_handling_no_c2pa():
    """Test with file that has no C2PA metadata."""
    # Create an empty temp file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
        tmp.write(b"test")
        tmp.flush()
        
        # Should not raise exception but return empty or None
        result = read_c2pa_from_file(tmp.name)
        assert result is None or result == {} or "error" in result 