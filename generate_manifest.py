import argparse  # For command-line arguments for debugging
import json
import os
from datetime import datetime
from pathlib import Path
import io

import pillow_avif  # Register AVIF support in PIL
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.TiffImagePlugin import IFDRational
import exifread

# --- Configuration ---
# The root directory where your YYYY/MM/DD structured photos are.
PHOTO_ROOT_DIR = Path("/mnt/Web")  # Changed to /mnt/Web
# The name of the output JSON file.
OUTPUT_JSON_FILE = Path("/mnt/Web/image_manifest.json")  # Changed output path
# Tags to exclude from the manifest (case-insensitive)
# These are typically technical tags added by photo editing software that aren't useful for users
EXCLUDED_TAGS = {
    "darktable",  # Darktable editor tag
    "exported",   # Export status tag
    "format",     # Format-related tags
    "dng",        # RAW format tags
    "raw",        # RAW format indicator
    "nef",        # Nikon RAW format tag
    "g500",       # Canon printer tag
}
# --- End Configuration ---

def clean_exif_string(value):
    """Cleans null characters from a string and strips whitespace."""
    if isinstance(value, str):
        return value.replace(
            "\x00", ""
        ).strip()  # Correctly replace actual null character
    return value

def format_ifd_rational_value(value):
    """Converts IFDRational objects to float for JSON serialization."""
    if isinstance(value, IFDRational):
        return float(value)  # IFDRational can be directly converted to float
    elif isinstance(value, tuple):
        # If it's a tuple, process each element.
        return tuple(format_ifd_rational_value(item) for item in value)
    return value  # Return other types as is

