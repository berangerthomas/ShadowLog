import pandas as pd
import polars as pl
import plotly.express as px
import streamlit as st

if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None

# Page title
st.title("Data Analysis")

# Vérifier que les données sont chargées
if st.session_state.parsed_df is None:
    st.info("Please upload a log file on the 'Upload' page.")
    st.stop()

data = st.session_state.parsed_df

# Créer les onglets principaux
tab1, tab2 = st.tabs(["Analysis", "Sankey"])

# Onglet Analysis
with tab1:
    st.subheader("Analysis")

    # Vérifier que la colonne timestamp existe et est bien de type datetime
    if "timestamp" in data.columns and data["timestamp"].dtype == pl.Datetime:
        # Obtenir les valeurs min et max des dates
        min_date = data["timestamp"].min().date()
        max_date = data["timestamp"].max().date()

        # Disposition des filtres en colonnes
        col1, col2, col3 = st.columns(3)

        # ---- FILTRE DATE ----
        with col1:
            st.markdown("### 📅 Date")
            start_date = st.date_input("Date début", min_date)
            end_date = st.date_input("Date fin", max_date)

        # ---- FILTRE action----
        with col2:
            st.markdown("### 🔄 Action")
            if "action" in data.columns:
                unique_action = sorted(data["action"].unique().cast(pl.Utf8).to_list())  # S'assurer du bon format
                selected_action= st.selectbox("Sélectionnez un action", ["Tous"] + unique_action)
            else:
                selected_action= "Tous"
                st.warning("Colonne 'action' non trouvée.")

        # ---- FILTRE portdst ----
        with col3:
            st.markdown("### 🔢 Port")
            if "portdst" in data.columns:
                min_port, max_port = int(data["portdst"].min()), int(data["portdst"].max())
                selected_port = st.slider("Sélectionnez un port destination", min_port, max_port, (min_port, max_port))
            else:
                min_port, max_port = 0, 600000  # Valeurs par défaut si la colonne est absente
                selected_port = (min_port, max_port)
                st.warning("Colonne 'portdst' non trouvée, valeurs par défaut appliquées.")

        # Vérification des dates sélectionnées
        if start_date > end_date:
            st.error("La date de début ne peut pas être postérieure à la date de fin.")
        else:
            # Conversion des dates en datetime
            start_datetime = pl.datetime(start_date.year, start_date.month, start_date.day)
            end_datetime = pl.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

            # ---- APPLICATION DES FILTRES ----
            filtered_data = data.filter(
                (pl.col("timestamp") >= start_datetime) & (pl.col("timestamp") <= end_datetime)
            )

            # Correction du filtrage par action(forcer conversion Utf8)
            if "action" in data.columns and selected_action!= "Tous":
                filtered_data = filtered_data.filter(pl.col("action").cast(pl.Utf8) == selected_action)

            # Filtrer par portdst en prenant en compte min/max
            if "portdst" in data.columns:
                filtered_data = filtered_data.filter(
                    (pl.col("portdst").cast(pl.Int64) >= selected_port[0]) & 
                    (pl.col("portdst").cast(pl.Int64) <= selected_port[1])
                )

            # Affichage des données filtrées
            st.write("### 🔍 Data filtred :")
            st.dataframe(filtered_data)

    else:
        st.warning("La colonne 'timestamp' n'existe pas ou n'est pas au format datetime.")

# Onglet Sankey
with tab2:
    st.subheader("Sankey Diagram")
    
