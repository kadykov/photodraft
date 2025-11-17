# photodraft

Photo and image manifest generator for building a personal website with static assets hosted on a web server.

## Overview

This project provides two separate manifest generators for different types of image collections:

1. **Photo Manifest** (`generate_manifest.py`) - For curated photography exported from Darktable
   - Rich EXIF/XMP metadata extraction
   - Structured as `YYYY/MM/DD/filename` 
   - Outputs: `/mnt/Web/photo_manifest.json`

2. **Image Manifest** (`generate_image_manifest.py`) - For general images like screenshots, diagrams
   - Basic metadata (dimensions, file size, timestamps)
   - Flexible folder structure
   - Outputs: `/mnt/Web/image_manifest.json`

### Folder Structure on Web Server

```
/mnt/Web/
  ├── photos/              # Darktable photography
  │   └── YYYY/MM/DD/*.avif
  ├── images/              # General images  
  │   └── blog/post-name/*.webp
  ├── photo_manifest.json
  ├── image_manifest.json
  ├── photo_manifest.schema.json
  └── image_manifest.schema.json
```

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

### Photo Manifest (`generate_manifest.py`)

Open `generate_manifest.py` and modify these variables at the top if needed:

-   `WEB_ROOT`: Path to the web server root directory. Defaults to `"/mnt/Web"`.
-   `PHOTO_ROOT_DIR`: Path to the root directory of your photos. Defaults to `"/mnt/Web/photos"`.
-   `OUTPUT_JSON_FILE`: Path where the `photo_manifest.json` will be saved. Defaults to `"/mnt/Web/photo_manifest.json"`.
-   `EXCLUDED_TAGS`: Set of tags to exclude from metadata (e.g., technical tags like "darktable", "exported").

The script automatically calculates `COLLECTION_PATH` as the relative path from `WEB_ROOT` to `PHOTO_ROOT_DIR`, so changing the folder structure is flexible.

### Image Manifest (`generate_image_manifest.py`)

-   `WEB_ROOT`: Path to the web server root directory. Defaults to `"/mnt/Web"`.
-   `IMAGE_ROOT_DIR`: Path to general images. Defaults to `"/mnt/Web/images"`.
-   `OUTPUT_JSON_FILE`: Path where the `image_manifest.json` will be saved. Defaults to `"/mnt/Web/image_manifest.json"`.

The script automatically calculates `COLLECTION_PATH` as the relative path from `WEB_ROOT` to `IMAGE_ROOT_DIR`.

### Flexible Configuration Examples

The scripts automatically adapt to your folder structure by calculating the collection path relative to `WEB_ROOT`:

**Example 1: Nested collections**
```python
WEB_ROOT = Path("/mnt/Web")
PHOTO_ROOT_DIR = Path("/mnt/Web/photography/archive")
# → Paths in manifest: "photography/archive/2025/05/17/photo.avif"
```

**Example 2: Custom image location**
```python
WEB_ROOT = Path("/var/www/html")
IMAGE_ROOT_DIR = Path("/var/www/html/assets/img")
# → Paths in manifest: "assets/img/blog/post/screenshot.webp"
```

**Example 3: Flat structure**
```python
WEB_ROOT = Path("/mnt/Web")
PHOTO_ROOT_DIR = Path("/mnt/Web/pics")
# → Paths in manifest: "pics/2025/05/17/photo.avif"
```

The key is that `PHOTO_ROOT_DIR` and `IMAGE_ROOT_DIR` must be subdirectories of `WEB_ROOT`, and the manifest files should be placed at `WEB_ROOT` level.

## Usage

### Using Just (recommended)

The project includes a `justfile` with convenient commands:

```bash
# Generate both photo and image manifests
just generate

# Generate only photo manifest
just generate-photos

# Generate only image manifest
just generate-images

# Publish schemas to web server
just publish-schema

# Generate manifests and publish schemas
just publish
```

### Manual Usage

1.  **Ensure your images are organized** according to the folder structure above.

2.  **Activate your virtual environment** if you haven't already:
    ```bash
    source .venv/bin/activate
    ```

3.  **Run the scripts:**
    ```bash
    # For photos
    python generate_manifest.py
    
    # For general images
    python generate_image_manifest.py
    ```

### Debugging Metadata

To inspect all available EXIF and XMP metadata for a specific image (useful for identifying correct tags or troubleshooting), use the `--debug-image` argument:

```bash
python generate_manifest.py --debug-image path/to/your/image.jpg
```
For example:
```bash
python generate_manifest.py --debug-image sample-data/2025/05/17/DSC_5322.jpg
```

## Output Files

### Photo Manifest (`photo_manifest.json`)

A JSON array where each object represents a curated photograph. The structure is defined by `photo_manifest.schema.json`. Key fields include:

-   `relativePath`: Path relative to `/mnt/Web/` (includes `photos/` prefix, e.g., `photos/2025/05/17/photo.avif`)
-   `filename`: Image filename
-   `year`, `month`, `day`: Date from folder structure
-   `width`, `height`: Image dimensions
-   `dateTaken`: ISO 8601 timestamp from EXIF
-   `title`, `description`: From EXIF or XMP
-   `tags`: From XMP `dc:subject` or EXIF `XPKeywords` (filtered)
-   `cameraModel`, `lensModel`: From EXIF
-   `flash`: Boolean indicating if flash fired
-   `focalLength`, `focalLength35mmEquiv`, `focalLengthCategory`: Lens data
-   `cropFactor`: Calculated sensor crop factor
-   `apertureValue`, `isoSpeedRatings`, `exposureTime`: Camera settings
-   `creator`, `copyright`, `notes`: Author and metadata
-   `slug`: URL-friendly identifier (e.g., `photos-2025-05-17-DSC_1234`)

### Image Manifest (`image_manifest.json`)

A simpler JSON array for general images. The structure is defined by `image_manifest.schema.json`. Fields include:

-   `relativePath`: Path relative to `/mnt/Web/` (includes `images/` prefix, e.g., `images/blog/post/screenshot.webp`)
-   `filename`: Image filename
-   `width`, `height`: Image dimensions
-   `slug`: URL-friendly identifier (e.g., `images-blog-post-screenshot`)
-   `fileSize`: File size in bytes
-   `lastModified`: ISO 8601 timestamp

## Future Considerations / Improvements

-   Refactor to use Pydantic for data modeling and validation, which can also auto-generate the JSON schema.
-   Add more robust error handling for various image formats or corrupted metadata.
-   Allow configuration of EXIF/XMP fields to extract via a config file.