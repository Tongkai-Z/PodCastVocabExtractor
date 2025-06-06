import sys
import os
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QLineEdit, QFileDialog, QTextEdit, QTableWidget, QTableWidgetItem, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import subprocess
import whisper
import spacy
from wordfreq import word_frequency
import genanki
import pandas as pd
from PyQt5.QtGui import QPixmap, QMovie  # 加入 QMovie
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget  # 不用于音频但需导入
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWidgets import QSlider 
from PyQt5.QtWidgets import QSplitter


my_vocab_model = genanki.Model(
    1607392320,
    'My Vocabulary Card v3',
    fields=[
        {'name': 'Word'},
        {'name': 'DefinitionAndExamples'},
        {'name': 'Audio'},
        {'name': 'Phonetics'},
        {'name': 'VerbForms'},
        {'name': 'Image'},
        {'name': 'Context'},
    ],
    templates=[
        {
            'name': 'Card 1',
            'qfmt': '''
<div class="front">{{Word}} {{Audio}} <br> {{VerbForms}}</div>
''',
            'afmt': '''
<div class="front">{{Word}} {{Audio}} <br> {{VerbForms}}</div>
<hr id="answer">
<div class="img" id="img_div">{{Image}}</div>
<hr id="image_hr">
<div id="to_replace">
{{DefinitionAndExamples}}
</div>
<script>
    document.getElementById('to_replace').innerHTML =
    document.getElementById('to_replace').innerHTML.replace(/[#]([^#]+)[#]/ig, "<b>$1</b>");
    
    if (document.getElementById('img_div').innerHTML.toString().length == 0)
    {
        document.getElementById('image_hr').style.display = 'none';
    }
</script>
<br>
<div style='font-family: "Arial"; font-size: 20px;'>{{Context}}</div>
'''
        }
    ],
    css='''
.card {
  font-family: arial;
  font-size: 20px;
  color: black;
  background-color: white;
  text-align: left;
}

.front {
  text-align: center;
}

.do_not_show {
  display: none;
}

.img {
  text-align: center;
}

img {
  padding-left: 5px;
  padding-right: 5px;
}

b {
  color: black;
}

i {
  color: grey;
}

.nightMode b {
  color: #8ab4f8;
}

.nightMode i {
  color: silver;
}

.nightMode a {
  color: #8ab4f8;
}
'''
)

class PodcastVocabApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Podcast Vocabulary Extractor")
        self.resize(800, 600)

        self.audio_path = "app_audio"
        self.transcript_path = "app_transcripts/transcript.txt"
        self.vocab_data = []
        self.audio_title = None
        self.anki_dir = "anki_exports"
        self.seen_path = os.path.join(self.anki_dir, "seen_words.csv")
        os.makedirs(self.anki_dir, exist_ok=True)
        self.transcript_viewer = QTextEdit()
        self.transcript_viewer.setReadOnly(True)
        self.transcript_viewer.setPlaceholderText("Transcript will appear here after transcription...")
        self.transcript_viewer.setStyleSheet("""
            font-family: monospace;
            font-size: 13px;
            background-color: black;
            color: white;
            border: 1px solid #555;
            padding: 4px;
        """)
        # Layouts
        layout = QVBoxLayout()
        # App header (logo + title)
        header_layout = QHBoxLayout()

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(32, 32)
        self.logo_label.setScaledContents(True)
        self.logo_label.setStyleSheet("margin-right: 8px;")
        self.movie = QMovie("logo.gif")
        self.logo_label.setMovie(self.movie)
        self.movie.start()

        self.header_label = QLabel("Podcast Vocabulary Extractor")
        self.header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # type: ignore
        self.header_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 4px;")
        header_layout.addWidget(self.logo_label)
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(80)
        self.log_area.setStyleSheet("font-family: monospace; font-size: 12px; background-color: black; color: white; margin-bottom: 12px;")
        layout.addWidget(self.log_area)

        # Link input
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("Paste YouTube/Spotify audio link here...")
        download_button = QPushButton("Download")
        download_button.clicked.connect(self.download_audio)

        link_layout = QHBoxLayout()
        link_layout.addWidget(self.link_input)
        link_layout.addWidget(download_button)

        # File select
        file_button = QPushButton("Choose Local MP3")
        file_button.clicked.connect(self.select_file)
        self.file_label = QLabel("No file selected")

        file_layout = QHBoxLayout()
        file_layout.addWidget(file_button)
        file_layout.addWidget(self.file_label)

        # Action buttons
        open_output_button = QPushButton("📂 Open Output Folder")
        open_output_button.clicked.connect(self.open_output_folder)

        transcribe_button = QPushButton("Transcribe")
        transcribe_button.clicked.connect(self.transcribe_audio)

        extract_button = QPushButton("Extract Vocabulary")
        extract_button.clicked.connect(self.extract_vocab)

        export_button = QPushButton("Export to Anki / CSV")
        export_button.clicked.connect(self.export_output)

        # Output area
        self.output_table = QTableWidget()
        self.output_table.setColumnCount(3)
        self.output_table.setHorizontalHeaderLabels(["Word", "Frequency", "Context"])

        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: white;")
        self.total_time_label.setStyleSheet("color: white;")

        # Add widgets to layout
        layout.addLayout(link_layout)
        layout.addLayout(file_layout)
        layout.addWidget(transcribe_button)
        layout.addWidget(extract_button)
        layout.addWidget(export_button)
        layout.addWidget(open_output_button)
        # search bar
        # 查找框初始化（隐藏）
        self.find_bar = QLineEdit()
        self.find_bar.setPlaceholderText("Find word in transcript...")
        self.find_bar.setStyleSheet("background-color: #222; color: white; padding: 4px; border: 1px solid #555;")
        self.find_bar.hide()
        self.find_bar.returnPressed.connect(self.find_text)
        layout.addWidget(self.find_bar)

        # splitter
        # 包含词汇表格和转录区的可分割区域
        splitter = QSplitter(Qt.Vertical) # type: ignore

        # 上面放词汇表
        splitter.addWidget(self.output_table)

        # 下面放 transcript 区（加上标题 label）
        transcript_container = QWidget()
        transcript_layout = QVBoxLayout()
        transcript_layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Transcript Preview:")
        label.setStyleSheet("color: white; font-weight: bold; margin-top: 8px;")

        transcript_layout.addWidget(label)
        transcript_layout.addWidget(self.transcript_viewer)
        transcript_container.setLayout(transcript_layout)

        splitter.addWidget(transcript_container)

        # 设置默认高度比例
        splitter.setStretchFactor(0, 3)  # table
        splitter.setStretchFactor(1, 2)  # transcript

        layout.addWidget(splitter)

        # Media Player
        self.player = QMediaPlayer()
        self.play_button = QPushButton("▶Play")
        self.pause_button = QPushButton("⏸Pause")
        self.progress_slider = QSlider(Qt.Horizontal) # type: ignore
        self.progress_slider.setRange(0, 100)

        # 控制逻辑绑定
        self.play_button.clicked.connect(self.play_audio)
        self.pause_button.clicked.connect(self.pause_audio)
        self.progress_slider.sliderMoved.connect(self.seek_position)

        # 播放器 UI Layout
        player_layout = QHBoxLayout()
        player_layout.addWidget(self.play_button)
        player_layout.addWidget(self.pause_button)
        player_layout.addWidget(self.current_time_label)
        player_layout.addWidget(self.progress_slider)
        player_layout.addWidget(self.total_time_label)

        layout.addLayout(player_layout)

        # 定时器用于更新进度条
        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_slider)


        self.setLayout(layout)

        # init common word set
        self.common_words_set = set()
        for level in ['a1', 'a2']:
            with open(f"cefr_lists/{level}.txt", "r", encoding="utf-8") as f:
                self.common_words_set.update(w.strip().lower() for w in f if w.strip())


    def download_audio(self):
        self.log_area.append("[INFO] Starting download...")
        url = self.link_input.text().strip()
        
        if not url:
            self.file_label.setText("❌ No link provided.")
            return
        
        os.makedirs(self.audio_path, exist_ok=True)

        title_cmd = ["yt-dlp", "--get-filename", "-o", "%(title)s", url]
        try:
            title = subprocess.check_output(title_cmd).decode("utf-8").strip()
            output_path = os.path.join(self.audio_path, f"{title}.mp3")
            self.audio_title = title
            subprocess.run([
                "yt-dlp",
                "--extract-audio",
                "--audio-format", "mp3",
                "--no-keep-video",
                "--rm-cache-dir",
                "--output", output_path,
                url
            ])
            self.audio_path = output_path
            self.file_label.setText(f"✅ Downloaded: {self.audio_path}")
            self.log_area.append(f"[SUCCESS] Downloaded audio: {self.audio_path}")
        except subprocess.CalledProcessError:
            self.log_area.append("[ERROR] Download failed.")
            self.file_label.setText("❌ Download failed.")

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select MP3 File", "", "Audio Files (*.mp3)")
        if file_path:
            self.audio_path = file_path
            self.file_label.setText(f"Selected: {file_path}")
            self.audio_title = os.path.splitext(os.path.basename(file_path))[0]

    def transcribe_audio(self):
        self.log_area.append("[INFO] Starting transcription...")
        if not self.audio_path:
            self.file_label.setText("❌ No audio file to transcribe.")
            return
        try:
            self.file_label.setText("⏳ Transcribing...")
            model = whisper.load_model("small")
            result = model.transcribe(self.audio_path)
            os.makedirs(os.path.dirname(self.transcript_path), exist_ok=True)
            with open(self.transcript_path, "w", encoding="utf-8") as f:
                f.write(result["text"]) # type: ignore
            self.file_label.setText("✅ Transcription completed")
            self.log_area.append("[SUCCESS] Transcription completed")
            self.transcript_viewer.setPlainText(result["text"])  # type: ignore
        except Exception as e:
            self.file_label.setText(f"❌ Transcription failed: {e}")
            self.log_area.append(f"[ERROR] Transcription failed: {e}")

    def extract_vocab(self):
        self.log_area.append("[INFO] Extracting vocabulary...")
        try:
            self.file_label.setText("⏳ Extracting vocabulary...")
            with open(self.transcript_path, "r", encoding="utf-8") as f:
                text = f.read()

            nlp = spacy.load("en_core_web_sm")
            doc = nlp(text)
            total_count = 0
            words = {}
            for token in doc:
                if token.is_alpha and not token.is_stop:
                    word = token.lemma_.lower()
                    freq = word_frequency(word, 'en')
                    total_count += 1
                    if word not in words:
                        if freq < 0.0001 and freq > 0 :
                            words[word] = {
                                'freq': freq,
                                'context': token.sent.text.strip()
                            }

            sorted_words = sorted(words.items(), key=lambda x: x[1]['freq'])
            self.vocab_data = [(w, v['freq'], v['context']) for w, v in sorted_words]

            self.output_table.setRowCount(len(self.vocab_data))
            for row, entry in enumerate(self.vocab_data):
                for col, value in enumerate(entry):
                    self.output_table.setItem(row, col, QTableWidgetItem(str(value)))

            self.file_label.setText("✅ Vocabulary extracted")
            self.log_area.append(f"[SUCCESS] Extracted {len(self.vocab_data)} words")
            difficulty = self.calculate_difficulty_score(total_count)
            self.log_area.append(f"[INFO] Estimated difficulty: {difficulty}")
        except Exception as e:
            self.file_label.setText(f"❌ Vocabulary extraction failed: {e}")
            self.log_area.append(f"[ERROR] Vocabulary extraction failed: {e}")

    def export_output(self):
        self.log_area.append("[INFO] Exporting to Anki and CSV...")
        try:
            csv_path = f"output/{self.audio_title}_words.csv"
            apkg_path = f"output/{self.audio_title}_cards.apkg"
            os.makedirs("output", exist_ok=True)
            # Load seen words
            if os.path.exists(self.seen_path):
                seen_df = pd.read_csv(self.seen_path)
                seen_words = set(seen_df["word"])
            else:
                seen_words = set()

            with open(csv_path, "w", newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Word", "Frequency", "Context"])
                for row in self.vocab_data:
                    writer.writerow(row)

            model = my_vocab_model

            deck = genanki.Deck(2059400110, 'All Ears English Vocabulary')
            for word, _, context in self.vocab_data:
                if word in seen_words:
                     continue
                note = genanki.Note(
                    model=model,
                    fields=[word, "", "", "", "", "", context]
                )
                deck.add_note(note)
            
            # Save seen words
            seen_df = pd.DataFrame({"word": [w for w, _, _ in self.vocab_data]})
            if seen_words:
                seen_df = pd.concat([seen_df, pd.read_csv(self.seen_path)], ignore_index=True).drop_duplicates(subset="word")
            seen_df.to_csv(self.seen_path, index=False)

            genanki.Package(deck).write_to_file(apkg_path)
            self.file_label.setText("✅ Exported CSV and Anki deck")
            self.log_area.append(f"[SUCCESS] Exported to {csv_path} and {apkg_path}")
        except Exception as e:
            self.file_label.setText(f"❌ Export failed: {e}")
            self.log_area.append(f"[ERROR] Export failed: {e}")

    def open_output_folder(self):
        path = os.path.abspath("output")
        if not os.path.exists(path):
            os.makedirs(path)
        subprocess.run(["open", path] if sys.platform == "darwin" else ["xdg-open", path] if sys.platform.startswith("linux") else ["explorer", path], check=False)

    def play_audio(self):
        if self.audio_path and os.path.exists(self.audio_path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(self.audio_path))))
            self.player.play()
            self.timer.start()
            self.log_area.append("[INFO] Playing audio...")

    def pause_audio(self):
        self.player.pause()
        self.log_area.append("[INFO] Paused audio.")

    def update_slider(self):
        if self.player.duration() > 0:
            pos = self.player.position()
            dur = self.player.duration()
            progress = int((pos / dur) * 100)
            self.progress_slider.setValue(progress)

            self.current_time_label.setText(self.format_ms(pos))
            self.total_time_label.setText(self.format_ms(dur))

    def format_ms(self, ms):
        seconds = int(ms / 1000)
        minutes = int(seconds / 60)
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def seek_position(self, value):
        if self.player.duration() > 0:
            new_pos = int((value / 100) * self.player.duration())
            self.player.setPosition(new_pos)
    
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_F: # type: ignore
            self.show_find_bar()

    def show_find_bar(self):
        self.find_bar.show()
        self.find_bar.setFocus()

    def find_text(self):
        keyword = self.find_bar.text()
        if not keyword:
            return

        cursor = self.transcript_viewer.textCursor()
        document = self.transcript_viewer.document()

        # 从当前光标位置开始查找
        found = document.find(keyword, cursor) # type: ignore

        if found.isNull():
            # 从头开始查找
            cursor.setPosition(0)
            found = document.find(keyword, cursor) # type: ignore

        if found.isNull():
            self.log_area.append(f"[INFO] '{keyword}' not found in transcript.")
        else:
            self.transcript_viewer.setTextCursor(found)
            self.transcript_viewer.setFocus()

    def calculate_difficulty_score(self, total_words):
        low_freq_count = len(self.vocab_data)
        if total_words == 0:
            return "Unknown"
        for word, freq, _ in self.vocab_data:
            if not self.is_difficult_word(word, freq):
                low_freq_count -= 1

        score = (low_freq_count / total_words) * 100
        if score < 5:
            level = "🟢 Easy (Beginner)"
        elif score < 10:
            level = "🟡 Medium (Intermediate)"
        else:
            level = "🔴 Hard (Advanced)"

        return f"{level} — {score:.1f}% low-frequency words"
    def is_difficult_word(self, word, freq):
        if len(word) < 4:
            return False
        if freq >= 0.00005:
            return False
        if word in self.common_words_set:
            return False
        return True

    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PodcastVocabApp()
    window.show()
    sys.exit(app.exec_())
