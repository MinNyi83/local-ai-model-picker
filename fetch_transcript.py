"""Fetch the full transcript for the video and save to transcript.txt."""
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

VIDEO_ID = "tek-IY9BRWc"


def main():
    ytt = YouTubeTranscriptApi()
    t = ytt.fetch(VIDEO_ID)
    lines = [f"[{s.start:.2f}] {s.text}" for s in t.snippets]
    out = "\n".join(lines)
    Path("transcript.txt").write_text(out, encoding="utf-8")
    print(f"Wrote {len(t.snippets)} snippets ({len(out)} chars) to transcript.txt")


if __name__ == "__main__":
    main()
"""
path">
D:\AI_Choice\fetch_transcript.py