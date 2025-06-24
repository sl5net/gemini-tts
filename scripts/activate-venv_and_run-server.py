
draft

exit(1)

# NEUER, VERBESSERTER CODE
if result.returncode != 0:
    print(f"'{service_name}' not running. Starting it now...")
    # Stelle sicher, dass das Skript ausführbar ist!
    subprocess.Popen([START_SERVER_SCRIPT]) # Popen statt run, da es nicht wartet

    # Warte in einer Schleife, bis der Server antwortet (maximal 10 Sekunden)
    server_ready = False
    max_wait_time = 10  # Sekunden
    start_time = time.time()
    url_to_check = "https://127.0.0.1:5002/speak" # Die URL, die wir abfragen

    print("Waiting for server to become ready...")
    while time.time() - start_time < max_wait_time:
        try:
            # Wir benutzen einen HEAD-Request, da wir nur den Status wollen, nicht den Inhalt
            requests.head(url_to_check, verify=False, timeout=1)
            print("Server is ready!")
            server_ready = True
            break # Die Schleife verlassen, wenn der Server antwortet
        except requests.exceptions.ConnectionError:
            # Server noch nicht bereit, kurz warten und erneut versuchen
            time.sleep(0.5)

    if not server_ready:
        print(f"Server did not start within {max_wait_time} seconds. Check server.log.")
        exit(1) # Beenden, da der Server nicht gestartet ist

# Jetzt, da wir wissen, dass der Server läuft, senden wir die eigentliche Anfrage
