\
# Default task: list available commands
default: list

# List available commands
list:
    @just --list

# Install dependencies
install:
    uv sync --all-extras

# Show how to activate the virtual environment
activate:
    @echo "To activate the virtual environment, run: source .venv/bin/activate"

# Generate the image manifest
generate:
    uv run -- python generate_manifest.py

# Lint with Ruff
lint:
    uv run -- ruff check .

# Format with Ruff
format:
    uv run -- ruff format .

# Type check with MyPy
typecheck:
    uv run -- mypy generate_manifest.py

# Lint with Ruff and apply automatic fixes
lint-fix:
    uv run -- ruff check . --fix

# Format imports with Ruff
format-imports:
    uv run -- ruff check . --select I --fix

# Run all quality checks (format, lint, typecheck)
qa:
    just format
    just format-imports
    just lint-fix
    just typecheck
