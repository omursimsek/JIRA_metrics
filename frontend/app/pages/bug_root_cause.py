import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Define the backend endpoint
ENDPOINT = "http://backend:8000/bugsrootcause/rootcause"

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

    # Allow filtering by project
    projects = df["project"].unique()
    selected_project = st.selectbox("Select a Project", ["All"] + list(projects))
    
    if selected_project != "All":
        filtered_df = df[df["project"] == selected_project]
    else:
        filtered_df = df

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

    # Create the stacked bar chart
    fig = px.bar(
        filtered_df,
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

else:
    st.warning("No data available to display.")
