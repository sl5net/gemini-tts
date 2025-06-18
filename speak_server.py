#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS  # <-- NEUE ZEILE 1
import subprocess
import shlex

# --- KONFIGURATION ---
MODEL_PATH = "/home/seeh/Downloads/de_DE-kerstin-low.onnx"
PORT = 5002
APLAY_CMD = "aplay -r 22050 -f S16_LE -t raw -"
# --------------------

app = Flask(__name__)
CORS(app)  # <-- NEUE ZEILE 2: CORS für die gesamte App aktivieren

@app.route('/speak', methods=['POST'])
def speak():
    print("\n--- NEUE ANFRAGE EINGEGANGEN ---")

    try:
        print("Request Headers:\n", request.headers)
        raw_data = request.get_data(as_text=True)
        print("Raw Request Data:", raw_data)

        data = request.get_json()
        if not data or 'text' not in data:
            print("!!! FEHLER: JSON-Daten ungültig.")
            return jsonify({"status": "error", "message": "Kein Text übermittelt"}), 400

        text_to_speak = data['text']
        print(f"Erfolgreich geparster Text: {text_to_speak[:80]}...")

        # Piper-Prozess
        piper_cmd = ["piper-tts", "--model", MODEL_PATH, "--output-raw"]
        piper_process = subprocess.Popen(piper_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = piper_process.communicate(input=text_to_speak.encode('utf-8'))

        if piper_process.returncode != 0:
            print("!!! FEHLER von Piper-TTS:", stderr.decode('utf-8'))
            return jsonify({"status": "error", "message": "Piper-TTS Fehler"}), 500

        # Audio-Prozess
        aplay_process = subprocess.Popen(shlex.split(APLAY_CMD), stdin=subprocess.PIPE)
        aplay_process.communicate(input=stdout)

        print("--- WIEDERGABE ERFOLGREICH BEENDET ---")
        return jsonify({"status": "success"})

    except Exception as e:
        print(f"!!! EIN ALLGEMEINER FEHLER IST AUFGETRETEN: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print(f"Finaler Sprach-Server (mit CORS) startet auf http://localhost:{PORT}")
    ssl_context = ('cert.pem', 'key.pem')
    app.run(host='127.0.0.1', port=PORT, ssl_context=ssl_context)
