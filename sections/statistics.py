import streamlit as st

# Perform a statistical analysis
st.title("Statistical Analysis")

# Loading data
if st.session_state.parsed_df is None:
    st.info("Please upload a log file on the 'Upload' page.")
    st.stop()

# Create tabs for different statistical views
stat_tab1, stat_tab2, stat_tab3 = st.tabs(
    ["General Information", "Numerical Statistics", "Categorical Variables"]
)

with stat_tab1:
    st.write("### Dataset Overview")

    # Show basic dataframe information
    df = st.session_state.parsed_df
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Number of Rows", df.shape[0])
        st.metric(
            "Memory Usage",
            f"{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB",
        )

    with col2:
        st.metric("Number of Columns", df.shape[1])
        st.metric("Missing Values", df.isna().sum().sum())

    # Display data types distribution
    dtypes_dict = dict(df.dtypes.value_counts())
    st.write("### Data Types")
    for dtype, count in dtypes_dict.items():
        st.write(f"- {dtype}: {count} columns")

    # Show columns by type
    st.write("### Columns by Type")
    for dtype in df.dtypes.unique():
        cols = df.select_dtypes(include=[dtype]).columns.tolist()
        with st.expander(f"{dtype} columns ({len(cols)})", expanded=True):
            st.write(", ".join(cols))

with stat_tab2:
    # Display numerical statistics with better formatting
    st.write("### Numerical Summary Statistics")

    # Get numeric columns
    numeric_cols = st.session_state.parsed_df.select_dtypes(
        include=["number"]
    ).columns.tolist()

    if numeric_cols:
        # Allow user to select which columns to analyze
        selected_cols = st.multiselect(
            "Select columns for analysis (default shows all):",
            numeric_cols,
            default=numeric_cols[: min(5, len(numeric_cols))],
        )

        if selected_cols:
            # Show detailed stats with more percentiles
            detailed_stats = (
                st.session_state.parsed_df[selected_cols]
                .describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
                .transpose()
            )
            st.dataframe(detailed_stats, use_container_width=True)
    else:
        st.info("No numerical columns available for analysis.")

    # Add datetime variables analysis section
    st.write("### Datetime Variables Analysis")

    # Get datetime columns
    datetime_cols = st.session_state.parsed_df.select_dtypes(
        include=["datetime", "datetime64"]
    ).columns.tolist()

    if datetime_cols:
        # Allow user to select which datetime columns to analyze
        selected_dt_cols = st.multiselect(
            "Select datetime columns for analysis:",
            datetime_cols,
            default=datetime_cols,
        )

        if selected_dt_cols:
            for col in selected_dt_cols:
                with st.expander(f"Datetime analysis: {col}", expanded=True):
                    df = st.session_state.parsed_df
                    series = df[col].dropna()

                    if len(series) > 0:
                        # Calculate basic datetime statistics
                        min_date = series.min()
                        max_date = series.max()
                        time_span = max_date - min_date

                        # Display key metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Minimum Date", min_date.strftime("%Y-%m-%d %H:%M:%S")
                            )
                        with col2:
                            st.metric(
                                "Maximum Date", max_date.strftime("%Y-%m-%d %H:%M:%S")
                            )
                        with col3:
                            days = time_span.days
                            hours = time_span.seconds // 3600
                            st.metric("Time Span", f"{days} days, {hours} hours")

                        # Additional datetime metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Unique Dates", series.dt.date.nunique())
                        with col2:
                            missing = df[col].isna().sum()
                            st.metric(
                                "Missing Values",
                                missing,
                                f"{missing / len(df) * 100:.2f}%",
                            )
                        with col3:
                            st.metric(
                                "Unique Months", series.dt.to_period("M").nunique()
                            )
                    else:
                        st.warning(f"No valid datetime values in column '{col}'")
    else:
        st.info("No datetime columns available for analysis.")

with stat_tab3:
    # Analyze categorical and non-numeric variables
    non_numeric_cols = st.session_state.parsed_df.select_dtypes(
        exclude=["number"]
    ).columns.tolist()

    if non_numeric_cols:
        st.write("### Categorical Variables Analysis")
        selected_cat_cols = st.multiselect(
            "Select categorical columns to analyze:",
            non_numeric_cols,
            default=non_numeric_cols[: min(3, len(non_numeric_cols))],
        )

        if selected_cat_cols:
            for col in selected_cat_cols:
                unique_count = st.session_state.parsed_df[col].nunique()
                with st.expander(f"{col} - {unique_count} unique values"):
                    # Show value counts if not too many unique values
                    if unique_count <= 20:
                        st.write(st.session_state.parsed_df[col].value_counts())
                    else:
                        st.write(f"Top 10 most common values (out of {unique_count})")
                        st.write(
                            st.session_state.parsed_df[col].value_counts().head(10)
                        )

                    # Show missing values for this column
                    missing = st.session_state.parsed_df[col].isna().sum()
                    st.metric(
                        "Missing values",
                        missing,
                        f"{missing / len(st.session_state.parsed_df) * 100:.2f}%",
                    )
    else:
        st.info("No categorical or text columns available for analysis.")
