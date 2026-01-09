# Contributing to Drainloader

We welcome contributions! Please follow these simple steps:

1.  **Fork** the repository.
2.  **Create a branch** for your feature or fix.
3.  **Install dependencies** using `uv`:
    ```bash
    uv sync
    ```
4.  **Run checks** before committing:
    ```bash
    uv run ruff format .
    uv run ruff check .
    uv run pytest
    ```
5.  **Submit a Pull Request** with a clear description of your changes.

Thank you for helping make Drainloader better!
