# Gemini-TTS: Gemini-Antworten automatisch vorlesen lassen

Dieses Projekt ermöglicht es, Antworten von Google Gemini (und Google AI Studio) automatisch über eine lokale, qualitativ hochwertige Text-to-Speech (TTS) Engine (`piper-tts`) auf Manjaro Linux vorlesen zu lassen.

## Was ist das Ziel?

Das Ziel ist eine vollautomatische, freihändige Bedienung von Gemini, bei der die Antworten der KI nicht gelesen werden müssen, sondern direkt als Sprachausgabe erfolgen. Dies geschieht komplett offline (bis auf die Gemini-Seite selbst) und kostenlos.

## Die Komponenten

Das System besteht aus zwei Hauptteilen, die über eine "Brücke" miteinander kommunizieren:

1.  **Das Backend (Lokaler Server):**
    *   Ein kleiner Python-Server, der auf deinem PC läuft.
    *   Er verwendet das **Flask**-Framework, um auf Netzwerkanfragen zu lauschen.
    *   Er nutzt **piper-tts**, um Text in gesprochene Sprache umzuwandeln.
    *   Er läuft mit einem selbst-signierten **HTTPS/SSL-Zertifikat**, um mit sicheren Webseiten kommunizieren zu können.

2.  **Das Frontend (Browser-Skript):**
    *   Die Browser-Erweiterung **Tampermonkey** (nicht Greasemonkey!).
    *   Ein **Userscript**, das speziell auf der Gemini-Webseite läuft.
    *   Es beobachtet die Seite, erkennt neue Antworten der KI, extrahiert den Text und sendet ihn an das Backend.

---

## Voraussetzungen

Bevor du beginnst, stelle sicher, dass die folgenden Programme auf deinem Manjaro-System installiert sind:

1.  **piper-tts:** Die TTS-Engine.
    ```bash
    # Über das AUR, z.B. mit yay
    yay -S piper-tts
    ```

