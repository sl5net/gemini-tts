# Gemini-TTS: Automatically Read Gemini's Responses Aloud

This project enables you to have responses from Google Gemini (and the Google AI Studio) automatically read aloud using a local, high-quality Text-to-Speech (TTS) engine (`piper-tts`) on Manjaro Linux.

## Objective

The goal is a fully hands-free operation of Gemini, where the AI's answers are delivered as spoken audio output instead of requiring you to read them. This process is completely free and works offline (with the exception of the Gemini website itself).

## The Components

The system consists of two main parts that communicate via a "bridge":

1.  **The Backend (Local Server):**
    *   A small Python server that runs on your PC (`speak_server.py`).
    *   It uses the **Flask** framework to listen for network requests.
    *   It utilizes **piper-tts** to convert text into spoken language.
    *   It runs with a self-signed **HTTPS/SSL certificate** to communicate with secure websites.

2.  **The Frontend (Browser Scripts):**
    *   The **Tampermonkey** browser extension.
    *   Two **Userscripts** (`tampermonkey_v4.js` and `TTS-ButtonTest.js`) provided as separate files.
    *   The main script monitors the Gemini page, detects new, **fully generated** responses, and sends their text to the backend.

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
    *   [Tampermonkey for Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)
    *   [Tampermonkey for Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)

---

## Step-by-Step Guide

### Part 1: Setting up the Backend (Server)

1.  **Create and navigate to the project folder:**
    ```bash
    # Create the folder if it doesn't exist yet
    mkdir -p ~/projects/py/speak_server
    cd ~/projects/py/speak_server
    ```
    Ensure all project files (`speak_server.py`, `tampermonkey_v4.js`, etc.) are located in this folder.

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

6.  **Adjust the server script:**
    Open `speak_server.py` and make sure the `MODEL_PATH` variable points to the correct location of your downloaded `.onnx` file.

### Part 2: Setting up the Frontend (Browser Scripts)

#### 2a. Install the Main Script (`tampermonkey_v4.js`)

This script is the final, robust version. It waits until Gemini has finished writing, reliably preventing any overlapping voices.

1.  Click the Tampermonkey icon in your browser and select "Create a new script...".
2.  Delete all the boilerplate code in the editor.
3.  Open the file `tampermonkey_v4.js` from your project folder, copy its *entire contents*, and paste them into the empty Tampermonkey editor.
4.  Save the script (File -> Save).

#### 2b. Install the Test Script (`TTS-ButtonTest.js`) (Optional, but Recommended)

This script adds a test button to quickly check if the connection to the local TTS server is working. It is ideal for troubleshooting.

1.  Click the Tampermonkey icon again and select "Create a new script...".
2.  Delete all the boilerplate code.
3.  Open the file `TTS-ButtonTest.js`, copy its entire contents, and paste them into the editor.
4.  Save the script.

---

## Usage

1.1.  **Start the Server Option 1:**
    *   Open a terminal in your project folder (`~/projects/py/speak_server`).
    *   Activate the environment: `source venv/bin/activate`
    *   Start the server: `python3 speak_server.py`
    *   Keep this terminal window running.

1.2.  **Start the Server Option 2:** (probably the most easiest way to start)
    *   Open a terminal in your project folder (`~/projects/py/speak_server`).
    *   run `python3 ~/projects/py/speak_server/speak_file.py HelloWorld.txt

1.3.  **Start the Server Option 3:**
    *   Config your File-Explorer. E.g. when you use doublecomander
    *   add option to open file with `sh`
    *   use parameter `-c "python3 ~/projects/py/speak_server/speak_file.py %f > /tmp/speak_error.log 2>&1`
    
2.  **One-Time Browser Setup:**
    *   Open a new tab and navigate to `https://localhost:5002/`.
    *   Your browser will show a security warning. Click "Advanced" and then "Accept the Risk and Continue" (or similar) to trust the certificate.

3.  **(Optional) Test the Connection:**
    *   Visit `https://www.google.com`. An orange button labeled "Sage 'Hallo Welt'" should appear in the top-left corner.
    *   Click it. If you hear the sentence spoken aloud shortly after, the connection is successful!

4.  **Use Gemini:**
    *   Navigate to the Gemini website.
    *   Ask a question. After the AI has **fully** generated its response, it will be read aloud after a short pause.

