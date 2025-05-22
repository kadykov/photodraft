import os
import json
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.TiffImagePlugin import IFDRational
import argparse # For command-line arguments for debugging

# --- Configuration ---
# The root directory where your YYYY/MM/DD structured photos are.
PHOTO_ROOT_DIR = Path("/mnt/Web") # Changed to /mnt/Web
# The name of the output JSON file.
OUTPUT_JSON_FILE = Path("/mnt/Web/image_manifest.json") # Changed output path
# --- End Configuration ---

def clean_exif_string(value):
    """Cleans null characters from a string and strips whitespace."""
    if isinstance(value, str):
        return value.replace('\x00', '').strip() # Correctly replace actual null character
    return value

def format_ifd_rational_value(value):
    """Converts IFDRational objects to float for JSON serialization."""
    if isinstance(value, IFDRational):
        return float(value)  # IFDRational can be directly converted to float
    elif isinstance(value, tuple):
        # If it's a tuple, process each element.
        return tuple(format_ifd_rational_value(item) for item in value)
    return value # Return other types as is


def get_exif_data(image_path):
    """Extracts EXIF and attempts to extract XMP data from an image."""
    exif_data = {}
    xmp_data_dict = {} # For parsed XMP

    try:
        img = Image.open(image_path)
        
        # Standard EXIF
        exif_data_raw = img._getexif() # pylint: disable=protected-access
        if exif_data_raw:
            for tag_id, value in exif_data_raw.items():
                tag_name = TAGS.get(tag_id, tag_id)
                
                if isinstance(value, bytes):
                    try:
                        # Special handling for XPKeywords (often UCS-2 encoded byte string)
                        if tag_name == 'XPKeywords': # Still attempt, but prioritize XMP dc:subject
                            decoded_value = value.decode('utf-16-le', errors='ignore')
                            cleaned_value = decoded_value.rstrip('\\x00')
                            exif_data[tag_name] = [tag.strip() for tag in cleaned_value.split(';') if tag.strip()]
                            continue
                        else:
                            value = value.decode('utf-8', errors='ignore')
                    except UnicodeDecodeError:
                        pass # Keep as bytes or try other decodings if necessary
                
                exif_data[tag_name] = clean_exif_string(value) if isinstance(value, str) else value

        # Attempt to get XMP data
        try:
            xmp_info = img.getxmp() # Returns a dictionary-like object
            if xmp_info:
                # Structure can be complex, e.g., xmp_info['xmpmeta']['RDF']['Description']
                # We need to navigate this. Common path for dc:subject:
                # rdf:RDF -> rdf:Description -> dc:subject -> rdf:Bag -> rdf:li (list of tags)
                
                # Helper to navigate the XMP structure
                def find_in_xmp(data, path_keys):
                    current = data
                    for key_part in path_keys:
                        if isinstance(current, list): # If path leads to a list, take the first item
                            if current:
                                current = current[0]
                            else:
                                return None
                        if not isinstance(current, dict) or key_part not in current:
                            return None
                        current = current[key_part]
                    return current

                # Path to dc:subject (adjust if Darktable's XMP structure differs)
                # Common XMP structure for dc:subject
                # It's often a list under ['xmpmeta']['RDF']['Description'][0]['subject']['Bag']['li']
                # Or sometimes directly under Description if only one Description block
                
                rdf_description = find_in_xmp(xmp_info, ['xmpmeta', 'RDF', 'Description'])
                if rdf_description:
                    # rdf_description might be a list of descriptions or a single one
                    descriptions = rdf_description if isinstance(rdf_description, list) else [rdf_description]
                    for desc_item in descriptions:
                        if isinstance(desc_item, dict):
                            subject_node = desc_item.get('subject') # dc:subject
                            if subject_node and isinstance(subject_node, dict) and 'Bag' in subject_node and \
                               isinstance(subject_node['Bag'], dict) and 'li' in subject_node['Bag']:
                                xmp_tags = subject_node['Bag']['li']
                                if isinstance(xmp_tags, list):
                                     xmp_data_dict['dc:subject'] = [str(tag).strip() for tag in xmp_tags if tag]
                                     break # Found tags
                                elif isinstance(xmp_tags, (str, dict)): # Single tag
                                     xmp_data_dict['dc:subject'] = [str(xmp_tags).strip()]
                                     break # Found tags
                            # Simpler structure sometimes:
                            elif 'subject' in desc_item and isinstance(desc_item['subject'], list):
                                xmp_data_dict['dc:subject'] = [str(tag).strip() for tag in desc_item['subject'] if tag]
                                break
                            elif 'subject' in desc_item and isinstance(desc_item['subject'], str):
                                 xmp_data_dict['dc:subject'] = [desc_item['subject'].strip()]
                                 break


        except AttributeError:
            # print(f"Info: img.getxmp() not available or XMP data not found for {image_path}")
            pass
        except Exception: # pylint: disable=broad-except
            # print(f"Warning: Could not parse XMP data for {image_path}: {e_xmp}")
            pass
        
        img.close() # Ensure image is closed after all data extraction attempts
        
        # Combine EXIF and parsed XMP (XMP takes precedence for tags if found)
        final_data = exif_data
        if 'dc:subject' in xmp_data_dict:
            final_data['ProcessedTags'] = xmp_data_dict['dc:subject']
        elif 'XPKeywords' in exif_data: # Fallback to XPKeywords if dc:subject not found
            final_data['ProcessedTags'] = exif_data['XPKeywords']


        return final_data
    except Exception: # pylint: disable=broad-except
        # print(f"Warning: Could not read metadata for {image_path}: {e}")
        return {}

