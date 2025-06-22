#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
from slugify import slugify
import shlex
import subprocess
import wave
import datetime
import argparse
import re

# --- install
# read
# - here: https://github.com/sl5net/gemini-tts
# - https://github.com/un33k/python-slugify
# source venv/bin/activate
# pip install python-slugify
#
# ---

# --- KONFIGURATION ---
MODEL_PATH = "/home/seeh/Downloads/de_DE-kerstin-low.onnx"
PORT = 5002

# Audio-Parameter (müssen zur config.json des Modells passen!)
# Für die meisten Piper-Modelle sind diese Werte korrekt:
SAMPLE_RATE = 22050
SAMPLE_WIDTH = 2  # 2 bytes = 16-bit
CHANNELS = 1      # Mono
MY_STOPWORDS = ['das', 'ist', 'ein', 'mit', 'und', 'a', 'is', 'with', 'the']
# --------------------

def create_slug(text, min_word_len=4):
    # https://github.com/un33k/python-slugify
    initial_slug = slugify(text, stopwords=MY_STOPWORDS, max_length=80)



    # 2. Kurze Wörter herausfiltern
    words = initial_slug.split('-')
    long_words = [w for w in words if len(w) >= min_word_len]

    return '-'.join(long_words)

parser = argparse.ArgumentParser()
parser.add_argument(
    '--no-save',
    action='store_false',
    dest='save',
    help="Audio nur ausgeben, nicht speichern."
)
args = parser.parse_args()

if args.save:
    print("Modus: Speichern & Ausgeben")
    # Dein Code hier
else:
    print("Modus: Nur Ausgeben")
    # Dein Code hier

app = Flask(__name__)
CORS(app)

# def slugify(text, max_length=50):
    # Ersetzt Umlaute und Sonderzeichen
#     text = text.lower()
#     text = re.sub(r'[\s_]+', '-', text) # Leerzeichen/Unterstriche -> -
#     text = re.sub(r'[^\w-]', '', text)  # Entfernt ungültige Zeichen
#     return text[:max_length]

@app.route('/speak', methods=['POST'])
def speak():
    print("\n--- NEUE ANFRAGE EINGEGANGEN ---")

    try:
        data = request.get_json()
        if not data or 'text' not in data:
            print("!!! FEHLER: JSON-Daten ungültig.")
            return jsonify({"status": "error", "message": "Kein Text übermittelt"}), 400

        text_to_speak = data['text']
        print(f"Erfolgreich geparster Text: {text_to_speak[:80]}...")

        if args.save:
            # 1. Piper-Prozess: Audio im Speicher erzeugen (output-raw)
            # Dadurch fangen wir die rohen Audiodaten in 'stdout' auf.
            piper_cmd = ["piper-tts", "--model", MODEL_PATH, "--output-raw"]
            piper_process = subprocess.Popen(
                piper_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

        # Jetzt werden 'stdout' und 'stderr' wieder korrekt befüllt
        raw_audio_data, stderr = piper_process.communicate(input=text_to_speak.encode('utf-8'))

        if piper_process.returncode != 0:
            print("!!! FEHLER von Piper-TTS:", stderr.decode('utf-8'))
            return jsonify({"status": "error", "message": "Piper-TTS Fehler"}), 500

        # Wenn keine Audiodaten erzeugt wurden, abbrechen
        if not raw_audio_data:
            print("!!! FEHLER: Piper hat keine Audiodaten erzeugt.")
            return jsonify({"status": "error", "message": "Leere Audioausgabe von Piper"}), 500

        print("Audio erfolgreich generiert, starte Wiedergabe...")

        # 2. Audio-Prozess: Die rohen Daten direkt an 'aplay' zur Wiedergabe senden
        aplay_cmd = f"aplay -r {SAMPLE_RATE} -f S16_LE -t raw -"
        aplay_process = subprocess.Popen(shlex.split(aplay_cmd), stdin=subprocess.PIPE)
        aplay_process.communicate(input=raw_audio_data)

        print("Wiedergabe beendet.")

        # 3. Speichern der Audiodatei mit Zeitstempel
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        ###############################
        ###############################
        ###############################
        slug = create_slug(text_to_speak, min_word_len=5)
        ###############################
        ###############################
        ###############################

        output_filename = f"{timestamp}_{slug}.wav"

        output_filename_txt = f"{timestamp}_{slug}.txt"

        # output_filename_txt = f"{timestamp}.txt"




        with open(output_filename_txt, "w") as text_file:
            text_file.write(text_to_speak)


        try:
            with wave.open(output_filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(SAMPLE_WIDTH)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(raw_audio_data)
            print(f"Audio erfolgreich in '{output_filename}' gespeichert.")
        except Exception as e:
            print(f"!!! FEHLER beim Speichern der WAV-Datei: {e}")
            # Dies ist kein kritischer Fehler, also läuft der Request weiter

        print("--- ANFRAGE ERFOLGREICH BEENDET ---")
        return jsonify({"status": "success", "file_saved": output_filename})

    except Exception as e:
        print(f"!!! EIN ALLGEMEINER FEHLER IST AUFGETRETEN: {e}")
        # Die traceback-Library hilft bei der Fehlersuche
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print(f"Finaler Sprach-Server (mit CORS) startet auf https://127.0.0.1:{PORT}")
    try:
        ssl_context = ('cert.pem', 'key.pem')
        app.run(host='127.0.0.1', port=PORT, ssl_context=ssl_context)
    except FileNotFoundError:
        print("\n--- WARNUNG ---")
        print("SSL-Zertifikatsdateien (cert.pem, key.pem) nicht gefunden.")
        print(f"Server startet unverschlüsselt auf http://127.0.0.1:{PORT}")
        app.run(host='127.0.0.1', port=PORT)
