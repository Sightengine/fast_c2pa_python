"""
Performance benchmark tests for fast_c2pa_reader.

These tests verify that our implementation maintains its expected performance
characteristics, focusing on relative performance and avoiding hard-coded thresholds
that depend on specific hardware.
"""

import os
import time
import pytest
import statistics
import platform
import mimetypes
from pathlib import Path

from fast_c2pa_reader import read_c2pa_from_bytes

# Test image path - update this to point to a test image with C2PA metadata
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"
# TEST_IMAGE = str(TEST_IMAGES_DIR / "adobe_firefly_image.jpg")
TEST_IMAGE = str(TEST_IMAGES_DIR / "chatgpt_image.png")

# Number of iterations for reliable benchmarking
ITERATIONS = 10

# Environment-aware thresholds
def get_performance_thresholds():
    """
    Return performance thresholds based on the current environment.
    These thresholds can be overridden by environment variables.
    """
    # Default thresholds (can be overridden by environment variables)
    default_avg_ms = 10.0
    default_max_ms = 15.0
    
    # Allow overriding thresholds via environment variables
    avg_threshold = float(os.environ.get("FAST_C2PA_MAX_AVG_TIME_MS", default_avg_ms))
    max_threshold = float(os.environ.get("FAST_C2PA_MAX_SINGLE_TIME_MS", default_max_ms))
    
    # Skip tests if environment variable is set
    skip_perf_tests = os.environ.get("SKIP_PERFORMANCE_TESTS", "").lower() in ("1", "true", "yes")
    
    return {
        "avg_threshold": avg_threshold,
        "max_threshold": max_threshold,
        "skip_tests": skip_perf_tests
    }

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
        image_bytes = f.read()
    
    return image_bytes, get_mime_type(TEST_IMAGE)

def test_performance_bytes(setup_test_image_bytes):
    """Test performance of C2PA reading from bytes."""
    thresholds = get_performance_thresholds()
    if thresholds["skip_tests"]:
        pytest.skip("Performance tests skipped via environment variable")

    image_bytes, mime_type = setup_test_image_bytes
    
    if not mime_type:
        pytest.skip(f"Could not determine MIME type for {TEST_IMAGE}")
    
    times = []
    for _ in range(ITERATIONS):
        start_time = time.time()
        read_c2pa_from_bytes(image_bytes, mime_type, allow_threads=True)
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        times.append(elapsed_ms)
    
    avg_time = statistics.mean(times)
    max_time = max(times)
    
    print(f"\nPerformance results:")
    print(f"  Average time: {avg_time:.2f}ms")
    print(f"  Maximum time: {max_time:.2f}ms")
    print(f"  All times: {[f'{t:.2f}' for t in times]}")
    print(f"  System: {platform.system()} {platform.version()}")
    print(f"  MIME type: {mime_type}")
    
    # Use environment-aware thresholds for assertions
    assert avg_time < thresholds["avg_threshold"], f"Average time ({avg_time:.2f}ms) exceeds maximum ({thresholds['avg_threshold']}ms)"
    assert max_time < thresholds["max_threshold"], f"Maximum time ({max_time:.2f}ms) exceeds threshold ({thresholds['max_threshold']}ms)"