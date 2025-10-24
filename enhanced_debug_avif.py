#!/usr/bin/env python3
"""
Enhanced AVIF metadata extraction using multiple methods
"""

import sys
from pathlib import Path
import pillow_avif
from PIL import Image
from PIL.ExifTags import TAGS
import json
import io
import exifread

def explore_avif_metadata_enhanced(image_path):
    """Enhanced exploration of AVIF metadata using multiple extraction methods"""
    print(f"=== Enhanced AVIF Metadata Analysis: {image_path} ===\n")
    
    try:
        img = Image.open(image_path)
        print(f"Image format: {img.format}")
        print(f"Image size: {img.size}")
        print(f"Image mode: {img.mode}")
        print()
        
        # Method 1: Standard getexif() 
        print("--- Method 1: PIL getexif() ---")
        try:
            exif_dict = img.getexif()
            if exif_dict:
                print(f"Found {len(exif_dict)} EXIF entries:")
                for tag_id, value in exif_dict.items():
                    tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")
                    print(f"  {tag_name} ({tag_id}): {value}")
            else:
                print("No EXIF data found with getexif()")
        except Exception as e:
            print(f"Error with getexif(): {e}")
        print()
        
        # Method 2: Raw EXIF bytes with exifread
        print("--- Method 2: Raw EXIF bytes with exifread ---")
        try:
            if 'exif' in img.info:
                exif_bytes = img.info['exif']
                print(f"Raw EXIF data length: {len(exif_bytes)} bytes")
                
                # Parse with exifread
                exif_stream = io.BytesIO(exif_bytes)
                tags = exifread.process_file(exif_stream, details=True)
                
                if tags:
                    print(f"Found {len(tags)} EXIF tags with exifread:")
                    
                    # Group tags by category for better readability
                    image_tags = {}
                    exif_tags = {}
                    gps_tags = {}
                    iop_tags = {}
                    other_tags = {}
                    
                    for tag_name, tag_value in tags.items():
                        if tag_name.startswith('Image '):
                            image_tags[tag_name] = str(tag_value)
                        elif tag_name.startswith('EXIF '):
                            exif_tags[tag_name] = str(tag_value)
                        elif tag_name.startswith('GPS '):
                            gps_tags[tag_name] = str(tag_value)
                        elif tag_name.startswith('Interoperability '):
                            iop_tags[tag_name] = str(tag_value)
                        else:
                            other_tags[tag_name] = str(tag_value)
                    
                    if image_tags:
                        print("\n  Image Tags:")
                        for tag, value in image_tags.items():
                            print(f"    {tag}: {value}")
                    
                    if exif_tags:
                        print("\n  EXIF Tags:")
                        for tag, value in exif_tags.items():
                            print(f"    {tag}: {value}")
                    
                    if gps_tags:
                        print("\n  GPS Tags:")
                        for tag, value in gps_tags.items():
                            print(f"    {tag}: {value}")
                    
                    if iop_tags:
                        print("\n  Interoperability Tags:")
                        for tag, value in iop_tags.items():
                            print(f"    {tag}: {value}")
                    
                    if other_tags:
                        print("\n  Other Tags:")
                        for tag, value in other_tags.items():
                            print(f"    {tag}: {value}")
                            
                else:
                    print("No tags found with exifread")
            else:
                print("No raw EXIF data found in image info")
        except Exception as e:
            print(f"Error parsing raw EXIF data: {e}")
        print()
        
        # Method 3: XMP data analysis
        print("--- Method 3: XMP Data Analysis ---")
        try:
            xmp_data = img.getxmp()
            if xmp_data:
                print("XMP data structure analysis:")
                
                # Navigate to Description
                desc = xmp_data.get('xmpmeta', {}).get('RDF', {}).get('Description', {})
                if desc:
                    # Look for camera-specific XMP data
                    camera_fields = ['exif:FNumber', 'exif:ExposureTime', 'exif:ISOSpeedRatings', 
                                   'exif:FocalLength', 'exif:Flash', 'exif:WhiteBalance',
                                   'exif:ExposureMode', 'exif:MeteringMode', 'exif:SceneCaptureType']
                    
                    print("  Camera settings in XMP:")
                    for field in camera_fields:
                        if field in desc:
                            print(f"    {field}: {desc[field]}")
                    
                    # Check for any field that starts with 'exif:'
                    exif_xmp_fields = {k: v for k, v in desc.items() if k.startswith('exif:')}
                    if exif_xmp_fields:
                        print("  All EXIF fields in XMP:")
                        for key, value in exif_xmp_fields.items():
                            print(f"    {key}: {value}")
                    else:
                        print("  No EXIF fields found in XMP")
                else:
                    print("  No Description section found in XMP")
            else:
                print("No XMP data found")
        except Exception as e:
            print(f"Error analyzing XMP data: {e}")
        print()
        
        # Method 4: Check for IFD (Image File Directory) data
        print("--- Method 4: IFD Data ---")
        try:
            exif_ifd = img.getexif().get_ifd(0x8769)  # EXIF IFD
            if exif_ifd:
                print(f"Found EXIF IFD with {len(exif_ifd)} entries:")
                for tag_id, value in exif_ifd.items():
                    tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")
                    print(f"  {tag_name} ({tag_id}): {value}")
            else:
                print("No EXIF IFD found")
        except Exception as e:
            print(f"Error accessing EXIF IFD: {e}")
        print()
        
        img.close()
        
    except Exception as e:
        print(f"Error opening image: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python enhanced_debug_avif.py <path_to_avif_file>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"File not found: {image_path}")
        sys.exit(1)
    
    explore_avif_metadata_enhanced(image_path)