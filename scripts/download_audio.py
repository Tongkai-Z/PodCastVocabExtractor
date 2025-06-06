# scripts/download_audio.py

import os
import subprocess

# Create audio directory if not exists
audio_dir = "audio"
os.makedirs(audio_dir, exist_ok=True)

# Paste your episode URL here (can be from YouTube, RSS page, or open MP3 link)
episode_url = input("Enter podcast episode URL: ")

# Set output file name pattern
output_template = os.path.join(audio_dir, "%(title)s.%(ext)s")

# Run yt-dlp
subprocess.run([
    "yt-dlp",
    "--extract-audio",
    "--audio-format", "mp3",
    "--no-keep-video",              # ✅ Delete video after audio extraction
    "--rm-cache-dir",               # ✅ Clean yt-dlp cache
    "--output", output_template,
    episode_url
])
