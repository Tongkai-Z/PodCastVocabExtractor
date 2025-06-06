# scripts/download_transcribe_extract.py

import os
import subprocess
import whisper
import spacy
from wordfreq import word_frequency
import pandas as pd
from nltk.corpus import wordnet

def get_definition(word):
    synsets = wordnet.synsets(word)
    return synsets[0].definition() if synsets else "Definition not found" # type: ignore

def start():
# Directories
    audio_dir = "audio"
    transcript_dir = "transcripts"
    vocab_dir = "vocab_analysis"
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(transcript_dir, exist_ok=True)
    os.makedirs(vocab_dir, exist_ok=True)

    # Step 1: Download podcast
    episode_url = input("🎧 Enter podcast episode URL: ")
    output_template = os.path.join(audio_dir, "%(title)s.%(ext)s")

    print("⬇️  Downloading audio...")
    subprocess.run([
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--no-keep-video",
        "--rm-cache-dir",
        "--output", output_template,
        episode_url
    ])

    # Step 2: Find latest MP3
    mp3_files = [f for f in os.listdir(audio_dir) if f.endswith(".mp3")]
    latest_file = max(mp3_files, key=lambda f: os.path.getmtime(os.path.join(audio_dir, f)))
    audio_path = os.path.join(audio_dir, latest_file)
    print(f"🎙 Transcribing: {latest_file}")

    # Step 3: Transcribe
    model = whisper.load_model("small")
    result = model.transcribe(audio_path, language="English")
    transcript_text = result["text"]

    # Save transcript
    txt_filename = os.path.splitext(latest_file)[0] + ".txt"
    txt_path = os.path.join(transcript_dir, txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(transcript_text) # type: ignore
    print(f"📄 Transcript saved to: {txt_path}")

    # Step 4: Vocabulary extraction
    print("🧠 Extracting vocabulary...")
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(transcript_text) # type: ignore

    vocab_data = []

    for token in doc:
        if token.is_alpha and not token.is_stop:
            word = token.lemma_.lower()
            freq = word_frequency(word, 'en')
            if freq < 0.0001 and freq > 0 :  # Very uncommon word threshold
                vocab_data.append({"word": word, "context": token.sent.text.strip(), "frequency": freq})

    # Save to CSV
    csv_filename = os.path.splitext(latest_file)[0] + "_vocab.csv"
    csv_path = os.path.join(vocab_dir, csv_filename)
    df = pd.DataFrame(vocab_data).drop_duplicates(subset="word").sort_values(by="frequency")
    df["definition"] = df["word"].apply(get_definition)
    df.to_csv(csv_path, index=False)

    print(f"✅ Vocabulary list saved to: {csv_path}")
