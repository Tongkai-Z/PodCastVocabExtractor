# scripts/transcribe_audio.py

import whisper
import os

# Load Whisper model (choose from: tiny, base, small, medium, large)
model = whisper.load_model("small")

audio_dir = "audio"
output_dir = "transcripts"
os.makedirs(output_dir, exist_ok=True)

# Loop through all MP3 files in the audio directory
for filename in os.listdir(audio_dir):
    if filename.endswith(".mp3"):
        audio_path = os.path.join(audio_dir, filename)
        print(f"Transcribing {filename}...")

        result = model.transcribe(audio_path, language="English")

        # Save transcript as .txt
        transcript_txt_path = os.path.join(output_dir, filename.replace(".mp3", ".txt"))
        with open(transcript_txt_path, "w", encoding="utf-8") as f:
            f.write(result["text"]) # type: ignore

        print(f"Saved transcript to {transcript_txt_path}")
