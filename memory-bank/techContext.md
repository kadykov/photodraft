# Tech Context: Photodraft

**Version:** 0.1.2 (Reflects creator/copyright, title/desc fixes, schema publishing, debug command)
**Date:** 2025-06-02

## 1. Core Technologies

*   **Programming Language:** Python (version >=3.13 as specified in `pyproject.toml`).
*   **Image Processing:** Pillow (Python Imaging Library fork) version >=11.2.1. Used for:
    *   Opening image files (JPG, JPEG, PNG, WEBP).
    *   Reading image dimensions (width, height).
    *   Accessing EXIF metadata (`_getexif()`).
    *   Accessing XMP metadata (`getxmp()`). Pillow's `getxmp()` returns a dictionary-like structure representing the XMP packet.
*   **XML Parsing (Indirectly for XMP):** `defusedxml` version >=0.7.1. Pillow uses this internally for safer XMP parsing if XMP data is XML-based. The script itself does not directly parse XML; it consumes the dictionary from Pillow.
*   **Standard Library Modules:**
    *   `json`: For serializing data to `image_manifest.json`.
    *   `os`: For `os.walk` to traverse directories.
    *   `datetime` (from `datetime`): For parsing and formatting date strings.
    *   `pathlib.Path`: For object-oriented filesystem path manipulation.
    *   `argparse`: For handling command-line arguments (e.g., `--debug-image`).

## 2. Development & Build Environment

*   **Dependency Management:** `uv`.
    *   `pyproject.toml`: Defines project metadata, dependencies, and Python version.
    *   `uv.lock`: Lock file for reproducible dependency installation.
    *   `uv sync --all-extras`: Command to install/update dependencies.
    *   `uv run -- <command>`: Command to run scripts within the managed environment.
*   **Task Runner:** `just` (`justfile`). Provides aliases for common development tasks:
    *   `install`: Installs dependencies.
    *   `generate`: Runs the `generate_manifest.py` script.
    *   `lint`: Runs Ruff linter.
    *   `format`: Runs Ruff formatter.
    *   `typecheck`: Runs MyPy for static type checking.
    *   `qa`: Runs all quality checks.
    *   `publish-schema`: Copies `image_manifest.schema.json` to the output directory.
    *   `publish`: Runs `generate` and then `publish-schema`.
    *   `debug-image <path>`: Runs `generate_manifest.py --debug-image <path>`.
*   **Linting & Formatting:** Ruff (versions >=0.11.11).
*   **Static Type Checking:** MyPy (version >=1.15.0).
*   **Virtual Environment:** Managed by `uv`.

## 3. Technical Constraints & Assumptions

*   **Operating System:** Python-based, largely OS-agnostic. Default paths suggest Linux-like environment.
*   **Photo Organization:** Assumes `PHOTO_ROOT_DIR/YYYY/MM/DD/` structure.
*   **Metadata Availability:** Relies on well-formed EXIF and/or XMP metadata in images.
    *   **XMP Fields Used:** `dc:title`, `dc:description`, `dc:subject`, `dc:creator`, `dc:rights`.
    *   **EXIF Fallbacks:** `ImageDescription`, `ObjectName`, `UserComment`, `XPKeywords`, `Artist`, `Copyright`, and various technical photo parameters.
*   **Darktable Workflow:** Assumed for embedding rich metadata.
*   **Pillow Capabilities:** Image format support and metadata extraction are bound by Pillow.

## 4. Key Files & Their Roles

*   **`generate_manifest.py`:** Core Python script. Contains XMP helper functions (`find_in_xmp`, `get_xmp_text_or_list_first`, `get_xmp_lang_alt`) for parsing different XMP data structures.
*   **`image_manifest.schema.json`:** Defines the output JSON structure, including new fields for `creator` and `copyright`.
*   **`README.md`:** Setup, configuration, usage.
*   **`pyproject.toml`:** Project dependencies for `uv`.
*   **`justfile`:** Task automation, including new `publish-schema`, `publish`, and `debug-image` commands.
*   **`.gitignore`:** Untracked files for Git.
*   **`uv.lock`:** Reproducible dependency versions.
*   **`LICENSE`:** Licensing terms.
*   **`sample-data/`:** Sample images.
*   **`local-docs/`:** For local documentation.

## 5. Integration Points

*   **Input:** Filesystem (`PHOTO_ROOT_DIR`).
*   **Output:** Filesystem (`OUTPUT_JSON_FILE`, and `image_manifest.schema.json` via `publish-schema`).
*   **External Consumer:** AstroJS website (consumes `image_manifest.json`).

## 6. Key Data Structures (within `generate_manifest.py`)

*   **`exif_data` (raw EXIF from Pillow):** Dictionary-like.
*   **`xmp_data_dict` (parsed XMP):** Dictionary storing extracted XMP values like `dc:title`, `dc:description`, `dc:subject`, `dc:creator`, `dc:rights`.
*   **`final_data` (merged and processed):** Dictionary holding `ProcessedTitle`, `ProcessedDescription`, `ProcessedTags`, `ProcessedCreator`, `ProcessedCopyright`, and other EXIF fields before being used in `main`.
*   **Output Manifest:** JSON array of image data objects.
