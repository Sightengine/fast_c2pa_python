import time
import statistics
import json
from pathlib import Path
import fast_c2pa_python
from fast_c2pa_python import setup_trust_verification

def setup_trust_if_available():
    """Setup trust verification if config files are available."""
    trust_dir = Path("./tests/tmp_cert")
    anchors_file = trust_dir / "anchors.pem" 
    allowed_file = trust_dir / "allowed.pem"
    config_file = trust_dir / "store.cfg"
    
    if all(f.exists() for f in [anchors_file, allowed_file, config_file]):
        try:
            setup_trust_verification(str(anchors_file), str(allowed_file), str(config_file))
            print("Trust verification enabled")
            return True
        except Exception as e:
            print(f"Failed to setup trust: {e}")
            return False
    else:
        print("Trust files not found, running without trust verification")
        return False

def benchmark_c2pa_read(image_path, iterations=200):
    print(f"\nRunning FAST C2PA reading benchmark over {iterations} iterations...")
    print(f"File: {image_path}")
    
    print("Reading file into memory...")
    with open(image_path, 'rb') as f:
        data = f.read()
    print(f"File read complete. Size: {len(data)} bytes")
    
    result = fast_c2pa_python.read_c2pa_from_bytes(data, "image/jpeg", allow_threads=True)
    if result:
        print("\nC2PA Data Found (full data):")
        print(f"  Title: {result.get('title')}")
        print(f"  Claim Generator: {result.get('claim_generator')}")
        signature_info = result.get('signature_info', {})
        if signature_info:
            print(f"  Signed by: {signature_info.get('issuer')}")
        
        # Print the complete data structure
        print("\nComplete C2PA Data:")
        print(json.dumps(result, indent=2))
    else:
        print("No C2PA metadata found in the image")
    
    print("\nBenchmarking:")
    times_full = []
    for i in range(iterations):
        start_time = time.perf_counter()
        fast_c2pa_python.read_c2pa_from_bytes(data, "image/jpeg", allow_threads=True)
        duration = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
        times_full.append(duration)
        print(f"Iteration {i + 1}: {duration:.3f}ms")
    
    avg_time_full = statistics.mean(times_full)
    std_dev_full = statistics.stdev(times_full) if len(times_full) > 1 else 0
    min_time_full = min(times_full)
    max_time_full = max(times_full)

    print(f"\nBenchmark Results:")
    print(f"\nFull version:")
    print(f"  Average time: {avg_time_full:.3f}ms")
    print(f"  Standard deviation: {std_dev_full:.3f}ms")
    print(f"  Min time: {min_time_full:.3f}ms")
    print(f"  Max time: {max_time_full:.3f}ms")
    
if __name__ == "__main__":
    # Setup trust verification if available
    setup_trust_if_available()
    
    # Replace with your image path
    image_path = "./tests/test_images/adobe_firefly_image.jpg"
    benchmark_c2pa_read(image_path) 