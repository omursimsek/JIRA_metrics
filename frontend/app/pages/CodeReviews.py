import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# API URL to get code review history data
API_URL = "http://backend:8000/code-review-history"

# Fetch data from the API
@st.cache_data

def fetch_code_review_data():
    response = requests.get(API_URL)
    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        df['changed_at'] = pd.to_datetime(df['changed_at'])
        return df
    else:
        st.error("Failed to fetch data from backend.")
        return pd.DataFrame()

# Main Streamlit app
st.title("Code Review Results Overview")
if st.button("Reload Data"):
        st.cache_data.clear()
# Fetch data
data = fetch_code_review_data()

if data.empty:
    st.warning("No data available.")
else:
    # Sidebar for selecting week range
    st.sidebar.header("Filters")
    today = datetime.now()
    last_week = today - timedelta(weeks=1)

    week_start = st.sidebar.date_input("Start Date", last_week.date())
    week_end = st.sidebar.date_input("End Date", today.date())

    # Filter data based on the selected week range
    filtered_data = data[(data['changed_at'].dt.date >= pd.to_datetime(week_start).date()) & 
                         (data['changed_at'].dt.date <= pd.to_datetime(week_end).date())]

    st.sidebar.write(f"Showing data from {week_start} to {week_end}")

    # Pie chart for filtered data
    if not filtered_data.empty:
        st.subheader(f"Code Review Results from {week_start} to {week_end}")
        pie_fig = px.pie(
            filtered_data,
            names="code_review_status",
            title="Code Review Results",
            labels={"code_review_result": "Review Result"},
            hole=0.3
        )
        st.plotly_chart(pie_fig)

    # Pie chart for all data
    st.dataframe(data)
    st.subheader("All Code Review Results")
    all_pie_fig = px.pie(
        data,
        names="code_review_status",
        title="All Code Review Results",
        labels={"code_review_result": "Review Result"},
        hole=0.3
    )
    st.plotly_chart(all_pie_fig)
