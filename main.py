import pandas as pd
import argparse
import sys
from src.db import init_db
from src.downloader import download_playlist

def main():
    parser = argparse.ArgumentParser(description="Optimal YTMusic Downloader")
    parser.add_argument("--lyric", action="store_true", help="[Future] Fetch lyrics for downloaded songs from Paxsenix, LRCLIB, Musixmatch")
    args = parser.parse_args()

    if args.lyric:
        print("[i] Lyric fetching is planned for a future update (Providers: Paxsenix -> LRCLIB -> Musixmatch)")
        sys.exit(0)

    # Initialize SQLite database
    init_db()

    try:
        # Based on the exact headers seen in the user's file: "Playlist ID,Title,Description"
        df = pd.read_csv("data/playlists.csv")
    except FileNotFoundError:
        print("[-] data/playlists.csv not found. Please ensure it exists.")
        return

    if "Playlist ID" in df.columns and "Title" in df.columns:
        for _, row in df.iterrows():
            playlist_id = str(row["Playlist ID"]).strip()
            title = str(row["Title"]).strip()
            if not playlist_id or playlist_id == 'nan':
                continue
            download_playlist(playlist_id, title)
    else:
        print("[-] CSV missing required columns: 'Playlist ID' and 'Title'")

if __name__ == "__main__":
    main()
