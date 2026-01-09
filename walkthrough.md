# Walkthrough: Refactoring Megaloader to Drainloader

I have successfully refactored the project into **drainloader**, a dedicated, high-speed downloader for Pixeldrain.

## Key Accomplishments

### 1. Project Rebranding & Specialization
- **Renamed to Drainloader**: Updated all configurations (`pyproject.toml`), source directories, and internal Python imports from `megaloader` to `drainloader`.
- **Pixeldrain Focus**: Removed all non-Pixeldrain plugins (Bunkr, GoFile, etc.) to create a lightweight, specialized tool.
- **Simplified Architecture**: Removed unused `apps/` and `docs/` directories, focusing on the core library and CLI.

### 2. High-Speed aria2c Integration
- **Aria2c Support**: Integrated `aria2c` as an optional download engine via the `--aria2c` flag.
- **Optimized Defaults**: Configured balanced defaults (`-x 5 -s 5`) for multi-connection acceleration.
- **Smart Resumption**: Implemented logic to detect `.aria2` control files, allowing seamless resumption of partial downloads.

### 3. User Experience Improvements
- **Robust Interruption**: Added signal handling for `SIGINT` (Ctrl+C). The CLI now uses a daemon thread to ensure instant and clean exits.
- **Skip behavior**: Implemented smart skipping (don't re-download if file exists and is complete) with an optional `--overwrite` flag.
- **Modern CLI**: Updated help text, examples, and version info to reflect the new `drainloader` identity.

## Verification

### 1. Structure Verification
- Sources correctly moved to `packages/core/drainloader` and `packages/cli/drainloader_cli`.
- `PLUGIN_REGISTRY` in `drainloader.plugins` contains only Pixeldrain.

### 2. CLI Verification
- Running `drainloader --help` confirmed the new branding and flags.
- Confirmed `aria2c` arguments are correctly constructed and executed.

### 3. Import Verification
- Verified all internal imports use `from drainloader...` or `import drainloader`.

## Summary of Changes

| Category | Description |
| :--- | :--- |
| **Naming** | `megaloader` → `drainloader` |
| **Scope** | Multi-platform → Pixeldrain Only |
| **Engine** | Standard Requests + Aria2c Support |
| **Interruption** | Signal-based immediate exit |
| **Resumption** | Smart skip/resume by default |

This transformation provides a more focused, faster, and more reliable tool for Pixeldrain users.
