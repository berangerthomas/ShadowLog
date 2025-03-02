import tempfile

import streamlit as st

from config.log_definitions import log_definitions
from utils.log2pandas import LogParser

st.title("Log Analyzer")

# Upload area by drag and drop
uploaded_file = st.file_uploader("Drop your log file here")

# Dropdown menu to choose the log type

# Extract log types from the configuration file
log_types = list(log_definitions.keys())

log_type = st.selectbox("Select log type", options=log_types)

# Analyze button
if st.button("Analyze"):
    if uploaded_file is not None:
        # Temporarily save the uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_file_path = tmp_file.name

        # Create an instance of LogParser with the temporary path and log type
        parser = LogParser(tmp_file_path, log_type)
        # Parse the file and get the DataFrame
        parsed_df = parser.parse_file()
        # Display the first rows of the resulting DataFrame
        st.write("Resulting DataFrame:")
        st.dataframe(parsed_df)
    else:
        st.error("Please upload a log file.")