def get_exif_data(image_path):
    """Extracts EXIF and attempts to extract XMP data from an image."""
    exif_data = {}
    xmp_data_dict = {}  # For parsed XMP

    try:
        img = Image.open(image_path)

        # Handle EXIF extraction based on image format
        if img.format == 'AVIF':
            # For AVIF files, use multiple methods to get comprehensive EXIF data
            
            # Method 1: Standard getexif() for basic data
            try:
                basic_exif = img.getexif()
                if basic_exif:
                    for tag_id, value in basic_exif.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        exif_data[tag_name] = value
            except Exception:
                pass
            
            # Method 2: Get detailed EXIF data from IFD
            try:
                exif_ifd = img.getexif().get_ifd(0x8769)  # EXIF IFD
                if exif_ifd:
                    for tag_id, value in exif_ifd.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        exif_data[tag_name] = value
            except Exception:
                pass
            
            # Method 3: Parse raw EXIF bytes with exifread for maximum compatibility
            try:
                if 'exif' in img.info:
                    exif_bytes = img.info['exif']
                    exif_stream = io.BytesIO(exif_bytes)
                    tags = exifread.process_file(exif_stream, details=False)
                    
                    for tag_name, tag_value in tags.items():
                        # Convert exifread tag names to standard EXIF tag names
                        if tag_name.startswith('EXIF '):
                            clean_tag = tag_name.replace('EXIF ', '')
                        elif tag_name.startswith('Image '):
                            clean_tag = tag_name.replace('Image ', '')
                        else:
                            clean_tag = tag_name
                        
                        # Convert common tag names to PIL standard names
                        tag_mapping = {
                            'ExposureTime': 'ExposureTime',
                            'FNumber': 'FNumber', 
                            'ISOSpeedRatings': 'ISOSpeedRatings',
                            'FocalLength': 'FocalLength',
                            'Flash': 'Flash',
                            'DateTimeOriginal': 'DateTimeOriginal',
                            'DateTime': 'DateTime',
                            'Make': 'Make',
                            'Model': 'Model',
                            'Artist': 'Artist',
                            'Copyright': 'Copyright',
                            'LensModel': 'LensModel'
                        }
                        
                        mapped_tag = tag_mapping.get(clean_tag, clean_tag)
                        
                        # Convert exifread values to appropriate types
                        str_value = str(tag_value)
                        if '/' in str_value and clean_tag in ['ExposureTime', 'FNumber', 'FocalLength']:
                            # Handle fractional values
                            try:
                                parts = str_value.split('/')
                                if len(parts) == 2:
                                    exif_data[mapped_tag] = float(parts[0]) / float(parts[1])
                                else:
                                    exif_data[mapped_tag] = str_value
                            except ValueError:
                                exif_data[mapped_tag] = str_value
                        elif clean_tag in ['ISOSpeedRatings'] and str_value.isdigit():
                            # Convert ISO to integer
                            exif_data[mapped_tag] = int(str_value)
                        elif clean_tag in ['FNumber'] and str_value.replace('.', '').isdigit():
                            # Convert f-number to float
                            exif_data[mapped_tag] = float(str_value)
                        else:
                            exif_data[mapped_tag] = str_value
            except Exception:
                pass
                
        else:
            # Standard EXIF extraction for JPEG and other formats
            exif_data_raw = img._getexif()  # pylint: disable=protected-access
            if exif_data_raw:
                for tag_id, value in exif_data_raw.items():
                    tag_name = TAGS.get(tag_id, tag_id)

                    if isinstance(value, bytes):
                        try:
                            # Special handling for XPKeywords (often UCS-2 encoded byte string)
                            if (
                                tag_name == "XPKeywords"
                            ):
                                decoded_value = value.decode("utf-16-le", errors="ignore")
                                cleaned_value = decoded_value.rstrip("\x00")
                                exif_data[tag_name] = [
                                    tag.strip()
                                    for tag in cleaned_value.split(";")
                                    if tag.strip()
                                ]
                                continue
                            else:
                                value = value.decode("utf-8", errors="ignore")
                        except UnicodeDecodeError:
                            pass

                    exif_data[tag_name] = (
                        clean_exif_string(value) if isinstance(value, str) else value
                    )

        # Attempt to get XMP data
        try:
            xmp_info = img.getxmp()
            if xmp_info:
                # Helper to navigate the XMP structure
                def find_in_xmp(data, path_keys):
                    current = data
                    for key_part in path_keys:
                        if isinstance(current, list):
                            if current:
                                current = current[0]
                            else:
                                return None
                        if not isinstance(current, dict) or key_part not in current:
                            return None
                        current = current[key_part]
                    return current

                # Helper to get a simple text value or the first from a list of text values
                def get_xmp_text_or_list_first(item_dict, key):
                    value = item_dict.get(key)
                    if isinstance(value, list) and value:
                        if all(isinstance(v, str) for v in value):
                            return str(value[0]).strip()
                    elif isinstance(value, str):
                        return value.strip()
                    elif isinstance(value, dict) and "Bag" in value and isinstance(value["Bag"], dict) and "li" in value["Bag"]:
                        li_items = value["Bag"]["li"]
                        if isinstance(li_items, list) and li_items:
                            if all(isinstance(v, str) for v in li_items):
                                return str(li_items[0]).strip()
                        elif isinstance(li_items, str):
                            return li_items.strip()
                    return None

                # Helper to get text from a language alternative structure
                def get_xmp_lang_alt(item_dict, key):
                    value = item_dict.get(key)
                    if isinstance(value, dict):
                        alt_node = value.get("Alt")
                        if isinstance(alt_node, dict) and "li" in alt_node:
                            li_items = alt_node["li"]
                            if not isinstance(li_items, list):
                                li_items = [li_items]
                            for li_item in li_items:
                                if isinstance(li_item, dict) and li_item.get("xml:lang") == "x-default":
                                    return str(li_item.get("#text", li_item.get("text"))).strip() # Handle cases where text is under #text or text
                            for li_item in li_items: # Fallback if no x-default
                                if isinstance(li_item, dict) and ("#text" in li_item or "text" in li_item):
                                    return str(li_item.get("#text", li_item.get("text"))).strip()
                                elif isinstance(li_item, str):
                                    return str(li_item).strip()
                        elif 'x-default' in value and isinstance(value['x-default'], str):
                            return value['x-default'].strip()
                    elif isinstance(value, str):
                        return value.strip()
                    return None

                rdf_description = find_in_xmp(xmp_info, ["xmpmeta", "RDF", "Description"])
                if rdf_description:
                    descriptions_list = rdf_description if isinstance(rdf_description, list) else [rdf_description]
                    for desc_item in descriptions_list:
                        if isinstance(desc_item, dict):
                            # Subject (Tags)
                            subject_node = desc_item.get("subject")
                            if subject_node and isinstance(subject_node, dict) and "Bag" in subject_node and \
                               isinstance(subject_node["Bag"], dict) and "li" in subject_node["Bag"]:
                                xmp_tags_list = subject_node["Bag"]["li"]
                                if isinstance(xmp_tags_list, list):
                                    xmp_data_dict["dc:subject"] = [str(tag).strip() for tag in xmp_tags_list if tag]
                                elif isinstance(xmp_tags_list, (str, dict)):
                                    xmp_data_dict["dc:subject"] = [str(xmp_tags_list).strip()]
                            elif "subject" in desc_item: # Simpler structure
                                subject_val = desc_item["subject"]
                                if isinstance(subject_val, list):
                                    xmp_data_dict["dc:subject"] = [str(tag).strip() for tag in subject_val if tag]
                                elif isinstance(subject_val, str):
                                    xmp_data_dict["dc:subject"] = [subject_val.strip()]

                            # Title
                            if "dc:title" not in xmp_data_dict:
                                xmp_title = get_xmp_lang_alt(desc_item, "title")
                                if xmp_title:
                                    xmp_data_dict["dc:title"] = xmp_title

                            # Description
                            if "dc:description" not in xmp_data_dict:
                                xmp_desc_val = get_xmp_lang_alt(desc_item, "description")
                                if xmp_desc_val:
                                    xmp_data_dict["dc:description"] = xmp_desc_val

                            # Creator
                            if "dc:creator" not in xmp_data_dict:
                                xmp_creator = get_xmp_text_or_list_first(desc_item, "creator")
                                if xmp_creator:
                                    xmp_data_dict["dc:creator"] = xmp_creator

                            # Rights (Copyright)
                            if "dc:rights" not in xmp_data_dict:
                                xmp_rights = get_xmp_lang_alt(desc_item, "rights")
                                if xmp_rights:
                                    xmp_data_dict["dc:rights"] = xmp_rights

                            # Notes (Darktable-specific field)
                            if "xmp:notes" not in xmp_data_dict:
                                xmp_notes = desc_item.get("notes")
                                if xmp_notes and isinstance(xmp_notes, str):
                                    xmp_data_dict["xmp:notes"] = xmp_notes.strip()

                            # If we found all desired XMP fields in one description block, we can often break
                            # However, sometimes fields are split, so we iterate all for safety unless performance dictates otherwise.
        except AttributeError:
            pass # img.getxmp() not available
        except Exception:
            pass # General XMP parsing error

        img.close()

        final_data = exif_data.copy() # Start with EXIF data

        # Title: XMP dc:title or EXIF ImageDescription
        if "dc:title" in xmp_data_dict:
            final_data["ProcessedTitle"] = clean_exif_string(xmp_data_dict["dc:title"])
        elif "ImageDescription" in exif_data: # EXIF ImageDescription as fallback for title
            final_data["ProcessedTitle"] = clean_exif_string(exif_data["ImageDescription"])
        elif "ObjectName" in exif_data: # Another potential EXIF/IPTC title field
             final_data["ProcessedTitle"] = clean_exif_string(exif_data["ObjectName"])


        # Description: XMP dc:description or EXIF UserComment (or ImageDescription if not used for title)
        if "dc:description" in xmp_data_dict:
            final_data["ProcessedDescription"] = clean_exif_string(xmp_data_dict["dc:description"])
        elif "UserComment" in exif_data: # EXIF UserComment as fallback
            final_data["ProcessedDescription"] = clean_exif_string(exif_data["UserComment"])
        # If ImageDescription was not used for title and no XMP description, consider it here.
        elif "ImageDescription" in exif_data and final_data.get("ProcessedTitle") != clean_exif_string(exif_data["ImageDescription"]):
            final_data["ProcessedDescription"] = clean_exif_string(exif_data["ImageDescription"])


        # Tags: XMP dc:subject or EXIF XPKeywords
        if "dc:subject" in xmp_data_dict:
            final_data["ProcessedTags"] = xmp_data_dict["dc:subject"]
        elif "XPKeywords" in exif_data:
            final_data["ProcessedTags"] = exif_data["XPKeywords"]

        # Creator: XMP dc:creator or EXIF Artist
        if "dc:creator" in xmp_data_dict:
            final_data["ProcessedCreator"] = clean_exif_string(xmp_data_dict["dc:creator"])
        elif "Artist" in exif_data:
            final_data["ProcessedCreator"] = clean_exif_string(exif_data["Artist"])

        # Copyright: XMP dc:rights or EXIF Copyright
        if "dc:rights" in xmp_data_dict:
            final_data["ProcessedCopyright"] = clean_exif_string(xmp_data_dict["dc:rights"])
        elif "Copyright" in exif_data:
            final_data["ProcessedCopyright"] = clean_exif_string(exif_data["Copyright"])

        # Notes: XMP xmp:notes (Darktable-specific field)
        if "xmp:notes" in xmp_data_dict:
            final_data["ProcessedNotes"] = clean_exif_string(xmp_data_dict["xmp:notes"])

        return final_data
    except Exception:
        return {}

