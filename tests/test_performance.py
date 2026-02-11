"""
Performance benchmark tests for fast_c2pa_python.

These tests verify that our implementation is at least 10x faster than c2pa-python,
focusing on relative performance rather than absolute time measurements.
"""

import os
import time
import pytest
import statistics
import platform
import mimetypes
from pathlib import Path
from io import BytesIO

from fast_c2pa_python import read_c2pa_from_bytes, read_c2pa_from_file, get_mime_type

# Import c2pa-python for comparison
from c2pa import Reader

# Test image path - update this to point to a test image with C2PA metadata
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"
# TEST_IMAGE = str(TEST_IMAGES_DIR / "adobe_firefly_image.jpg")
TEST_IMAGE = str(TEST_IMAGES_DIR / "chatgpt_image.png")

# Number of iterations for reliable benchmarking
ITERATIONS = 10

# Environment-aware settings
def get_performance_settings():
    """
    Return performance settings based on the current environment.
    These settings can be overridden by environment variables.
    """
    # Default minimum speedup factor (can be overridden)
    default_speedup_factor = 10.0
    
    # Allow overriding thresholds via environment variables
    speedup_factor = float(os.environ.get("FAST_C2PA_MIN_SPEEDUP_FACTOR", default_speedup_factor))
    
    # Skip tests if environment variable is set
    skip_perf_tests = os.environ.get("SKIP_PERFORMANCE_TESTS", "").lower() in ("1", "true", "yes")
    
    return {
        "speedup_factor": speedup_factor,
        "skip_tests": skip_perf_tests
    }

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

def test_compare_performance(setup_test_image_bytes):
    """Test performance of fast_c2pa_python vs c2pa-python."""
    settings = get_performance_settings()
    if settings["skip_tests"]:
        pytest.skip("Performance tests skipped via environment variable")

    image_bytes, mime_type = setup_test_image_bytes
    
    if not mime_type:
        pytest.skip(f"Could not determine MIME type for {TEST_IMAGE}")
    
    # Test fast_c2pa_python performance
    fast_c2pa_times = []
    for _ in range(ITERATIONS):
        start_time = time.time()
        read_c2pa_from_bytes(image_bytes, mime_type, allow_threads=True)
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        fast_c2pa_times.append(elapsed_ms)
    
    fast_c2pa_avg = statistics.mean(fast_c2pa_times)
    
    # Test c2pa-python performance
    c2pa_python_times = []
    for _ in range(ITERATIONS):
        stream = BytesIO(image_bytes)
        start_time = time.time()
        reader = Reader(mime_type, stream)
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        c2pa_python_times.append(elapsed_ms)
    
    c2pa_python_avg = statistics.mean(c2pa_python_times)
    
    # Calculate speedup factor
    speedup = c2pa_python_avg / fast_c2pa_avg
    
    print(f"\nPerformance comparison results:")
    print(f"  fast_c2pa_python average time: {fast_c2pa_avg:.2f}ms")
    print(f"  c2pa-python average time: {c2pa_python_avg:.2f}ms")
    print(f"  Speedup factor: {speedup:.2f}x")
    print(f"  Required minimum speedup: {settings['speedup_factor']}x")
    print(f"  System: {platform.system()} {platform.version()}")
    print(f"  MIME type: {mime_type}")
    
    # Check if our library is at least N times faster
    assert speedup >= settings["speedup_factor"], (
        f"fast_c2pa_python is only {speedup:.2f}x faster than c2pa-python, "
        f"but at least {settings['speedup_factor']}x speedup is required"
    )
