#!/usr/bin/env python
"""
Test runner for fast_c2pa_reader.

This script runs both API compatibility tests and performance benchmarks.
"""

import os
import sys
import pytest
import argparse
from pathlib import Path

def main():
    """Run tests for fast_c2pa_reader."""
    parser = argparse.ArgumentParser(description="Run tests for fast_c2pa_reader")
    parser.add_argument("--api-only", action="store_true", help="Run only API tests")
    parser.add_argument("--perf-only", action="store_true", help="Run only performance tests")
    parser.add_argument("--image", type=str, help="Path to test image with C2PA metadata")
    args = parser.parse_args()
    
    # Set path to test directory
    test_dir = Path(__file__).parent / "tests"
    
    # Create test image directory if it doesn't exist
    test_images_dir = test_dir / "test_images"
    test_images_dir.mkdir(exist_ok=True, parents=True)
    
    # If a test image is provided, copy it to the test directory
    if args.image:
        import shutil
        src_path = Path(args.image).resolve()
        if not src_path.exists():
            print(f"Error: Test image not found: {src_path}")
            return 1
        
        dst_path = test_images_dir / "sample_firefly.jpg"
        print(f"Copying test image from {src_path} to {dst_path}")
        shutil.copy(src_path, dst_path)
    
    # Determine which tests to run
    if args.api_only:
        test_paths = [str(test_dir / "test_api.py")]
    elif args.perf_only:
        test_paths = [str(test_dir / "test_performance.py")]
    else:
        test_paths = [str(test_dir)]
    
    # Run the tests
    return pytest.main(["-v"] + test_paths)

if __name__ == "__main__":
    sys.exit(main()) 