# 🎧 Podcast Vocabulary Extractor

> A GUI tool that helps English learners extract new vocabulary from podcasts and export it to Anki.

![screenshot](iShot_2025-06-06_17.13.25.png) <!-- 可以替换成你的项目截图路径 -->

---

## ✨ Features

- 🎙️ Download and transcribe podcast audio (YouTube, Spotify, local MP3)
- 📜 Whisper-powered transcription (supports English & Chinese)
- 📚 Vocabulary extraction using spaCy + wordfreq
- 🔍 CEFR-based vocabulary difficulty analysis (A1–C2)
- 📝 Export to Anki (.apkg) and CSV
- 🔊 Built-in audio player with seekbar and time display
- 👀 Transcript viewer with Ctrl+F search
- 💻 Cross-platform PyQt5 GUI

---

## 📸 Interface Preview

> Main Features:
> - Paste link or select file
> - One-click transcription & extraction
> - Vocabulary table + transcript viewer
> - Play, pause and seek audio
> - Export to Anki + CEFR-level analysis

---

## 🛠 Tech Stack

| Component       | Technology           |
|----------------|----------------------|
| UI              | PyQt5                |
| Audio download  | yt-dlp               |
| Speech-to-text  | OpenAI Whisper       |
| NLP             | spaCy + wordfreq     |
| Vocabulary grading | CEFR (A1–C2)      |
| Export          | genanki (.apkg), CSV |
| Audio playback  | QMediaPlayer         |

---

## 📊 Difficulty Scoring (CEFR)

The app analyzes vocabulary and estimates overall difficulty based on CEFR levels:

