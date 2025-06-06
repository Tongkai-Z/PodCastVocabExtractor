from download_and_transcribe import start as download_transcribe
from anki_exporter import export_to_anki


print("🎙️ Starting Podcast Vocabulary Learning Tool...")

# Step 1: Download and transcribe audio
download_transcribe()

# Step 2: Export new vocabulary to Anki
export_to_anki()

print("✅ All tasks completed successfully!")