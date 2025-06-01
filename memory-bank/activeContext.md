# Active Context: Photodraft

**Version:** 0.1.2 (Feature Update & Bugfix)
**Date:** 2025-06-02
**Status:** Corrected title/description extraction, added creator/copyright fields, and added debug command. Preparing to update Memory Bank.

## 1. Current Work Focus

*   **Task:** Finalize feature implementation (creator/copyright, schema publishing, debug command) and correct title/description extraction. Then, update the Memory Bank.
*   **Objective:**
    1.  Ensure `justfile` correctly includes commands for schema publishing and debugging.
    2.  Ensure `image_manifest.schema.json` is updated with `creator` and `copyright`.
    3.  Ensure `generate_manifest.py` correctly extracts `title`, `description`, `creator`, and `copyright` with proper XMP/EXIF prioritization.
    4.  Update all Memory Bank files to reflect these changes.

## 2. Recent Changes & Activities

*   **`justfile` updated:**
    *   Added `publish-schema` command.
    *   Added `publish` command (runs `generate` then `publish-schema`).
    *   Added `debug-image <path>` command.
*   **`image_manifest.schema.json` updated:**
    *   Added `creator` property (string, null).
    *   Added `copyright` property (string, null).
*   **`generate_manifest.py` significantly updated (via `write_to_file`):**
    *   Corrected extraction logic for `title` and `description`:
        *   `title`: Prioritizes XMP `dc:title`, falls back to EXIF `ImageDescription`, then EXIF `ObjectName`.
        *   `description`: Prioritizes XMP `dc:description`, falls back to EXIF `UserComment`, then EXIF `ImageDescription` (if not used for title).
    *   Implemented extraction for `creator` and `copyright`:
        *   `creator`: Prioritizes XMP `dc:creator`, falls back to EXIF `Artist`.
        *   `copyright`: Prioritizes XMP `dc:rights`, falls back to EXIF `Copyright`.
    *   Refined XMP helper functions (`find_in_xmp`, `get_xmp_text_or_list_first`, `get_xmp_lang_alt`) within `get_exif_data` for robustness.
    *   Updated `main` to use `ProcessedTitle`, `ProcessedDescription`, `ProcessedCreator`, `ProcessedCopyright` from `get_exif_data`'s return.
    *   Simplified `interpret_flash_value` for manifest output.
    *   Increased raw XMP output in `print_all_metadata_for_image` for debugging.
*   **Memory Bank Initialization Completed (previous task).**

## 3. Next Steps

1.  Update all Memory Bank files:
    *   `memory-bank/activeContext.md` (this file - currently being updated)
    *   `memory-bank/progress.md`
    *   `memory-bank/systemPatterns.md`
    *   `memory-bank/techContext.md`
    *   `memory-bank/.clinerules.md`
    *   `memory-bank/projectbrief.md` (update version)
2.  Inform user of completion and await further instructions.

## 4. Active Decisions & Considerations

*   **XMP Helper Functions Location:** Kept helper functions inside `get_exif_data` for now. Can be refactored to module level later if desired.
*   **`write_to_file` Fallback:** Used `write_to_file` for `generate_manifest.py` due to difficulties with `replace_in_file` for complex, multi-step changes.
*   **Version Bump:** Incrementing project version to 0.1.2 to reflect the new features and bugfix.
