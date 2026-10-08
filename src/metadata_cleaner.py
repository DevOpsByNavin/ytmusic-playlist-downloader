import re

TITLE_CLEANUP_PATTERNS = [
    re.compile(r'\s*\(.*?(official|video|audio|lyrics|lyric|visualizer|hd|hq|4k|remaster|remix|live|acoustic|version|edit|extended|radio|clean|explicit).*?\)', re.IGNORECASE),
    re.compile(r'\s*\[.*?(official|video|audio|lyrics|lyric|visualizer|hd|hq|4k|remaster|remix|live|acoustic|version|edit|extended|radio|clean|explicit).*?\]', re.IGNORECASE),
    re.compile(r'\s*【.*?】'),
    re.compile(r'\s*\|.*$'),
    re.compile(r'\s*-\s*(official|video|audio|lyrics|lyric|visualizer).*$', re.IGNORECASE),
    re.compile(r'\s*\(feat\..*?\)', re.IGNORECASE),
    re.compile(r'\s*\(ft\..*?\)', re.IGNORECASE),
    re.compile(r'\s*feat\..*$', re.IGNORECASE),
    re.compile(r'\s*ft\..*$', re.IGNORECASE),
    re.compile(r'\s*\([^)]*\d{4}[^)]*\)', re.IGNORECASE),
]

ARTIST_SEPARATORS = [
    " & ", " and ", ", ", " x ", " X ", " feat. ", " feat ", " ft. ", " ft ", " featuring ", " with "
]

def clean_title(title: str) -> str:
    cleaned = title.strip()
    for pattern in TITLE_CLEANUP_PATTERNS:
        cleaned = pattern.sub('', cleaned)
    return cleaned.strip()

def clean_artist(artist: str) -> str:
    cleaned = artist.strip()
    for separator in ARTIST_SEPARATORS:
        lower_cleaned = cleaned.lower()
        lower_sep = separator.lower()
        idx = lower_cleaned.find(lower_sep)
        if idx != -1:
            cleaned = cleaned[:idx]
            break
    return cleaned.strip()

def split_title_artist(raw_title: str, channel_name: str) -> tuple[str, str]:
    """
    Attempts to separate artist and title from a YouTube video title.
    Returns (artist, title).
    """
    # Often YT videos are "Artist - Title"
    if " - " in raw_title:
        parts = raw_title.split(" - ", 1)
        artist = clean_artist(parts[0])
        title = clean_title(parts[1])
        return artist, title
    
    # If no dash, assume channel name is artist, and title is the video title
    return clean_artist(channel_name), clean_title(raw_title)
