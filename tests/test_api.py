"""
API compatibility tests for fast_c2pa_python.

These tests verify that our implementation correctly reads C2PA metadata
and maintains compatibility with expected output formats.
"""

import os
import pytest
import json
import mimetypes
from pathlib import Path

from fast_c2pa_python import read_c2pa_from_bytes, read_c2pa_from_file, get_mime_type, setup_trust_verification

# Test images - both JPEG and PNG formats
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"
TEST_IMAGES = [
    str(TEST_IMAGES_DIR / "chatgpt_image.png"),
    str(TEST_IMAGES_DIR / "adobe_firefly_image.jpg")
]
TEST_IMAGE_NOT_C2PA = str(TEST_IMAGES_DIR / "screenshot_noc2pa.png")

# Trust settings files
TRUST_ANCHORS_FILE = str(Path(__file__).parent / "tmp_cert" / "anchors.pem")
TRUST_ALLOWED_FILE = str(Path(__file__).parent / "tmp_cert" / "allowed.pem") 
TRUST_CONFIG_FILE = str(Path(__file__).parent / "tmp_cert" / "store.cfg")

@pytest.fixture(scope="session", params=TEST_IMAGES)
def setup_test_image_bytes(request):
    """Ensure test images directory exists and return image bytes for each test image."""
    TEST_IMAGES_DIR.mkdir(exist_ok=True)
    test_image = request.param
    
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found: {test_image}")
    
    # Read file into bytes
    with open(test_image, "rb") as f:
        image_bytes = f.read()
    
    return image_bytes, get_mime_type(test_image), test_image

def get_active_manifest(metadata):
    """Helper function to get the active manifest from c2pa structure."""
    if not metadata or "active_manifest" not in metadata or "manifests" not in metadata:
        return None
    active_manifest_id = metadata["active_manifest"]
    return metadata["manifests"].get(active_manifest_id)

def has_trust_files():
    """Check if trust configuration files exist."""
    return (os.path.exists(TRUST_ANCHORS_FILE) and 
            os.path.exists(TRUST_ALLOWED_FILE) and 
            os.path.exists(TRUST_CONFIG_FILE))

def setup_trust_settings():
    """Configure trust settings for C2PA validation."""
    if not has_trust_files():
        return False
    
    try:
        setup_trust_verification(TRUST_ANCHORS_FILE, TRUST_ALLOWED_FILE, TRUST_CONFIG_FILE)
        return True
    except Exception as e:
        print(f"Failed to setup trust settings: {e}")
        return False

def test_read_c2pa_from_bytes(setup_test_image_bytes):
    """Test reading C2PA metadata from bytes."""
    image_bytes, mime_type, test_image = setup_test_image_bytes
    
    print(f"Testing {test_image} with MIME type {mime_type}")
    
    # Read metadata from bytes
    metadata = read_c2pa_from_bytes(image_bytes, mime_type)
    
    # Basic validation - check c2pa structure
    assert metadata is not None
    assert "active_manifest" in metadata
    assert "manifests" in metadata
    
    # Get active manifest
    active_manifest = get_active_manifest(metadata)
    assert active_manifest is not None
    assert "title" in active_manifest or "generator" in active_manifest or "claim_generator" in active_manifest
    
    # Verify signature info exists if the file has valid C2PA data
    if "signature_info" in active_manifest:
        assert "issuer" in active_manifest["signature_info"]

@pytest.mark.parametrize("test_image", TEST_IMAGES)
@pytest.mark.order(1)  # Run this test early before any trust setup
def test_validation_state_without_trust(test_image):
    """Test that validation_state is 'Valid' when no trust settings are configured."""
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found: {test_image}")
    
    # This test should only run if trust hasn't been configured yet
    # We'll check this by reading metadata and seeing the state
    metadata = read_c2pa_from_file(test_image)
    
    if metadata is None:
        pytest.skip(f"No C2PA metadata found in {test_image}")
    
    # If trust was already configured by previous tests, skip this test
    if metadata["validation_state"] == "Trusted":
        pytest.skip("Trust settings already configured globally - cannot test without trust")
    
    # Verify validation_state is 'Valid' 
    assert "validation_state" in metadata
    assert metadata["validation_state"] == "Valid", f"Expected 'Valid' but got '{metadata['validation_state']}'"
    
    # Verify no signingCredential.trusted validation result
    if "validation_results" in metadata and "activeManifest" in metadata["validation_results"]:
        success_results = metadata["validation_results"]["activeManifest"].get("success", [])
        trusted_results = [r for r in success_results if r.get("code") == "signingCredential.trusted"]
        assert len(trusted_results) == 0, "Should not have signingCredential.trusted without trust settings"

