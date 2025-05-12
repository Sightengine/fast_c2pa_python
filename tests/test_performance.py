"""
Performance benchmark tests for fast_c2pa_reader.

These tests verify that our implementation maintains its expected performance
characteristics, specifically ensuring that reading operations complete in < 8ms.
"""

import os
import time
import pytest
import statistics
from pathlib import Path

from fast_c2pa_reader import read_c2pa_from_file, read_c2pa_from_bytes

# Test image path - update this to point to a test image with C2PA metadata
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"
TEST_IMAGE = str(TEST_IMAGES_DIR / "sample_firefly.jpg")

# Number of iterations for reliable benchmarking
ITERATIONS = 10
# Maximum acceptable average time in milliseconds
MAX_AVG_TIME_MS = 8.0
# Maximum acceptable time for any single operation in milliseconds
MAX_SINGLE_TIME_MS = 15.0  # Allow slightly higher for occasional peaks

@pytest.fixture(scope="session")
def setup_test_images():
    """Ensure test images directory exists."""
    TEST_IMAGES_DIR.mkdir(exist_ok=True)
    if not os.path.exists(TEST_IMAGE):
        pytest.skip(f"Test image not found: {TEST_IMAGE}")
    return TEST_IMAGE

def test_performance_file_full(setup_test_images):
    """Test performance of full C2PA reading from file."""
    test_image = setup_test_images
    
    times = []
    for _ in range(ITERATIONS):
        start_time = time.time()
        read_c2pa_from_file(test_image)
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        times.append(elapsed_ms)
    
    avg_time = statistics.mean(times)
    max_time = max(times)
    
    print(f"\nFull mode performance (file):")
    print(f"  Average time: {avg_time:.2f}ms")
    print(f"  Maximum time: {max_time:.2f}ms")
    print(f"  All times: {[f'{t:.2f}' for t in times]}")
    
    # Assert performance requirements
    assert avg_time < MAX_AVG_TIME_MS, f"Average time ({avg_time:.2f}ms) exceeds maximum ({MAX_AVG_TIME_MS}ms)"
    assert max_time < MAX_SINGLE_TIME_MS, f"Maximum time ({max_time:.2f}ms) exceeds threshold ({MAX_SINGLE_TIME_MS}ms)"

def test_performance_file_minimal(setup_test_images):
    """Test performance of minimal C2PA reading from file."""
    test_image = setup_test_images
    
    times = []
    for _ in range(ITERATIONS):
        start_time = time.time()
        read_c2pa_from_file(test_image, minimal=True)
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        times.append(elapsed_ms)
    
    avg_time = statistics.mean(times)
    max_time = max(times)
    
    print(f"\nMinimal mode performance (file):")
    print(f"  Average time: {avg_time:.2f}ms")
    print(f"  Maximum time: {max_time:.2f}ms")
    print(f"  All times: {[f'{t:.2f}' for t in times]}")
    
    # Assert performance requirements
    assert avg_time < MAX_AVG_TIME_MS, f"Average time ({avg_time:.2f}ms) exceeds maximum ({MAX_AVG_TIME_MS}ms)"
    assert max_time < MAX_SINGLE_TIME_MS, f"Maximum time ({max_time:.2f}ms) exceeds threshold ({MAX_SINGLE_TIME_MS}ms)"

def test_performance_bytes(setup_test_images):
    """Test performance of C2PA reading from bytes."""
    test_image = setup_test_images
    
    # Read file into bytes once
    with open(test_image, "rb") as f:
        image_bytes = f.read()
    
    times = []
    for _ in range(ITERATIONS):
        start_time = time.time()
        read_c2pa_from_bytes(image_bytes, "image/jpeg")
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        times.append(elapsed_ms)
    
    avg_time = statistics.mean(times)
    max_time = max(times)
    
    print(f"\nBytes mode performance:")
    print(f"  Average time: {avg_time:.2f}ms")
    print(f"  Maximum time: {max_time:.2f}ms")
    print(f"  All times: {[f'{t:.2f}' for t in times]}")
    
    # Assert performance requirements
    assert avg_time < MAX_AVG_TIME_MS, f"Average time ({avg_time:.2f}ms) exceeds maximum ({MAX_AVG_TIME_MS}ms)"
    assert max_time < MAX_SINGLE_TIME_MS, f"Maximum time ({max_time:.2f}ms) exceeds threshold ({MAX_SINGLE_TIME_MS}ms)"

def test_performance_comparison():
    """Compare performance between full and minimal modes."""
    if not os.path.exists(TEST_IMAGE):
        pytest.skip(f"Test image not found: {TEST_IMAGE}")
    
    # Measure full mode
    full_times = []
    for _ in range(ITERATIONS):
        start_time = time.time()
        read_c2pa_from_file(TEST_IMAGE)
        end_time = time.time()
        full_times.append((end_time - start_time) * 1000)
    
    # Measure minimal mode
    minimal_times = []
    for _ in range(ITERATIONS):
        start_time = time.time()
        read_c2pa_from_file(TEST_IMAGE, minimal=True)
        end_time = time.time()
        minimal_times.append((end_time - start_time) * 1000)
    
    avg_full = statistics.mean(full_times)
    avg_minimal = statistics.mean(minimal_times)
    
    print(f"\nPerformance comparison:")
    print(f"  Full mode average: {avg_full:.2f}ms")
    print(f"  Minimal mode average: {avg_minimal:.2f}ms")
    print(f"  Difference: {avg_full - avg_minimal:.2f}ms ({(avg_full/avg_minimal - 1)*100:.1f}% slower in full mode)")
    
    # Minimal should be faster
    assert avg_minimal <= avg_full, "Minimal mode should be at least as fast as full mode" 