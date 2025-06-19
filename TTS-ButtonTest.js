// ==UserScript==
// @name         TTS - Button Test (v1.2 - Korrigiert)
// @namespace    http://tampermonkey.net/
// @version      1.2
// @description  Fügt einen Button hinzu, um die TTS-Server-Verbindung zu testen.
// @author       Test
// @match        https://www.google.com/*
// @match        https://sl5.de/*
// @connect      localhost
// @grant        GM_xmlhttpRequest
// @run-at       document-end  // <-- WICHTIGE ZUSÄTZLICHE ZEILE
// ==/UserScript==

(function() {
    'use strict'; // <-- TIPPFEHLER KORRIGIERT

    console.log('[TTS Button Test v1.2] Skript wird ausgeführt.');

    const testButton = document.createElement('button');
    testButton.textContent = 'Sage "Hallo Welt"';
    testButton.style.position = 'fixed';
    testButton.style.top = '20px';
    testButton.style.left = '20px';
    testButton.style.zIndex = '9999';
    testButton.style.padding = '10px';
    testButton.style.fontSize = '14px';
    testButton.style.backgroundColor = '#FF9800'; // Orange
    testButton.style.color = 'white';
    testButton.style.border = 'none';
    testButton.style.cursor = 'pointer';

    testButton.addEventListener('click', () => {
        console.log('[TTS Button Test v1.2] Button geklickt. Sende "Hallo Welt" zum Server...');
        const textToSend = 'Hallo Welt, dieser Test funktioniert.';

        GM_xmlhttpRequest({
            method: 'POST',
            url: 'https://localhost:5002/speak',
            data: JSON.stringify({ text: textToSend }),
                          headers: { 'Content-Type': 'application/json' },
                          onload: function(response) {
                              console.log('[TTS Button Test v1.2] Server-Antwort:', response.responseText);
                              alert('Anfrage an den Server gesendet! Status: ' + response.status);
                          },
                          onerror: function(response) {
                              console.error('[TTS Button Test v1.2] Server-Fehler-Details:', response);
                              alert('FEHLER! Details aus dem Fehler-Objekt:\n\n' + JSON.stringify(response, null, 2));
                          }
        });
    });

    document.body.appendChild(testButton);
    console.log('[TTS Button Test v1.2] Button wurde zur Seite hinzugefügt.');

})();
