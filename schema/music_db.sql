-- Database schema for YTMusic Downloader tracking

CREATE TABLE IF NOT EXISTS downloaded (
    video_id TEXT PRIMARY KEY,
    playlist_id TEXT,
    file_path TEXT,
    is_downloaded INTEGER NOT NULL DEFAULT 0,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
