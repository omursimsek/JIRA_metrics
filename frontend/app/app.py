import streamlit as st
import pandas as pd
import plotly.express as px
import requests

API_URL = "http://backend:8000/average-times"

def fetch_data():
    """Fetch data from the FastAPI backend."""
    response = requests.get(API_URL)
    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        # Convert date columns to datetime objects
        df['changed_at_start'] = pd.to_datetime(df['changed_at_start'], utc=True, format='mixed')
        df['changed_at_end'] = pd.to_datetime(df['changed_at_end'], utc=True, format='mixed')
        return df
    else:
        st.error("Failed to fetch data from backend.")
        return pd.DataFrame()

def calculate_average_time(df, group_by_columns):
    """Calculate average time spent on a status grouped by specified columns."""
    df['time_spent'] = (pd.to_datetime(df['changed_at_end']) - pd.to_datetime(df['changed_at_start'])).dt.total_seconds() / 3600  # Convert to hours
    grouped = df.groupby(group_by_columns)['time_spent'].mean().reset_index()
    return grouped

def main():
    st.title("Average Time Analysis Dashboard")

    # Fetch data from the backend
    st.write("Loading data...")
    data = fetch_data()

    if data.empty:
        return

    # Process data
    data = data.dropna(subset=['changed_at_end'])  # Drop rows without an end timestamp

    # Visualization 1: Average time spent on status per owner
    st.subheader("Average Time Spent on Status Per Owner")
    avg_time_owner = calculate_average_time(data, ['owner', 'status'])
    fig1 = px.bar(avg_time_owner, x='owner', y='time_spent', color='status', barmode='group',
                  labels={'time_spent': 'Avg Time Spent (hours)'}, title="Average Time Spent on Status Per Owner")
    st.plotly_chart(fig1)

    # Visualization 2: Average time spent per status per story point
    st.subheader("Average Time Spent Per Status Per Story Point")
    avg_time_status_story = calculate_average_time(data, ['story_points', 'status'])
    fig2 = px.bar(avg_time_status_story, x='story_points', y='time_spent', color='status', barmode='group',
                  labels={'time_spent': 'Avg Time Spent (hours)', 'story_points': 'Story Points'},
                  title="Average Time Spent Per Status Per Story Point")
    st.plotly_chart(fig2)

    # Visualization 3: Average time spent per status per story point per owner
    st.subheader("Average Time Spent Per Status Per Story Point Per Owner")
    avg_time_status_story_owner = calculate_average_time(data, ['owner', 'story_points', 'status'])
    fig3 = px.bar(avg_time_status_story_owner, x='story_points', y='time_spent', color='status', barmode='group',
                  facet_col='owner', labels={'time_spent': 'Avg Time Spent (hours)', 'story_points': 'Story Points'},
                  title="Average Time Spent Per Status Per Story Point Per Owner")
    st.plotly_chart(fig3)

if __name__ == "__main__":
    main()
