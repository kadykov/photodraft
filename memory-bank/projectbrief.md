# Project Brief: Photodraft

**Version:** 0.1.2
**Date:** 2025-06-02
**Status:** Feature update: Creator/Copyright metadata, schema publishing, debug command. Bugfix: Title/Description extraction.

## 1. Project Overview

Photodraft is a Python script designed to complement a personal website (built with AstroJS). Its primary function is to scan a directory of photos, extract metadata (EXIF and XMP), and generate a JSON manifest file (`image_manifest.json`).

This manifest file is then used by the AstroJS website during its build process. The website downloads the manifest, uses it as a collection of images, creates optimized versions and thumbnails (served via CDN), and provides links to the original full-resolution photos, which are self-hosted on a home server.

## 2. Core Requirements & Features (as of v0.1.2)

*   **Scan Photo Directory:** The script must recursively scan a specified root directory (`PHOTO_ROOT_DIR`, default `/mnt/Web`) for image files (JPG, JPEG, PNG, WEBP).
*   **Metadata Extraction:** Extract relevant metadata from each image, including:
    *   File path information (relative path, filename, year/month/day from folder structure).
    *   Image dimensions (width, height).
    *   Date taken (from EXIF).
    *   **Title:** Prioritizes XMP `dc:title`, falls back to EXIF `ImageDescription`, then EXIF `ObjectName`.
    *   **Description:** Prioritizes XMP `dc:description`, falls back to EXIF `UserComment`, then EXIF `ImageDescription` (if not used for title).
    *   **Tags:** Prioritizes XMP `dc:subject`, falls back to EXIF `XPKeywords`.
    *   **Creator:** Prioritizes XMP `dc:creator`, falls back to EXIF `Artist`.
    *   **Copyright:** Prioritizes XMP `dc:rights`, falls back to EXIF `Copyright`.
    *   Camera and lens model (from EXIF).
    *   Flash status (from EXIF).
    *   Technical EXIF data (focal length, aperture, ISO, exposure time).
*   **JSON Manifest Generation:** Create a JSON file (`OUTPUT_JSON_FILE`, default `/mnt/Web/image_manifest.json`) containing an array of image objects. The structure of these objects must conform to `image_manifest.schema.json`.
*   **Schema Publishing:** The `image_manifest.schema.json` can be copied to the output directory using `just publish-schema`.
*   **Sorting:** The images in the manifest should be sorted by `dateTaken` in descending order (most recent first).
*   **Configuration:** Allow basic configuration of `PHOTO_ROOT_DIR` and `OUTPUT_JSON_FILE` via variables in the script.
*   **Debugging:** Provide a command-line option (`--debug-image <path>`) to inspect all available EXIF and XMP metadata for a specific image, accessible via `just debug-image path=<path_to_image>`.

## 3. Key Goals

*   Automate the process of creating an image manifest for a personal photography website.
*   Enable a workflow where photos exported from Darktable to a specific directory can be easily cataloged with rich metadata.
*   Provide a structured data source for an AstroJS website to build image galleries with optimized images and links to originals.
*   Ensure metadata extraction is reasonably robust, prioritizing XMP tags where available and handling various XMP structures (Bag, Seq, Alt).

## 4. Scope

*   **In Scope:**
    *   The Python script `generate_manifest.py` and its core functionalities.
    *   Definition and publishing of the JSON manifest schema (`image_manifest.schema.json`).
    *   Basic setup and usage instructions (`README.md`).
    *   Dependency management using `uv` and `pyproject.toml`.
    *   Task automation using `justfile`.
*   **Out of Scope (for this specific project, though related to the overall system):**
    *   The AstroJS website itself.
    *   The home server setup for serving full-resolution images.
    *   The CDN setup for optimized images.
    *   Advanced error handling beyond basic try-except blocks for file processing.
    *   GUI for the script.
    *   Automatic watching of the photo directory for changes.

## 5. Stakeholders

*   Primary User: The project owner (developer using this script for their personal website).

## 6. Assumptions

*   Photos are organized in a `YYYY/MM/DD/` directory structure under `PHOTO_ROOT_DIR`.
*   The primary image editing software (Darktable) can export photos with necessary EXIF and XMP metadata.
*   The user has a Python environment (>=3.13) and `uv` installed.
