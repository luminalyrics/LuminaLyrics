import re

def parse_lrc(content: str) -> list:
    """
    Parses LRC content into a list of dictionaries:
    [{"start": float, "end": float, "text": str}]
    """
    lines = content.split('\n')
    pattern = re.compile(r'\[(\d+):(\d+(?:\.\d+)?)\](.*)')
    lyrics = []

    for line in lines:
        match = pattern.match(line.strip())
        if match:
            minutes = int(match.group(1))
            seconds = float(match.group(2))
            text = match.group(3).strip()
            # Convert to seconds
            timestamp = minutes * 60 + seconds
            lyrics.append({
                "start": timestamp,
                "end": None, # Will fill in next
                "text": text
            })

    # Sort lyrics by start time
    lyrics.sort(key=lambda x: x["start"])

    # Determine end times
    for i in range(len(lyrics)):
        if i < len(lyrics) - 1:
            lyrics[i]["end"] = lyrics[i + 1]["start"]
        else:
            # For the last line, display for 5 seconds or until the song ends
            lyrics[i]["end"] = lyrics[i]["start"] + 5.0

    # Filter out empty lyric lines
    return [l for l in lyrics if l["text"]]

def parse_srt(content: str) -> list:
    """
    Parses SRT content into a list of dictionaries:
    [{"start": float, "end": float, "text": str}]
    """
    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    # Split by double newline (or multiple newlines)
    blocks = re.split(r'\n\s*\n', content.strip())
    lyrics = []

    time_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})')

    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) < 2:
            continue
        
        # Line 0 is usually index, Line 1 is the timeline, remainder is text
        timeline_line = ""
        text_lines = []
        
        # Sometimes there's no index line, so check if line 0 matches time pattern
        if time_pattern.match(lines[0]):
            timeline_line = lines[0]
            text_lines = lines[1:]
        elif len(lines) >= 2 and time_pattern.match(lines[1]):
            timeline_line = lines[1]
            text_lines = lines[2:]
        else:
            continue

        match = time_pattern.match(timeline_line)
        if match:
            start_sec = (int(match.group(1)) * 3600 +
                         int(match.group(2)) * 60 +
                         int(match.group(3)) +
                         int(match.group(4)) / 1000.0)
            
            end_sec = (int(match.group(5)) * 3600 +
                       int(match.group(6)) * 60 +
                       int(match.group(7)) +
                       int(match.group(8)) / 1000.0)
            
            text = " ".join(text_lines)
            lyrics.append({
                "start": start_sec,
                "end": end_sec,
                "text": text
            })

    lyrics.sort(key=lambda x: x["start"])
    return lyrics

def parse_lyrics(content: str, filename: str) -> list:
    """
    Parses lyrics based on file extension
    """
    ext = filename.lower().split('.')[-1]
    if ext == 'lrc':
        return parse_lrc(content)
    elif ext == 'srt':
        return parse_srt(content)
    else:
        # Try both as fallback
        if "-->" in content:
            return parse_srt(content)
        else:
            return parse_lrc(content)
