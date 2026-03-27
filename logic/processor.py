import os
import sqlite3
from PIL import Image, ExifTags
import imagehash
from datetime import datetime
import pandas as pd

class ImageProcessor:
    @staticmethod
    def get_technical_metadata(image_path):
        """Extracts technical tags: date, dimensions, camera mode, file size."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
                
                metadata = {
                    "path": image_path,
                    "filename": os.path.basename(image_path),
                    "width": width,
                    "height": height,
                    "file_size_mb": round(file_size, 2),
                    "date_taken": None,
                    "camera_model": "Unknown",
                    "folder": os.path.basename(os.path.dirname(image_path))
                }

                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag == "DateTimeOriginal":
                            try:
                                metadata["date_taken"] = datetime.strptime(value, "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
                            except:
                                metadata["date_taken"] = value
                        elif tag == "Model":
                            metadata["camera_model"] = value
                
                return metadata
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return None

    @staticmethod
    def get_image_hash(image_path):
        """Generates a perceptual hash for the image."""
        try:
            with Image.open(image_path) as img:
                # Use dhash or phash for similarity
                return str(imagehash.dhash(img))
        except Exception as e:
            print(f"Error hashing {image_path}: {e}")
            return None

    @staticmethod
    def create_thumbnail(image_path, thumb_dir, size=(200, 200)):
        """Creates a small thumbnail for the UI."""
        try:
            if not os.path.exists(thumb_dir):
                os.makedirs(thumb_dir)
            
            thumb_name = f"thumb_{os.path.basename(image_path)}"
            thumb_path = os.path.join(thumb_dir, thumb_name)
            
            if os.path.exists(thumb_path):
                return thumb_path
                
            with Image.open(image_path) as img:
                img.thumbnail(size)
                img.save(thumb_path)
                return thumb_path
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None
