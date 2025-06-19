# Gemini-TTS: Antworten von Gemini automatisch vorlesen lassen

Dieses Projekt ermöglicht es, Antworten von Google Gemini (und dem Google AI Studio) automatisch von einer lokalen, hochqualitativen Text-to-Speech (TTS) Engine (`piper-tts`) auf Manjaro Linux vorlesen zu lassen.

## Ziel

Das Ziel ist eine vollautomatische, freihändige Bedienung von Gemini, bei der die Antworten der KI als gesprochene Audioausgabe geliefert werden, anstatt sie lesen zu müssen. Dieser Prozess ist komplett kostenlos und funktioniert offline (mit Ausnahme der Gemini-Website selbst).

## Die Komponenten

Das System besteht aus zwei Hauptteilen, die über eine "Brücke" kommunizieren:

1.  **Das Backend (Lokaler Server):**
    *   Ein kleiner Python-Server, der auf deinem PC läuft (`speak_server.py`).
    *   Er nutzt das **Flask**-Framework, um auf Netzwerkanfragen zu lauschen.
    *   Er verwendet **piper-tts**, um Text in gesprochene Sprache umzuwandeln.
    *   Er läuft mit einem selbst-signierten **HTTPS/SSL-Zertifikat**, um mit sicheren Webseiten kommunizieren zu können.

2.  **Das Frontend (Browser-Skripte):**
    *   Die **Tampermonkey** Browser-Erweiterung.
    *   Zwei **Userscripts** (`tampermonkey_v4.js` und `TTS-ButtonTest.js`), die als separate Dateien vorliegen.
    *   Das Hauptskript überwacht die Gemini-Seite, erkennt neue, **vollständig generierte** Antworten und sendet deren Text an das Backend.

---

## Voraussetzungen

Bevor du beginnst, stelle sicher, dass die folgende Software auf deinem Manjaro-System installiert ist:

1.  **piper-tts:** Die TTS-Engine.
    ```bash
    # Über das AUR, z.B. mit yay
    yay -S piper-tts
    ```

2.  **Ein deutsches Sprachmodell für Piper:**
    *   Lade eine Stimme herunter, zum Beispiel die "kerstin"-Stimme von [Hugging Face](https://huggingface.co/rhasspy/piper-voices/tree/main/de/de_DE/kerstin/low).
    *   Du benötigst sowohl die `.onnx`- als auch die `.onnx.json`-Datei.
    *   Speichere sie an einem bekannten Ort, z. B. `~/Downloads/`.

3.  **Python 3 und pip:** Sind auf Manjaro standardmäßig installiert.

4.  **Ein Webbrowser:** z.B. Firefox oder Chrome.

5.  **Die Tampermonkey Browser-Erweiterung:**
    *   [Tampermonkey für Firefox](https://addons.mozilla.org/de/firefox/addon/tampermonkey/)
    *   [Tampermonkey für Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)

---

## Schritt-für-Schritt-Anleitung

### Teil 1: Backend (Server) einrichten

1.  **Projektordner erstellen und navigieren:**
    ```bash
    # Erstelle den Ordner, falls noch nicht geschehen
    mkdir -p ~/projects/py/speak_server
    cd ~/projects/py/speak_server
    ```
    Stelle sicher, dass alle Projektdateien (`speak_server.py`, `tampermonkey_v4.js` etc.) in diesem Ordner liegen.

2.  **Virtuelle Python-Umgebung erstellen:**
    ```bash
    python -m venv venv
    ```

3.  **Virtuelle Umgebung aktivieren:**
    ```bash
    source venv/bin/activate
    ```
    *(Deine Terminal-Eingabeaufforderung sollte nun mit `(venv)` beginnen.)*

4.  **Benötigte Python-Pakete installieren:**
    ```bash
    pip install Flask Flask-CORS
    ```

5.  **SSL-Zertifikat für HTTPS erstellen:**
    ```bash
    openssl req -x509 -newkey rsa:4096 -nodes -keyout key.pem -out cert.pem -days 365
    ```
    *(Drücke bei allen Fragen einfach `Enter`.)*

6.  **Server-Skript anpassen:**
    Öffne `speak_server.py` und stelle sicher, dass der `MODEL_PATH` korrekt auf deine heruntergeladene `.onnx`-Datei zeigt.

### Teil 2: Frontend (Browser-Skripte) einrichten

#### 2a. Das Hauptskript installieren (`tampermonkey_v4.js`)

Dieses Skript ist die finale, robuste Version. Es wartet, bis Gemini mit dem Schreiben fertig ist, und verhindert so zuverlässig überlappende Stimmen.

1.  Klicke auf das Tampermonkey-Symbol in deinem Browser und wähle "Neues Skript erstellen...".
2.  Lösche den gesamten vorgegebenen Beispielcode im Editor.
3.  Öffne die Datei `tampermonkey_v4.js` aus deinem Projektordner, kopiere den *gesamten Inhalt* und füge ihn in den leeren Tampermonkey-Editor ein.
4.  Speichere das Skript (Datei -> Speichern).

#### 2b. (Optional, aber empfohlen) Das Test-Skript installieren (`TTS-ButtonTest.js`)

Dieses Skript fügt einen Test-Button hinzu, um schnell zu prüfen, ob die Verbindung zum lokalen TTS-Server funktioniert. Ideal für die Fehlersuche.

1.  Klicke erneut auf das Tampermonkey-Symbol und wähle "Neues Skript erstellen...".
2.  Lösche wieder den gesamten Beispielcode.
3.  Öffne die Datei `TTS-ButtonTest.js`, kopiere den gesamten Inhalt und füge ihn ein.
4.  Speichere das Skript.

---

## Benutzung

1.  **Server starten:**
    *   Öffne ein Terminal im Projektordner (`~/projects/py/speak_server`).
    *   Aktiviere die Umgebung: `source venv/bin/activate`
    *   Starte den Server: `python3 speak_server.py`
    *   Lasse dieses Terminalfenster laufen.

2.  **Einmalige Browser-Einrichtung:**
    *   Öffne einen neuen Tab und navigiere zur Adresse `https://localhost:5002/`.
    *   Dein Browser wird eine Sicherheitswarnung anzeigen. Klicke auf "Erweitert" und "Risiko akzeptieren und fortfahren" (o.ä.), um das Zertifikat zu akzeptieren.

3.  **(Optional) Verbindung testen:**
    *   Besuche `https://www.google.de`. Oben links sollte ein oranger Button "Sage 'Hallo Welt'" erscheinen.
    *   Klicke darauf. Wenn du kurz darauf den Satz hörst, ist die Verbindung erfolgreich!

4.  **Gemini verwenden:**
    *   Navigiere zur Gemini-Website.
    *   Stelle eine Frage. Nachdem die KI ihre Antwort **vollständig** generiert hat, wird sie nach einer kurzen Pause vorgelesen.

Viel Spaß mit dem stabilen, freihändigen Gemini-Erlebnis!
