import streamlit as st
import polars as pl

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
        st.metric("Number of Rows", df.height)
        st.metric(
            "Memory Usage",
            f"{df.estimated_size() / (1024 * 1024):.2f} MB",
        )

    with col2:
        st.metric("Number of Columns", df.width)
        st.metric("Missing Values", df.null_count().sum())

    # Display data types distribution
    dtypes_dict = {
        str(dtype): sum(1 for dt in df.schema.values() if str(dt) == str(dtype))
        for dtype in set(str(dt) for dt in df.schema.values())
    }
    st.write("### Data Types")
    for dtype, count in dtypes_dict.items():
        st.write(f"- {dtype}: {count} columns")

    # Show columns by type
    st.write("### Columns by Type")
    for dtype in set(str(dt) for dt in df.schema.values()):
        cols = [
            name for name, dt in zip(df.columns, df.schema.values()) if str(dt) == dtype
        ]
        with st.expander(f"{dtype} columns ({len(cols)})", expanded=True):
            st.write(", ".join(cols))

with stat_tab2:
    # Display numerical statistics with better formatting
    st.write("### Numerical Summary Statistics")

    # Get numeric columns
    numeric_cols = [
        name
        for name, dtype in zip(df.columns, df.schema.values())
        if pl.datatypes.is_numeric(dtype)
    ]

    if numeric_cols:
        # Allow user to select which columns to analyze
        selected_cols = st.multiselect(
            "Select columns for analysis (default shows all):",
            numeric_cols,
            default=numeric_cols[: min(5, len(numeric_cols))],
        )

        if selected_cols:
            # Show detailed stats
            detailed_stats = df.select(selected_cols).describe()
            st.dataframe(detailed_stats, use_container_width=True)
    else:
        st.info("No numerical columns available for analysis.")

    # Add datetime variables analysis section
    st.write("### Datetime Variables Analysis")

    # Get datetime columns
    datetime_cols = [
        name
        for name, dtype in zip(df.columns, df.schema.values())
        if pl.datatypes.is_temporal(dtype)
    ]

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
                    series = df.filter(pl.col(col).is_not_null()).select(pl.col(col))

                    if series.height > 0:
                        # Calculate basic datetime statistics
                        min_date = series.select(pl.col(col).min()).item()
                        max_date = series.select(pl.col(col).max()).item()
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
                            st.metric(
                                "Unique Dates",
                                df.select(pl.col(col).dt.date()).n_unique(),
                            )
                        with col2:
                            missing = df.select(pl.col(col).is_null().sum()).item()
                            st.metric(
                                "Missing Values",
                                missing,
                                f"{missing / df.height * 100:.2f}%",
                            )
                        with col3:
                            st.metric(
                                "Unique Months",
                                df.select(pl.col(col).dt.month()).n_unique(),
                            )
                    else:
                        st.warning(f"No valid datetime values in column '{col}'")
    else:
        st.info("No datetime columns available for analysis.")

with stat_tab3:
    # Analyze categorical and non-numeric variables
    non_numeric_cols = [
        name
        for name, dtype in zip(df.columns, df.schema.values())
        if not pl.datatypes.is_numeric(dtype)
    ]

    if non_numeric_cols:
        st.write("### Categorical Variables Analysis")
        selected_cat_cols = st.multiselect(
            "Select categorical columns to analyze:",
            non_numeric_cols,
            default=non_numeric_cols[: min(3, len(non_numeric_cols))],
        )

        if selected_cat_cols:
            for col in selected_cat_cols:
                unique_count = df.select(pl.col(col)).n_unique()
                with st.expander(f"{col} - {unique_count} unique values"):
                    # Show value counts if not too many unique values
                    if unique_count <= 20:
                        st.write(
                            df.select(pl.col(col).value_counts()).sort(
                                "count", descending=True
                            )
                        )
                    else:
                        st.write(f"Top 10 most common values (out of {unique_count})")
                        st.write(
                            df.select(pl.col(col).value_counts())
                            .sort("count", descending=True)
                            .head(10)
                        )

                    # Show missing values for this column
                    missing = df.select(pl.col(col).is_null().sum()).item()
                    st.metric(
                        "Missing values",
                        missing,
                        f"{missing / df.height * 100:.2f}%",
                    )
    else:
        st.info("No categorical or text columns available for analysis.")
