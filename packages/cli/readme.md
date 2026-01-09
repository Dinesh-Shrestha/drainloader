# [pkg]: drainloader-cli

Command-line interface for **drainloader**, a high-speed Pixeldrain downloader.

## Installation

```bash
pip install drainloader-cli
```

## Basic usage

Download a file or collection:

```bash
drainloader download https://pixeldrain.com/l/abc123
```

Extract metadata without downloading:

```bash
drainloader extract https://pixeldrain.com/u/xyz789
```

## High-speed downloads with aria2c

Use the `--aria2c` flag for multi-connection acceleration:

```bash
drainloader download --aria2c https://pixeldrain.com/l/abc123
```

You can pass custom arguments to aria2c:

```bash
drainloader download --aria2c --aria2c-args="-x 16 -s 16" https://pixeldrain.com/l/abc123
```
