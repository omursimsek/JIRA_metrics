import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

# Define the backend endpoint
ENDPOINT = "http://backend:8000/bugsrootcauseresolution/rootcausewithrd"

# Page Title
st.title("Bug Root Cause Analysis")

# Fetch data from the backend
@st.cache_data(ttl=600)  # Cache data for 10 minutes
def fetch_data(endpoint):
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        data = response.json()
        return data["root_causes"]
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return []

# Process the data
data = fetch_data(ENDPOINT)

if data:
    # Convert data to a Pandas DataFrame
    df = pd.DataFrame(data)

    # Ensure "date" column is in datetime format if it exists
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    # Allow filtering by project
    projects = df["project"].unique()
    selected_project = st.selectbox("Select a Project", ["All"] + list(projects))

    if selected_project != "All":
        filtered_df = df[df["project"] == selected_project]
    else:
        filtered_df = df

    # Add a date filter (week picker, date range, or all)
    st.subheader("Filter by Date")

    # Option to filter by week, date range, or show all
    filter_option = st.radio("Filter by:", ("All", "Specific Week", "Date Range"))

    if filter_option == "Specific Week":
        # Select a specific week
        selected_date = st.date_input("Select a date within the week", value=datetime.now())
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        st.write(f"Selected Week: {start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}")

        filtered_df = filtered_df[(filtered_df["date"] >= start_of_week) & (filtered_df["date"] <= end_of_week)]

    elif filter_option == "Date Range":
        # Select a date range
        date_range = st.date_input("Select Date Range", value=[datetime.now() - timedelta(days=30), datetime.now()])

        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[(filtered_df["date"] >= start_date) & (filtered_df["date"] <= end_date)]

    # If "All" is selected, no additional filtering is applied

    # Aggregate data by root cause    
    agg_data = filtered_df.groupby("root_Cause")["count"].sum().reset_index()

    # Display the pie chart
    st.subheader(f"Pie Chart for {'All Projects' if selected_project == 'All' else selected_project}")
    fig = px.pie(
        agg_data,
        names="root_Cause",
        values="count",
        title="Root Cause Distribution",
        hole=0.3
    )
    st.plotly_chart(fig, use_container_width=True)

    agg_data_bar = filtered_df.groupby(["project","root_Cause"])["count"].sum().reset_index()

    # Create the stacked bar chart
    fig = px.bar(
        agg_data_bar,
        x="project",
        y="count",
        color="root_Cause",
        title="Root Causes per Project",
        labels={"count": "Count", "project": "Project", "root_Cause": "Root Cause"},
        text="count",
    )

    # Update the layout for better readability
    fig.update_layout(
        barmode="stack",
        xaxis_title="Project",
        yaxis_title="Count",
        legend_title="Root Cause",
        title_x=0.5,
    )

    # Display the chart
    st.plotly_chart(fig)

    # Create a line chart showing weekly root cause types for resolved bugs
    st.subheader("Weekly Root Cause Trends")

    # Extract the week from the date
    filtered_df = filtered_df.dropna(subset=["date"])
    filtered_df["date"] = pd.to_datetime(filtered_df["date"])
    #st.dataframe(filtered_df)
    filtered_df["week"] = filtered_df["date"].dt.to_period("W").apply(lambda r: r.start_time)

    # Aggregate data by week and root cause
    weekly_data = filtered_df.groupby(["week", "root_Cause"]).agg({"count": "sum"}).reset_index()

    # Create the line chart
    fig = px.line(
        weekly_data,
        x="week",
        y="count",
        color="root_Cause",
        title="Weekly Root Cause Types for Resolved Bugs",
        labels={"week": "Week", "count": "Count", "root_Cause": "Root Cause"},
    )

    # Update layout for better readability
    fig.update_layout(
        xaxis_title="Week",
        yaxis_title="Count",
        legend_title="Root Cause",
        title_x=0.5,
    )

    # Display the line chart
    st.plotly_chart(fig)

else:
    st.warning("No data available to display.")
