#!/usr/bin/env python3
"""
Quick schema validation test for the generated manifest
"""

import json
import jsonschema
from pathlib import Path

def validate_manifest():
    """Validate the test manifest against the schema"""
    
    # Load schema
    schema_path = Path("image_manifest.schema.json")
    if not schema_path.exists():
        print("Schema file not found")
        return
    
    with open(schema_path) as f:
        schema = json.load(f)
    
    # Load test manifest
    manifest_path = Path("test_image_manifest.json")
    if not manifest_path.exists():
        print("Test manifest file not found")
        return
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    try:
        jsonschema.validate(manifest, schema)
        print(f"✅ Validation successful!")
        print(f"📊 Validated {len(manifest)} images")
        
        # Show specific data types for key fields
        if manifest:
            sample = manifest[-1]  # Get the AVIF file (last in list)
            print(f"\n🔍 Sample data types (from {sample['filename']}):")
            print(f"  apertureValue: {type(sample.get('apertureValue')).__name__} = {sample.get('apertureValue')}")
            print(f"  isoSpeedRatings: {type(sample.get('isoSpeedRatings')).__name__} = {sample.get('isoSpeedRatings')}")
            print(f"  focalLength: {type(sample.get('focalLength')).__name__} = {sample.get('focalLength')}")
            print(f"  exposureTime: {type(sample.get('exposureTime')).__name__} = {sample.get('exposureTime')}")
            
    except jsonschema.ValidationError as e:
        print(f"❌ Validation failed:")
        print(f"  Path: {' -> '.join(map(str, e.path))}")
        print(f"  Error: {e.message}")
        print(f"  Value: {e.instance}")
    except Exception as e:
        print(f"❌ Error during validation: {e}")

if __name__ == "__main__":
    validate_manifest()