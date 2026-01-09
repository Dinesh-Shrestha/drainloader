# [pkg]: drainloader (core)

Library for extracting downloadable content metadata from Pixeldrain.

## Installation

```bash
pip install drainloader
```

## Basic usage

Call `extract()` with a Pixeldrain URL:

```python
from drainloader import extract

for item in extract("https://pixeldrain.com/l/abc123"):
    print(f"{item.filename} - {item.download_url}")
```

## Error handling

```python
from drainloader import extract, ExtractionError, UnsupportedDomainError

try:
    items = list(extract(url))
except UnsupportedDomainError:
    print("Platform not supported")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
```