def interpret_flash_value(flash_val):
    """Interprets the EXIF Flash tag value."""
    if flash_val is None:
        return None
    flash_fired = bool(flash_val & 0x1)
    if not flash_fired:
        return "Flash did not fire"
    # Simplified interpretation for now
    return "Flash fired"


def print_all_metadata_for_image(image_path_str):
    """Prints all EXIF and attempts to print XMP for a single image."""
    image_path = Path(image_path_str)
    if not image_path.exists():
        print(f"Error: Image not found at {image_path_str}")
        return

    print(f"--- Metadata for {image_path.name} ---")
    try:
        img = Image.open(image_path)
        print(f"Image format: {img.format}")
        print(f"Image size: {img.size}")
        
        print("\n-- EXIF Data --")
        if img.format == 'AVIF':
            # For AVIF files, use enhanced extraction methods
            print("Using AVIF-compatible extraction methods:")
            
            # Method 1: Basic getexif()
            try:
                basic_exif = img.getexif()
                if basic_exif:
                    print(f"Basic EXIF ({len(basic_exif)} entries):")
                    for tag_id, value in basic_exif.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        print(f"  {tag_name} (ID: {tag_id}): {value}")
            except Exception as e:
                print(f"  Error with basic getexif(): {e}")
            
            # Method 2: EXIF IFD
            try:
                exif_ifd = img.getexif().get_ifd(0x8769)
                if exif_ifd:
                    print(f"\nEXIF IFD ({len(exif_ifd)} entries):")
                    for tag_id, value in exif_ifd.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        print(f"  {tag_name} (ID: {tag_id}): {value}")
            except Exception as e:
                print(f"  Error with EXIF IFD: {e}")
            
            # Method 3: Raw EXIF bytes
            try:
                if 'exif' in img.info:
                    exif_bytes = img.info['exif']
                    exif_stream = io.BytesIO(exif_bytes)
                    tags = exifread.process_file(exif_stream, details=False)
                    if tags:
                        print(f"\nRaw EXIF parsing ({len(tags)} entries):")
                        for tag_name, tag_value in sorted(tags.items()):
                            print(f"  {tag_name}: {tag_value}")
            except Exception as e:
                print(f"  Error with raw EXIF parsing: {e}")
        else:
            # Standard _getexif() for other formats
            exif_data_raw = img._getexif()
            if exif_data_raw:
                for tag_id, value in exif_data_raw.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    print(f"  {tag_name} (ID: {tag_id}): {value}")
            else:
                print("  No EXIF data found.")

        print("\n-- XMP Data --")
        try:
            xmp_info = img.getxmp()
            if xmp_info:
                print("  Raw XMP Packet (first 1000 chars):")
                print(f"    {str(xmp_info)[:1000]}...")
                # Further parsing can be added here if needed for debug
            else:
                print("  No XMP data returned by img.getxmp().")
        except AttributeError:
            print("  img.getxmp() not available or XMP data not found.")
        except Exception as e_xmp_debug:
            print(f"  Error parsing XMP data: {e_xmp_debug}")
        img.close()
    except Exception as e_main_debug:
        print(f"Error opening or processing image {image_path_str}: {e_main_debug}")
    print("--- End Metadata ---")

