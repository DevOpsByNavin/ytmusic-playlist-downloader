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
            has_lyrics INTEGER NOT NULL DEFAULT 0,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Attempt to add columns if table already exists from previous runs
    try:
        cursor.execute("ALTER TABLE downloaded ADD COLUMN file_path TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE downloaded ADD COLUMN has_lyrics INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
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
        if file_path and os.path.exists(file_path):
            return True
        elif not file_path:
            return True
    return False

def get_lyrics_status(video_id: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT has_lyrics FROM downloaded WHERE video_id = ?", (video_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def mark_downloaded(video_id: str, playlist_id: str, file_path: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Using INSERT OR IGNORE and then UPDATE to ensure we don't overwrite has_lyrics
    cursor.execute("""
        INSERT OR IGNORE INTO downloaded (video_id, playlist_id)
        VALUES (?, ?)
    """, (video_id, playlist_id))
    cursor.execute("""
        UPDATE downloaded SET is_downloaded = 1, file_path = ? WHERE video_id = ?
    """, (file_path, video_id))
    conn.commit()
    conn.close()

def mark_lyrics_status(video_id: str, status: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE downloaded SET has_lyrics = ? WHERE video_id = ?
    """, (status, video_id))
    conn.commit()
    conn.close()
