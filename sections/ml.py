import pandas as pd
import plotly.express as px
import streamlit as st

if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None

# Page title
st.title("Machine Learning")

# Loading data
if st.session_state.parsed_df is None:
    st.info("Please upload a log file on the 'Upload' page.")
    st.stop()

data = st.session_state.parsed_df

# Sidebar for controls
st.dataframe(data)


##############################################
####            Preprocessing             ####
##############################################



###############################################
####              Clustering               ####
###############################################