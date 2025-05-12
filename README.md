# fast_c2pa_reader

A high-performance Python library for reading C2PA metadata.

## Overview

This library provides extremely fast C2PA metadata extraction from digital assets using direct PyO3 bindings to the Rust C2PA implementation. It was created to address performance bottlenecks in existing Python C2PA libraries.

> **Note:** This library is designed for reading C2PA metadata only. It does not support writing or creating C2PA metadata at this time.

## Benchmarks

| Implementation | Average Read Time |
| -------------- | ---------------- |
| c2pa-python (UniFFI) | ~486ms |
| numbers-c2pa (subprocess) | ~17ms |
| fast_c2pa_reader (PyO3) | ~8ms |
| Native Rust | ~7ms |

## Features

- **Extreme Performance**: Much faster than c2pa-python and approaching native Rust performance

## Installation

```bash
pip install fast-c2pa-reader
```

## Usage

### Basic Usage

```python
from fast_c2pa_reader import read_c2pa_from_file

# Read C2PA metadata from a file (with automatic MIME type detection)
metadata = read_c2pa_from_file("path/to/image.jpg")
print(metadata)

# You can also specify the MIME type explicitly if needed
metadata = read_c2pa_from_file("path/to/image.jpg", "image/jpeg")
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

### Example Output

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

## Testing

The library includes both API compatibility tests and performance benchmarks to ensure functionality and speed.

### Running Tests

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

Run all tests:

```bash
python run_tests.py 
```

## License

MIT 