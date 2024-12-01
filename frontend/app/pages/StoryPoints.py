import streamlit as st
import pandas as pd
import requests

API_URL = "http://backend:8000/stories"

@st.cache_data
def fetch_data():
    """Fetch data from the FastAPI backend."""
    response = requests.get(API_URL)
    if response.status_code == 200:
        df = pd.DataFrame(response.json(),columns=["issue_id","key","project","status","story_points","owner"])
        return df
    else:
        st.error("Failed to fetch data from backend.")
        return pd.DataFrame()

def preprocess_data(data):
    """Preprocess the data to handle non-numeric or missing story points."""
    data['story_points'] = pd.to_numeric(data['story_points'], errors='coerce')
    data = data.dropna(subset=['story_points'])  # Drop rows where story points are null
    return data

def calculate_metrics(data, only_closed):
    """Calculate the metrics based on the filtered data."""
    if only_closed:
        data = data[data['status'] == "Closed"]

    # Total story points per owner
    total_points_per_owner = data.groupby('owner')['story_points'].sum()

    # Total story points grouped by story points per owner (matrix form)
    df = data
    df['sp'] = df.loc[:, 'story_points']
    points_grouped_by_sp_per_owner = pd.pivot_table(
        df,
        values='sp',
        index='owner',
        columns=['story_points'],
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Sum'
    )

    # Total number of stories per story points per owner (matrix form)
    total_stories_per_sp_per_owner = pd.pivot_table(
        data,
        values='status',
        index='owner',
        columns='story_points',
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='Sum'
    )

    return total_points_per_owner, points_grouped_by_sp_per_owner, total_stories_per_sp_per_owner

def main():
    st.title("Story Metrics per Owner")

    # Fetch data from the backend
    st.write("Loading data...")
    data = fetch_data()

    if data.empty:
        return

    # Preprocess data
    data = preprocess_data(data)

    # Checkbox to filter closed stories
    only_closed = st.checkbox("Only show closed stories", value=True)

    # Calculate metrics
    total_points_per_owner, points_grouped_by_sp_per_owner, total_stories_per_sp_per_owner = calculate_metrics(data, only_closed)

    #total_points_per_owner, points_grouped_by_sp_per_owner = calculate_metrics(data, only_closed)

    # Display metrics
    st.header("Metrics")
    st.subheader("Total Story Points per Owner")
    st.dataframe(total_points_per_owner.reset_index().rename(columns={'owner': 'Owner', 'story_points': 'Total Story Points'}))

    #st.dataframe(data)

    #st.subheader("Total Story Points Grouped by Story Points per Owner (Matrix)")
    st.dataframe(points_grouped_by_sp_per_owner)

    #st.subheader("Total Number of Stories per Story Points per Owner (Matrix)")
    st.dataframe(total_stories_per_sp_per_owner)

if __name__ == "__main__":
    main()