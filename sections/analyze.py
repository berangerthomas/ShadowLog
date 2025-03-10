import polars as pl
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
            start_date = st.date_input("Start Date", min_date)
            end_date = st.date_input("End Date", max_date)

        # ---- FILTRE action----
        with col2:
            st.markdown("### 🔄 Action")
            if "action" in data.columns:
                unique_action = sorted(
                    data["action"].unique().cast(pl.Utf8).to_list()
                )  # S'assurer du bon format
                selected_action = st.selectbox(
                    "Select an action", ["All"] + unique_action
                )
            else:
                selected_action = "All"
                st.warning("Column 'action' not found.")

        # ---- FILTRE portdst ----
        with col3:
            st.markdown("### 🔢 Port")
            if "portdst" in data.columns:
                min_port, max_port = (
                    int(data["portdst"].min()),
                    int(data["portdst"].max()),
                )

                # Initialize port range in session state if not present
                if "port_range" not in st.session_state:
                    st.session_state.port_range = (min_port, max_port)

                # Quick port range selection buttons
                col_ports1, col_ports2, col_ports3 = st.columns(3)

                # Define button handlers to update session state
                def set_well_known():
                    st.session_state.port_range = (0, 1023)

                def set_registered():
                    st.session_state.port_range = (1024, 49151)

                def set_dynamic():
                    st.session_state.port_range = (49152, 65535)

                with col_ports1:
                    st.button("Well-known (0-1023)", on_click=set_well_known)

                with col_ports2:
                    st.button("Registered (1024-49151)", on_click=set_registered)

                with col_ports3:
                    st.button("Dynamic (49152-65535)", on_click=set_dynamic)

                # Custom range slider that uses and updates the session state
                selected_port = st.slider(
                    "Custom port range",
                    min_port,
                    max_port,
                    value=st.session_state.port_range,
                    key="port_slider",
                )

                # Update port_range when slider changes
                st.session_state.port_range = selected_port
            else:
                min_port, max_port = 0, 65535  # Standard TCP/IP port range
                selected_port = (min_port, max_port)
                st.warning("Column 'portdst' not found, default values applied.")

        # Vérification des dates sélectionnées
        if start_date > end_date:
            st.error("The start date cannot be later than the end date.")
        else:
            # Conversion des dates en datetime
            start_datetime = pl.datetime(
                start_date.year, start_date.month, start_date.day
            )
            end_datetime = pl.datetime(
                end_date.year, end_date.month, end_date.day, 23, 59, 59
            )

            # ---- APPLICATION DES FILTRES ----
            filtered_data = data.filter(
                (pl.col("timestamp") >= start_datetime)
                & (pl.col("timestamp") <= end_datetime)
            )

            # Correction du filtrage par action(forcer conversion Utf8)
            if "action" in data.columns and selected_action != "All":
                filtered_data = filtered_data.filter(
                    pl.col("action").cast(pl.Utf8) == selected_action
                )

            # Filtrer par portdst en prenant en compte min/max
            if "portdst" in data.columns:
                filtered_data = filtered_data.filter(
                    (pl.col("portdst").cast(pl.Int64) >= selected_port[0])
                    & (pl.col("portdst").cast(pl.Int64) <= selected_port[1])
                )

            # Affichage des données filtrées
            st.write(f"### 🔍 Data filtered : {filtered_data.shape[0]} entries")
            st.dataframe(filtered_data)

    else:
        st.warning(
            "The 'timestamp' column does not exist or is not in datetime format."
        )

# Onglet Sankey
with tab2:
    st.subheader("Sankey Diagram")
