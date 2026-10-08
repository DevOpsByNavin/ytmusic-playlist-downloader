# YTMusic Downloader

An automated, highly-optimized YouTube Music downloader built in Python. This tool reads public playlists, downloads high-quality audio (`.m4a`) using `yt-dlp`, embeds clean metadata and cover art, and features a robust lyrics fetching engine capable of embedding word-by-word synced lyrics.

## 🔗 Dependency Note

This project relies on a `playlists.csv` file to know what to download. You can generate this file automatically using the companion project:
**[ytmusic-classifier](https://github.com/DevOpsByNavin/ytmusic-classifier)**

## ⚙️ How It Works

1. **Playlist Parsing:** Reads `data/playlists.csv` for YouTube Playlist IDs.
2. **Audio Downloading:** Uses `yt-dlp` to download the best audio format, extract it to `.m4a`, and embed thumbnail art.
3. **Metadata Cleaning:** Strips common YouTube junk (e.g., "(Official Music Video)", "[Lyrics]") from titles to ensure clean metadata.
4. **Lyrics Engine (Optional):** When run with `--lyric`, the script intelligently hunts for the highest quality lyrics:
   - **Paxsenix (Apple Music):** Scrapes Apple Music tokens and fetches Word-by-Word synced lyrics (parsing raw TTML and Syllable structures).
   - **LRCLIB:** Falls back to the open-source LRCLIB for line-synced lyrics if word-by-word isn't available.
5. **Database Caching:** A local SQLite database (`data/music.db`) tracks what has been downloaded and whether lyrics searches succeeded or failed (so it doesn't spam APIs for songs that genuinely lack lyrics).
6. **Smart Retries:** If you manually delete your `downloads/` folder, the script is smart enough to redownload the audio and force a retry for the lyrics, bypassing the database cache automatically.

## 🚀 Usage

### Prerequisites
1. Clone the repository and navigate to it.
2. Ensure you have `ffmpeg` installed on your system (required by `yt-dlp` for audio extraction).
3. Install the dependencies inside a virtual environment:
   ```bash
   pip install -r requirements.txt
   ```
4. Generate or place your `playlists.csv` (from [ytmusic-classifier](https://github.com/DevOpsByNavin/ytmusic-classifier)) into the `data/` directory.
5. Initialize the database schema (useful for reproducibility on fresh installs):
   ```bash
   sqlite3 data/music.db < schema/music_db.sql
   ```

### Running the Downloader

Download songs only (fast):
```bash
python main.py
```

Download songs and meticulously fetch/embed synchronized lyrics:
```bash
python main.py --lyric
```
*Note: The script has built-in sleep intervals (2-5 seconds per song) to avoid triggering YouTube's 403 Forbidden anti-bot measures on massive playlists.*

## 📂 Project Structure

```text
.
├── data/
│   ├── music.db            # SQLite database tracking downloaded songs and lyrics statuses
│   └── playlists.csv       # Input CSV containing playlist names and YouTube playlist IDs
├── schema/
│   └── music_db.sql        # SQL schema to initialize the database for reproducibility
├── src/
│   ├── db.py               # Database interaction logic (checking cache, tracking downloads & lyrics)
│   ├── downloader.py       # Core yt-dlp downloader handling audio extraction, caching, and metadata embedding
│   ├── lyrics.py           # Lyrics fetching engine (Paxsenix, LRCLIB)
│   └── metadata_cleaner.py # Regex-based cleaner for stripping junk from YouTube titles
├── main.py                 # Main entry point and CLI for running the downloader
└── requirements.txt        # Python dependencies required for the project
```
