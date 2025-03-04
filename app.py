#####################################################
####                 Imports                     ####
#####################################################
import os
import tempfile
from datetime import datetime

import streamlit as st

from config.log_definitions import log_definitions
from utils.log2pandas import LogParser
from utils.pandas2sql import Pandas2SQL

#####################################################
####              Interface Setup               ####
#####################################################

st.title("ShadowLog - Log File Analyzer")
st.write("Upload a log file to analyze and/or convert it to SQLite")

# File upload widget
uploaded_file = st.file_uploader("Choose a log file")

# Get available log types from log_definitions
log_types = list(log_definitions.keys())
# Set default log type if not already in session state
if "log_type" not in st.session_state:
    st.session_state.log_type = log_types[0]  # Default to first log type

st.session_state.log_type = st.selectbox(
    "Select log type", log_types, index=log_types.index(st.session_state.log_type)
)

# Store the parsed dataframe in the session state
if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None

if uploaded_file is not None:
    # Create two columns for the buttons
    col1, col2 = st.columns(2)

    with col1:
        # Button to parse the log file
        if st.button("Parse the log file"):
            with st.spinner("Analyzing the file..."):
                # Create a temporary file
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".log"
                ) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                try:
                    # Parse the log file
                    parser = LogParser(tmp_path, st.session_state.log_type)
                    st.session_state.parsed_df = parser.parse_file()

                    # Display a success message and the dataframe
                    st.success("Log file successfully analyzed!")
                    # st.dataframe(st.session_state.parsed_df)
                except Exception as e:
                    st.error(f"Error analyzing the file: {e}")
                finally:
                    # Clean up the temporary file
                    os.unlink(tmp_path)

    with col2:
        # Button to convert to SQLite and download
        if st.button("Convert to SQLite"):
            if st.session_state.parsed_df is not None:
                with st.spinner("Converting to SQLite..."):
                    try:
                        # Create a temporary SQLite file
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        sqlite_path = os.path.join(
                            tempfile.gettempdir(), f"log_data_{timestamp}.sqlite"
                        )

                        # Create the SQL converter
                        sql_converter = Pandas2SQL(sqlite_path)

                        # Convert the dataframe to SQLite
                        sql_converter.create_table(
                            st.session_state.parsed_df, st.session_state.log_type
                        )

                        # Read the SQLite file for download
                        with open(sqlite_path, "rb") as file:
                            sqlite_data = file.read()

                        # Success message and immediate download
                        st.success("SQLite file created successfully!")

                        # Download button
                        st.download_button(
                            label="Download SQLite file",
                            data=sqlite_data,
                            file_name=f"log_file_{st.session_state.log_type}_{timestamp}.sqlite",
                            mime="application/octet-stream",
                            key="auto_download",
                        )
                    except Exception as e:
                        st.error(f"Error converting to SQLite: {e}")
                    finally:
                        # Clean up the temporary file
                        if os.path.exists(sqlite_path):
                            os.unlink(sqlite_path)
            else:
                st.warning("Please parse the log file first.")

# Display the dataframe if available
if st.session_state.parsed_df is not None:
    st.subheader("Analyzed log data")
    st.dataframe(st.session_state.parsed_df)
