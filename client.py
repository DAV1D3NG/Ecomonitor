import socket

# Definizione dei parametri di indirizzamento per la connessione al server centrale
HOST = '127.0.0.1'
PORT = 5000

def main():
    """
    Avvia l'interfaccia interattiva a riga di comando (CLI) del client manuale,
    permettendo all'utente di connettersi al server e inviare singole misurazioni.
    :returns: Nessun valore di ritorno.
    :rtype: None
    """
    # Creazione del socket endpoint del client per comunicazioni su protocollo TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Avvio della procedura di connessione verso il server
        client.connect((HOST, PORT))

    except ConnectionRefusedError:
        print("Errore: Impossibile stabilire una connessione. Il server centrale è offline.")
        return

    # Inizializzazione della sessione con l'identificativo dell'operatore
    # Viene applicata una sostituzione protettiva per evitare che l'uso accidentale di virgole corrompa il formato del protocollo
    nome = input("Inserire il nome dello studente rilevatore: ").replace(",", " ")

    while True:
        # Menù interattivo di selezione comandi
        comando = input("Digitare comando operativo (INVIA / CODA / ESCI): ").upper().strip()

        if comando == "INVIA":
            # Acquisizione e sanificazione dei dati
            sensore = input("Specificare tipologia sensore (luce / rumore): ").replace(",", " ")
            valore = input("Inserire l'intensità numerica rilevata (es. 2): ").replace(",", " ")
            luogo = input("Specificare l'ambiente di campionamento (es. Aula 1): ").replace(",", " ")

            # Composizione della stringa di pacchetto secondo la sintassi del protocollo applicativo
            msg = f"INVIA,{nome},{sensore},{valore},{luogo}"

            # Serializzazione della stringa in flusso di byte e trasmissione sul socket TCP
            client.send(msg.encode())

            # Lettura sincrona della risposta inviata dal server (chiamata bloccante)
            risposta = client.recv(1024).decode()
            print("Risposta Server:", risposta)

        elif comando == "CODA":
            # Richiesta dello stato di riempimento della coda del server
            client.send("CODA".encode())
            risposta = client.recv(1024).decode()
            print("Stato Server:", risposta)

        elif comando == "ESCI":
            # Segnalazione di terminazione controllata al server
            client.send("ESCI".encode())
            break  # Interruzione del ciclo principale di input

    # Rilascio delle risorse di rete lato client
    client.close()
    print("Sessione terminata correttamente.")

if __name__ == "__main__":
    main()