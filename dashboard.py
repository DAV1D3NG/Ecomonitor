import pandas as pd
import streamlit as st
from pathlib import Path

# Definizione del percorso relativo dell'archivio centrale e dello schema colonne atteso
CSV_FILE = Path("misure.csv")
COLUMNS = ["studente", "sensore", "valore", "luogo", "data_ora"]

def load_data():
    """
    Verifica l'esistenza del database CSV, importa i record grezzi utilizzando Pandas,
    converte i tipi di dato e rimuove le righe non conformi o con misurazioni vuote.
    :returns: Un DataFrame contenente il dataset pulito, normalizzato e pronto all'analisi visiva.
    :rtype: pandas.DataFrame
    """
    # Se il server non ha ancora creato il file, o se il dataframe del csv è vuoto, ritorna un DataFrame vuoto strutturato
    if not CSV_FILE.exists():
        return pd.DataFrame(columns=COLUMNS)

    df = pd.read_csv(CSV_FILE)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)

    # Assicura la presenza di tutte le colonne richieste per evitare KeyError nella UI
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Trasformazione e conversione dei tipi per la manipolazione analitica
    df["valore"] = pd.to_numeric(df["valore"], errors="coerce")  # Forza i valori a float, inserendo NaN dove fallisce
    df["data_ora"] = pd.to_datetime(df["data_ora"], errors="coerce")  # Converte le stringhe in oggetti Datetime nativi

    # Rimozione preventiva di righe prive di valore numerico valido
    df = df.dropna(subset=["valore"])
    return df

