import pandas as pd
import os

# Configurazione del percorso del file sorgente e dei metadati associati all'esperimento reale
FILE_PHYPHOX = "Light.csv"  # File di input generato dall'esportazione di Phyphox
NOME_STUDENTE = "Davide"  # Autore del campionamento sul campo
LUOGO_MISURA = "Lab. Info 6"  # Ambiente fisico in cui è avvenuto il test

def main():
    """
    Analizza un file CSV grezzo esportato dall'app Phyphox, ne identifica il sensore,
    normalizza i separatori decimali e lo schema colonne, salvandolo in un formato compatibile.
    :returns: Nessun valore di ritorno.
    :rtype: None
    """
    # Verifica preventiva di esistenza del file sorgente dei dati grezzi (per evitare eccezioni di tipo FileNotFoundError)
    if not os.path.exists(FILE_PHYPHOX):
        print(f"Errore di configurazione: Il file sorgente '{FILE_PHYPHOX}' non è presente nella cartella corrente.")
        return

    try:
        # Controllo del separatore: Phyphox esporta usando la virgola o il punto e virgola
        df = pd.read_csv(FILE_PHYPHOX, sep=",")

        # Se il DataFrame possiede una sola colonna, significa che il file utilizza il punto e virgola come separatore
        if len(df.columns) <= 1:
            df = pd.read_csv(FILE_PHYPHOX, sep=";")

        # Rimozione di spazi bianchi inutili dai nomi delle colonne tramite una list comprehension
        colonne = [col.strip() for col in df.columns]

        tipo_sensore = None
        colonna_valore = None

        # Riconoscimento automatico del sensore basato sulle stringhe di intestazione esatte di Phyphox
        if "Illuminance (lx)" in colonne:
            tipo_sensore = "luce"
            colonna_valore = "Illuminance (lx)"
            print("Firma strutturale riconosciuta: Tracciato sensore di LUMINOSITÀ (Luce)")

        elif "Sound pressure level (dB)" in colonne:
            tipo_sensore = "rumore"
            colonna_valore = "Sound pressure level (dB)"
            print("Firma strutturale riconosciuta: Tracciato sensore di PRESSIONE ACUSTICA (Rumore)")

        else:
            # Flusso di controllo alternativo in caso di intestazioni personalizzate o versioni software differenti
            print("Analisi automatica fallita. Colonne rilevate nel file sorgente:", colonne)
            risposta = input("Digitare manualmente la tipologia di dati (luce / rumore): ").strip().lower()
            if risposta in ["luce", "rumore"]:
                tipo_sensore = risposta
                colonna_valore = df.columns[1]  # Assunzione standard: la seconda colonna contiene la grandezza misurata
            else:
                print("Opzione non valida. Procedura di conversione interrotta.")
                return

        # Costruzione del nuovo schema dati normalizzato tramite allocazione di un DataFrame vuoto
        df_nuovo = pd.DataFrame()

        # Clona i metadati fissi (studente, sensore, e dopo luogo) su tutte le righe del nuovo DataFrame
        df_nuovo["studente"] = [NOME_STUDENTE] * len(df)
        df_nuovo["sensore"] = [tipo_sensore] * len(df)

        # Normalizzazione dei valori numerici e sostituzione delle virgole decimali con i punti prima del casting numerico
        valori = df[colonna_valore].astype(str).str.replace(",", ".")

        # Conversione al tipo numerico float ed eventuali record corrotti o stringhe vuote vengono convertiti in NaN (coerce)
        df_nuovo["valore"] = pd.to_numeric(valori, errors="coerce")

        df_nuovo["luogo"] = [LUOGO_MISURA] * len(df)

        # La colonna data_ora viene lasciata intenzionalmente vuota,
        # poiché sarà il server ad apporre l'orario ufficiale di ricezione dei pacchetti
        df_nuovo["data_ora"] = ""

        # Pulizia del dataset eliminando le righe che presentano valori non numerici validi (NaN)
        df_nuovo = df_nuovo.dropna(subset=["valore"])

        # Esportazione del file normalizzato definitivo, pronto per essere elaborato dal modulo client phyphox
        df_nuovo.to_csv("dati_phyphox.csv", index=False, sep=",")
        print(f"Operazione completata con successo. Generati {len(df_nuovo)} record coerenti in 'dati_phyphox.csv'.")

    except Exception as e:
        print(f"Errore fatale imprevisto durante la trasformazione del dataset: {e}")

if __name__ == "__main__":
    main()