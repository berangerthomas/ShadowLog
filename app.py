import tempfile

import streamlit as st

from config.log_definitions import log_definitions
from utils.log2pandas import LogParser

st.title("Analyseur de Logs")

# Zone d'upload par drag and drop
uploaded_file = st.file_uploader("Déposez votre fichier log")

# Menu déroulant pour choisir le type de log

# Extraire les types de log à partir du fichier de configuration
log_types = list(log_definitions.keys())

log_type = st.selectbox("Sélectionnez le type de log", options=log_types)

# Bouton d'analyse
if st.button("Analyser"):
    if uploaded_file is not None:
        # Sauvegarder temporairement le fichier uploader
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_file_path = tmp_file.name

        # Créer une instance de LogParser avec le chemin temporaire et le type de log
        parser = LogParser(tmp_file_path, log_type)
        # Analyser le fichier et récupérer le DataFrame
        parsed_df = parser.parse_file()
        # Afficher les premières lignes du DataFrame résultat
        st.write("DataFrame résultant:")
        st.dataframe(parsed_df)
    else:
        st.error("Veuillez charger un fichier log.")
