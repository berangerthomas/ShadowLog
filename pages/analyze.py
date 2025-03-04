import pandas as pd
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

# Check if there are datetime columns
datetime_columns = data.select_dtypes(include=["datetime64"]).columns.tolist()
# Try to detect string columns that could be dates
if not datetime_columns:
    for col in data.select_dtypes(include=["object"]).columns:
        try:
            pd.to_datetime(data[col], errors="raise")
            datetime_columns.append(col)
        except (ValueError, TypeError):
            pass

# Chart type options
chart_options = ["Pie Chart", "Bar Chart", "Histogram"]
if datetime_columns:
    chart_options.append("Time Series")

chart_type = st.sidebar.selectbox("Choose chart type", chart_options)

# Get categorical columns
categorical_columns = data.select_dtypes(include=["object"]).columns.tolist()

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

elif chart_type == "Bar Chart":
    st.header("Bar Chart")

    selected_column = st.sidebar.selectbox("Select a variable", categorical_columns)

    results = data[selected_column].value_counts().reset_index()
    results.columns = ["category", "count"]  # Explicitly rename columns
    fig = px.bar(
        results,
        x="category",
        y="count",
        labels={"category": selected_column, "count": "Count"},
    )
    st.plotly_chart(fig)

elif chart_type == "Histogram":
    st.header("Histogram")

    numerical_columns = data.select_dtypes(include=["int", "float"]).columns.tolist()
    if numerical_columns:
        selected_column = st.sidebar.selectbox(
            "Select a numerical variable", numerical_columns
        )
        fig = px.histogram(data, x=selected_column)
        st.plotly_chart(fig)
    else:
        st.write("No numerical columns available for histogram.")

elif chart_type == "Time Series":
    st.header("Time Series")

    # Select datetime column for x-axis
    datetime_col = st.sidebar.selectbox("Select datetime column", datetime_columns)

    # Convert to datetime if needed
    if data[datetime_col].dtype != "datetime64[ns]":
        data[datetime_col] = pd.to_datetime(data[datetime_col])

    # Get numerical columns for y-axis
    numerical_columns = data.select_dtypes(include=["int", "float"]).columns.tolist()

    if numerical_columns:
        y_column = st.sidebar.selectbox("Select y-axis variable", numerical_columns)

        # Option to aggregate data
        if st.sidebar.checkbox("Aggregate by time period"):
            period = st.sidebar.selectbox(
                "Select period", ["Day", "Week", "Month", "Year"]
            )
            freq_map = {"Day": "D", "Week": "W", "Month": "M", "Year": "Y"}

            grouped_data = (
                data.groupby(pd.Grouper(key=datetime_col, freq=freq_map[period]))[
                    y_column
                ]
                .mean()
                .reset_index()
            )

            fig = px.line(
                grouped_data,
                x=datetime_col,
                y=y_column,
                title=f"{y_column} over time (by {period.lower()})",
            )
        else:
            fig = px.line(
                data.sort_values(by=datetime_col),
                x=datetime_col,
                y=y_column,
                title=f"{y_column} over time",
            )

        st.plotly_chart(fig)
    else:
        st.write("No numerical columns available for y-axis.")

# Option to display raw data
if st.sidebar.checkbox("Show raw data"):
    st.subheader("Data")

    if chart_type in ["Pie Chart", "Bar Chart"]:
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

    elif chart_type == "Histogram" and numerical_columns:
        # For histogram, allow filtering by value range
        min_val = float(data[selected_column].min())
        max_val = float(data[selected_column].max())

        selected_range = st.slider(
            f"Filter by {selected_column} range:", min_val, max_val, (min_val, max_val)
        )

        filtered_data = data[
            (data[selected_column] >= selected_range[0])
            & (data[selected_column] <= selected_range[1])
        ]
        st.write(filtered_data)
    elif chart_type == "Time Series":
        # For time series, filter by date range
        min_date = data[datetime_col].min().date()
        max_date = data[datetime_col].max().date()

        date_range = st.date_input(
            "Filter by date range",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date,
        )

        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_data = data[
                (data[datetime_col].dt.date >= start_date)
                & (data[datetime_col].dt.date <= end_date)
            ]
            st.write(filtered_data)
        else:
            st.write(data)
    else:
        st.write(data)
