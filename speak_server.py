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
import os

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter # Not for output, but for tokenizing
from pygments.token import Comment, String
from bs4 import BeautifulSoup

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

# --- Our custom command translator from before ---
def _translate_shell_command(command: str) -> str | None:
    command = command.strip()
    if command.startswith('python3 -m venv') or command.startswith('python -m venv'):
        return f"Create a Python virtual environment named '{command.split()[-1]}'."
    if command.startswith('source') and 'activate' in command:
        return "Activate the virtual environment."
    if command.startswith('pip install'):
        return f"Install the packages: {' '.join(command.split()[2:])}."
    return f"Run the command: {command}." # Fallback

def clean_text_for_tts(text: str) -> str:
    """
    Cleans a string by removing source code and other content that is
    difficult to read aloud for a Text-to-Speech (TTS) engine.

    The process is a pipeline of cleaning steps:
    1. Remove multi-line code blocks (like ```...```).
    2. Remove inline code snippets (like `...`).
    3. Remove HTML/XML tags.
    4. Replace URLs with the phrase "a web address".
    5. Replace file paths with the phrase "a file path".
    6. "Humanize" variable names (camelCase -> camel case, snake_case -> snake case).
    7. Remove remaining programming symbols and artifacts.
    8. Normalize whitespace to clean up the result.
    """
    if not isinstance(text, str):
        return ""

    # 1. Remove multi-line code blocks (like ```python...```)
    # The re.DOTALL flag makes '.' match newlines as well.
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

    # 2. Remove inline code snippets (like `my_variable`)
    # We will process the content of these later, but for now, just remove the backticks.
    text = re.sub(r'`', '', text)

    # 3. Remove HTML/XML tags
    text = re.sub(r'<[^>]+>', '', text)

    # 4. Replace URLs with a more speakable alternative
    text = re.sub(r'https?://\S+', ' a web address ', text)

    # 5. Replace file paths (e.g., /home/user/file.txt)
    # This is a simple heuristic looking for paths with multiple slashes.
    text = re.sub(r'\b(?:[a-zA-Z]:)?/[^:\s\n\r]+', ' a file path ', text)

    # 6. "Humanize" variable names
    # a. Convert camelCase to "camel case"
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)
    # b. Convert snake_case to "snake case"
    text = text.replace('_', ' ')

    # 7. Remove common programming symbols and other non-speakable characters
    # This keeps basic punctuation but removes things like #, {}, [], <, >, etc.
    text = re.sub(r'[{}()\[\]#*<>;|\\/]', ' ', text)

    # 8. Normalize whitespace
    # Replace multiple spaces/newlines with a single space
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def clean_interactive_text_for_tts(text: str) -> str:
    """
    Cleans text from an interactive session (like a tutorial) for a TTS engine.

    This is more advanced than the basic cleaner. It tries to interpret
    the intent behind the code and translate it into a spoken narrative.
    """
    if not isinstance(text, str):
        return ""

    # 1. Remove specific guard text and metadata
    # This targets the blocks like IGNORE_WHEN_COPYING_START...END
    text = re.sub(
        r'IGNORE_WHEN_COPYING_START.*?IGNORE_WHEN_COPYING_END',
        '',
        text,
        flags=re.DOTALL
    )
    # This targets the lines with 'content_copy', 'download', etc.
    text = re.sub(r'\b(content_copy|download|Use code with caution.)\b', '', text)


    # 2. Remove multi-line, un-speakable code output.
    # This regex looks for lines that start with file permissions (e.g., -rw-r--r-- or drwxr-xr-x)
    # It will remove the entire block of such lines.
    text = re.sub(r'(?m)^[d-][rwx-]{9}.*?$\n?', '', text)


    # 3. Translate common, simple shell commands into spoken instructions.
    # We use a function for replacement to handle the command's arguments.
    def translate_command(match):
        command = match.group(1).strip()
        # Simple cd command
        if command.startswith('cd '):
            path = command.split(' ', 1)[1]
            # Make the path a little more speakable
            path = path.replace('~', 'your home directory')
            return f'First, change directory to {path}.'
        # Simple ls command
        if command.startswith('ls'):
            return 'Now, list the files in the directory.'
        # Simple unzip command
        if command.startswith('unzip '):
            filename = command.split(' ', 1)[1]
            return f'Next, unzip the file named {filename}.'
        # Fallback for other commands
        return f'Run the command: {command}.'

    # The regex finds lines that start with 'Generated bash' or 'Generated code'
    # and then captures the command on the next line(s).
    text = re.sub(r'Generated (bash|code)\n(.*?)\n\n', translate_command, text, flags=re.DOTALL)


    # 4. Final whitespace normalization
    text = re.sub(r'\n+', '\n', text) # Consolidate multiple newlines
    text = re.sub(r' +', ' ', text).strip() # Consolidate spaces
    text = text.replace('\n', ' ') # Replace newlines with spaces for a single block of text

    return text






