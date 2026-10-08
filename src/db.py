import sqlite3
import os

DB_PATH = "data/music.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS downloaded (
            video_id TEXT PRIMARY KEY,
            playlist_id TEXT,
            file_path TEXT,
            is_downloaded INTEGER NOT NULL DEFAULT 0,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Attempt to add file_path column if table already exists from previous runs
    try:
        cursor.execute("ALTER TABLE downloaded ADD COLUMN file_path TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    conn.commit()
    conn.close()

def is_downloaded(video_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT is_downloaded, file_path FROM downloaded WHERE video_id = ?", (video_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] == 1:
        file_path = row[1]
        # If we have a file path, verify the file actually exists on disk
        if file_path and os.path.exists(file_path):
            return True
        elif not file_path:
            # Fallback for old entries without file_path
            return True
    return False

def mark_downloaded(video_id: str, playlist_id: str, file_path: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO downloaded (video_id, playlist_id, file_path, is_downloaded)
        VALUES (?, ?, ?, 1)
    """, (video_id, playlist_id, file_path))
    conn.commit()
    conn.close()