def interpret_flash_value(flash_val):
    """Interprets the EXIF Flash tag value."""
    if flash_val is None:
        return None
    
    flash_fired = bool(flash_val & 0x1) # Bit 0: Flash fired
    
    # Bits 1-2: Flash return status
    return_status = (flash_val >> 1) & 0x3
    if return_status == 0b10: # No strobe return detection
        return_info = "No strobe return detection"
    elif return_status == 0b11: # Strobe return light detected
        return_info = "Strobe return light detected"
    else: # Strobe return not applicable or unknown
        return_info = "Strobe return status unknown"

    # Bits 3-4: Flash mode
    mode_status = (flash_val >> 3) & 0x3
    if mode_status == 0b01: # Compulsory firing
        mode_info = "Compulsory firing"
    elif mode_status == 0b10: # Compulsory suppression
        mode_info = "Compulsory suppression (off)"
    elif mode_status == 0b11: # Auto mode
        mode_info = "Auto mode"
    else:
        mode_info = "Flash mode unknown"

    # Bit 5: Flash function present (0 = no flash function, 1 = flash function present)
    # We don't typically show this directly

    # Bit 6: Red-eye reduction
    red_eye = bool((flash_val >> 6) & 0x1)
    red_eye_info = "Red-eye reduction" if red_eye else "No red-eye reduction"
    
    if not flash_fired:
        return "Flash did not fire"

    return f"Flash fired ({mode_info}, {return_info}, {red_eye_info})"


def print_all_metadata_for_image(image_path_str):
    """Prints all EXIF and attempts to print XMP for a single image."""
    image_path = Path(image_path_str)
    if not image_path.exists():
        print(f"Error: Image not found at {image_path_str}")
        return

    print(f"--- Metadata for {image_path.name} ---")
    try:
        img = Image.open(image_path)

        # EXIF Data
        print("\n-- EXIF Data --")
        exif_data_raw = img._getexif() # pylint: disable=protected-access
        if exif_data_raw:
            for tag_id, value in exif_data_raw.items():
                tag_name = TAGS.get(tag_id, tag_id)
                print(f"  {tag_name} (ID: {tag_id}): {value}")
        else:
            print("  No EXIF data found.")

        # XMP Data (Raw and Attempted Parsed)
        print("\n-- XMP Data --")
        try:
            xmp_info = img.getxmp()
            if xmp_info:
                print("  Raw XMP Packet (first 500 chars):")
                # The xmp_info is already a dict-like structure from getxmp()
                print(f"    {str(xmp_info)[:500]}...")
                print("\n  Attempted Parsed XMP (dc:subject if found):")
                
                # Re-using the XMP navigation logic from get_exif_data for consistency
                def find_in_xmp_debug(data, path_keys):
                    current = data
                    for key_part in path_keys:
                        if isinstance(current, list):
                            if current: current = current[0]
                            else: return None
                        if not isinstance(current, dict) or key_part not in current: return None
                        current = current[key_part]
                    return current

                rdf_description = find_in_xmp_debug(xmp_info, ['xmpmeta', 'RDF', 'Description'])
                if rdf_description:
                    descriptions = rdf_description if isinstance(rdf_description, list) else [rdf_description]
                    for desc_item in descriptions:
                        if isinstance(desc_item, dict):
                            subject_node = desc_item.get('subject')
                            if subject_node and isinstance(subject_node, dict) and 'Bag' in subject_node and \
                               isinstance(subject_node['Bag'], dict) and 'li' in subject_node['Bag']:
                                print(f"    dc:subject (from Bag/li): {subject_node['Bag']['li']}")
                                break
                            elif 'subject' in desc_item: # Simpler structure
                                print(f"    dc:subject (direct): {desc_item['subject']}")
                                break
                    else:
                        print("    dc:subject not found in expected XMP structure.")
                else:
                    print("    RDF Description not found in XMP.")
            else:
                print("  No XMP data returned by img.getxmp().")
        except AttributeError:
            print("  img.getxmp() not available or XMP data not found.")
        except Exception as e_xmp_debug: # pylint: disable=broad-except
            print(f"  Error parsing XMP data: {e_xmp_debug}")
        
        img.close()
    except Exception as e_main_debug: # pylint: disable=broad-except
        print(f"Error opening or processing image {image_path_str}: {e_main_debug}")
    print("--- End Metadata ---")


