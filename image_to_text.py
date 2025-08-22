import pytesseract
from PIL import Image
import os
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from PIL.ExifTags import TAGS

OUTPUT_FOLDER="../clio-out"

def get_image_creation_time(image_path: Path) -> Tuple[datetime, str]:
    """
    Get image creation time from EXIF data or fall back to file modification time.
    Returns tuple of (datetime, source) where source is either 'EXIF' or 'mtime'
    """
    try:
        with Image.open(image_path) as img:
            # Get EXIF data
            exif = img._getexif()
            if exif:
                # Look for DateTimeOriginal or DateTime tags
                for tag_id in exif:
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ['DateTimeOriginal', 'DateTime']:
                        date_str = exif[tag_id]
                        # EXIF date format: 'YYYY:MM:DD HH:MM:SS'
                        try:
                            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S'), 'EXIF'
                        except ValueError:
                            pass
    except Exception:
        pass
    
    # Fallback to modification time if EXIF data is not available
    return datetime.fromtimestamp(image_path.stat().st_mtime), 'mtime'

def get_image_files(folder_path: str) -> List[Path]:
    """Get all image files from the folder and sort them by creation time."""
    supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    image_files = []
    
    for file_path in Path(folder_path).iterdir():
        if file_path.suffix.lower() in supported_formats:
            image_files.append(file_path)
    
    # Sort files by creation time (EXIF if available, else modification time)
    return sorted(image_files, key=lambda x: get_image_creation_time(x)[0])

def process_images(folder_path: str, output_file: str) -> None:
    """Process all images in the folder and append their text to the output file."""
    image_files = get_image_files(folder_path)
    
    if not image_files:
        print(f"No supported image files found in {folder_path}")
        return
    
    for image_path in image_files:
        try:
            # Get timestamp and its source
            timestamp, time_source = get_image_creation_time(image_path)
            formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            # Open and process the image
            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img)
                
            # Append the text to the output file with a separator
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"\n--- Text from {image_path.name} ({time_source} time: {formatted_time}) ---\n")
                f.write(text)
                f.write("\n")
                
            print(f"Processed: {image_path.name} (using {time_source} timestamp)")
            
        except Exception as e:
            print(f"Error processing {image_path.name}: {str(e)}")

if __name__ == "__main__":
    input_folder = "images"  # folder containing the images
    output_file = os.path.join(OUTPUT_FOLDER, "extracted_text.txt") # file where the text will be saved
    
    # Create output directory and file if they don't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.touch(exist_ok=True)
    
    # Process all images
    process_images(input_folder, output_file)