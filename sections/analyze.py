import pandas as pd
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

# Check if there are datetime columns
datetime_columns = [
    name
    for name, dtype in data.schema.items()
    if isinstance(dtype, pl.datatypes.Datetime) or isinstance(dtype, pl.datatypes.Date)
]
# Try to detect string columns that could be dates
if not datetime_columns:
    string_cols = [
        name for name, dtype in data.schema.items() if pl.is_string_dtype(dtype)
    ]
    for col in string_cols:
        try:
            data.select(pl.col(col).str.to_datetime())
            datetime_columns.append(col)
        except (ValueError, TypeError):
            pass

# Chart type options
chart_options = ["Pie Chart", "Sunburst Chart", "Histogram"]
if datetime_columns:
    chart_options.extend(["Time Series", "Seasonnality"])

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
    group_counts = data.groupby(selected_columns).agg(pl.count().alias("Count"))
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

elif chart_type == "Time Series":
    st.header("Time Series")

    # Select datetime column for x-axis
    datetime_col = st.sidebar.selectbox("Select datetime column", datetime_columns)

    # Convert to datetime if needed
    # Check if it's not already a datetime type
    if data.schema[datetime_col] not in [pl.Date, pl.Datetime]:
        data = data.with_columns(
            pl.col(datetime_col).str.to_datetime().alias(datetime_col)
        )

    # Add option to choose between numeric values or counts
    ts_mode = st.sidebar.radio(
        "Time Series type", ["Numeric Values", "Count Over Time"]
    )

    # Option to aggregate data
    do_aggregate = st.sidebar.checkbox(
        "Aggregate by time period", value=(ts_mode == "Count Over Time")
    )
    if do_aggregate:
        period = st.sidebar.selectbox(
            "Select period",
            [
                "Second",
                "Minute",
                "5 Minutes",
                "15 Minutes",
                "30 Minutes",
                "Hour",
                "6 Hours",
                "Day",
                "Week",
                "Month",
                "Year",
            ],
            index=5,
        )
        freq_map = {
            "Second": "s",
            "Minute": "min",
            "5 Minutes": "5min",
            "15 Minutes": "15min",
            "30 Minutes": "30min",
            "Hour": "h",
            "6 Hours": "6h",
            "Day": "D",
            "Week": "W",
            "Month": "M",
            "Year": "Y",
        }
        freq = freq_map[period]
    else:
        period = None
        freq = None

    if ts_mode == "Numeric Values" and numerical_columns:
        y_column = st.sidebar.selectbox("Select y-axis variable", numerical_columns)

        if do_aggregate:
            grouped_data = (
                data.groupby_dynamic(datetime_col, every=freq, closed="left")
                .agg([pl.col(y_column).mean().alias(y_column)])
                .sort(datetime_col)
            )
            fig = px.line(
                grouped_data,
                x=datetime_col,
                y=y_column,
                title=f"{y_column} over time (by {period.lower()})",
            )
        else:
            fig = px.line(
                data.sort(datetime_col).to_pandas(),
                x=datetime_col,
                y=y_column,
                title=f"{y_column} over time",
            )

        st.plotly_chart(fig)

    elif ts_mode == "Count Over Time" and categorical_columns:
        count_column = st.sidebar.selectbox(
            "Select column to count", categorical_columns
        )

        # Create time series of counts
        if do_aggregate:
            # Group by time period and count values in the selected column
            count_data = (
                data.with_columns(
                    pl.col(datetime_col).dt.truncate(freq).alias(datetime_col)
                )
                .groupby([datetime_col, count_column])
                .agg(pl.count().alias("count"))
                .pivot(
                    index=datetime_col,
                    columns=count_column,
                    values="count",
                )
                .fill_null(0)
                .sort(datetime_col)
                .to_pandas()
            )

            # Create line plot for each category
            fig = px.line(
                count_data,
                x=datetime_col,
                y=count_data.columns[1:],  # All columns except datetime
                title=f"Count of {count_column} over time (by {period.lower()})",
            )
        else:
            # Count by date without further aggregation
            count_data = (
                data.groupby([data[datetime_col].dt.date, count_column])
                .size()
                .reset_index(name="count")
                .pivot(
                    index=data[datetime_col].dt.date.name,
                    columns=count_column,
                    values="count",
                )
                .fillna(0)
                .reset_index()
            )

            fig = px.line(
                count_data,
                x=count_data.columns[0],  # Date column
                y=count_data.columns[1:],  # All columns except date
                title=f"Count of {count_column} over time",
            )

        st.plotly_chart(fig)
    else:
        st.write("No suitable columns available for the selected time series type.")

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