def parse_exif_date(date_str):
    """Parses EXIF date string (YYYY:MM:DD HH:MM:SS) to ISO 8601 format."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        # Common EXIF date format
        dt_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        return dt_obj.isoformat()
    except ValueError:
        # Try other common formats or return None
        return None

def main(args): # Modified to accept args
    if args.debug_image:
        print_all_metadata_for_image(args.debug_image)
        return # Exit after printing debug info

    all_images_data = []
    processed_count = 0
    skipped_count = 0

    print(f"Scanning for images in: {PHOTO_ROOT_DIR.resolve()}")

    for root, _, files in os.walk(PHOTO_ROOT_DIR):
        for filename in files:
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue  # Skip non-image files

            image_path = Path(root) / filename
            try:
                relative_path = image_path.relative_to(PHOTO_ROOT_DIR)
                path_parts = relative_path.parts

                year, month, day = None, None, None
                if len(path_parts) >= 4: # Expects YYYY/MM/DD/filename.jpg
                    try:
                        year = int(path_parts[0])
                        month = int(path_parts[1])
                        day = int(path_parts[2])
                    except ValueError:
                        print(f"Warning: Could not parse date from path for {relative_path}. Skipping date parts.")

                # Open image once for dimensions and EXIF/XMP
                # Note: get_exif_data now handles closing the image.
                # However, to get dimensions here, we open/close it separately if get_exif_data doesn't return them.
                # For simplicity, let's assume get_exif_data is the primary source of image interaction.
                # To get width/height, we might need to open it here if get_exif_data doesn't pass it back.
                temp_img_for_dims = Image.open(image_path)
                width, height = temp_img_for_dims.size
                temp_img_for_dims.close()

                exif_data = get_exif_data(image_path) # This now returns combined EXIF and XMP

                date_taken_str = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
                date_taken_iso = parse_exif_date(date_taken_str)

                title = clean_exif_string(exif_data.get('ImageDescription', ''))
                if not title and 'ObjectName' in exif_data:
                     title = clean_exif_string(exif_data.get('ObjectName', ''))

                description = clean_exif_string(exif_data.get('UserComment', ''))
                
                tags = exif_data.get('ProcessedTags', []) # Use the new combined field
                if not isinstance(tags, list): tags = []

                lens_model_raw = exif_data.get('LensModel', '')
                lens_model_processed = clean_exif_string(lens_model_raw)
                if not lens_model_processed:
                    lens_model_processed = None
                
                # Ensure camera_model_processed is defined before use in image_data
                camera_model_raw = exif_data.get('Model', '')
                camera_model_processed = clean_exif_string(camera_model_raw)
                if not camera_model_processed:
                    camera_model_processed = None
                
                flash_info_raw = exif_data.get('Flash')
                # For the JSON, we'll use a simple boolean for whether flash fired.
                flash_fired_boolean = None
                if flash_info_raw is not None:
                    flash_fired_boolean = bool(flash_info_raw & 0x1) # Bit 0 indicates if flash fired

                # The detailed interpretation is still available via interpret_flash_value for debugging
                # flash_info_interpreted_string = interpret_flash_value(flash_info_raw)

                image_data = {
                    "relativePath": str(relative_path.as_posix()),
                    "filename": filename,
                    "year": year,
                    "month": month,
                    "day": day,
                    "width": width,
                    "height": height,
                    "dateTaken": date_taken_iso,
                    "title": title if title else None,
                    "description": description if description else None,
                    "tags": tags if tags else None,
                    "cameraModel": camera_model_processed,
                    "lensModel": lens_model_processed,
                    "flash": flash_fired_boolean, # Changed to boolean
                    "focalLength": format_ifd_rational_value(exif_data.get('FocalLength')),
                    "apertureValue": format_ifd_rational_value(exif_data.get('FNumber')),
                    "isoSpeedRatings": exif_data.get('ISOSpeedRatings'),
                    "exposureTime": format_ifd_rational_value(exif_data.get('ExposureTime')),
                }
                all_images_data.append(image_data)
                processed_count += 1
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                skipped_count += 1

    # Sort images by dateTaken (most recent first), handling None dates
    all_images_data.sort(
        key=lambda x: x.get('dateTaken') or "0000-00-00T00:00:00",
        reverse=True
    )

    with open(OUTPUT_JSON_FILE, 'w') as f:
        json.dump(all_images_data, f, indent=2)

    print(f"\nSuccessfully processed {processed_count} images.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} files due to errors.")
    print(f"Manifest file created: {OUTPUT_JSON_FILE.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a JSON manifest from image metadata.")
    parser.add_argument(
        "--debug-image", 
        type=str, 
        help="Path to a single image file to print all its metadata for debugging."
    )
    cli_args = parser.parse_args()
    main(cli_args)
