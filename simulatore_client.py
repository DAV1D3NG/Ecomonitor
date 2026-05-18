import socket
import time
import random

# Parametri di connessione all'infrastruttura server
HOST = '127.0.0.1'
PORT = 5000

def genera_luce():
    """
    Genera un valore numerico decimale casuale per simulare la misurazione dell'intensità luminosa.
    :returns: Un valore casuale arrotondato a due cifre decimali.
    :rtype: float
    """
    return round(random.uniform(0.0, 10.0), 2)

def genera_rumore():
    """"
    Genera un valore numerico decimale casuale per simulare la misurazione dell'intensità sonora.
    :returns: Un valore  casuale arrotondato a due cifre decimali.
    :rtype: float
    """
    return round(random.uniform(-50.0, 50.0), 2)

def main():
    """
    Ciclo principale del simulatore automatico.
    Genera autonomamente e trasmette dati al server ogni tot secondi ed è arrestabile con CTRL+C.
    :returns: Nessun valore di ritorno.
    :rtype: None
    """
    # Definizione delle costanti fisse del simulatore
    nome = "Simulatore"
    luogo = "Ambiente_Simulato"
    tempo_trasmissione = 60

    print("Simulatore automatico avviato. Premere CTRL+C per interrompere.")
    try:
        while True:
            try:
                # Il socket viene istanziato, connesso e chiuso all'interno del ciclo.
                # Questo approccio garantisce che, in caso di riavvio temporaneo del server,
                # il simulatore non vada in crash definitivo, ma tenti di riconnettersi al ciclo successivo.
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((HOST, PORT))

                # Generazione e trasmissione dei dati di luminosità
                val_luce = genera_luce()
                msg_luce = f"INVIA,{nome},luce,{val_luce},{luogo}"
                client.send(msg_luce.encode())
                print(f"Inviato parametro Luce: {val_luce} -> Risposta: {client.recv(1024).decode()}")

                # Generazione e trasmissione dei dati di pressione acustica
                val_rumore = genera_rumore()
                msg_rumore = f"INVIA,{nome},rumore,{val_rumore},{luogo}"
                client.send(msg_rumore.encode())
                print(f"Inviato parametro Rumore: {val_rumore} -> Risposta: {client.recv(1024).decode()}")

                # Chiusura del socket corrente per liberare risorse durante la fase di sleep
                client.close()

            except ConnectionRefusedError:
                print(f"Server momentaneamente non raggiungibile. Nuovo tentativo tra {tempo_trasmissione} secondi.")

            # Temporizzazione del campionamento: sospende il thread per tot secondi
            time.sleep(tempo_trasmissione)

    except KeyboardInterrupt:
        print("\nProcesso di simulazione interrotto dall'utente.")

if __name__ == "__main__":
    main()