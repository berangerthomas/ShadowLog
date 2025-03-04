import base64

import streamlit as st

st.set_page_config(page_title=" ShadowLog ", page_icon="assets/logo.png", layout="wide")


def add_logo():
    # Lecture du fichier image local
    with open("assets/small_logo_no_text.png", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
            [data-testid="stSidebarNav"] {{
                background-image: url("data:image/png;base64,{logo_data}");
                background-repeat: no-repeat;
                padding-top: 225px;
                background-position: center 20px;
                background-size: 50%;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


add_logo()


# Pages definition
home = st.Page("sections/home.py", title="🏠 Home")
upload = st.Page("sections/upload.py", title="📥 Upload")
analyze = st.Page("sections/analyze.py", title=" 📊 Analyze")
alerts = st.Page("sections/alerts.py", title=" 📊 Alerts")
about = st.Page("sections/about.py", title="📄 About")

pg = st.navigation([home, upload, analyze, alerts, about])
pg.run()
