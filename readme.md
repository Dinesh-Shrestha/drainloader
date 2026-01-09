# drainloader

High-speed, dedicated downloader for [pixeldrain.com](https://pixeldrain.com) powered by `aria2c`.

## Features

- **Dedicated to Pixeldrain**: Specialized extraction for lists and individual files.
- **High-Speed Downloads**: Optional `aria2c` integration for multi-connection acceleration.
- **Smart Resumption**: Automatically resumes interrupted downloads (default).
- **Clean CLI**: Minimalist and focused command-line interface.
- **Robust Interruptions**: Instant response to `Ctrl+C`.

## Installation

```bash
# Recommendation: use uv to install
pip install .
```

## Usage

### Basic Usage
```bash
drainloader download https://pixeldrain.com/l/abc123
```

### High-Speed (aria2c)
```bash
drainloader download --aria2c https://pixeldrain.com/u/xyz789
```

### Advanced aria2c Arguments
```bash
drainloader download --aria2c --aria2c-args="-x 16 -s 16" https://pixeldrain.com/l/def456
```

### Dry Run (Extract Metadata)
```bash
drainloader extract https://pixeldrain.com/l/abc123
```

## Command Line Options

- `--aria2c`: Enable high-speed downloads via `aria2c`.
- `--aria2c-args`: Custom arguments for `aria2c`.
- `--overwrite`: Force re-download even if file exists.
- `--flat`: Download all files directly into the output directory (ignore collections).
- `--filter`: Filter files by glob pattern (e.g., `*.jpg`).

## CLI vs Library

Drainloader is built on a modular architecture:
- Core extraction logic is in `packages/core`.
- CLI interface is in `packages/cli`.

## Development

Set up a development environment using `uv`:

```bash
uv sync
```

Run tests and checks:
```bash
uv run ruff format .
uv run ruff check --fix .
uv run pytest
```

## Acknowledgments

Based on the original `megaloader` project. Refactored to focus exclusively on Pixeldrain excellence.
