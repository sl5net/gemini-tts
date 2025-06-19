// ==UserScript==
// @name         Gemini to Piper TTS (v3.4 - Targeted Search)
// @namespace    http://tampermonkey.net/
// @version      3.4
// @description  Liest die neueste Gemini-Antwort mit gezielter, zweistufiger Suche und intelligentem Streaming vor.
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
    const DEBOUNCE_DELAY = 1500;
    // --- ENDE KONFIGURATION ---

    console.log('[Piper TTS v3.3] Skript aktiv. Nutzt gezielte Suche.');

    let speechTimer = null;
    let lastProcessedContainer = null;
    let textCurrentlyBeingProcessed = ""; // Text, der für den nächsten Sendevorgang vorgesehen ist
    let textAlreadySentToServer = "";   // Text, der tatsächlich schon gesendet wurde

    const onMutation = () => {
        const allTurnContainers = document.querySelectorAll('div.chat-turn-container.model');
        if (allTurnContainers.length === 0) return;

        const latestTurnContainer = allTurnContainers[allTurnContainers.length - 1];
        const textElement = latestTurnContainer.querySelector('ms-cmark-node, .model-response-text');
        if (!textElement) return;

        // Wenn eine komplett neue Antwort-Box erscheint, alles zurücksetzen
        if (latestTurnContainer !== lastProcessedContainer) {
            console.log('[Piper TTS v3.3] Neue Antwort-Box erkannt. Status wird zurückgesetzt.');
            lastProcessedContainer = latestTurnContainer;
            textCurrentlyBeingProcessed = "";
            textAlreadySentToServer = "";
            clearTimeout(speechTimer);
        }

        const currentFullTextFromDOM = textElement.innerText.trim();

        // Wenn sich der Text im DOM nicht geändert hat, seit wir ihn das letzte Mal
        // für die Verarbeitung vorgemerkt haben, müssen wir nichts tun.
        if (currentFullTextFromDOM === textCurrentlyBeingProcessed) {
            return;
        }

        // Der Text im DOM hat sich geändert. Merke ihn für den nächsten Sendevorgang.
        textCurrentlyBeingProcessed = currentFullTextFromDOM;
        console.log(`[Piper TTS v3.3] DOM aktualisiert. textCurrentlyBeingProcessed: "${textCurrentlyBeingProcessed}"`);


        clearTimeout(speechTimer);
        speechTimer = setTimeout(() => {
            if (document.hidden) {
                console.log('[Piper TTS v3.3] Tab im Hintergrund. Senden unterdrückt.');
                return;
            }

            // Nur den NEUEN Textteil extrahieren, basierend auf dem, was WIRKLICH schon gesendet wurde
            // und dem, was aktuell (zum Zeitpunkt des Timeout-Feuerns) zur Verarbeitung ansteht.
            const textToSendNow = textCurrentlyBeingProcessed; // Momentaufnahme des Texts zur Verarbeitung

            // Vergleiche mit dem, was tatsächlich schon gesendet wurde
            if (textToSendNow === textAlreadySentToServer) {
                console.log('[Piper TTS v3.3] Text zur Verarbeitung ist identisch mit bereits gesendetem. Überspringe Senden.');
                return;
            }

            const newTextChunk = textToSendNow.substring(textAlreadySentToServer.length).trim();

            console.log(`[Piper TTS v3.3] Timeout! textToSendNow: "${textToSendNow}"`);
            console.log(`[Piper TTS v3.3] textAlreadySentToServer: "${textAlreadySentToServer}"`);
            console.log(`[Piper TTS v3.3] newTextChunk: "${newTextChunk}"`);


            if (newTextChunk) {
                console.log('[Piper TTS v3.3] Sende neuen Textteil zum Server:', newTextChunk);
                sendTextToServer(newTextChunk, () => {
                    // Erfolgscallback: Aktualisiere, was tatsächlich gesendet wurde
                    textAlreadySentToServer = textToSendNow;
                    console.log(`[Piper TTS v3.3] textAlreadySentToServer aktualisiert auf: "${textAlreadySentToServer}"`);
                });
            }
        }, DEBOUNCE_DELAY);
    };

    const sendTextToServer = (text, onSuccessCallback) => { // onSuccessCallback hinzugefügt
        const cleanedText = text.trim(); // Sollte schon getrimmt sein, aber sicher ist sicher
        if (!cleanedText) {
            console.log('[Piper TTS v3.3] Leerer Text (nach Trim) wird ignoriert.');
            return;
        }

        GM_xmlhttpRequest({
            method: 'POST',
            url: SERVER_URL,
            data: JSON.stringify({ text: cleanedText }),
                          headers: { 'Content-Type': 'application/json' },
                          onload: (response) => {
                              if (response.status >= 200 && response.status < 300) {
                                  console.log(`[Piper TTS v3.3] Server meldet Erfolg (${response.status}) für Text: "${cleanedText}"`);
                                  if (onSuccessCallback) {
                                      onSuccessCallback(); // Rufe den Callback auf, um textAlreadySentToServer zu aktualisieren
                                  }
                              } else {
                                  console.error(`[Piper TTS v3.3] Server meldet Problem: Status ${response.status} für Text: "${cleanedText}"`, response);
                              }
                          },
                          onerror: (response) => {
                              console.error(`[Piper TTS v3.3] Server-Fehler für Text: "${cleanedText}". Läuft der Piper-Server? Ist die URL korrekt?`, response);
                          },
                          ontimeout: () => {
                              console.error(`[Piper TTS v3.3] Timeout für Text: "${cleanedText}". Der Server antwortet nicht.`);
                          }
        });
    };

    const observer = new MutationObserver(onMutation);
    observer.observe(document.body, { childList: true, subtree: true });

})();

