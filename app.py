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
home = st.Page("pages/home.py", title="🏠 Home")
upload = st.Page("pages/upload.py", title="📥 Upload")
analyze = st.Page("pages/analyze.py", title=" 📊 Analyze")
about = st.Page("pages/about.py", title="📄 About")

pg = st.navigation([home, upload, analyze, about])
pg.run()
