
### Install c2pa-python library to run this benchmark
import time
import statistics
import json
from io import BytesIO
from c2pa import Reader

def benchmark_c2pa_python(image_path, iterations=200):
    print(f"\nRunning c2pa-python reading benchmark over {iterations} iterations...")
    print(f"File: {image_path}")
    
    # Read file into memory once
    print("Reading file into memory...")
    with open(image_path, 'rb') as f:
        data = f.read()
    print(f"File read complete. Size: {len(data)} bytes")
    
    # First run to show the metadata
    stream = BytesIO(data)
    reader = Reader("image/jpeg", stream)
    result = reader.get_active_manifest()
    
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
    
    # Benchmark runs
    print("\nBenchmarking full version:")
    times_full = []
    for i in range(iterations):
        stream = BytesIO(data)
        start_time = time.perf_counter()
        reader = Reader("image/jpeg", stream)
        duration = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
        times_full.append(duration)
        print(f"Iteration {i + 1}: {duration:.3f}ms")
    
    # Calculate statistics
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
    # Use the same test image as in the fast_c2pa_reader benchmark
    image_path = "./tests/test_images/adobe_firefly_image.jpg"
    benchmark_c2pa_python(image_path, 10) 