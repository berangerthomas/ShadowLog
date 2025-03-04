import altair as alt
import pandas as pd
import streamlit as st

st.title("📊 Alerts and Anomalies")

if "parsed_df" not in st.session_state or st.session_state.parsed_df is None:
    st.warning(
        "No log data is available. Please first upload and parse a log file in the Upload section."
    )
else:
    df = st.session_state.parsed_df

    # Display overall statistics
    st.subheader("Overview of logs")
    col1, col2, col3 = st.columns(3)

    with col1:
        total_entries = len(df)
        st.metric("Total number of entries", total_entries)

    with col2:
        # Check if the 'level' column exists, otherwise look for a similar column
        level_col = None
        possible_level_cols = ["level", "severity", "log_level", "type", "status"]
        for col in possible_level_cols:
            if col in df.columns:
                level_col = col
                break

        if level_col:
            error_count = df[
                df[level_col]
                .str.upper()
                .isin(["ERROR", "CRITICAL", "FATAL", "FAIL", "I"])
            ].shape[0]
            error_percent = (
                (error_count / total_entries) * 100 if total_entries > 0 else 0
            )
            st.metric("Error entries", f"{error_count} ({error_percent:.1f}%)")
        else:
            # Search in the entire log text if no specific column is found
            text_col = (
                df.select_dtypes(include=["object"]).columns[0]
                if not df.select_dtypes(include=["object"]).empty
                else None
            )
            if text_col:
                error_count = df[
                    df[text_col].str.contains(
                        "ERROR|CRITICAL|FATAL|FAIL|EXCEPTION", case=False, na=False
                    )
                ].shape[0]
                error_percent = (
                    (error_count / total_entries) * 100 if total_entries > 0 else 0
                )
                st.metric("Error entries", f"{error_count} ({error_percent:.1f}%)")
            else:
                st.metric("Error entries", "Not detectable")

    with col3:
        # Search for a datetime type column
        timestamp_col = None

        # First, look for columns that are already of datetime type
        datetime_cols = [
            col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])
        ]
        if datetime_cols:
            timestamp_col = datetime_cols[0]
        else:
            # If no datetime column is found, try to find by name
            possible_ts_cols = ["timestamp", "date", "time", "datetime"]
            for col in possible_ts_cols:
                if col in df.columns:
                    timestamp_col = col
                    break

        if timestamp_col:
            time_range = f"{df[timestamp_col].min()} to {df[timestamp_col].max()}"
            st.markdown(
                f"**Time range**<br><small>{time_range}</small>",
                unsafe_allow_html=True,
            )
        else:
            st.metric("Time range", "Not detectable")

    # Detection of critical errors
    st.subheader("Detected critical errors")

    # Function to identify errors by keywords
    def detect_errors(dataframe):
        # Search in all textual columns
        error_patterns = [
            "error",
            "critical",
            "fatal",
            "fail",
            "exception",
            "crash",
            "timeout",
        ]

        error_df = pd.DataFrame()
        for col in dataframe.select_dtypes(include=["object"]).columns:
            mask = dataframe[col].str.contains(
                "|".join(error_patterns), case=False, na=False
            )
            if error_df.empty:
                error_df = dataframe[mask].copy()
            else:
                error_df = pd.concat([error_df, dataframe[mask]]).drop_duplicates()

        return error_df

    error_logs = detect_errors(df)

    if not error_logs.empty:
        st.write(f"**{len(error_logs)} critical errors detected**")
        st.dataframe(error_logs)

        # Extraction of the most common error types
        if len(error_logs) > 5:
            st.subheader("Frequent error types")
            error_types = {}

            # Browse textual columns to extract error patterns
            for col in error_logs.select_dtypes(include=["object"]).columns:
                for pattern in ["error", "exception", "fail"]:
                    pattern_errors = error_logs[
                        error_logs[col].str.contains(pattern, case=False, na=False)
                    ]
                    if not pattern_errors.empty:
                        # Extract error context (words after the pattern)
                        for _, row in pattern_errors.iterrows():
                            text = str(row[col])
                            if pattern.lower() in text.lower():
                                idx = text.lower().find(pattern.lower())
                                context = (
                                    text[idx : idx + 50].strip()
                                    if idx + 50 < len(text)
                                    else text[idx:].strip()
                                )
                                if context not in error_types:
                                    error_types[context] = 0
                                error_types[context] += 1

            # Display the most frequent error types
            sorted_errors = sorted(
                error_types.items(), key=lambda x: x[1], reverse=True
            )[:10]
            error_df = pd.DataFrame(
                sorted_errors, columns=["Error type", "Occurrences"]
            )
            st.dataframe(error_df)

            # Visualization of errors
            if timestamp_col:
                st.subheader("Temporal distribution of errors")

                # Convert to datetime if necessary
                if not pd.api.types.is_datetime64_any_dtype(error_logs[timestamp_col]):
                    try:
                        error_logs[timestamp_col] = pd.to_datetime(
                            error_logs[timestamp_col]
                        )
                    except:
                        pass

                if pd.api.types.is_datetime64_any_dtype(error_logs[timestamp_col]):
                    # Group by time period
                    error_count = (
                        error_logs.groupby(pd.Grouper(key=timestamp_col, freq="1H"))
                        .size()
                        .reset_index()
                    )
                    error_count.columns = [timestamp_col, "count"]

                    # Create the chart
                    chart = (
                        alt.Chart(error_count)
                        .mark_line()
                        .encode(
                            x=alt.X(f"{timestamp_col}:T", title="Time"),
                            y=alt.Y("count:Q", title="Number of errors"),
                            tooltip=[f"{timestamp_col}:T", "count:Q"],
                        )
                        .properties(width=700, height=300, title="Errors per hour")
                    )
                    st.altair_chart(chart, use_container_width=True)
    else:
        st.success("No critical errors detected in the logs.")

    # Detection of anomalies
    st.subheader("Anomaly detection")

    # Temporal analysis if possible
    if timestamp_col is not None and (
        pd.api.types.is_datetime64_any_dtype(df[timestamp_col])
        or pd.api.types.is_datetime64_any_dtype(
            pd.to_datetime(df[timestamp_col], errors="coerce")
        )
    ):
        try:
            # Convert to datetime if necessary
            if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")

            # Group by time period
            time_df = (
                df.groupby(pd.Grouper(key=timestamp_col, freq="5Min"))
                .size()
                .reset_index()
            )
            time_df.columns = [timestamp_col, "count"]

            # Calculate moving average and limits
            time_df["moving_avg"] = (
                time_df["count"].rolling(window=5, min_periods=1).mean()
            )
            time_df["std"] = (
                time_df["count"].rolling(window=5, min_periods=1).std().fillna(0)
            )
            time_df["upper_bound"] = time_df["moving_avg"] + 2 * time_df["std"]
            time_df["lower_bound"] = (time_df["moving_avg"] - 2 * time_df["std"]).clip(
                lower=0
            )

            # Detection of peaks
            time_df["is_anomaly"] = (time_df["count"] > time_df["upper_bound"]) | (
                time_df["count"] < time_df["lower_bound"]
            )

            # Visualization
            anomaly_points = time_df[time_df["is_anomaly"]]

            if not anomaly_points.empty:
                st.write(
                    f"**{len(anomaly_points)} periods with abnormal activity detected**"
                )

                # Create the chart
                base = alt.Chart(time_df).encode(
                    x=alt.X(f"{timestamp_col}:T", title="Time")
                )

                line = base.mark_line().encode(
                    y=alt.Y("count:Q", title="Number of log entries")
                )

                bands = base.mark_area(opacity=0.2).encode(
                    y="lower_bound:Q",
                    y2="upper_bound:Q",
                    tooltip=[
                        f"{timestamp_col}:T",
                        "count:Q",
                        "moving_avg:Q",
                        "lower_bound:Q",
                        "upper_bound:Q",
                    ],
                )

                points = (
                    base.mark_circle(size=100, color="red")
                    .encode(y="count:Q")
                    .transform_filter(alt.datum.is_anomaly == True)
                )

                chart = (line + bands + points).properties(
                    width=700,
                    height=300,
                    title="Anomaly detection (unusual activity)",
                )
                st.altair_chart(chart, use_container_width=True)

                # Table of anomalies
                st.write("Periods with abnormal activity:")
                anomaly_df = anomaly_points[
                    [timestamp_col, "count", "moving_avg", "upper_bound", "lower_bound"]
                ]
                anomaly_df.columns = [
                    "Period",
                    "Number of entries",
                    "Moving average",
                    "Upper limit",
                    "Lower limit",
                ]
                st.dataframe(anomaly_df)
            else:
                st.success("No temporal anomalies detected.")

        except Exception as e:
            st.error(f"Unable to analyze the temporal distribution of logs: {e}")

    # Detection of suspicious event sequences
    if timestamp_col and level_col:
        st.subheader("Unusual event sequences")
        try:
            # Search for consecutive error sequences
            df_sorted = df.sort_values(by=timestamp_col)
            consecutive_errors = []

            current_sequence = []
            for i, row in df_sorted.iterrows():
                if str(row[level_col]).upper() in ["ERROR", "CRITICAL", "FATAL"]:
                    current_sequence.append(i)
                else:
                    if len(current_sequence) >= 3:  # At least 3 consecutive errors
                        consecutive_errors.append(current_sequence)
                    current_sequence = []

            if len(current_sequence) >= 3:  # Don't forget the last sequence
                consecutive_errors.append(current_sequence)

            if consecutive_errors:
                st.write(
                    f"**{len(consecutive_errors)} sequences of 3+ consecutive errors detected**"
                )

                # For each sequence, display the relevant entries
                for i, sequence in enumerate(
                    consecutive_errors[:5]
                ):  # Limit to 5 sequences for clarity
                    with st.expander(
                        f"Sequence {i + 1}: {len(sequence)} consecutive errors"
                    ):
                        st.dataframe(df.loc[sequence])
            else:
                st.success("No sequences of consecutive errors detected.")

        except Exception as e:
            st.error(f"Unable to analyze event sequences: {e}")

    # Recommendations
    st.subheader("Recommendations")

    if not error_logs.empty:
        st.warning(
            "⚠️ Critical errors have been detected. Review the entries in red for more details."
        )

        if "error_types" in locals() and error_types:
            top_error = sorted_errors[0][0]
            st.info(
                f"💡 The most frequent error is '{top_error}'. Focus your analysis on this type of error."
            )

    if "anomaly_points" in locals() and not anomaly_points.empty:
        peak_time = anomaly_points.iloc[anomaly_points["count"].idxmax()][timestamp_col]
        st.warning(
            f"⚠️ A significant activity peak was detected around {peak_time}. Review this period."
        )

    if "consecutive_errors" in locals() and consecutive_errors:
        st.warning(
            "⚠️ Sequences of consecutive errors have been detected, which may indicate systemic issues."
        )

    if error_logs.empty and ("anomaly_points" not in locals() or anomaly_points.empty):
        st.success("✅ No major issues detected in the analyzed logs.")
