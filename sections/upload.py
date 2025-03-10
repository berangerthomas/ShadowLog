import os
import tempfile
from datetime import datetime

import polars as pl
import streamlit as st

from utils.pandas2sql import Pandas2SQL

st.title("ShadowLog - Log File Analyzer")
st.write("Upload a log file to analyze with the following format :")
st.write("date;ipsrc;ipdst;protocole;portsrc;portdst;rule;action;interface;unknown;fw")

uploaded_file = st.file_uploader("Choose a log file")

if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None

if uploaded_file is not None:
    with st.spinner("Parsing and filtering the file..."):
        try:
            st.session_state.parsed_df = (
                pl.read_csv(
                    uploaded_file,
                    separator=";",
                    has_header=False,
                    infer_schema_length=10000,
                    dtypes={
                        "date": pl.Datetime,
                        "ipsrc": pl.Utf8,
                        "ipdst": pl.Utf8,
                        "protocole": pl.Utf8,
                        "portsrc": pl.Int64,
                        "portdst": pl.Int64,
                        "rule": pl.Int64,
                        "action": pl.Utf8,
                        "interface": pl.Utf8,
                        "unknown": pl.Utf8,
                        "fw": pl.Int64,
                    },
                )
                .filter(
                    (pl.col("date") >= pl.datetime(2024, 11, 1))
                    & (pl.col("date") < pl.datetime(2025, 3, 1))
                )
                .drop(["portsrc", "unknown", "fw"])
            )
            st.success("File parsed and filtered successfully!")
        except Exception as e:
            st.error(f"Error parsing the file: {e}")

    if st.session_state.parsed_df is not None:
        if st.button("Convert to SQLite"):
            with st.spinner("Converting to SQLite..."):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    sqlite_path = os.path.join(
                        tempfile.gettempdir(), f"log_data_{timestamp}.sqlite"
                    )
                    sql_converter = Pandas2SQL(sqlite_path)
                    sql_converter.create_table(
                        st.session_state.parsed_df.to_pandas(),
                        st.session_state.log_type,
                    )
                    with open(sqlite_path, "rb") as file:
                        sqlite_data = file.read()
                    st.success("SQLite file created successfully!")
                    st.download_button(
                        label="Download SQLite file",
                        data=sqlite_data,
                        file_name=f"log_file_{st.session_state.log_type}_{timestamp}.sqlite",
                        mime="application/octet-stream",
                    )
                except Exception as e:
                    st.error(f"Error converting to SQLite: {e}")
                finally:
                    if os.path.exists(sqlite_path):
                        os.unlink(sqlite_path)

if st.session_state.parsed_df is not None:
    st.subheader("Parsed log data")
    st.dataframe(st.session_state.parsed_df)
