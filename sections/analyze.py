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
tab1, tab2, tab3, tab4 = st.tabs(
    ["Dataviz", "Analysis", "Foreign IP addresses", "Sankey"]
)

# Onglet Analysis
with tab1:
    st.subheader("Dataviz")

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
            st.dataframe(filtered_data, use_container_width=True)

    else:
        st.warning(
            "The 'timestamp' column does not exist or is not in datetime format."
        )

# Onglet Analysis
with tab2:
    st.subheader("Analysis")

    # Afficher ici le top 10 des ports inférieurs à 1024 avec accès autorisé
    st.write(
        "### 🔢 Top 10 ports with authorized access"
        " (portdst < 1024 and action == 'PERMIT')"
    )
    top_ports = (
        data.filter((pl.col("portdst") < 1024) & (pl.col("action") == "PERMIT"))
        .group_by("portdst")
        .agg(pl.count("portdst").alias("count"))
        .sort("count", descending=True)
        .head(10)
    )
    st.dataframe(top_ports, use_container_width=True)

    # Afficher ici le top 5 des IP sources les plus émettrices
    st.write("### 🌐 Top 5 emitting IP addresses (ipsource and action == 'PERMIT')")
    top_ips = (
        data.filter(pl.col("action") == "PERMIT")
        .group_by("ipsrc")
        .agg(pl.count("ipsrc").alias("count"))
        .sort("count", descending=True)
        .head(5)
    )
    st.dataframe(top_ips, use_container_width=True)


# Onglet Foreign IP addresses
with tab3:
    # Afficher ici la liste des accès hors plan d’adressage universitaire
    st.write("### 🚫 List of access outside the university network")
    external_access = data.filter(
        ~pl.col("ipdst").cast(pl.Utf8).str.contains(r"^192\.168\.")
        & ~pl.col("ipdst").cast(pl.Utf8).str.contains(r"^10\.79\.")
        & ~pl.col("ipdst").cast(pl.Utf8).str.contains(r"^159\.84\.")
    )
    st.dataframe(external_access, use_container_width=True)

# Onglet Sankey
with tab4:
    st.subheader("Sankey Diagram")
