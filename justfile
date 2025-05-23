\
# Default task: list available commands
default: list

# List available commands
list:
    @just --list

# Install dependencies
install:
    uv sync

# Show how to activate the virtual environment
activate:
    @echo "To activate the virtual environment, run: source .venv/bin/activate"

# Generate the image manifest
generate:
    uv run -- python generate_manifest.py
