# Product Context: Photodraft

**Version:** 0.1.0 (Initial)
**Date:** 2025-06-02

## 1. Purpose & Problem Solved

**Why does this project exist?**
Photodraft exists to bridge the gap between a local photo management workflow (exporting from Darktable to a home server) and a modern web publishing workflow (AstroJS static site with optimized images). Manually creating and maintaining a data source for a large collection of photos for a website is tedious and error-prone.

**What problems does it solve?**
*   **Automates Manifest Creation:** It automates the generation of a structured JSON manifest of photos, including essential metadata. This saves significant manual effort.
*   **Decouples Photo Management from Web Development:** Photographers can manage their photos in their preferred directory structure and with their chosen tools (like Darktable), and Photodraft handles the preparation of data for the website.
*   **Enables Efficient Web Publishing:** Provides the AstroJS website with a clean, predictable data source (`image_manifest.json`) to:
    *   Dynamically build image galleries.
    *   Generate optimized image renditions (thumbnails, responsive sizes) for fast loading via CDN.
    *   Link to original, full-resolution images hosted separately (e.g., on a home server).
*   **Centralizes Metadata:** Consolidates key EXIF and XMP metadata into a single, easily consumable format for the website.

## 2. How It Should Work (User Experience & Workflow)

**User Workflow:**
1.  **Photo Export:** The user exports photos from their editing software (e.g., Darktable) into a designated directory structure on their home server (e.g., `/mnt/Web/YYYY/MM/DD/image.jpg`). This directory is the `PHOTO_ROOT_DIR`.
2.  **Run Script:** The user runs the `python generate_manifest.py` script.
    *   The script scans the `PHOTO_ROOT_DIR`.
    *   It extracts metadata from each valid image file.
    *   It generates/overwrites the `image_manifest.json` file in the `OUTPUT_JSON_FILE` location (typically within `PHOTO_ROOT_DIR`).
3.  **Website Build:** The AstroJS website (during its build process, either locally or on a platform like Netlify) is configured to:
    *   Fetch this `image_manifest.json` file (e.g., from a publicly accessible URL on the home server or by including it in the site's repository if updated regularly).
    *   Use the manifest data to build photo galleries, create optimized images, and link to originals.

**Key Characteristics:**
*   **CLI-Based:** Interaction is through the command line.
*   **Batch Processing:** Designed to process a directory of images at once.
*   **Idempotent:** Running the script multiple times with the same photo set should produce the same manifest (unless photos or their metadata have changed).
*   **Configuration:** Simple configuration via variables within the script for key paths.

## 3. User Experience Goals

*   **Simplicity:** The script should be easy to run with minimal setup.
*   **Reliability:** It should consistently and accurately extract common metadata fields.
*   **Speed:** While not a primary constraint for potentially thousands of images, it should be reasonably performant.
*   **Transparency:** The `--debug-image` option allows users to inspect metadata for troubleshooting.
*   **Flexibility (Basic):** Handles common image formats (JPG, PNG, WEBP).

## 4. Target User

*   A technically inclined photographer or individual who manages their own personal website (likely a static site).
*   Comfortable with command-line tools and basic Python script usage.
*   Wants to automate the process of getting their photo library metadata into their website.
*   Likely uses software like Darktable that embeds rich EXIF/XMP metadata.