2.  **Ein deutsches Stimm-Modell für Piper:**
    *   Lade dir eine Stimme herunter, z.B. die "kerstin"-Stimme von [Hugging Face](https://huggingface.co/rhasspy/piper-voices/tree/main/de/de_DE/kerstin/low).
    *   Du benötigst die `.onnx`- und die `.onnx.json`-Datei.
    *   Speichere sie an einem bekannten Ort, z.B. `~/Downloads/`.

3.  **Python 3 und pip:** Ist auf Manjaro standardmäßig vorinstalliert.

4.  **Ein Webbrowser:** z.B. Firefox oder Chrome.

5.  **Die Tampermonkey Browser-Erweiterung:**
    *   **Wichtig:** Verwende **Tampermonkey**, nicht das originale Greasemonkey, da es besser mit lokalen HTTPS-Zertifikaten umgehen kann.
    *   [Tampermonkey für Firefox](https://addons.mozilla.org/de/firefox/addon/tampermonkey/)
    *   [Tampermonkey für Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)

---

## Installation Schritt-für-Schritt

### Teil 1: Das Backend (Server) einrichten

1.  **Projektordner erstellen:**
    ```bash
    mkdir -p ~/projects/py/speak_server
    cd ~/projects/py/speak_server
    ```

2.  **Python Virtual Environment erstellen:**
    ```bash
    python -m venv venv
    ```

3.  **Virtuelle Umgebung aktivieren:**
    ```bash
    source venv/bin/activate
    ```
    *(Dein Terminal-Prompt sollte sich ändern und `(venv)` am Anfang anzeigen.)*

4.  **Benötigte Python-Pakete installieren:**
    ```bash
    pip install Flask Flask-CORS
    ```

5.  **SSL-Zertifikat für HTTPS erstellen:**
    ```bash
    openssl req -x509 -newkey rsa:4096 -nodes -keyout key.pem -out cert.pem -days 365
    ```
    *(Drücke bei allen Fragen einfach `Enter`.)*

6.  **Die Server-Datei `speak_server.py` erstellen:**
    Erstelle eine neue Datei mit dem Namen `speak_server.py` und füge den folgenden Code ein:

    ```python
    #!/usr/bin/env python3
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import subprocess
    import shlex

    # --- KONFIGURATION (Hier anpassen!) ---
    MODEL_PATH = "/home/seeh/Downloads/de_DE-kerstin-low.onnx" # <-- Passe den Pfad zu deiner .onnx-Datei an!
    PORT = 5002
    APLAY_CMD = "aplay -r 22050 -f S16_LE -t raw -"
    # ----------------------------------------

    app = Flask(__name__)
    CORS(app) # Aktiviert Cross-Origin Resource Sharing

    @app.route('/speak', methods=['POST'])
    def speak():
        try:
            data = request.get_json()
            if not data or 'text' not in data:
                return jsonify({"status": "error", "message": "Kein Text übermittelt"}), 400

            text_to_speak = data['text']
            
            piper_cmd = ["piper-tts", "--model", MODEL_PATH, "--output-raw"]
            piper_process = subprocess.Popen(piper_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = piper_process.communicate(input=text_to_speak.encode('utf-8'))

            if piper_process.returncode != 0:
                print("Piper-TTS Fehler:", stderr.decode('utf-8'))
                return jsonify({"status": "error", "message": "Piper-TTS Fehler"}), 500

            aplay_process = subprocess.Popen(shlex.split(APLAY_CMD), stdin=subprocess.PIPE)
            aplay_process.communicate(input=stdout)

            return jsonify({"status": "success"})
        except Exception as e:
            print(f"Ein allgemeiner Fehler ist aufgetreten: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    if __name__ == '__main__':
        print(f"Finaler Sprach-Server (mit HTTPS und CORS) startet auf https://localhost:{PORT}")
        ssl_context = ('cert.pem', 'key.pem')
        app.run(host='127.0.0.1', port=PORT, ssl_context=ssl_context)

    ```
    **Wichtig:** Passe den `MODEL_PATH` am Anfang des Skripts an den tatsächlichen Speicherort deines Piper-Modells an!

### Teil 2: Das Frontend (Tampermonkey-Skript) einrichten

1.  Klicke auf das Tampermonkey-Icon in deinem Browser und wähle "Neues Skript erstellen...".
2.  Lösche den gesamten Vorlagen-Code.
3.  Füge den folgenden Code ein:

    ```javascript
    // ==UserScript==
    // @name         Gemini to Piper TTS (v3.1 - Final)
    // @namespace    http://tampermonkey.net/
    // @version      3.1
    // @description  Liest die neueste Antwort von Gemini/AI Studio vor.
    // @author       Seeh & AI
    // @match        https://aistudio.google.com/prompts/*
    // @match        https://gemini.google.com/app/*
    // @connect      localhost
    // @grant        GM_xmlhttpRequest
    // @run-at       document-idle
    // ==/UserScript==

    (function() {
        'use strict';

        const SERVER_URL = 'https://localhost:5002/speak';
        const DEBOUNCE_DELAY = 1500;

        console.log('[Piper TTS v3.1] Skript ist aktiv und bereit.');

        let speechTimer = null;
        let lastTextContent = "";

        const onMutation = () => {
            const allAnswerElements = document.querySelectorAll('div[data-turn-role="Model"] ms-cmark-node');
            if (allAnswerElements.length === 0) return;

            const latestAnswerElement = allAnswerElements[allAnswerElements.length - 1];
            const currentText = latestAnswerElement.innerText;

            if (currentText === lastTextContent) {
                return;
            }
            
            lastTextContent = currentText;
            clearTimeout(speechTimer);

            speechTimer = setTimeout(() => {
                console.log('[Piper TTS v3.1] Text scheint vollständig. Sende zum Server:', currentText);
                sendTextToServer(currentText);
            }, DEBOUNCE_DELAY);
        };

        const sendTextToServer = (text) => {
            const cleanedText = text.trim();
            if (!cleanedText) {
                console.log('[Piper TTS v3.1] Leerer Text wird ignoriert.');
                return;
            }

            GM_xmlhttpRequest({
                method: 'POST',
                url: SERVER_URL,
                data: JSON.stringify({ text: cleanedText }),
                headers: { 'Content-Type': 'application/json' },
                onload: (response) => console.log('[Piper TTS v3.1] Server-Antwort:', response.status),
                onerror: (response) => console.error('[Piper TTS v3.1] Server-Fehler:', response)
            });
        };

        const observer = new MutationObserver(onMutation);
        observer.observe(document.body, { childList: true, subtree: true });

    })();
    ```
4.  Speichere das Skript (Datei -> Speichern).

---

## Anwendung

1.  **Server starten:**
    *   Öffne ein Terminal.
    *   Navigiere zum Projektordner: `cd ~/projects/py/speak_server`
    *   Aktiviere die Umgebung: `source venv/bin/activate`
    *   Starte den Server: `python3 speak_server.py`
    *   Lass dieses Terminalfenster laufen.

2.  **Einmalige Browser-Konfiguration:**
    *   Öffne einen neuen Tab in deinem Browser.
    *   Gehe zur Adresse `https://localhost:5002/`.
    *   Dein Browser wird eine große Sicherheitswarnung anzeigen. Das ist normal.
    *   Klicke auf "Erweitert" und dann auf "Ausnahme hinzufügen" oder "Trotzdem fortfahren", um deinem Browser zu sagen, dass er diesem Zertifikat vertrauen soll.

3.  **Gemini nutzen:**
    *   Gehe zur Gemini-Webseite. Das Tampermonkey-Skript wird automatisch geladen.
    *   Stelle eine Frage.
    *   Nachdem die KI ihre Antwort fertig generiert hat, wird sie nach einer kurzen Pause automatisch vorgelesen.
