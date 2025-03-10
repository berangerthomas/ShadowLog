import polars as pl
import plotly.express as px
import streamlit as st

if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None

# Page title
st.title("Data Analysis")

# Loading data
if st.session_state.parsed_df is None:
    st.info("Please upload a log file on the 'Upload' page.")
    st.stop()

data = st.session_state.parsed_df

# Sidebar for controls
st.sidebar.header("Visualization Options")

# Chart type options
chart_options = ["Pie Chart", "Sunburst Chart", "Histogram"]

chart_type = st.sidebar.selectbox("Choose chart type", chart_options)

# Get categorical columns
categorical_columns = [
    name
    for name, dtype in data.schema.items()
    if dtype == pl.Utf8 or dtype == pl.Categorical
]
# Get numerical columns
numeric_dtypes = [
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.UInt8,
    pl.UInt16,
    pl.UInt32,
    pl.UInt64,
    pl.Float32,
    pl.Float64,
]
numerical_columns = [
    name for name, dtype in data.schema.items() if dtype in numeric_dtypes
]

# Data filtering tools in main page
st.header("Filter Data")

filtered_data = data.clone()
original_count = data.shape[0]

col1, col2 = st.columns(2)

with col1:
    # Look for accept/reject status columns
    status_cols = [
        col
        for col in categorical_columns
        if any(term in col.lower() for term in ["status", "action", "result"])
    ]

    if status_cols:
        status_col = st.selectbox("Status field:", status_cols)
        status_values = filtered_data[status_col].unique().to_list()

        # Identify accepted/rejected values
        accept_values = [
            val
            for val in status_values
            if any(
                term in str(val).lower()
                for term in ["accept", "allow", "permit", "pass"]
            )
        ]
        reject_values = [
            val
            for val in status_values
            if any(
                term in str(val).lower() for term in ["reject", "deny", "drop", "block"]
            )
        ]

        if accept_values or reject_values:
            flow_status = st.radio(
                "Flow status:", ["All", "Accepted", "Rejected"], horizontal=True
            )

            if flow_status == "Accepted" and accept_values:
                filtered_data = filtered_data.filter(
                    pl.col(status_col).is_in(accept_values)
                )
            elif flow_status == "Rejected" and reject_values:
                filtered_data = filtered_data.filter(
                    pl.col(status_col).is_in(reject_values)
                )

with col2:
    # Port range filter according to RFC 6056
    port_cols = [col for col in numerical_columns if "port" in col.lower()]

    if port_cols:
        port_col = st.selectbox("Port field:", port_cols)

        # RFC 6056 port ranges
        rfc_ranges = {
            "Well-known ports (0-1023)": (0, 1023),
            "Windows ephemeral (1024-5000)": (1024, 5000),
            "Linux/BSD ephemeral (1024-65535)": (1024, 65535),
            "IANA ephemeral (49152-65535)": (49152, 65535),
        }

        selected_ranges = st.multiselect(
            "RFC 6056 port ranges:", options=list(rfc_ranges.keys())
        )

        if selected_ranges:
            range_filter = None
            for range_name in selected_ranges:
                min_port, max_port = rfc_ranges[range_name]
                current_filter = (pl.col(port_col) >= min_port) & (
                    pl.col(port_col) <= max_port
                )

                if range_filter is None:
                    range_filter = current_filter
                else:
                    range_filter = range_filter | current_filter

            filtered_data = filtered_data.filter(range_filter)

if filtered_data.shape[0] != original_count:
    st.write(f"Showing {filtered_data.shape[0]} of {original_count} records")
    data = filtered_data

st.write("---")


# Main area for visualization
if chart_type == "Pie Chart":
    st.header("Pie Chart")

    # Select variable to visualize
    selected_column = st.sidebar.selectbox(
        "Select a categorical variable", categorical_columns
    )

    # Create and display pie chart
    fig = px.pie(
        data,
        names=selected_column,
        title=f"Distribution of '{selected_column}'",
    )
    st.plotly_chart(fig)

    # Display value table
    st.write("Value distribution:")
    st.write(data[selected_column].value_counts())

elif chart_type == "Sunburst Chart":
    st.header("Sunburst Chart")

    selected_columns = st.sidebar.multiselect(
        "Select one or more categorical variables:",
        categorical_columns,
        default=categorical_columns[:1],
    )

    if not selected_columns:
        st.warning("Please select at least one variable.")
        st.stop()

    fig = px.sunburst(
        data,
        path=selected_columns,
        title="Sunburst Chart",
    )
    fig.update_traces(textinfo="label+percent parent")
    st.plotly_chart(fig)

    st.write("Value distribution:")
    group_counts = data.group_by(selected_columns).agg(pl.count().alias("Count"))
    st.write(group_counts)

elif chart_type == "Histogram":
    st.header("Histogram")

    # Add option to choose between numeric values or counts
    hist_mode = st.sidebar.radio("Histogram type", ["Numeric Values", "Count Values"])

    if hist_mode == "Numeric Values" and numerical_columns:
        selected_column = st.sidebar.selectbox(
            "Select a numerical variable", numerical_columns
        )
        fig = px.histogram(data, x=selected_column)
        st.plotly_chart(fig)
    elif hist_mode == "Count Values" and categorical_columns:
        selected_column = st.sidebar.selectbox(
            "Select a categorical variable", categorical_columns
        )
        # Get counts and create histogram
        st.write(type(data.select(pl.col(selected_column))))
        counts = data.select(pl.col(selected_column)).value_counts()

        counts = counts.rename({selected_column: "value"})
        fig = px.bar(
            counts,
            x="value",
            y="count",
            labels={"value": selected_column, "count": "Count"},
            title=f"Count of {selected_column} values",
        )
        st.plotly_chart(fig)
    else:
        st.write("No suitable columns available for the selected histogram type.")


# Option to display raw data
if st.sidebar.checkbox("Show raw data"):
    st.subheader("Data")

    if chart_type == "Pie Chart":
        # For categorical charts, allow filtering by category
        filter_option = st.selectbox(
            f"Filter by {selected_column}:",
            ["Show all data"] + sorted(data[selected_column].unique().tolist()),
        )

        if filter_option != "Show all data":
            filtered_data = data[data[selected_column] == filter_option]
            st.write(filtered_data)
        else:
            st.write(data)

    elif chart_type == "Histogram":
        if hist_mode == "Numeric Values" and numerical_columns:
            # For histogram, allow filtering by value range
            min_val = float(data[selected_column].min())
            max_val = float(data[selected_column].max())

            selected_range = st.slider(
                f"Filter by {selected_column} range:",
                min_val,
                max_val,
                (min_val, max_val),
            )

            filtered_data = data[
                (data[selected_column] >= selected_range[0])
                & (data[selected_column] <= selected_range[1])
            ]
            st.write(filtered_data)
        else:
            # For categorical histogram
            filter_option = st.selectbox(
                f"Filter by {selected_column}:",
                ["Show all data"] + sorted(data[selected_column].unique().tolist()),
            )

            if filter_option != "Show all data":
                filtered_data = data[data[selected_column] == filter_option]
                st.write(filtered_data)
            else:
                st.write(data)
else:
    st.write(data)
