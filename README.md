# EcoMonitor - Sistema di Monitoraggio Ambientale Scolastico

**EcoMonitor** è una piattaforma analitica client-server in Python progettata per il monitoraggio concorrente dell'**intensità luminosa (lux)** e dell'**inquinamento acustico (dB)** all'interno degli ambienti scolastici. 

Il sistema adotta un'architettura disaccoppiata in grado di raccogliere dati in tempo reale da inserimenti manuali, agenti di simulazione automatica o flussi pre-registrati sul campo tramite l'applicazione mobile smartphone **Phyphox**.

---

## Architettura del Sistema

Il nucleo dell'infrastruttura si basa sul pattern architetturale **Produttore-Consumatore**:
* **Produttori (Client):** Gestiscono le letture hardware o simulate e inviano stringhe di testo codificate tramite socket TCP.
* **Coda Bloccante (`queue.Queue`):** Il server smista istantaneamente i pacchetti in arrivo in una coda FIFO, liberando subito il socket del client.
* **Consumatore (Thread Worker):** Un thread dedicato in background estrae sequenzialmente i dati dalla coda e invoca la scrittura persistente su disco tramite un **Mutex Lock (`threading.Lock`)**, prevenendo qualsiasi fenomeno di *race condition* o corruzione del database CSV.

---

## Struttura del Progetto

```text
EcoMonitor/
│
├── server.py              # Server TCP multithread (gestore code e dati)
├── client.py              # Interfaccia CLI manuale per l'operatore/studente
├── simulatore_client.py   # Agente per invio automatico di dati generati casualmente
├── adattatore_formati.py  # Script che normalizza i dati di Phyphox in formato desiderato
├── client_phyphox.py      # Caricatore dei dati Phyphox normalizzati
├── dashboard.py           # Interfaccia grafica analitica tramite Streamlit
│
├── misure.csv             # Database centrale centralizzato (Formato unico)
└── requirements.txt       # Elenco dipendenze software del progetto
```

---

## Schema del Database (```misure.csv```)

Tutti i dati confluiscono in un unico file standardizzato privo di indici di riga, strutturato secondo i seguenti campi:


| Campo | Tipo | Descrizione |
| :--- | :--- | :--- |
| **studente** | `string` | Identificativo del rilevatore |
| **sensore** | `string` | Tipologia standardizzata di sensore (luce o rumore) |
| **valore** | `float` | Misura numerica convertita e normalizzata (punto decimale) |
| **luogo** | `string` | Ambiente in cui è avvenuto il campionamento |
| **data_ora** | `string` | Timestamp ufficiale apposto dal server (AAAA-MM-GG HH:MM:SS) |

## Protocollo di Comunicazione Applicativo (TCP)

Il server risponde a comandi testuali inviati in formato stringa (`UTF-8`) con campi delimitati da virgole.

### Comandi Disponibili

* **`INVIA,[studente],[sensore],[valore],[luogo]`**
  * **Azione:** Valida il pacchetto, accoda la richiesta nella coda bloccante e risponde al client con la stringa:  
    `OK, salvato alle [timestamp]`

* **`CODA`**
  * **Azione:** Restituisce lo stato attuale di carico del server, indicando il numero di record in attesa di essere scritti su disco:  
    `In coda: X`

* **`ESCI`**
  * **Azione:** Interrompe la sessione di comunicazione con il client in modo pulito lato server (avviando la procedura di chiusura della connessione).

## Requisiti

Assicurati di avere **Python 3.8+** installato sul tuo sistema.
Sono inoltre necessari i moduli **pandas** e **streamlit**, installabili tramite:

   ```bash
   pip install -r requirements.txt
   ```
## Guida all'Avvio Operativo

I moduli devono essere avviati in **terminali separati** seguendo rigorosamente l'ordine logico della rete.

### 1. Inizializzazione dell'Infrastruttura (Server)

Il server si mette in ascolto sulla porta `5000` di `localhost`. È configurato con l'opzione `SO_REUSEADDR` per consentire riavvii immediati senza bloccare la porta.

```bash
python server.py
```

### 2. Monitoraggio Visivo (Dashboard)

Avvia il server web locale per visualizzare i grafici e le analisi aggregate in tempo reale tramite l'interfaccia grafica.

```bash
python -m streamlit run dashboard.py
```

### 3. Connessione Sorgenti Dati (Opzionale)

* **Per inserimenti manuali** tramite terminale interattivo:
  ```bash
  python client.py
  ```

* **Per avviare la simulazione continua** (con una trasmissione sequenziale temporizzata di 1 invio ogni tot secondi):
  ```bash
  python simulatore_client.py
  ```

## Pipeline d'Integrazione dati Smartphone (Phyphox)

Per caricare sessioni storiche di campionamento registrate dal vivo in classe tramite i sensori dello smartphone, segui questo flusso di lavoro:

```text
[Phyphox App] ──> Esporta CSV ──> [adattatore_formati.py] ──> dati_phyphox.csv ──> [client_phyphox.py] ──> [Server TCP]
```

### Passaggi Operativi

1. **Esportazione dei dati grezzi**:
   Esporta la registrazione dall'app *Phyphox* in formato **CSV** e copia il file (es. `Light.csv` o `Amplitudes.csv`) all'interno della cartella del progetto.

2. **Sanificazione e Mappatura dei dati**:
   Configura i metadati in cima al file `adattatore_formati.py` ed eseguilo per correggere i separatori decimali e mappare lo schema dei dati:
   ```bash
   python adattatore_formati.py
   ```

3. **Caricamento sul Server (Uploader Batch)**:
   Avvia l'uploader in modalità batch per trasferire i record storici sanificati al server tramite una trasmissione sequenziale temporizzata a intervalli controllati di 500ms (scelta che serve a **scongiurare** la saturazione dei buffer):
   ```bash
   python client_phyphox.py
   ```