import requests
import re
import urllib.parse
import time
import html
import xml.etree.ElementTree as ET

def parse_time(time_str: str) -> float:
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                return float(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        return float(time_str)
    except:
        return 0.0

def parse_ttml(ttml: str) -> str:
    try:
        # Remove xml declarations
        ttml_clean = re.sub(r'<\?xml[^>]+\?>', '', ttml).strip()
        # Remove all xmlns
        ttml_clean = re.sub(r'\sxmlns(:\w+)?="[^"]*"', '', ttml_clean)
        # Remove namespace prefixes from tags (e.g. <tt:p -> <p)
        ttml_clean = re.sub(r'(<\/?)\w+:', r'\1', ttml_clean)
        # Remove namespace prefixes from attributes (e.g. itunes:key="val" -> key="val")
        ttml_clean = re.sub(r'\s\w+:(\w+="[^"]*")', r' \1', ttml_clean)
        
        root = ET.fromstring(ttml_clean)
        
        lines = []
        for p in root.iter('p'):
            begin = p.get('begin', '')
            if not begin: continue
            start_time = parse_time(begin)
            
            words = []
            for span in p.iter('span'):
                role = span.get('role', '')
                if role in ('x-bg', 'x-translation', 'x-roman'):
                    continue
                    
                w_begin = span.get('begin', '')
                w_end = span.get('end', '')
                w_text = span.text.strip() if span.text else ''
                
                if w_begin and w_end and w_text:
                    words.append({
                        'text': w_text,
                        'start': parse_time(w_begin),
                        'end': parse_time(w_end)
                    })
            
            # If we couldn't extract words via spans, fallback to raw text
            if not words:
                text_raw = "".join(p.itertext()).strip()
                if text_raw:
                    mins = int(start_time // 60)
                    secs = int(start_time % 60)
                    ms = int(round((start_time % 1) * 100))
                    lines.append(f"[{mins:02d}:{secs:02d}.{ms:02d}]{text_raw}")
            else:
                line_text = " ".join([w['text'] for w in words])
                if line_text.strip():
                    mins = int(start_time // 60)
                    secs = int(start_time % 60)
                    ms = int(round((start_time % 1) * 100))
                    lines.append(f"[{mins:02d}:{secs:02d}.{ms:02d}]{line_text}")
                    
                    # Vivi Music's custom word format
                    words_data = "|".join([f"{w['text']}:{w['start']}:{w['end']}" for w in words])
                    if words_data:
                        lines.append(f"<{words_data}>")
                        
        return "\n".join(lines)
    except Exception as e:
        print(f"    [!] TTML Parse Error: {e}")
        return ""

def fetch_lrclib(title: str, artist: str) -> str | None:
    try:
        url = "https://lrclib.net/api/search"
        params = {"track_name": title, "artist_name": artist}
        headers = {"User-Agent": "YTMusic-Downloader/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list):
                for track in data:
                    if track.get('syncedLyrics'):
                        return track['syncedLyrics']
                if data[0].get('plainLyrics'):
                    return data[0]['plainLyrics']
    except Exception as e:
        pass
    return None

def fetch_musixmatch(title: str, artist: str) -> str | None:
    return None

def fetch_paxsenix(title: str, artist: str) -> str | None:
    try:
        # 1. Scrape Apple Music for Bearer Token
        resp = requests.get("https://beta.music.apple.com", timeout=10)
        index_match = re.search(r"/assets/index~[^/]+\.js", resp.text)
        if not index_match: return None
        
        js_url = "https://beta.music.apple.com" + index_match.group(0)
        js_resp = requests.get(js_url, timeout=10)
        token_match = re.search(r"eyJ[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+", js_resp.text)
        if not token_match: return None
        token = token_match.group(0)
        
        # 2. Search Apple Music for Track ID
        q = urllib.parse.quote(f"{title} {artist}")
        search_url = f"https://amp-api.music.apple.com/v1/catalog/us/search?term={q}&types=songs&limit=3"
        headers = {"Authorization": f"Bearer {token}", "Origin": "https://music.apple.com"}
        s_resp = requests.get(search_url, headers=headers, timeout=10)
        if s_resp.status_code != 200: return None
        
        songs = s_resp.json().get("results", {}).get("songs", {}).get("data", [])
        if not songs: return None
        
        for song in songs:
            track_id = song.get("id")
            if not track_id: continue
            
            pax_url = f"https://lyrics.paxsenix.org/apple-music/lyrics?id={track_id}"
            
            for attempt in range(3):
                try:
                    pax_resp = requests.get(pax_url, timeout=15)
                    if pax_resp.status_code == 503:
                        time.sleep(3)
                        continue
                    break
                except requests.exceptions.RequestException:
                    time.sleep(3)
                    continue
            else:
                continue
                
            if pax_resp.status_code == 200:
                p_data = pax_resp.json()
                
                # Priority 1: TTML Parser (Word-by-Word extraction)
                if p_data.get("ttmlContent"):
                    parsed = parse_ttml(p_data["ttmlContent"])
                    if parsed: return parsed

                # Priority 2: ELRC Fallbacks
                if p_data.get("elrcMultiPerson"): return p_data["elrcMultiPerson"]
                if p_data.get("elrc"): return p_data["elrc"]
                
                # Priority 3: Plain
                if p_data.get("plain"): return p_data["plain"]

                # Priority 4: Content Array (Syllable logic)
                if p_data.get("content"):
                    has_word_level = (p_data.get("type") == "Syllable")
                    
                    if not has_word_level:
                        lines = []
                        for line in p_data.get("content", []):
                            text = " ".join([w.get("text", "") for w in line.get("text", [])])
                            if text.strip(): lines.append(text)
                        return "\n".join(lines)
                        
                    lines = []
                    for line in p_data.get("content", []):
                        ts = line.get("timestamp", 0)
                        mins = ts // 60000
                        secs = (ts // 1000) % 60
                        ms = (ts % 1000) // 10
                        
                        words = line.get("text", [])
                        line_text = " ".join([w.get("text", "") for w in words])
                        
                        if line_text.strip():
                            lines.append(f"[{mins:02d}:{secs:02d}.{ms:02d}]{line_text}")
                            words_data = "|".join([f'{w.get("text", "")}:{w.get("timestamp", 0)/1000}:{w.get("endtime", 0)/1000}' for w in words])
                            if words_data:
                                lines.append(f"<{words_data}>")
                    if lines:
                        return "\n".join(lines)

    except Exception as e:
        print(f"    [!] Paxsenix error: {e}")
    return None

def get_quality(lrc: str) -> int:
    if not lrc: return 0
    if "<" in lrc and ">" in lrc and ("|" in lrc or ":" in lrc):
        return 3
    if re.search(r'<\d{1,2}:\d{2}\.\d{2,3}>', lrc):
        return 3
    if re.search(r'\[\d{2}:\d{2}\.\d{2,3}\]', lrc):
        return 2
    return 1

def fetch_lyrics(title: str, artist: str) -> str | None:
    best_lrc = None
    best_quality = 0
    best_source = ""

    # 1. Paxsenix
    lrc_pax = fetch_paxsenix(title, artist)
    q_pax = get_quality(lrc_pax)
    if q_pax == 3:
        print("    [+] Lyrics found on Paxsenix (Word-by-Word)")
        return lrc_pax
    elif q_pax > best_quality:
        best_lrc = lrc_pax
        best_quality = q_pax
        best_source = "Paxsenix"
        
    # If Paxsenix isn't word-by-word, check others to see if we can find word-by-word
    # Actually, user logic: "we first search for paxsenix for word to word lyrics. if not word to word then entire sentence sync lyrics"
    # Wait, the user priority means we should just accept sentence sync from Paxsenix!
    if best_quality == 2:
        print("    [+] Lyrics found on Paxsenix (Line-Synced)")
        return best_lrc

    # 2. LRCLIB
    lrc_lrc = fetch_lrclib(title, artist)
    q_lrc = get_quality(lrc_lrc)
    if q_lrc == 3:
        print("    [+] Lyrics found on LRCLIB (Word-by-Word)")
        return lrc_lrc
    elif q_lrc > best_quality:
        best_lrc = lrc_lrc
        best_quality = q_lrc
        best_source = "LRCLIB"

    if best_quality == 2:
        print(f"    [+] Lyrics found on {best_source} (Line-Synced)")
        return best_lrc

    # 3. Musixmatch (Placeholder if implemented)
    lrc_mx = fetch_musixmatch(title, artist)
    q_mx = get_quality(lrc_mx)
    if q_mx == 3:
        print("    [+] Lyrics found on Musixmatch (Word-by-Word)")
        return lrc_mx
    elif q_mx > best_quality:
        best_lrc = lrc_mx
        best_quality = q_mx
        best_source = "Musixmatch"

    if best_quality > 0:
        if best_quality == 2:
            print(f"    [+] Lyrics found on {best_source} (Line-Synced)")
        else:
            print(f"    [+] Lyrics found on {best_source} (Unsynced)")
        return best_lrc

    return None
