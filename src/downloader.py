import os
import yt_dlp
from mutagen.mp4 import MP4
from .metadata_cleaner import split_title_artist
from .db import is_downloaded, mark_downloaded, get_lyrics_status, mark_lyrics_status
from .lyrics import fetch_lyrics

# --- RATE LIMITING CONFIGURATION ---
# Sleep a random number of seconds between downloads to avoid YouTube bans.
SLEEP_INTERVAL_MIN = 2      # Minimum seconds to sleep
SLEEP_INTERVAL_MAX = 5      # Maximum seconds to sleep
# Optional: Throttle download speed (e.g., 1024 * 1024 for 1MB/s). None for unlimited.
RATE_LIMIT_BYTES = None 
# -----------------------------------

def download_playlist(playlist_id: str, playlist_name: str, fetch_lyrics_flag: bool = False):
    safe_playlist_name = "".join(c for c in playlist_name if c.isalnum() or c in " -_").strip()
    download_dir = os.path.join("downloads", safe_playlist_name)
    os.makedirs(download_dir, exist_ok=True)

    ydl_opts_extract = {
        'extract_flat': True,
        'quiet': True,
        'sleep_requests': 1, # Sleep between pagination requests for massive playlists
    }

    print(f"\n[INFO] Fetching playlist: {playlist_name}")
    with yt_dlp.YoutubeDL(ydl_opts_extract) as ydl:
        try:
            info = ydl.extract_info(f"https://www.youtube.com/playlist?list={playlist_id}", download=False)
            if not info or 'entries' not in info:
                print(f"[-] Could not extract playlist {playlist_name}")
                return
            entries = list(info['entries'])
        except Exception as e:
            print(f"[-] Failed to fetch playlist {playlist_name}: {e}")
            return

    for entry in entries:
        if not entry: continue
        video_id = entry.get('id')
        if not video_id: continue
        
        raw_title = entry.get('title', 'Unknown Title')
        channel = entry.get('uploader', 'Unknown Artist')
        artist, title = split_title_artist(raw_title, channel)
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
        safe_artist = "".join(c for c in artist if c.isalnum() or c in " -_").strip()
        
        clean_filename = os.path.join(download_dir, f"{safe_artist} - {safe_title}.m4a")

        # 1. DOWNLOAD AUDIO IF NEEDED
        just_downloaded = False
        if not is_downloaded(video_id):
            out_temp = os.path.join(download_dir, f"{video_id}")
            
            print(f"[*] Downloading: {artist} - {title}")
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': out_temp + '.%(ext)s',
                'writethumbnail': True,
                'sleep_interval': SLEEP_INTERVAL_MIN,
                'max_sleep_interval': SLEEP_INTERVAL_MAX,
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'},
                    {'key': 'EmbedThumbnail'},
                ],
                'quiet': True,
                'no_warnings': True,
            }
            
            if RATE_LIMIT_BYTES is not None:
                ydl_opts['ratelimit'] = RATE_LIMIT_BYTES

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                
                final_file = out_temp + '.m4a'
                if os.path.exists(final_file):
                    try:
                        audio = MP4(final_file)
                        audio['\xa9nam'] = title
                        audio['\xa9ART'] = artist
                        audio['\xa9alb'] = playlist_name
                        audio.save()
                        
                        if os.path.exists(clean_filename):
                            clean_filename = os.path.join(download_dir, f"{safe_artist} - {safe_title}_{video_id}.m4a")
                        os.rename(final_file, clean_filename)
                    except Exception as e:
                        print(f"    [!] Error setting metadata: {e}")
                
                mark_downloaded(video_id, playlist_id, clean_filename)
                print(f"    [+] Audio Done: {artist} - {title}")
                just_downloaded = True
            except Exception as e:
                print(f"    [!] Failed to download: {e}")
                continue # Skip lyrics if audio failed

        # 2. FETCH LYRICS IF REQUESTED
        if fetch_lyrics_flag:
            l_status = get_lyrics_status(video_id)
            lrc_filename = clean_filename.rsplit('.', 1)[0] + '.lrc'
            
            if l_status == 1:
                if os.path.exists(lrc_filename) and not just_downloaded:
                    continue
                # If DB says 1 but file missing, or audio just redownloaded, we re-fetch
            if l_status == -1:
                # Already tried, none exist. Only retry if we just redownloaded the audio
                if not just_downloaded:
                    continue
            
            print(f"[*] Fetching lyrics for: {artist} - {title}")
            lrc_content = fetch_lyrics(title, artist)
            
            if lrc_content:
                # Save .lrc file
                lrc_filename = clean_filename.rsplit('.', 1)[0] + '.lrc'
                try:
                    with open(lrc_filename, 'w', encoding='utf-8') as f:
                        f.write(lrc_content)
                    
                    # Embed in .m4a
                    if os.path.exists(clean_filename):
                        audio = MP4(clean_filename)
                        audio['\xa9lyr'] = lrc_content
                        audio.save()
                        
                    mark_lyrics_status(video_id, 1)
                    print("    [+] Lyrics saved & embedded.")
                except Exception as e:
                    print(f"    [!] Error saving lyrics: {e}")
            else:
                mark_lyrics_status(video_id, -1)
                print("    [-] No lyrics found for this song.")
