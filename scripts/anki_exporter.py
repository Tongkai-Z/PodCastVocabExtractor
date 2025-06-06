# scripts/anki_exporter.py

import genanki
import pandas as pd
import os

import genanki

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


def export_to_anki():
    """
    Exports new vocabulary words to Anki deck.
    - Reads latest vocab CSV from 'vocab_analysis' directory.
    - Filters out words already seen in Anki.
    - Creates a new Anki deck with Word, Context, and Definition fields.
    - Saves the deck as an .apkg file in 'anki_exports' directory.
    - Updates seen words record.
    """
    
    print("📦 Exporting new vocabulary to Anki...")
    # Paths
    vocab_dir = "vocab_analysis"
    anki_dir = "anki_exports"
    seen_path = os.path.join(anki_dir, "seen_words.csv")
    os.makedirs(anki_dir, exist_ok=True)

    # Load latest vocab CSV
    csv_files = [f for f in os.listdir(vocab_dir) if f.endswith("_vocab.csv")]
    latest_csv = max(csv_files, key=lambda f: os.path.getmtime(os.path.join(vocab_dir, f)))
    csv_path = os.path.join(vocab_dir, latest_csv)
    df = pd.read_csv(csv_path)

    # Load seen words
    if os.path.exists(seen_path):
        seen_df = pd.read_csv(seen_path)
        seen_words = set(seen_df["word"])
    else:
        seen_words = set()

    # Filter new words
    df_new = df[~df["word"].isin(seen_words)]

    if df_new.empty:
        print("🟡 No new words to add to Anki.")
        exit()

    # Deck ID is consistent for merging
    deck = genanki.Deck(
        2059400110,
        'All Ears English Vocabulary'
    )

    # Add notes
    for _, row in df_new.iterrows():
        word = row['word']
        context = f"{row['context']} (freq: {row['frequency']:.10f})"
        # definition = row.get('definition', 'Definition not found')
        note = genanki.Note(model=my_vocab_model, fields=[word, "", "", "", "", "", context])
        deck.add_note(note)

    # Save .apkg file
    apkg_name = os.path.splitext(latest_csv)[0] + ".apkg"
    apkg_path = os.path.join(anki_dir, apkg_name)
    genanki.Package(deck).write_to_file(apkg_path)
    print(f"✅ Anki deck exported to: {apkg_path}")

    # Update seen words record
    df_seen_new = pd.DataFrame(df_new[["word"]])
    if seen_words:
        df_seen_new = pd.concat([seen_df, df_seen_new], ignore_index=True)
    df_seen_new.drop_duplicates().to_csv(seen_path, index=False)
    print(f"📚 Word list updated: {seen_path}")


# if run this file
if __name__ == "__main__":
    export_to_anki()