@pytest.mark.parametrize("test_image", TEST_IMAGES)
@pytest.mark.order(2)  # Run after the without-trust test
def test_validation_state_with_trust(test_image):
    """Test that validation_state is 'Trusted' when trust settings are configured."""
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found: {test_image}")
    
    if not has_trust_files():
        pytest.skip("Trust configuration files not found - cannot test trust validation")
    
    # Configure trust settings
    if not setup_trust_settings():
        pytest.skip("Could not configure trust settings")
    
    # Read metadata with trust settings
    metadata = read_c2pa_from_file(test_image)
    
    if metadata is None:
        pytest.skip(f"No C2PA metadata found in {test_image}")
    
    # Verify validation_state is 'Trusted'
    assert "validation_state" in metadata
    assert metadata["validation_state"] == "Trusted", (
        f"Expected validation_state 'Trusted' but got '{metadata['validation_state']}'"
    )
    
    # Verify signingCredential.trusted validation result is present
    if "validation_results" in metadata and "activeManifest" in metadata["validation_results"]:
        success_results = metadata["validation_results"]["activeManifest"].get("success", [])
        trusted_results = [r for r in success_results if r.get("code") == "signingCredential.trusted"]
        assert len(trusted_results) >= 1, (
            "Should have at least one signingCredential.trusted validation result with trust settings"
        )
        
        # Verify the trusted result has correct structure
        trusted_result = trusted_results[0]
        assert "url" in trusted_result
        assert "explanation" in trusted_result

@pytest.mark.parametrize("test_image", TEST_IMAGES) 
@pytest.mark.order(3)  # Run after trust is configured
def test_trust_enables_additional_validation(test_image):
    """Test that trust settings add the signingCredential.trusted validation result."""
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found: {test_image}")
    
    if not has_trust_files():
        pytest.skip("Trust configuration files not found - cannot test trust validation")
    
    # Ensure trust is configured (should be from previous test)
    if not setup_trust_settings():
        pytest.skip("Could not configure trust settings")
    
    metadata = read_c2pa_from_file(test_image)
    
    if metadata is None:
        pytest.skip(f"No C2PA metadata found in {test_image}")
    
    # With trust settings, validation_state must be "Trusted"
    assert metadata["validation_state"] == "Trusted"
    
    if "validation_results" in metadata and "activeManifest" in metadata["validation_results"]:
        success_results = metadata["validation_results"]["activeManifest"].get("success", [])
        
        # Check that signingCredential.trusted is present
        trusted_results = [r for r in success_results if r.get("code") == "signingCredential.trusted"]
        assert len(trusted_results) >= 1, "Trust settings should add signingCredential.trusted validation"
        
        # Check that we have the standard validation results plus the trust one
        validation_codes = {r.get("code") for r in success_results}
        expected_codes = {
            "claimSignature.insideValidity",
            "claimSignature.validated", 
            "assertion.hashedURI.match",
            "assertion.dataHash.match",
            "signingCredential.trusted"  # This should be added by trust settings
        }
        
        # All expected codes should be present (may have multiple assertion.hashedURI.match)
        for code in expected_codes:
            assert code in validation_codes, f"Missing expected validation code: {code}"

def test_mime_type_handling(setup_test_image_bytes):
    """Test handling of different MIME types."""
    image_bytes, correct_mime_type, test_image = setup_test_image_bytes
    
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

def test_no_jumbf_data():
    """Test error handling with invalid data."""
    # Test with invalid bytes - should return None instead of raising exception
    result = read_c2pa_from_bytes(b"no jumbf data", "image/jpeg")
    assert result is None

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

@pytest.mark.parametrize("test_image", TEST_IMAGES)
def test_thread_safety(test_image):
    """Test thread safety option."""
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found: {test_image}")
    
    # Read test image
    with open(test_image, "rb") as f:
        image_bytes = f.read()
    
    # Get MIME type
    mime_type = get_mime_type(test_image)
    if not mime_type:
        pytest.skip(f"Could not determine MIME type for {test_image}")
    
    print(f"Testing thread safety for {test_image} with MIME type {mime_type}")
    
    # Test with allow_threads=True (default)
    result_threaded = read_c2pa_from_bytes(image_bytes, mime_type, allow_threads=True)
    
    # Test with allow_threads=False
    result_unthreaded = read_c2pa_from_bytes(image_bytes, mime_type, allow_threads=False)
    
    # Results should be the same
    assert type(result_threaded) == type(result_unthreaded)
    if result_threaded is not None and result_unthreaded is not None:
        # Both should contain the same keys if they returned data
        assert result_threaded.keys() == result_unthreaded.keys()