def parse_exif_date(date_str):
    """Parses EXIF date string (YYYY:MM:DD HH:MM:SS) to ISO 8601 format."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        dt_obj = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        return dt_obj.isoformat()
    except ValueError:
        return None

def ensure_numeric_type(value, target_type='float'):
    """Ensures a value is converted to the correct numeric type for schema compliance."""
    if value is None:
        return None
    
    # If it's already the correct type, return as is
    if target_type == 'float' and isinstance(value, (int, float)):
        return float(value)
    elif target_type == 'int' and isinstance(value, int):
        return value
    
    # Try to convert from string or other types
    try:
        if target_type == 'float':
            return float(value)
        elif target_type == 'int':
            # Handle cases where ISO might be a float like "100.0"
            return int(float(value))
    except (ValueError, TypeError):
        return None

def filter_tags(tags, excluded_tags=None):
    """Filters out excluded tags (case-insensitive)."""
    if not tags or not isinstance(tags, list):
        return tags
    
    if excluded_tags is None:
        excluded_tags = EXCLUDED_TAGS
    
    # Convert excluded tags to lowercase for case-insensitive comparison
    excluded_lower = {tag.lower() for tag in excluded_tags}
    
    # Filter out excluded tags
    filtered = [tag for tag in tags if tag.lower() not in excluded_lower]
    
    # Return None if the list is empty after filtering
    return filtered if filtered else None

def classify_focal_length(focal_length_35mm):
    """
    Classifies focal length into categories based on 35mm equivalent.
    
    Args:
        focal_length_35mm: Focal length in 35mm equivalent (mm)
    
    Returns:
        String category or None if focal length is not available
    """
    if focal_length_35mm is None:
        return None
    
    try:
        fl = float(focal_length_35mm)
    except (ValueError, TypeError):
        return None
    
    # Classification based on 35mm equivalent focal length
    if fl < 24:
        return "ultra-wide"
    elif fl < 35:
        return "wide"
    elif fl < 70:
        return "normal"
    elif fl < 135:
        return "short-telephoto"
    elif fl < 300:
        return "telephoto"
    else:
        return "super-telephoto"

def calculate_crop_factor(focal_length, focal_length_35mm):
    """
    Calculates the crop factor from actual and 35mm equivalent focal lengths.
    
    Args:
        focal_length: Actual focal length (mm)
        focal_length_35mm: 35mm equivalent focal length (mm)
    
    Returns:
        Crop factor as float, or None if calculation not possible
    """
    if focal_length is None or focal_length_35mm is None:
        return None
    
    try:
        fl = float(focal_length)
        fl_35mm = float(focal_length_35mm)
        if fl > 0:
            return round(fl_35mm / fl, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    
    return None

def main(args):
    if args.debug_image:
        print_all_metadata_for_image(args.debug_image)
        return

    all_images_data = []
    processed_count = 0
    skipped_count = 0
    print(f"Scanning for images in: {PHOTO_ROOT_DIR.resolve()}")

    for root, _, files in os.walk(PHOTO_ROOT_DIR):
        for filename in files:
            if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".avif")):
                continue

            image_path = Path(root) / filename
            try:
                relative_path = image_path.relative_to(PHOTO_ROOT_DIR)
                print(f"Processing: {relative_path}")
                
                path_parts = relative_path.parts
                year, month, day = None, None, None
                if len(path_parts) >= 4:
                    try:
                        year = int(path_parts[0])
                        month = int(path_parts[1])
                        day = int(path_parts[2])
                    except ValueError:
                        print(f"Warning: Could not parse date from path for {relative_path}.")

                temp_img_for_dims = Image.open(image_path)
                width, height = temp_img_for_dims.size
                temp_img_for_dims.close()

                exif_data = get_exif_data(image_path)

                date_taken_str = exif_data.get("DateTimeOriginal") or exif_data.get("DateTime")
                date_taken_iso = parse_exif_date(date_taken_str)

                title = exif_data.get("ProcessedTitle", None)
                description = exif_data.get("ProcessedDescription", None)
                tags = exif_data.get("ProcessedTags", [])
                if not isinstance(tags, list):
                    tags = []
                
                # Filter out excluded tags
                tags = filter_tags(tags)
                
                lens_model_processed = clean_exif_string(exif_data.get("LensModel", None))
                camera_model_processed = clean_exif_string(exif_data.get("Model", None))

                flash_info_raw = exif_data.get("Flash")
                flash_fired_boolean = None
                if flash_info_raw is not None:
                    # Handle both integer and string flash values
                    if isinstance(flash_info_raw, (int, float)):
                        flash_fired_boolean = bool(int(flash_info_raw) & 0x1)
                    elif isinstance(flash_info_raw, str):
                        if "fired" in flash_info_raw.lower():
                            flash_fired_boolean = True
                        elif "not fire" in flash_info_raw.lower():
                            flash_fired_boolean = False
                        else:
                            # Try to parse as integer
                            try:
                                flash_fired_boolean = bool(int(flash_info_raw) & 0x1)
                            except ValueError:
                                flash_fired_boolean = None

                # Generate slug from relative_path
                slug = str(relative_path.with_suffix('')).replace(os.sep, '-')

                # Calculate crop factor and focal length classification
                focal_length_35mm = exif_data.get("FocalLengthIn35mmFilm")
                focal_length_category = classify_focal_length(focal_length_35mm)
                crop_factor = calculate_crop_factor(
                    exif_data.get("FocalLength"),
                    focal_length_35mm
                )

                image_data = {
                    "relativePath": str(relative_path.as_posix()),
                    "filename": filename, "year": year, "month": month, "day": day,
                    "slug": slug,
                    "width": width, "height": height, "dateTaken": date_taken_iso,
                    "title": title, "description": description,
                    "tags": tags,
                    "cameraModel": camera_model_processed,
                    "lensModel": lens_model_processed,
                    "flash": flash_fired_boolean,
                    "focalLength": ensure_numeric_type(format_ifd_rational_value(exif_data.get("FocalLength")), 'float'),
                    "focalLength35mmEquiv": ensure_numeric_type(focal_length_35mm, 'int'),
                    "focalLengthCategory": focal_length_category,
                    "cropFactor": crop_factor,
                    "apertureValue": ensure_numeric_type(format_ifd_rational_value(exif_data.get("FNumber")), 'float'),
                    "isoSpeedRatings": ensure_numeric_type(exif_data.get("ISOSpeedRatings"), 'int'),
                    "exposureTime": ensure_numeric_type(format_ifd_rational_value(exif_data.get("ExposureTime")), 'float'),
                    "creator": exif_data.get("ProcessedCreator", None),
                    "copyright": exif_data.get("ProcessedCopyright", None),
                    "notes": exif_data.get("ProcessedNotes", None),
                }
                all_images_data.append(image_data)
                processed_count += 1
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                skipped_count += 1

    all_images_data.sort(key=lambda x: x.get("dateTaken") or "0000-00-00T00:00:00", reverse=True)
    with open(OUTPUT_JSON_FILE, "w") as f:
        json.dump(all_images_data, f, indent=2)

    print(f"\nSuccessfully processed {processed_count} images.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} files due to errors.")
    print(f"Manifest file created: {OUTPUT_JSON_FILE.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a JSON manifest from image metadata.")
    parser.add_argument("--debug-image", type=str, help="Path to a single image file to print all its metadata for debugging.")
    cli_args = parser.parse_args()
    main(cli_args)