def clean_interactive_text_for_tts(text: str) -> str:
    """
    Cleans text from an interactive session (like a tutorial) for a TTS engine.

    This is more advanced than the basic cleaner. It tries to interpret
    the intent behind the code and translate it into a spoken narrative.
    """
    if not isinstance(text, str):
        return ""

    # 1. Remove specific guard text and metadata
    # This targets the blocks like IGNORE_WHEN_COPYING_START...END
    text = re.sub(
        r'IGNORE_WHEN_COPYING_START.*?IGNORE_WHEN_COPYING_END',
        '',
        text,
        flags=re.DOTALL
    )
    # This targets the lines with 'content_copy', 'download', etc.
    text = re.sub(r'\b(content_copy|download|Use code with caution.)\b', '', text)


    # 2. Remove multi-line, un-speakable code output.
    # This regex looks for lines that start with file permissions (e.g., -rw-r--r-- or drwxr-xr-x)
    # It will remove the entire block of such lines.
    text = re.sub(r'(?m)^[d-][rwx-]{9}.*?$\n?', '', text)


    # 3. Translate common, simple shell commands into spoken instructions.
    # We use a function for replacement to handle the command's arguments.
    def translate_command(match):
        command = match.group(1).strip()
        # Simple cd command
        if command.startswith('cd '):
            path = command.split(' ', 1)[1]
            # Make the path a little more speakable
            path = path.replace('~', 'your home directory')
            return f'First, change directory to {path}.'
        # Simple ls command
        if command.startswith('ls'):
            return 'Now, list the files in the directory.'
        # Simple unzip command
        if command.startswith('unzip '):
            filename = command.split(' ', 1)[1]
            return f'Next, unzip the file named {filename}.'
        # Fallback for other commands
        return f'Run the command: {command}.'

    # The regex finds lines that start with 'Generated bash' or 'Generated code'
    # and then captures the command on the next line(s).
    text = re.sub(r'Generated (bash|code)\n(.*?)\n\n', translate_command, text, flags=re.DOTALL)


    # 4. Final whitespace normalization
    text = re.sub(r'\n+', '\n', text) # Consolidate multiple newlines
    text = re.sub(r' +', ' ', text).strip() # Consolidate spaces
    text = text.replace('\n', ' ') # Replace newlines with spaces for a single block of text

    return text

def clean_python_code_for_tts(text: str) -> str:
    """
    Cleans a string by removing Python source code but preserving
    comments and surrounding natural language.

    The strategy is to process the text line by line:
    1. Keep full-line comments, extracting just the text.
    2. Discard lines that are clearly Python code (based on keywords,
       indentation, and syntax).
    3. Keep lines that appear to be normal text.
    4. Clean up the final result.
    """
    if not isinstance(text, str):
        return ""

    cleaned_lines = []
    # These are strong indicators that a line is code, not narration.
    python_keywords = (
        'def ', 'class ', 'import ', 'from ', 'try:', 'except:', 'finally:',
        'with ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'return '
    )

    lines = text.split('\n')

    for line in lines:
        stripped_line = line.strip()

        # Rule 1: If the line is empty, skip it.
        if not stripped_line:
            continue

        # Rule 2: If the line is a comment, extract the comment text.
        # This keeps valuable narrative text from the code.
        if stripped_line.startswith('#'):
            comment_text = stripped_line.lstrip('# ').strip()
            # Avoid keeping decorative lines like '#####'
            if len(comment_text.replace('-', '').replace('#', '').strip()) > 2:
                cleaned_lines.append(comment_text)
            continue

        # Rule 3: Check for strong indicators of code to DISCARD the line.
        # a) Starts with a common Python keyword.
        if stripped_line.startswith(python_keywords):
            continue
        # b) Starts with significant indentation (a key feature of Python code blocks).
        if line.startswith(('    ', '\t')):
            continue
        # c) Looks like a function call or assignment, a very common code pattern.
        # This checks for `variable = value` or `object.method()`
        if ('=' in stripped_line or '.' in stripped_line) and ('(' in stripped_line and ')' in stripped_line):
             # A weak heuristic to avoid filtering out sentences with parentheses.
             # If it has many spaces, it's more likely a sentence.
            if stripped_line.count(' ') < 5:
                continue
        # d) Contains `print()` with likely decorative content
        if 'print("' in stripped_line and ('#' in stripped_line or '*' in stripped_line):
            continue

        # Rule 4: If none of the above rules matched, assume it's regular text to KEEP.
        cleaned_lines.append(line)


    # Final Step: Join the kept lines and normalize whitespace.
    full_text = ' '.join(cleaned_lines)
    return re.sub(r'\s+', ' ', full_text).strip()

