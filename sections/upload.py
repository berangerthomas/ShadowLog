import os
import sqlite3
import tempfile
from datetime import datetime

import polars as pl
import streamlit as st

st.title("ShadowLog - Log File Analyzer")
st.write("Upload a log file to analyze with the following format :")
st.write(
    """
    <style>
        table, th, td {
            border: 1px solid black;
            border-collapse: collapse;
            text-align: center;
        }
    </style>
    <table>
        <thead>
            <tr>
                <th>Column name</th>
                <td>timestamp</td>
                <td>ipsrc</td>
                <td>ipdst</td>
                <td>protocole</td>
                <td>portsrc</td>
                <td>portdst</td>
                <td>rule</td>
                <td>action</td>
                <td>interface</td>
                <td>unknown</td>
                <td>fw</td>
            </tr>
        </thead>
        <tbody>
            <tr>
                <th>Format</th>
                <td>YYYY-MM-DD HH:MM:SS</td>
                <td>str</td>
                <td>str</td>
                <td>str</td>
                <td>int</td>
                <td>int</td>
                <td>int</td>
                <td>str</td>
                <td>str</td>
                <td>str</td>
                <td>int</td>
            </tr>
        </tbody>
    </table>
    """,
    unsafe_allow_html=True,
)

# Add checkbox for date filtering
apply_date_filter = st.checkbox(
    "Apply date filtering (Nov 1, 2024 - Mar 1, 2025)", value=True
)

uploaded_file = st.file_uploader("Choose a log file")

if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None

if uploaded_file is not None:
    with st.spinner("Parsing and filtering the file..."):
        try:
            # Read the CSV
            st.session_state.parsed_df = pl.read_csv(
                uploaded_file,
                separator=";",
                has_header=False,
                infer_schema_length=10000,
                dtypes={
                    "timestamp": pl.Datetime,
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
            ).drop(["portsrc", "unknown", "fw"])

            # Apply date filter only if checkbox is checked
            if apply_date_filter:
                st.session_state.parsed_df = st.session_state.parsed_df.filter(
                    (pl.col("timestamp") >= pl.datetime(2024, 11, 1))
                    & (pl.col("timestamp") < pl.datetime(2025, 3, 1))
                )

            row_count = st.session_state.parsed_df.height
            if row_count == 0:
                st.error("No data found in the file.")
            else:
                st.success(
                    f"File parsed and filtered successfully! After filtering, {row_count:,} rows remain."
                )
        except Exception as e:
            st.error(f"Error parsing the file: {e}")

    if st.session_state.parsed_df is not None:
        if st.button("Convert to SQLite"):
            with st.spinner("Converting to SQLite..."):
                # Create a temporary file for the SQLite database
                temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
                temp_db_path = temp_db_file.name
                temp_db_file.close()

                # Connect to SQLite database
                conn = sqlite3.connect(temp_db_path)

                # Convert Polars DataFrame to Pandas for easy SQLite export
                pandas_df = st.session_state.parsed_df.to_pandas()

                # Write to SQLite
                pandas_df.to_sql("logs", conn, if_exists="replace", index=False)
                conn.close()

                # Prepare file for download
                with open(temp_db_path, "rb") as file:
                    db_contents = file.read()

                # Create download button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="Download SQLite Database",
                    data=db_contents,
                    file_name=f"logs_{timestamp}.sqlite3",
                    mime="application/octet-stream",
                )

                # Clean up
                os.unlink(temp_db_path)

                st.success("SQLite conversion complete!")
