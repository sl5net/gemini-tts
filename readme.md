# Gemini-TTS: Automatically Read Gemini's Responses Aloud

This project enables you to have responses from Google Gemini (and Google AI Studio) automatically read aloud using a local, high-quality Text-to-Speech (TTS) engine (`piper-tts`) on Manjaro Linux.

## Objective

The goal is a fully automatic, hands-free operation of Gemini, where the AI's answers are delivered as spoken audio instead of requiring you to read them. This process is completely free and works offline (except for the Gemini website itself).

## The Components

The system consists of two main parts that communicate via a "bridge":

1.  **The Backend (Local Server):**
    *   A small Python server running on your PC.
    *   It uses the **Flask** framework to listen for network requests.
    *   It utilizes **piper-tts** to convert text into spoken language.
    *   It runs with a self-signed **HTTPS/SSL certificate** to communicate with secure websites.

2.  **The Frontend (Browser Script):**
    *   The **Tampermonkey** browser extension (Important: not Greasemonkey!).
    *   A **Userscript** that runs specifically on the Gemini website.
    *   It monitors the page, detects new answers from the AI, extracts the text, and sends it to the backend.

---

## Prerequisites

Before you start, ensure the following software is installed on your Manjaro system:

1.  **piper-tts:** The TTS engine.
    ```bash
    # Via the AUR, e.g., with yay
    yay -S piper-tts
    ```

2.  **A German Voice Model for Piper:**
    *   Download a voice, for example, the "kerstin" voice from [Hugging Face](https://huggingface.co/rhasspy/piper-voices/tree/main/de/de_DE/kerstin/low).
    *   You will need both the `.onnx` and the `.onnx.json` files.
    *   Save them in a known location, e.g., `~/Downloads/`.

3.  **Python 3 and pip:** These are installed by default on Manjaro.

4.  **A Web Browser:** e.g., Firefox or Chrome.

5.  **The Tampermonkey Browser Extension:**
    *   **Important:** Use **Tampermonkey**, not the original Greasemonkey, as it handles local HTTPS certificates more reliably.
    *   [Tampermonkey for Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)
    *   [Tampermonkey for Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)

---

## Step-by-Step Installation

### Part 1: Setting up the Backend (Server)

1.  **Create a project folder:**
    ```bash
    mkdir -p ~/projects/py/speak_server
    cd ~/projects/py/speak_server
    ```

2.  **Create a Python Virtual Environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    ```bash
    source venv/bin/activate
    ```
    *(Your terminal prompt should now start with `(venv)`.)*

4.  **Install the required Python packages:**
    ```bash
    pip install Flask Flask-CORS
    ```

5.  **Create an SSL certificate for HTTPS:**
    ```bash
    openssl req -x509 -newkey rsa:4096 -nodes -keyout key.pem -out cert.pem -days 365
    ```
    *(Simply press `Enter` for all questions.)*

6.  **Create the server file `speak_server.py`:**
    Create a new file named `speak_server.py` and paste the following code into it:

    ```python
    #!/usr/bin/env python3
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import subprocess
    import shlex

    # --- CONFIGURATION (Adjust this section!) ---
    MODEL_PATH = "/home/seeh/Downloads/de_DE-kerstin-low.onnx" # <-- Adjust the path to your .onnx file!
    PORT = 5002
    APLAY_CMD = "aplay -r 22050 -f S16_LE -t raw -"
    # --------------------------------------------

    app = Flask(__name__)
    CORS(app) # Enables Cross-Origin Resource Sharing

    @app.route('/speak', methods=['POST'])
    def speak():
        try:
            data = request.get_json()
            if not data or 'text' not in data:
                return jsonify({"status": "error", "message": "No text provided"}), 400

            text_to_speak = data['text']
            
            piper_cmd = ["piper-tts", "--model", MODEL_PATH, "--output-raw"]
            piper_process = subprocess.Popen(piper_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = piper_process.communicate(input=text_to_speak.encode('utf-8'))

            if piper_process.returncode != 0:
                print("Piper-TTS Error:", stderr.decode('utf-8'))
                return jsonify({"status": "error", "message": "Piper-TTS Error"}), 500

            aplay_process = subprocess.Popen(shlex.split(APLAY_CMD), stdin=subprocess.PIPE)
            aplay_process.communicate(input=stdout)

            return jsonify({"status": "success"})
        except Exception as e:
            print(f"A general error occurred: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    if __name__ == '__main__':
        print(f"Final Speech Server (with HTTPS and CORS) starting on https://localhost:{PORT}")
        ssl_context = ('cert.pem', 'key.pem')
        app.run(host='127.0.0.1', port=PORT, ssl_context=ssl_context)

    ```
    **Important:** Adjust the `MODEL_PATH` at the top of the script to the actual location of your Piper model!

### Part 2: Setting up the Frontend (Tampermonkey Script)

1.  Click the Tampermonkey icon in your browser and select "Create a new script...".
2.  Delete all the boilerplate code.
3.  Paste the following code:

    ```javascript
    // ==UserScript==
    // @name         Gemini to Piper TTS (v3.1 - Final)
    // @namespace    http://tampermonkey.net/
    // @version      3.1
    // @description  Reads the latest response from Gemini/AI Studio aloud.
    // @author       Your Name & AI
    // @match        https://aistudio.google.com/prompts/*
    // @match        https://gemini.google.com/app/*
    // @connect      localhost
    // @grant        GM_xmlhttpRequest
    // @run-at       document-idle
    // ==/UserScript==

    (function() {
        'use strict';

        const SERVER_URL = 'https://localhost:5002/speak';
        const DEBOUNCE_DELAY = 1500; // Wait 1.5 seconds after text has stopped changing

        console.log('[Piper TTS v3.1] Script is active and ready.');

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
                console.log('[Piper TTS v3.1] Text appears complete. Sending to server:', currentText);
                sendTextToServer(currentText);
            }, DEBOUNCE_DELAY);
        };

        const sendTextToServer = (text) => {
            const cleanedText = text.trim();
            if (!cleanedText) {
                console.log('[Piper TTS v3.1] Ignoring empty text.');
                return;
            }

            GM_xmlhttpRequest({
                method: 'POST',
                url: SERVER_URL,
                data: JSON.stringify({ text: cleanedText }),
                headers: { 'Content-Type': 'application/json' },
                onload: (response) => console.log('[Piper TTS v3.1] Server response:', response.status),
                onerror: (response) => console.error('[Piper TTS v3.1] Server error:', response)
            });
        };

        const observer = new MutationObserver(onMutation);
        observer.observe(document.body, { childList: true, subtree: true });

    })();
    ```
4.  Save the script (File -> Save).

---

## Usage

1.  **Start the Server:**
    *   Open a terminal.
    *   Navigate to the project folder: `cd ~/projects/py/speak_server`
    *   Activate the environment: `source venv/bin/activate`
    *   Start the server: `python3 speak_server.py`
    *   Keep this terminal window running.

2.  **One-Time Browser Setup:**
    *   Open a new tab in your browser.
    *   Navigate to the address `https://localhost:5002/`.
    *   Your browser will display a major security warning. This is normal and expected.
    *   Click "Advanced" and then "Accept the Risk and Continue" or "Proceed to localhost (unsafe)" to tell your browser to trust this certificate.

3.  **Use Gemini:**
    *   Navigate to the Gemini website. The Tampermonkey script will load automatically.
    *   Ask a question.
    *   After the AI has finished generating its response, it will be read aloud after a short pause.

Enjoy your new hands-free Gemini experience