def clean_text_with_libraries(text: str) -> str:
    """
    A robust text cleaner for TTS using dedicated libraries.
    - Uses markdown-it-py to parse document structure.
    - Uses pygments to intelligently extract comments from code.
    - Uses BeautifulSoup to clean any remaining HTML.
    """
    md = MarkdownIt()
    tokens = md.parse(text)

    speakable_parts = []

    for token in tokens:
        # Case 1: It's a code block (like ```python...```)
        if token.type == 'fence':
            lang = token.info.strip() # The language hint (e.g., 'python', 'bash')
            code_content = token.content

            # Sub-case: It's shell/bash commands we want to translate
            if lang in ['bash', 'sh', 'shell', 'zsh']:
                for line in code_content.split('\n'):
                    if line.strip():
                        translated = _translate_shell_command(line)
                        speakable_parts.append(translated)
            # Sub-case: It's Python or another language where we want comments
            elif lang:
                try:
                    lexer = get_lexer_by_name(lang)
                    code_tokens = lexer.get_tokens(code_content)
                    for ttype, tvalue in code_tokens:
                        # We keep comments and sometimes strings if they are user-facing
                        if ttype in Comment:
                            # Clean the comment syntax and add the text
                            speakable_parts.append(tvalue.strip('# \n'))
                except Exception:
                    # If language is unknown, just ignore the block
                    pass

        # Case 2: It's a paragraph or other inline text
        elif token.type == 'paragraph_open':
            # The actual content is in the next 'inline' token
            pass
        elif token.type == 'inline':
            # Use BeautifulSoup to strip any potential HTML tags (like <b>)
            soup = BeautifulSoup(token.content, 'html.parser')
            speakable_parts.append(soup.get_text())

    # Join all the collected parts and normalize whitespace
    final_text = ' '.join(filter(None, speakable_parts))
    return ' '.join(final_text.split())






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
        # you can run e.g. with 'curl -k -X POST https://127.0.0.1:5002/speak'
        if os.path.exists('/tmp/speak_server_input.txt'):
            with open('/tmp/speak_server_input.txt', 'r') as f:
                text_to_speak_easy = f.read()
                print(f"Transkribiert: '{text_to_speak_easy}'")
                os.remove('/tmp/speak_server_input.txt')

        else:
            data = request.get_json()
            if not data or 'text' not in data:
                print("!!! FEHLER: JSON-Daten ungültig.")
                return jsonify({"status": "error", "message": "Kein Text übermittelt"}), 400

            text_to_speak = data['text']

            text_to_speak_easy = text_to_speak
            text_to_speak_easy = clean_text_for_tts(text_to_speak_easy)
            text_to_speak_easy = clean_interactive_text_for_tts(text_to_speak_easy)
            text_to_speak_easy = clean_text_with_libraries(text_to_speak_easy)
            text_to_speak_easy = clean_python_code_for_tts(text_to_speak_easy)



        print(f"Erfolgreich geparster Text: {text_to_speak_easy[:80]}...")

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
        raw_audio_data, stderr = piper_process.communicate(input=text_to_speak_easy.encode('utf-8'))

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
