import csv
import socket
import time

# Costanti di instradamento verso il server di produzione
HOST = '127.0.0.1'
PORT = 5000

# File normalizzato generato dall'adattatore formati
FILE = "dati_phyphox.csv"

def main():
    """
    Legge il file CSV precedentemente normalizzato e
    invia in modo sequenziale temporizzato ogni record memorizzato verso il server TCP.
    :returns: Nessun valore di ritorno.
    :rtype: None
    """
    # Istanziazione del socket TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Avvio della connessione di rete verso il server
        client.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("Errore: Impossibile avviare la trasmissione. Assicurarsi che il server sia attivo.")
        return

    # Contatori statistici locali per il log di fine trasmissione
    light_count = 0
    noise_count = 0

    try:
        # Apertura sicura del file CSV normalizzato impostando la codifica corretta
        with open(FILE, newline="", encoding="utf-8") as f:
            # Utilizzo di DictReader per mappare automaticamente le colonne in chiavi di dizionario per riga
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Estrazione e rimozione di spazi di contorno dai campi testuali della riga corrente
                    studente = row["studente"].strip()
                    sensore = row["sensore"].lower().strip()
                    luogo = row["luogo"].strip()

                    # Casting esplicito del valore
                    valore = float(row["valore"])

                    # Selezione logica basata sulla tipologia normalizzata di sensore
                    if sensore in ["luce", "l"]:
                        msg = f"INVIA,{studente},luce,{valore},{luogo}"
                        client.send(msg.encode())
                        risposta = client.recv(1024).decode()
                        print(f"Canale Luce [Trasmesso] -> Feedback Server: {risposta}.")
                        light_count += 1

                    elif sensore in ["rumore", "r"]:
                        msg = f"INVIA,{studente},rumore,{valore},{luogo}"
                        client.send(msg.encode())
                        risposta = client.recv(1024).decode()
                        print(f"Canale Rumore [Trasmesso] -> Feedback Server: {risposta}.")
                        noise_count += 1

                    else:
                        # Avviso in caso di record spuri non filtrati dall'adattatore
                        print(f"Riga ignorata per anomalia sensore '{sensore}' legato a {studente}.")
                        continue

                    # Ritardo intenzionale di 0.5 secondi (mezzo secondo) tra gli invii per evitare la saturazione
                    # dei buffer del server e simulare un invio ordinato e controllabile dei record storici
                    time.sleep(0.5)

                except (KeyError, ValueError) as format_err:
                    # Cattura selettiva degli errori di formato del CSV interno, stampando l'esatta riga per debug
                    print(f"Errore di conformità dati alla riga {reader.line_num}: {format_err}. Record rimosso.")
                    continue

                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                    # Intercettazione del blocco di rete: se il server si spegne a metà della trasmissione, il client si arresta
                    print("\nErrore critico di rete: Il server centrale ha interrotto il canale. Trasmissione dati interrotta.")
                    break

                except Exception as e:
                    print(f"Anomalia imprevista alla riga {reader.line_num}: {e}")
                    continue

    except FileNotFoundError:
        print(f"Errore operativo: Il file di trasmissione '{FILE}' non è stato trovato. Eseguire prima l'adattatore.")
        client.close()
        return

    # Stampa del riepilogo finale dell'attività di caricamento dati
    print(f"Procedura conclusa. Record totali elaborati -> Luce: {light_count}, Rumore: {noise_count}")
    client.close()

if __name__ == "__main__":
    main()