elif chart_type == "Seasonnality":
    st.header("Seasonality Analysis")

    # Select datetime column for x-axis
    datetime_col = st.sidebar.selectbox("Select datetime column", datetime_columns)

    # Convert to datetime if needed
    if data.schema[datetime_col] not in [pl.Date, pl.Datetime]:
        data = data.with_columns(
            pl.col(datetime_col).str.to_datetime().alias(datetime_col)
        )

    # Add option to choose analysis variable
    analysis_options = ["Count"]
    if numerical_columns:
        analysis_options.extend(["Average", "Sum"])

    analysis_type = st.sidebar.selectbox("Analysis type", analysis_options)

    # Select variable for seasonality analysis
    if analysis_type in ["Average", "Sum"] and numerical_columns:
        # For Average and Sum, we need a numeric variable
        season_var = st.sidebar.selectbox("Select numeric variable", numerical_columns)
        y_label = f"{analysis_type} of {season_var}"
    else:
        # For Count, we can use an optional categorical variable for grouping
        season_var = st.sidebar.selectbox(
            "Group by (optional)", ["None"] + categorical_columns
        )
        if season_var == "None":
            season_var = None
            y_label = "Count"
        else:
            y_label = f"Count by {season_var}"

    # Add time granularity selection
    time_options = [
        "Year",
        "Year-Month",
        "Year-Week",
        "Day of Week",
        "Month of Year",
        "Hour of Day",
        "Day of Month",
    ]

    selected_time_periods = st.sidebar.multiselect(
        "Select time periods to analyze",
        time_options,
        default=["Year-Month", "Day of Week", "Hour of Day"],
    )

    if not selected_time_periods:
        st.warning("Please select at least one time period to analyze.")
        st.stop()

    # Prepare data with time components
    temp_data = data.clone()
    temp_data["year"] = temp_data[datetime_col].dt.year
    temp_data["month"] = temp_data[datetime_col].dt.month
    temp_data["month_name"] = temp_data[datetime_col].dt.month_name()
    temp_data["week"] = temp_data[datetime_col].dt.isocalendar().week
    temp_data["year_month"] = temp_data[datetime_col].dt.to_period("M").astype(str)
    temp_data["year_week"] = temp_data[datetime_col].dt.strftime("%Y-W%U")
    temp_data["day_of_week"] = temp_data[datetime_col].dt.day_name()
    temp_data["day_of_month"] = temp_data[datetime_col].dt.day
    temp_data["hour"] = temp_data[datetime_col].dt.hour

    # Define days order for correct sorting
    days_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    months_order = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    # Create a tab for each selected time period
    tabs = st.tabs(selected_time_periods)

    for i, period in enumerate(selected_time_periods):
        with tabs[i]:
            st.write(f"#### {period} Analysis")

            # Define groupby column and sorting based on period
            if period == "Year":
                groupby_col = "year"
                sort_index = True
            elif period == "Year-Month":
                groupby_col = "year_month"
                sort_index = True
            elif period == "Year-Week":
                groupby_col = "year_week"
                sort_index = True
            elif period == "Day of Week":
                groupby_col = "day_of_week"
                # Use categorical type for proper sorting
                temp_data["day_of_week"] = pd.Categorical(
                    temp_data["day_of_week"], categories=days_order, ordered=True
                )
                sort_index = False
            elif period == "Month of Year":
                groupby_col = "month_name"
                # Use categorical type for proper sorting
                temp_data["month_name"] = pd.Categorical(
                    temp_data["month_name"], categories=months_order, ordered=True
                )
                sort_index = False
            elif period == "Hour of Day":
                groupby_col = "hour"
                sort_index = True
            elif period == "Day of Month":
                groupby_col = "day_of_month"
                sort_index = True

            # Create the visualization
            if season_var and season_var != "None":
                # Group by time period and the selected variable
                if analysis_type == "Count":
                    period_data = (
                        temp_data.groupby([groupby_col, season_var])
                        .size()
                        .reset_index(name="count")
                    )
                    y_col = "count"
                elif analysis_type == "Average":
                    period_data = (
                        temp_data.groupby([groupby_col, season_var])[season_var]
                        .mean()
                        .reset_index(name="average")
                    )
                    y_col = "average"
                else:  # Sum
                    period_data = (
                        temp_data.groupby([groupby_col, season_var])[season_var]
                        .sum()
                        .reset_index(name="sum")
                    )
                    y_col = "sum"

                # Sort if needed
                if sort_index:
                    period_data = period_data.sort_values(groupby_col)

                # Create and display bar chart
                fig = px.bar(
                    period_data,
                    x=groupby_col,
                    y=y_col,
                    color=season_var,
                    barmode="group",
                    title=f"{period} Distribution by {season_var}",
                    labels={y_col: y_label},
                )
                st.plotly_chart(fig)

            else:
                # Simple time series without additional grouping
                if analysis_type == "Count":
                    if sort_index:
                        period_counts = (
                            temp_data[groupby_col].value_counts().sort_index()
                        )
                    else:
                        period_counts = temp_data[groupby_col].value_counts()
                elif analysis_type == "Average":
                    period_counts = temp_data.groupby(groupby_col)[season_var].mean()
                    if sort_index:
                        period_counts = period_counts.sort_index()
                else:  # Sum
                    period_counts = temp_data.groupby(groupby_col)[season_var].sum()
                    if sort_index:
                        period_counts = period_counts.sort_index()

                # Sort by natural order if day_of_week or month_name
                if groupby_col == "day_of_week":
                    period_counts = period_counts.reindex(days_order).fillna(0)
                elif groupby_col == "month_name":
                    period_counts = period_counts.reindex(months_order).fillna(0)

                fig = px.bar(
                    x=period_counts.index,
                    y=period_counts.values,
                    title=f"{period} {y_label}",
                    labels={"x": period, "y": y_label},
                )
                st.plotly_chart(fig)

else:
    st.write(data)