def main():
    """
    Costruisce la struttura grafica della Web Application interattiva di Streamlit,
    gestendo l'applicazione dei filtri e l'aggiornamento dei grafici.
    :returns: Nessun valore di ritorno.
    :rtype: None
    """
    # Configurazione dell'ambiente grafico della pagina Streamlit impostando il layout espanso (wide)
    st.set_page_config(page_title="EcoMonitor Analytics", layout="wide")
    st.title("Piattaforma di Monitoraggio Ambientale Scolastico - EcoMonitor")
    st.caption("Analisi statistica di dati relativi a luce e rumore.")

    # Caricamento del dataset memorizzato su disco
    df = load_data()

    # Interruzione anticipata del rendering se non vi sono informazioni utili da mostrare
    if df.empty:
        st.info("Nessun dato attualmente registrato nel database di sistema.")
        return

    # --- SEZIONE GESTIONE FILTRI INTERATTIVI (SIDEBAR) ---
    st.sidebar.header("Pannello di Controllo Filtri")

    # Estrazione e ordinamento dinamici delle voci del filtro Sensori
    sensors = ["Tutti"] + sorted(df["sensore"].dropna().astype(str).unique().tolist())
    selected_sensor = st.sidebar.selectbox("Filtra per Tipologia Sensore", sensors)

    # Estrazione e ordinamento dinamici delle voci del filtro Luoghi
    places = ["Tutti"] + sorted(df["luogo"].dropna().astype(str).unique().tolist())
    selected_place = st.sidebar.selectbox("Filtra per Ambiente / Aula", places)

    # Estrazione e ordinamento dinamici delle voci del filtro Studenti
    students = ["Tutti"] + sorted(df["studente"].dropna().astype(str).unique().tolist())
    selected_student = st.sidebar.selectbox("Filtra per Studente Rilevatore", students)

    # Applicazione sequenziale dei filtri selezionati riducendo progressivamente una copia del dataframe originale
    filtered = df.copy()
    if selected_sensor != "Tutti":
        filtered = filtered[filtered["sensore"] == selected_sensor]
    if selected_place != "Tutti":
        filtered = filtered[filtered["luogo"] == selected_place]
    if selected_student != "Tutti":
        filtered = filtered[filtered["studente"] == selected_student]

    # --- SEZIONE RENDERING METRICHE GENERALI ---
    st.subheader("Numero e Medie delle Misurazioni")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Visualizzazione del numero totale dei campionamenti effettuati nel set filtrato
        st.metric(label="Misure Totali", value=len(filtered))

    with col2:
        # Calcolo della media matematica per il sensore Luce (Lux) all'interno del dataset filtrato
        light_subset = filtered[filtered["sensore"] == "luce"]

        if not light_subset.empty:
            mean_light = round(light_subset["valore"].mean(), 2)
            st.metric(label="Intensità Luminosa Media", value=f"{mean_light} lx")
        else:
            st.metric(label="Intensità Luminosa Media", value="N/D")

    with col3:
        # Calcolo della media matematica per il sensore Rumore (Decibel) all'interno del dataset filtrato
        noise_subset = filtered[filtered["sensore"] == "rumore"]

        if not noise_subset.empty:
            mean_noise = round(noise_subset["valore"].mean(), 2)
            st.metric(label="Livello di Rumore Medio", value=f"{mean_noise} dB")
        else:
            st.metric(label="Livello di Rumore Medio", value="N/D")

    # --- SEZIONE RENDERING GRAFICI A BARRE ---
    st.write("---")
    left, right = st.columns(2)

    with left:
        st.subheader("Distribuzione dei Campionamenti per Luogo")
        # Raggruppamento Pandas per contare la frequenza delle misurazioni in ciascun ambiente
        place_counts = filtered.groupby("luogo").size().reset_index(name="conteggio")

        if not place_counts.empty:
            # Generazione automatica di un grafico a barre categorico impostando il luogo come indice grafico
            st.bar_chart(place_counts.set_index("luogo")["conteggio"])
        else:
            st.info("Nessun record disponibile per mappare la distribuzione spaziale.")

    with right:
        st.subheader("Attività di Campionamento per Singolo Studente")
        # Conteggio delle misure inviate da ciascuno studente per monitorare l'attività del progetto
        student_counts = filtered.groupby("studente").size().reset_index(name="conteggio")

        if not student_counts.empty:
            # Generazione automatica di un grafico a barre categorico impostando lo studente come indice grafico
            st.bar_chart(student_counts.set_index("studente")["conteggio"])
        else:
            st.info("Nessun record disponibile per mappare l'attività degli studenti.")

    # --- SEZIONE RENDERING ANDAMENTO TEMPORALE (GRAFICI LINEARI) ---
    st.write("---")
    st.subheader("Analisi Storica e Andamento Temporale dei Parametri")

    # Separazione netta dei tipi di dati per evitare la sovrapposizione geometrica di scale incompatibili (lx vs dB)
    light_chart = filtered[filtered["sensore"] == "luce"]
    noise_chart = filtered[filtered["sensore"] == "rumore"]

    # Visualizzazione andamento temporale sensore Luce
    st.write("Evoluzione Cronologica della Luminosità")
    if not light_chart.empty:
        # Ordinamento cronologico per garantire la correttezza geometrica del grafico lineare
        light_chart = light_chart.sort_values("data_ora")
        
        # Formattazione della stringa dell'asse temporale per ottimizzare la leggibilità sull'interfaccia
        light_chart["data_ora_str"] = light_chart["data_ora"].dt.strftime("%Y-%m-%d %H:%M")
        st.line_chart(light_chart.set_index("data_ora_str")["valore"])
    else:
        st.info("Nessun record storico di tipo luminosità registrato per i filtri correnti.")

    # Visualizzazione andamento temporale sensore Rumore
    st.write("Evoluzione Cronologica dell'Inquinamento Acustico")
    if not noise_chart.empty:
        noise_chart = noise_chart.sort_values("data_ora")
        noise_chart["data_ora_str"] = noise_chart["data_ora"].dt.strftime("%Y-%m-%d %H:%M")
        st.line_chart(noise_chart.set_index("data_ora_str")["valore"])
    else:
        st.info("Nessun record storico di tipo pressione acustica registrato per i filtri correnti.")

    # --- SEZIONE RENDERING TABELLA DATI (ADATTATA AI FILTRI) ---
    st.write("---")
    st.subheader("Tabella Dati Completa")
    # Rendering della tabella interattiva ordinata per la misura più recente in cima
    st.dataframe(filtered.sort_values("data_ora", ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()