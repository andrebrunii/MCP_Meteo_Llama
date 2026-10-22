# Llama + MCP: condizioni meteo

Un test funzionale nella cartella `MCP_Meteo_Llama`.
Il client scopre un vero strumento MCP, lo presenta a Llama tramite function calling,
esegue la richiesta tramite MCP e verifica la risposta finale rispetto ai dati ricevuti.

## File

| File | Funzione |
|---|---|
| `mcp_weather_server.py` | Server MCP via stdio, un solo tool: `get_current_weather` |
| `mcp_weather_test.py` | Client MCP, collegamento a Ollama e verifica dei dati |
| `requirements-mcp.txt` | SDK ufficiale MCP, versione 1.30.0 fissata |
| `test_mcp_weather.py` | Verifiche offline con modello e meteo simulati |
| `.gitignore` | Esclude ambiente virtuale, cache e configurazioni locali |

Questi file si affiancano a `lab.py`. Il server viene avviato dal client automaticamente.
Non serve aprire una seconda finestra o avviare manualmente il server MCP.

## Avvio su Windows / Git Bash

Copia i file di questo pacchetto direttamente in
`Documents\GitHub_Labs\MCP_Meteo_Llama`.
Usa Python 3.11 o successivo (consigliato 3.12) e avvia l'app Ollama.

```bash
cd ~Documents\GitHub_Labs\MCP_Meteo_Llama
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-mcp.txt
ollama list
./.venv/Scripts/python.exe mcp_weather_test.py --model llama3.1:8b --city Roma
```

Se il modello manca: `ollama pull llama3.1:8b`.
Si usa direttamente Python della venv: non occorre attivarla.
Su Linux/macOS il suo percorso e `.venv/bin/python`.

Citta disponibili: `Roma`, `Milano`, `Torino`, `Chieri`, `Napoli`.
Le coordinate del centro citta sono fisse nel server: nessuna geolocalizzazione del PC.

## Che cosa vedrai

1. Connessione MCP e scoperta di `get_current_weather` con `list_tools`.
2. Llama produce una chiamata strutturata per la citta richiesta.
3. Il client la valida e la esegue con `session.call_tool`; il server consulta Open-Meteo.
4. Llama restituisce un JSON con i dati; il client confronta ogni campo con l'originale.

Il test usa due generazioni del modello e al massimo una chiamata allo strumento.
Se il modello non richiede il tool, il programma non finge una chiamata riuscita.
La seconda generazione usa un formato JSON vincolato e nessuno strumento disponibile.
Non vengono richieste o valutate catene di ragionamento.

## Interpretare il report

Ogni avvio crea `weather-run-*/report.json`, anche in caso di errore.
Il report registra schema scoperto tramite MCP, chiamata, risposta API normalizzata,
risposte Ollama, controlli sui campi e tempi. I valori grezzi di Open-Meteo vengono
selezionati e normalizzati dal server, non archiviati nella loro interezza.

| Esito | Significato |
|---|---|
| `PASS` | Chiamata accettata, MCP riuscito e campi finali uguali ai dati del tool |
| `FAIL_DATA_MISMATCH` | Il modello ha cambiato o omesso almeno un campo |
| `ERROR` | Problema di connessione, chiamata non valida, generazione incompleta o JSON invalido |
| `MCP_OK_MODEL_NOT_TESTED` | Diagnostica MCP riuscita: Llama non e stato testato |

`PASS` verifica la fedelta ai dati della fonte, non l'accuratezza meteorologica sul posto.
Le condizioni attuali Open-Meteo derivano da modelli meteorologici. Sono riportati
ora di validita, fuso orario e ora UTC di recupero: non sono letture da un tuo sensore.
Una singola prova non misura affidabilita statistica o sicurezza generale.
Il benchmark nativo / function tools / MCP / A2A resta una fase successiva.

## Diagnostica

Per verificare solo MCP e Open-Meteo, senza utilizzare il modello:

```bash
./.venv/Scripts/python.exe mcp_weather_test.py --check-tool --city Roma
```

Per le verifiche offline del codice:

```bash
./.venv/Scripts/python.exe -m unittest -v test_mcp_weather.py
```

Questi test usano il trasporto MCP reale, ma risposte meteo e Ollama simulate.
Non sono risultati del benchmark di Llama.

Se compare 404 da Ollama, verifica il nome con `ollama list` e scarica il modello.
Se Open-Meteo non risponde, non viene inventato un risultato meteo.
Ctrl+C interrompe il test. Il timeout di rete non e una scadenza assoluta dell'intera prova.

## Accessi e dati

- Ollama viene contattato su `127.0.0.1:11434`; MCP comunica fra processi locali via stdio.
- Il server consulta soltanto `api.open-meteo.com` via HTTPS e non segue redirect.
- Open-Meteo vede l'indirizzo IP di connessione e le coordinate della citta scelta.
- Nessuna chiave API, carta, account bancario o documento personale richiesto.
- Il modello non puo scegliere URL, percorsi di file, programmi o comandi shell.
- Il client avvia esclusivamente il file locale `mcp_weather_server.py` con Python.
- Il modello deve essere locale: il controllo della parola `cloud` nel nome e solo
  una precauzione, non prova l'isolamento del servizio Ollama.
- Questo progetto non e una sandbox del sistema operativo.

L'API pubblica Open-Meteo e destinata all'uso non commerciale entro i limiti del servizio.
Dati: Open-Meteo, CC BY 4.0; conservare l'attribuzione quando si condividono i risultati.

Prima di pubblicare la cartella, verifica che il tuo `.gitignore` contenga almeno
`.venv/`, `__pycache__/` e `*.py[cod]`.

## Fonti

- https://github.com/modelcontextprotocol/python-sdk/tree/v1.30.0
- https://docs.ollama.com/capabilities/tool-calling
- https://docs.ollama.com/api/chat
- https://open-meteo.com/en/docs
- https://open-meteo.com/en/terms

Verifica dell'autore: 5 test offline superati su Python 3.12 con MCP 1.30.0,
compreso handshake, discovery e call_tool attraverso un processo stdio reale.
La connessione esterna a Open-Meteo non era disponibile nell'ambiente di verifica;
Ollama e i dati meteo sono stati simulati nei test. Windows e il modello reale
restano da verificare sul PC dell'utente.

Codice e documentazione preparati con assistenza AI. Il test live con il modello
va eseguito sul PC: non sono inclusi risultati inventati.
