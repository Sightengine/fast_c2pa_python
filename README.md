# fast-c2pa-python

A Python library for reading C2PA metadata based on c2pa-rs

## Overview

This library provides fast C2PA metadata extraction from digital assets using direct PyO3 bindings to the Rust C2PA implementation. It was created to address performance bottlenecks in existing Python C2PA libraries.

> **Note:** This library is designed for reading C2PA metadata only. It does not support writing or creating C2PA metadata at this time.

## Benchmarks

| Implementation | Average Read Time |
| -------------- | ---------------- |
| c2pa-python (UniFFI) v8 | ~486ms |
| fast-c2pa-python (PyO3) | ~18ms |
| Native Rust | ~7ms |

## Installation

```bash
pip install fast-c2pa-python
```

## Usage

### Basic Usage

```python
from fast_c2pa_python import read_c2pa_from_file

# Read C2PA metadata from a file (with automatic MIME type detection)
metadata = read_c2pa_from_file("path/to/image.jpg")
print(metadata)

# You can also specify the MIME type explicitly if needed
metadata = read_c2pa_from_file("path/to/image.jpg", "image/jpeg")
```

### Reading from Binary Data

```python
from fast_c2pa_python import read_c2pa_from_bytes

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

## Trust Settings and Certificates

### Adding Trust Settings

To properly verify C2PA signatures, you may need to configure trust settings for specific certificate authorities or individual certificates. The Content Authenticity Initiative maintains a list of known certificates that can be used for verification.

```python
from fast_c2pa_python import setup_trust_verification, read_c2pa_from_file

# Configure trust settings using certificate files
setup_trust_verification(
    anchors_file="path/to/anchors.pem",       # Root CA certificates
    allowed_file="path/to/allowed.pem",      # Allowed intermediate certificates  
    config_file="path/to/store.cfg"          # Trust store configuration
)

# After configuring trust, read C2PA metadata
# The validation_state will be "Trusted" instead of just "Valid"
metadata = read_c2pa_from_file("path/to/image.jpg")
print(f"Validation state: {metadata['validation_state']}")
```

### Validation States

Without trust configuration:
```python
metadata = read_c2pa_from_file("image.jpg")
print(metadata['validation_state'])  # "Valid" - signature verified but not trusted
```

With trust configuration:
```python
setup_trust_verification("anchors.pem", "allowed.pem", "store.cfg")
metadata = read_c2pa_from_file("image.jpg") 
print(metadata['validation_state'])  # "Trusted" - signature verified and trusted
```

### Finding Certificates

You can find trusted certificates and learn more about certificate verification at:
- **CAI Known Certificate List**: https://opensource.contentauthenticity.org/docs/verify-known-cert-list/

## Testing

The library includes API compatibility tests to ensure functionality.

### Running Tests

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

Run API tests:

```bash
python run_tests.py --api-only
```

## Development

This library is built using [Maturin](https://github.com/PyO3/maturin), which provides Python bindings for Rust with [PyO3](https://github.com/PyO3/pyo3).

### Setting Up Development Environment

```bash
# Install Maturin
pip install maturin

# Development build (debug mode)
maturin develop

# Run in release mode for better performance
maturin develop --release
```

## License

This project is dual-licensed under both MIT and Apache 2.0 licenses to ensure compatibility with the underlying c2pa-rs library.

## Attribution

This library is built upon the excellent work of the [c2pa-rs](https://github.com/contentauth/c2pa-rs) library by the Content Authenticity Initiative. The c2pa-rs library provides the core C2PA implementation in Rust, and this project creates Python bindings using PyO3 for improved performance.

**Developed by:** [Sightengine](https://sightengine.com) - AI-powered content moderation

**Key Dependencies:**
- [c2pa-rs](https://github.com/contentauth/c2pa-rs) - Core C2PA implementation
- [PyO3](https://github.com/PyO3/pyo3) - Rust bindings for Python

Special thanks to the Content Authenticity Initiative and the c2pa-rs contributors for their foundational work on C2PA standards and implementation.