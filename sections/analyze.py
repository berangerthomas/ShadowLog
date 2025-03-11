import polars as pl
import streamlit as st
import ipaddress
import plotly.express as px
import pandas as pd

if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None

# Page title
st.title("Data Analysis")

# Vérifier que les données sont chargées
if st.session_state.parsed_df is None:
    st.info("Please upload a log file on the 'Upload' page.")
    st.stop()

data = st.session_state.parsed_df

university_subnets = [
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("10.79.0.0/16"),
    ipaddress.ip_network("159.84.0.0/16"),
]

# Fonction pour vérifier si une IP appartient aux sous-réseaux universitaires
def is_university_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in subnet for subnet in university_subnets)
    except ValueError:
        return False 

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

    # Graphique

    st.write("### 🔴 Analysis of Blocked Attempts")

    if "ipsrc" in data.columns and "action" in data.columns:
        # Filtrer uniquement les tentatives bloquées
        blocked_attempts = data.filter(pl.col("action") == "DENY")

        # Compter les occurrences des IP sources bloquées
        blocked_ips = (
            blocked_attempts
            .group_by("ipsrc")
            .agg(pl.count("ipsrc").alias("count"))
            .sort("count", descending=True)
        )

       
        top_n = st.slider(" ", 5, 20, 10, key="top_n_slider")

        # Sélectionner le Top N des IP bloquées
        top_blocked_ips = blocked_ips.head(top_n)


        # ---- GRAPHIQUE AVEC PLOTLY ----
        color_palette = px.colors.sequential.Blues
        if not top_blocked_ips.is_empty():
            fig = px.bar(
                top_blocked_ips.to_pandas(),  # Convertir en DataFrame Pandas pour Plotly
                x="count",
                y="ipsrc",
                orientation="h",
                text="count",
                title=f"Top {top_n} Most Blocked IPs",
                labels={"ipsrc": "IP Source", "count": "Number of Blocked Attempts"},
                color_discrete_sequence=["#3d85c6"] 
            )

            # Amélioration du layout
            fig.update_traces(texttemplate='%{text}', textposition='inside')
            fig.update_layout(yaxis=dict(categoryorder="total ascending"))

            # Afficher le graphique interactif
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No blocked attempts found.")
    else:
        st.warning("Columns 'ipsrc' or 'action' not found.")

    # Graphique de série temporelle des connexions par heure
    st.write("### 📊 Hourly Connection Activity")

    if "timestamp" in data.columns:
        # Extraire uniquement les connexions autorisées (PERMIT) et valider le format datetime
        activity_data = (
            data
            .filter(pl.col("action") == "PERMIT")  # Ne garder que les connexions autorisées
            .with_columns(pl.col("timestamp").dt.strftime("%Y-%m-%d %H:00:00").alias("hour"))  # Normaliser à l'heure
            .group_by("hour")
            .agg(pl.count("hour").alias("connection_count"))  # Compter les connexions par heure
            .sort("hour")  # Trier chronologiquement
        )

        # Vérifier si on a des données après filtrage
        if not activity_data.is_empty():
            # Convertir en DataFrame Pandas pour Plotly
            df_activity = activity_data.to_pandas()
            df_activity["hour"] = pd.to_datetime(df_activity["hour"])  # Assurer le bon format datetime

            # Tracer le graphique
            fig = px.line(
                df_activity,
                x="hour",
                y="connection_count",
                markers=True,  # Ajouter des points pour bien voir les pics
                title="Hourly Connection Activity",
                labels={"hour": "Hour", "connection_count": "Number of Connections"},
                line_shape="spline"  # Rendre les courbes lisses
            )

            # Afficher le graphique
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No connection data found for the selected period.")
    else:
        st.warning("Column 'timestamp' not found.")



# Onglet Foreign IP addresses
with tab3:
    st.subheader("🚫 List of access outside the university network")

    if "ipsrc" in data.columns and "action" in data.columns:
        # Conversion des IPs en chaînes de caractères pour éviter les erreurs de type
        data = data.with_columns([
            pl.col("ipsrc").cast(pl.Utf8).alias("ipsrc"),
            pl.col("action").cast(pl.Utf8).alias("action")
        ])

        # Vérification des IPs avec la fonction is_university_ip
        data = data.with_columns([
            pl.col("ipsrc").map_elements(is_university_ip, return_dtype=pl.Boolean).alias("is_src_university_ip")
        ])

        # filtrer toutes les connexions impliquant une adresse externe
        intrusion_attempts = data.filter(
            (~pl.col("is_src_university_ip"))
        )
        # Ajout d'un filtre par action
        selected_action = st.selectbox("Select action type", ["All", "PERMIT", "DENY"])

        if selected_action != "All":
            intrusion_attempts = intrusion_attempts.filter(
                pl.col("action") == selected_action
            )
        # Affichage des accès externes
        st.write(f"### 🔍 External accesses: {intrusion_attempts.shape[0]} entries")
        st.dataframe( intrusion_attempts.drop(["is_src_university_ip"]), use_container_width=True)

    else:
        st.warning("Columns 'ipsrc' not found.")



# Onglet Sankey
with tab4:
    st.subheader("Sankey Diagram")