@pytest.mark.parametrize("test_image", TEST_IMAGES)
def test_read_c2pa_from_file_with_explicit_mime(test_image):
    """Test reading C2PA metadata from file with explicit MIME type."""
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found: {test_image}")
    
    # Get MIME type
    mime_type = get_mime_type(test_image)
    if not mime_type:
        pytest.skip(f"Could not determine MIME type for {test_image}")
    
    print(f"Testing explicit MIME for {test_image} with MIME type {mime_type}")
    
    # Read metadata with explicit MIME type
    metadata = read_c2pa_from_file(test_image, mime_type)
    
    # Basic validation - check c2pa structure
    assert metadata is not None
    assert "active_manifest" in metadata
    assert "manifests" in metadata
    
    # Get active manifest
    active_manifest = get_active_manifest(metadata)
    assert active_manifest is not None
    assert "title" in active_manifest or "generator" in active_manifest or "claim_generator" in active_manifest
    
    # Verify signature info exists if the file has valid C2PA data
    if "signature_info" in active_manifest:
        assert "issuer" in active_manifest["signature_info"]

@pytest.mark.parametrize("test_image", TEST_IMAGES)
def test_read_c2pa_from_file_with_auto_mime(test_image):
    """Test reading C2PA metadata from file with automatic MIME type detection."""
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found: {test_image}")
    
    mime_type = get_mime_type(test_image)
    print(f"Testing auto MIME for {test_image} with detected MIME type {mime_type}")
    
    # Read metadata with automatic MIME type detection
    metadata = read_c2pa_from_file(test_image)
    
    # Basic validation - check c2pa structure
    assert metadata is not None
    assert "active_manifest" in metadata
    assert "manifests" in metadata
    
    # Get active manifest
    active_manifest = get_active_manifest(metadata)
    assert active_manifest is not None
    assert "title" in active_manifest or "generator" in active_manifest or "claim_generator" in active_manifest
    
    # Verify signature info exists if the file has valid C2PA data
    if "signature_info" in active_manifest:
        assert "issuer" in active_manifest["signature_info"]

def test_read_c2pa_from_file_no_c2pa():
    """Test with file that has no C2PA metadata."""
    if not os.path.exists(TEST_IMAGE_NOT_C2PA):
        pytest.skip(f"Test image without C2PA not found: {TEST_IMAGE_NOT_C2PA}")
    
    # Should not raise exception but return None
    result = read_c2pa_from_file(TEST_IMAGE_NOT_C2PA)
    assert result is None

@pytest.mark.parametrize("test_image", TEST_IMAGES)
def test_read_c2pa_from_file_thread_safety(test_image):
    """Test thread safety option for read_c2pa_from_file."""
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found: {test_image}")
    
    mime_type = get_mime_type(test_image)
    print(f"Testing file thread safety for {test_image} with MIME type {mime_type}")
    
    # Test with allow_threads=True (default)
    result_threaded = read_c2pa_from_file(test_image, allow_threads=True)
    
    # Test with allow_threads=False
    result_unthreaded = read_c2pa_from_file(test_image, allow_threads=False)
    
    # Results should be the same
    assert type(result_threaded) == type(result_unthreaded)
    if result_threaded is not None and result_unthreaded is not None:
        # Both should contain the same keys if they returned data
        assert result_threaded.keys() == result_unthreaded.keys()

def test_read_c2pa_from_file_invalid_path():
    """Test error handling with invalid file path."""
    # Test with invalid file path
    with pytest.raises(Exception):
        read_c2pa_from_file("nonexistent_file.jpg")

@pytest.mark.parametrize("test_image", TEST_IMAGES)
def test_read_c2pa_from_file_empty_mime(test_image):
    """Test with empty MIME type (should use auto-detection)."""
    if not os.path.exists(test_image):
        pytest.skip(f"Test image not found: {test_image}")
    
    mime_type = get_mime_type(test_image)
    print(f"Testing empty MIME for {test_image} with detected MIME type {mime_type}")
    
    # Read with empty MIME type string
    result_empty = read_c2pa_from_file(test_image, "")
    
    # Read with automatic MIME type
    result_auto = read_c2pa_from_file(test_image)
    
    # Both should work the same
    assert type(result_empty) == type(result_auto)
    if result_empty is not None and result_auto is not None:
        assert result_empty.keys() == result_auto.keys() 