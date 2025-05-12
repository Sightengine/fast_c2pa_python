# fast_c2pa_reader

A high-performance Python library for reading C2PA metadata.

## Overview

This library provides extremely fast C2PA metadata extraction from digital assets using direct PyO3 bindings to the Rust C2PA implementation. It was created to address performance bottlenecks in existing Python C2PA libraries.

## Benchmarks

| Implementation | Average Read Time |
| -------------- | ---------------- |
| c2pa-python (UniFFI) | ~486ms |
| numbers-c2pa (subprocess) | ~17ms |
| fast_c2pa_reader (PyO3) | ~8ms |
| Native Rust | ~7ms |

## Features

- **Extreme Performance**: 100x faster than the official c2pa-python library
- **Full and Minimal Reading Modes**: Choose between complete manifest data or just essential metadata
- **Memory Efficiency**: Optimized memory usage and GIL management
- **Binary Data Support**: Read from both file paths and in-memory binary data
- **Simple API**: Clean, Pythonic interface

## Installation

```bash
pip install fast-c2pa-reader
```

## Usage

### Basic Usage

```python
from fast_c2pa_reader import read_c2pa_from_file

# Read C2PA metadata from a file
metadata = read_c2pa_from_file("path/to/image.jpg")
print(metadata)

# Get just the minimal required information (faster)
minimal_data = read_c2pa_from_file("path/to/image.jpg", minimal=True)
print(minimal_data)
```

### Reading from Binary Data

```python
from fast_c2pa_reader import read_c2pa_from_bytes

# From HTTP response or other binary source
response = requests.get("https://example.com/image.jpg")
metadata = read_c2pa_from_bytes(response.content, "image/jpeg")

# Or from a file opened in binary mode
with open("path/to/image.jpg", "rb") as f:
    data = f.read()
    metadata = read_c2pa_from_bytes(data, "image/jpeg")
```

### Example Output (Full Mode)

```python
{
    "title": "Image Title",
    "generator": "Adobe Photoshop",
    "thumbnail": {...},
    "assertions": [...],
    "signature_info": {
        "issuer": "Example Issuer",
        "time": "2023-05-23T10:30:15Z",
        "cert_serial_number": "1234567890"
    },
    "ingredients": [...],
    # Additional manifest data
}
```

### Example Output (Minimal Mode)

```python
{
    "title": "Image Title",
    "generator": "Adobe Photoshop",
    "signature_info": {
        "issuer": "Example Issuer",
        "time": "2023-05-23T10:30:15Z"
    }
}
```

## Testing

The library includes both API compatibility tests and performance benchmarks to ensure functionality and speed.

### Running Tests

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

Run all tests:

```bash
python run_tests.py --image /path/to/c2pa_image.jpg
```

Run only API compatibility tests:

```bash
python run_tests.py --api-only --image /path/to/c2pa_image.jpg
```

Run only performance benchmarks:

```bash
python run_tests.py --perf-only --image /path/to/c2pa_image.jpg
```

### Performance Guarantees

The performance tests enforce that all operations complete faster than our 8ms benchmark:

- Average read time must be < 8ms
- Individual operations must be < 15ms (allowing for occasional system variance)
- Minimal mode must be at least as fast as full mode

If any benchmark fails, the tests will fail, ensuring we maintain our performance commitment.

## Implementation Details

1. **Direct PyO3 Bindings**: Native Rust-to-Python integration without intermediaries
2. **GIL Management**: Releases the Python GIL during I/O operations
3. **Optimized Rust Compilation**: LTO and codegen-units=1 for maximum performance
4. **Memory Optimization**: Minimal copying of data between Rust and Python
5. **Streamlined Data Extraction**: Only extracts what's needed

## Requirements

- Python 3.7+
- Compatible with Linux, macOS, and Windows

## License

MIT 