import streamlit as st
import pandas as pd
import ipaddress
import plotly.express as px
import os

# 📌 Définition du plan d'adressage de l'Université
UNIVERSITY_IP_RANGES = [
    "192.168.0.0/16",
    "10.0.0.0/8",
    "172.16.0.0/12"
]

# 📌 Fichier cache pour accélérer les chargements suivants
CACHE_FILE = "logs_cache.parquet"

# 📌 Fonction optimisée pour lire un gros fichier .log par morceaux (chunks)
@st.cache_data
def load_logs(file, max_lines=1000000):
    col_names = ["timestamp", "ipsource", "ipdestination", "protocole", "portsource", "portdest",
                 "regle1", "status", "interface", "inconnu", "regle2"]
    
    logs_list = []
    chunk_size = 50000  # Charger les logs par paquets de 50 000 lignes pour éviter de saturer la mémoire
    total_loaded = 0

    with st.spinner("⏳ Chargement des logs..."):
        for chunk in pd.read_csv(file, sep=";", names=col_names, parse_dates=["timestamp"], dtype=str, chunksize=chunk_size):
            chunk["portsource"] = pd.to_numeric(chunk["portsource"], errors='coerce')
            chunk["portdest"] = pd.to_numeric(chunk["portdest"], errors='coerce')
            logs_list.append(chunk)
            total_loaded += chunk.shape[0]
            
            if total_loaded >= max_lines:
                break  # On stoppe après max_lines lignes pour un chargement plus rapide

    df = pd.concat(logs_list, ignore_index=True)
    return df

# 📌 Traitement des logs pour extraire les statistiques demandées
def process_logs(df):
    # 📊 1️⃣ TOP 5 des IP sources les plus émettrices
    df_top_ips = df["ipsource"].value_counts().nlargest(5).reset_index()
    df_top_ips.columns = ["ipsource", "count"]

    # 📊 2️⃣ TOP 10 des ports < 1024 avec accès autorisé
    df_ports = df[(df["portdest"] < 1024) & (df["status"] == "PERMIT")]
    df_top_ports = df_ports["portdest"].value_counts().nlargest(10).reset_index()
    df_top_ports.columns = ["portdest", "count"]

    # 🚫 3️⃣ Lister les accès hors plan d’adressage universitaire
    df["is_outside"] = df["ipsource"].apply(lambda ip: not any(ipaddress.ip_address(ip) in ipaddress.ip_network(net) for net in UNIVERSITY_IP_RANGES))
    df_outside_university = df[df["is_outside"]]

    return df_top_ips, df_top_ports, df_outside_university

# 🎨 Interface Streamlit
st.title("⚡ Analyse Optimisée des Logs Réseau")

# 📂 Upload du fichier log
uploaded_file = st.file_uploader("📂 Charger un fichier .log", type="log")

# 🚀 CHARGEMENT OPTIMISÉ
if uploaded_file:
    if os.path.exists(CACHE_FILE):
        st.info("📂 Chargement des logs depuis le cache...")
        df_logs = pd.read_parquet(CACHE_FILE)
    else:
        df_logs = load_logs(uploaded_file)  # Charger seulement 200 000 lignes pour un affichage rapide
        df_logs.to_parquet(CACHE_FILE)  # Stocker en cache pour éviter de recharger à chaque fois

    # 📌 Traitement des logs
    df_top_ips, df_top_ports, df_outside_university = process_logs(df_logs)

    # 📊 TOP 5 des IP sources les plus émettrices
    st.subheader("📊 TOP 5 des IP sources les plus émettrices")
    fig_ips = px.bar(df_top_ips, x="ipsource", y="count", title="TOP 5 IP Sources")
    st.plotly_chart(fig_ips, use_container_width=True)

    # 📊 TOP 10 des ports < 1024 avec accès autorisé
    st.subheader("📊 TOP 10 des ports < 1024 avec accès autorisé")
    fig_ports = px.bar(df_top_ports, x="portdest", y="count", title="TOP 10 Ports Destinataires < 1024 Autorisés")
    st.plotly_chart(fig_ports, use_container_width=True)

    # 🚫 Liste des accès hors plan d’adressage universitaire
    st.subheader("🚫 Accès hors plan d’adressage universitaire")
    st.dataframe(df_outside_university)

    # 💾 Télécharger les résultats filtrés
    st.download_button("💾 Télécharger les IP hors plan d'adressage", df_outside_university.to_csv(index=False), file_name="ips_hors_universite.csv")

st.info("📌 Charge un fichier `.log` pour voir l'analyse.")
