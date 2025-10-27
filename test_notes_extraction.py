#!/usr/bin/env python3
"""
Test notes field extraction for specific files
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from generate_manifest import get_exif_data, format_ifd_rational_value, parse_exif_date, clean_exif_string, ensure_numeric_type, filter_tags
from PIL import Image
import json

def test_notes_extraction():
    """Test notes extraction for files with notes field"""
    
    test_files = [
        Path("sample-data/2025/05/17/GR002092.jpg"),
        Path("sample-data/2025/05/17/GR002083.avif"),
    ]
    
    for image_path in test_files:
        if not image_path.exists():
            print(f"File not found: {image_path}")
            continue
            
        print(f"\n{'='*60}")
        print(f"Testing: {image_path.name}")
        print(f"{'='*60}")
        
        # Extract metadata
        exif_data = get_exif_data(image_path)
        
        # Check for notes
        notes = exif_data.get("ProcessedNotes", None)
        title = exif_data.get("ProcessedTitle", None)
        description = exif_data.get("ProcessedDescription", None)
        
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Notes: {notes}")
        
        if notes:
            print(f"✓ Notes field extracted successfully")
        else:
            print(f"✗ No notes field found (this is okay if notes weren't set in Darktable)")

if __name__ == "__main__":
    test_notes_extraction()