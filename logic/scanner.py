import os
import sqlite3
from logic.processor import ImageProcessor

class ImageScanner:
    def __init__(self, db_path="photos.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                filename TEXT,
                folder TEXT,
                width INTEGER,
                height INTEGER,
                file_size_mb REAL,
                date_taken TEXT,
                camera_model TEXT,
                phash TEXT
            )
        """)
        conn.commit()
        conn.close()

    def scan_directory(self, directory, thumb_dir):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        valid_extensions = (".jpg", ".jpeg", ".png", ".webp")
        
        for root, dirs, files in os.walk(directory):
            if ".thumbnails" in root:
                continue
                
            for file in files:
                if file.lower().endswith(valid_extensions):
                    path = os.path.join(root, file)
                    
                    # Check if already indexed
                    cursor.execute("SELECT id FROM images WHERE path = ?", (path,))
                    if cursor.fetchone():
                        continue
                        
                    metadata = ImageProcessor.get_technical_metadata(path)
                    phash = ImageProcessor.get_image_hash(path)
                    
                    if metadata and phash:
                        cursor.execute("""
                            INSERT INTO images 
                            (path, filename, folder, width, height, file_size_mb, date_taken, camera_model, phash)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            metadata["path"], metadata["filename"], metadata["folder"],
                            metadata["width"], metadata["height"], metadata["file_size_mb"],
                            metadata["date_taken"], metadata["camera_model"], phash
                        ))
                        # Create thumbnail pre-emptively
                        ImageProcessor.create_thumbnail(path, thumb_dir)
        
        conn.commit()
        conn.close()

    def get_all_images(self):
        import pandas as pd
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM images", conn)
        conn.close()
        return df
