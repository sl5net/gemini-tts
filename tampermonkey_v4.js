// ==UserScript==
// @name         Gemini to Piper TTS (v4.0 - Robust Final)
// @namespace    http://tampermonkey.net/
// @version      4.0
// @description  Liest die neueste, vollständig generierte Gemini-Antwort vor. Verhindert überlappende Stimmen.
// @author       Seeh & AI
// @match        https://gemini.google.com/app/*
// @match        https://aistudio.google.com/prompts/*
// @connect      localhost
// @grant        GM_xmlhttpRequest
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    // --- KONFIGURATION ---
    const SERVER_URL = 'https://localhost:5002/speak';
    // Die Zeit in Millisekunden, die gewartet wird, nachdem sich der Text nicht mehr ändert.
    // Ein höherer Wert ist sicherer, um überlappende Stimmen zu vermeiden.
    const DEBOUNCE_DELAY = 2000; // 2 Sekunden
    // --- ENDE KONFIGURATION ---

    console.log('[Piper TTS v4.0] Skript aktiv. Modus: Robust Final.');

    let speechTimer = null;

    // Diese Funktion wird bei jeder Änderung auf der Seite aufgerufen
    const onMutation = () => {
        // Finde den Container der letzten Antwort von Gemini
        const latestAnswerContainer = findLatestAnswerContainer();
        if (!latestAnswerContainer) return;

        // PRÜFUNG 1: Wurde dieser Container bereits verarbeitet?
        // Wenn ja, ignoriere alle weiteren Änderungen darin.
        if (latestAnswerContainer.dataset.ttsProcessed === 'true') {
            return;
        }

        // Setze den Timer bei jeder erkannten Textänderung zurück.
        clearTimeout(speechTimer);

        // Starte einen neuen Timer.
        speechTimer = setTimeout(() => {
            // Dieser Code wird erst ausgeführt, wenn DEBOUNCE_DELAY abgelaufen ist.

            // Finde den Container und den Text erneut, um den finalen Stand zu haben.
            const finalContainer = findLatestAnswerContainer();
            if (!finalContainer || finalContainer.dataset.ttsProcessed === 'true') {
                return;
            }

            // Der Tab muss im Vordergrund sein, um zu sprechen.
            if (document.hidden) {
                console.log('[Piper TTS v4.0] Tab im Hintergrund. Senden unterdrückt.');
                return;
            }

            const textElement = finalContainer.querySelector('ms-cmark-node, .model-response-text');
            if (!textElement) return;

            const finalFullText = textElement.innerText.trim();

            if (finalFullText) {
                // PRÜFUNG 2: Markiere den Container SOFORT als verarbeitet.
                // Dies ist die wichtigste Sperre, um doppeltes Senden zu verhindern.
                console.log('[Piper TTS v4.0] Timer abgelaufen. Markiere Container als verarbeitet.');
                finalContainer.dataset.ttsProcessed = 'true';

                console.log('[Piper TTS v4.0] Sende finale Antwort zum Server:', finalFullText);
                sendTextToServer(finalFullText);
            }
        }, DEBOUNCE_DELAY);
    };

    // Eine Hilfsfunktion, um den richtigen Antwort-Container zu finden.
    const findLatestAnswerContainer = () => {
        // Gemini verwendet 'div.chat-turn-container.model' für die gesamte Box
        const allTurnContainers = document.querySelectorAll('div.chat-turn-container.model, div[data-turn-role="Model"]');
        if (allTurnContainers.length > 0) {
            return allTurnContainers[allTurnContainers.length - 1];
        }
        return null;
    };


    const sendTextToServer = (text) => {
        GM_xmlhttpRequest({
            method: 'POST',
            url: SERVER_URL,
            data: JSON.stringify({ text: text }),
                          headers: { 'Content-Type': 'application/json' },
                          onload: (response) => {
                              if (response.status >= 200 && response.status < 300) {
                                  console.log(`[Piper TTS v4.0] Server meldet Erfolg (${response.status})`);
                              } else {
                                  console.error(`[Piper TTS v4.0] Server meldet Problem: Status ${response.status}`, response);
                              }
                          },
                          onerror: (response) => {
                              console.error(`[Piper TTS v4.0] Server-Fehler. Läuft der Piper-Server? Ist die URL korrekt?`, response);
                          },
                          ontimeout: () => {
                              console.error(`[Piper TTS v4.0] Timeout. Der Server antwortet nicht.`);
                          }
        });
    };

    // Starte die Überwachung der Seite
    const observer = new MutationObserver(onMutation);
    observer.observe(document.body, { childList: true, subtree: true });

})();
