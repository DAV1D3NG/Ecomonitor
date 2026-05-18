import socket
import threading
import queue
import csv
import os
from datetime import datetime

# Definizione delle costanti di rete per il binding del socket
HOST = '127.0.0.1'  # Indirizzo di loopback locale
PORT = 5000  # Porta di ascolto del servizio

# Inizializzazione delle strutture dati globali per la concorrenza
q = queue.Queue()  # Coda FIFO bloccante per disaccoppiare la ricezione dalla scrittura
lock = threading.Lock()  # Mutex per garantire la mutua esclusione nell'accesso al file CSV

def normalizza_sensore(s):
    """
    Normalizza il nome del sensore convertendolo in minuscolo ed eliminando gli spazi bianchi.
    :param s: Il nome grezzo o l'abbreviazione del sensore ricevuto dal client.
    :type s: str
    :returns: Il nome standardizzato ('luce' o 'rumore'), oppure None se il sensore non è valido.
    :rtype: str or None
    """
    s = s.strip().lower()
    if s in ["luce", "l"]:
        return "luce"
    elif s in ["rumore", "r"]:
        return "rumore"
    return None

def salva_csv(dati):
    """
    Salva una riga di dati nel file CSV in modo sicuro utilizzando un mutex (lock).
    :param dati: Lista contenente i campi ordinati della misurazione da scrivere (studente, sensore, valore, luogo, data_ora).
    :type dati: list
    :returns: Nessun valore di ritorno.
    :rtype: None
    """
    with lock:
        with open("misure.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(dati)

def worker():
    """
    Funzione eseguita in background dal thread worker. Estrae continuamente le richieste
    dalla coda condivisa e ne invoca il salvataggio persistente su file CSV.
    :returns: Nessun valore di ritorno (esegue un ciclo infinito).
    :rtype: None
    """
    while True:
        richiesta = q.get()  # Chiamata bloccante: il thread si sospende se la coda è vuota
        salva_csv(richiesta)  # Esegue l'operazione di I/O su file
        q.task_done()  # Invia il segnale di sblocco alla coda per notificare l'avvenuta elaborazione


def gestisci_client(conn, addr):
    """
    Gestisce la sessione di comunicazione e lo scambio di messaggi TCP con un singolo client connesso.
    :param conn: Il socket dedicato alla comunicazione con lo specifico client.
    :type conn: socket.socket
    :param addr: La tupla contenente l'indirizzo IP e la porta del client connesso.
    :type addr: tuple
    :returns: Nessun valore di ritorno.
    :rtype: None
    """
    print(f"Connesso: {addr}")

    while True:
        try:
            # Ricezione del flusso di byte dal canale TCP ed esecuzione della decodifica in stringa UTF-8
            msg = conn.recv(1024).decode()
            if not msg:
                break  # Se recv ritorna una stringa vuota, significa che il client vuole chiudere la connessione

            msg = msg.strip()
            if not msg:
                continue  # Salta l'elaborazione se il messaggio contiene solo spazi bianchi

            # Lettura e scomposizione (Parsing) del pacchetto stringa basato sul delimitatore a virgola
            parti = msg.split(",")
            comando = parti[0].upper().strip()  # Normalizzazione del comando per renderlo case-insensitive

            if comando == "INVIA":
                try:
                    # Validazione della lunghezza del pacchetto per prevenire errori di indice (IndexError)
                    if len(parti) != 5:
                        raise ValueError("Numero di parametri non conforme alla specifica del protocollo.")

                    # Destrutturazione posizionale dei parametri del messaggio
                    _, nome, sensore_raw, valore_raw, luogo = parti

                    # Eliminazione degli spazi di contorno indesiderati dalle stringhe
                    nome = nome.strip()
                    luogo = luogo.strip()

                    # Validazione semantica del sensore
                    sensore = normalizza_sensore(sensore_raw)
                    if sensore is None:
                        conn.send("ERRORE sensore non valido.".encode())
                        continue

                    # Conversione esplicita del valore (da stringa a float)
                    valore = float(valore_raw)

                    # Generazione del timestamp corrente lato server
                    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Impacchettamento del record strutturato in una lista
                    richiesta = [nome, sensore, valore, luogo, data_ora]

                    # Inserimento nella coda dei dati normalizzati
                    q.put(richiesta)

                    # Feedback positivo al client e il timestamp di ricezione
                    conn.send(f"OK, salvato alle {data_ora}.".encode())

                except ValueError as ve:
                    # Gestione specifica di errori di formato numerico o parametri mancanti
                    print(f"Errore sintattico nei dati estratti da {addr}: {ve}.")
                    conn.send("ERRORE formato dati non valido.".encode())

                except Exception as e:
                    # Eccezione generica interna al blocco di invio per prevenire crash
                    print(f"Errore imprevisto durante l'elaborazione dell'invio da {addr}: {e}.")
                    conn.send("ERRORE interno del server.".encode())

            elif comando == "CODA":
                # Interrogazione dello stato della coda e invio della sua dimensione attuale
                conn.send(f"In coda: {q.qsize()}.".encode())

            elif comando == "ESCI":
                break  # Esce dal ciclo di ricezione interrompendo la connessione in modo controllato

            else:
                conn.send("ERRORE comando sconosciuto.".encode())

        except (ConnectionResetError, ConnectionAbortedError):
            # Intercettazione della chiusura improvvisa della connessione lato client (es. Ctrl+C del client)
            print(f"Connessione interrotta bruscamente dal client {addr}.")
            break

        except Exception as e:
            # Cattura di errori generici di rete o di violazione di accesso del socket
            print(f"Errore generico di rete associato al socket {addr}: {e}.")
            break

    # Rilascio definitivo del descrittore di file del socket e chiusura del canale logico
    conn.close()
    print(f"Disconnesso: {addr}")

def main():
    """
    Funzione principale che inizializza la struttura del file CSV, avvia il thread
    worker per la gestione della coda e avvia il server in ascolto di nuove connessioni TCP.
    :returns: Nessun valore di ritorno.
    :rtype: None
    """
    # Controllo di esistenza del file CSV per evitare sovrascritture distruttive dell'intestazione
    if not os.path.exists("misure.csv"):
        with open("misure.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Definizione dell'header standard strutturato del database
            writer.writerow(["studente", "sensore", "valore", "luogo", "data_ora"])

    # Allocazione e avvio del thread consumatore (Worker).
    # Viene impostato come demone (daemon) in modo che termini automaticamente alla chiusura del processo main
    threading.Thread(target=worker, daemon=True).start()

    # Creazione del socket server basato sull'architettura IPv4 (AF_INET) e protocollo TCP (SOCK_STREAM)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Configurazione del socket a livello di sistema operativo per consentire il riutilizzo immediato dell'indirizzo
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Collegamento del socket all'interfaccia di rete e alla porta predefinita
    server.bind((HOST, PORT))

    # Messa in ascolto del socket
    server.listen()
    print(f"Server EcoMonitor avviato e in ascolto su {HOST}:{PORT}")

    try:
        while True:
            # Chiamata bloccante: il server si sospende in attesa di una richiesta di connessione
            conn, addr = server.accept()

            # Allocazione dinamica di un nuovo thread concorrente per gestire la sessione del client accettato
            t = threading.Thread(target=gestisci_client, args=(conn, addr))
            t.start()  # Avvio del thread: esegue la funzione gestisci_client in parallelo

    except KeyboardInterrupt:
        print("\nInterruzione manuale rilevata. Spegnimento del server.")

    finally:
        # Chiusura finale del socket principale per liberare la porta di sistema
        server.close()

if __name__ == "__main__":
    main()