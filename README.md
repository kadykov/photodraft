# photodraft

## Setup

This project uses `uv` for managing the Python environment and dependencies.

1.  **Create and activate a virtual environment:**
    ```bash
    uv venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    The primary dependency is Pillow for image processing and EXIF/XMP reading.
    If Pillow is listed as a dependency in your `pyproject.toml`, `uv` might pick it up automatically or you might use a command like `uv pip install .` (depending on your `pyproject.toml` setup).
    Otherwise, you can install it directly:
    ```bash
    uv pip install Pillow
    ```

## Configuration

Open `generate_manifest.py` and modify these variables at the top if needed:

-   `PHOTO_ROOT_DIR`: Path to the root directory of your photos. Defaults to `\"/mnt/Web\"`.
-   `OUTPUT_JSON_FILE`: Path where the `image_manifest.json` will be saved. Defaults to `\"/mnt/Web/image_manifest.json\"`.

## Usage

1.  **Ensure your photos are organized** in a structure like `PHOTO_ROOT_DIR/YYYY/MM/DD/your_image.jpg`.
2.  **Activate your virtual environment** if you haven\'t already:
    ```bash
    source .venv/bin/activate
    ```
3.  **Run the script:**
    ```bash
    python generate_manifest.py
    ```
    This will generate/overwrite the `image_manifest.json` file at the configured `OUTPUT_JSON_FILE` path.

### Debugging Metadata

To inspect all available EXIF and XMP metadata for a specific image (useful for identifying correct tags or troubleshooting), use the `--debug-image` argument:

```bash
python generate_manifest.py --debug-image path/to/your/image.jpg
```
For example:
```bash
python generate_manifest.py --debug-image sample-data/2025/05/17/DSC_5322.jpg
```

## Output File: `image_manifest.json`

The script generates a JSON array where each object represents an image. The structure of these objects is defined by `image_manifest.schema.json`. Key fields include:

-   `relativePath`: Path to the image relative to `PHOTO_ROOT_DIR`.
-   `filename`: Image filename.
-   `year`, `month`, `day`: Date components from the folder structure.
-   `width`, `height`: Image dimensions.
-   `dateTaken`: ISO 8601 timestamp from EXIF.
-   `title`, `description`: From EXIF.
-   `tags`: List of strings from XMP `dc:subject` or EXIF `XPKeywords`.
-   `cameraModel`, `lensModel`: From EXIF.
-   `flash`: Boolean indicating if flash fired.
-   And other technical EXIF data like `focalLength`, `apertureValue`, etc.

Refer to `image_manifest.schema.json` for the complete schema definition.

## Future Considerations / Improvements

-   Refactor to use Pydantic for data modeling and validation, which can also auto-generate the JSON schema.
-   Add more robust error handling for various image formats or corrupted metadata.
-   Allow configuration of EXIF/XMP fields to extract via a config file.