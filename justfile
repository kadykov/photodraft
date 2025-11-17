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

# Generate the photo manifest (Darktable exports with rich metadata)
generate-photos:
    uv run -- python generate_manifest.py

# Generate the image manifest (screenshots, diagrams with basic metadata)
generate-images:
    uv run -- python generate_image_manifest.py

# Generate both photo and image manifests
generate:
    just generate-photos
    just generate-images

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

# Copy the JSON schemas to the output directory
publish-schema:
    @echo "Copying schemas to /mnt/Web/..."
    cp photo_manifest.schema.json /mnt/Web/photo_manifest.schema.json
    cp image_manifest.schema.json /mnt/Web/image_manifest.schema.json

# Generate manifest and publish schema
publish:
    just generate
    just publish-schema

# Debug metadata for a specific image
# Usage: just debug-image path/to/your/image.jpg
debug-image path="":
    @echo "Debugging metadata for {{path}}..."
    uv run -- python generate_manifest.py --debug-image {{path}}
