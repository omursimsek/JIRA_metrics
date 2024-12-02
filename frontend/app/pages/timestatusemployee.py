import pandas as pd
import requests
import streamlit as st
import plotly.express as px

API_URL = "http://backend:8000/average-times"

# Product mapping moved to frontend
PRODUCT_MAPPING = {
    "RTMS": ["FFF", "SLY", "EXW"],
    "PTM/ROM": ["PB", "SMY"],
    "RSB/FLEET": ["AAV"],
    "Integration": ["ISY"]
}

# Fetch data from the API
def fetch_average_time():
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data from backend.")
        return []

# Function to calculate the time in progress
def calculate_time_in_progress(start_time, end_time):
    if not start_time or not end_time:
        return 0

    # Convert to datetime
    start_time = pd.to_datetime(start_time, utc=True, format='mixed')
    end_time = pd.to_datetime(end_time, utc=True, format='mixed')

    # Calculate the time difference in hours
    time_diff = (end_time - start_time).total_seconds() / 3600.0
    return time_diff

# Main function to process data and calculate metrics
def main():
    st.title("Average Time in Progress Analysis")

    # Fetch the raw data from the API
    raw_data = fetch_average_time()

    if not raw_data:
        return  # Exit if data fetch failed

    # Convert raw data to a DataFrame
    df = pd.DataFrame(raw_data)

    # Filter data for closed status stories
    df = df[df['current_status'] == 'Closed']

    # Map project to product
    df["product"] = df["project"].map(
        lambda x: next((product for product, projects in PRODUCT_MAPPING.items() if x in projects), None)
    )

    # Remove rows where product mapping was not found
    df = df.dropna(subset=["product"])

    # Ensure necessary columns exist
    required_columns = ['changed_at_start', 'changed_at_end', 'story_points', 'owner', 'product']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            return

    # Calculate time in progress for each story
    df['time_in_progress'] = df.apply(
        lambda row: calculate_time_in_progress(row['changed_at_start'], row['changed_at_end']), axis=1
    )

    # Calculate time in progress per story point per owner
    df['time_per_story_point_owner'] = df['time_in_progress'] / df['story_points']
    owner_metrics = df.groupby('owner')['time_per_story_point_owner'].mean().reset_index()
    owner_metrics.columns = ['owner', 'avg_time_per_story_point_owner']

    # Display owner metrics as a table
    st.subheader("Average Time in Progress per Story Point per Owner")
    st.dataframe(owner_metrics)

    # Plot average time per story point per owner
    fig_owner = px.bar(owner_metrics, x='owner', y='avg_time_per_story_point_owner',
                       title="Average Time in Progress per Story Point per Owner",
                       labels={'avg_time_per_story_point_owner': 'Average Time (hours)', 'owner': 'Owner'})
    st.plotly_chart(fig_owner)

    # Calculate overall average time in progress per story point
    overall_avg_time_per_story_point = df['time_per_story_point_owner'].mean()
    st.subheader("Overall Average Time in Progress per Story Point")
    st.metric("Overall Average Time (hours)", f"{overall_avg_time_per_story_point:.2f}")

    # Calculate time in progress per story point per product
    product_metrics = df.groupby('product')['time_per_story_point_owner'].mean().reset_index()
    product_metrics.columns = ['product', 'avg_time_per_story_point_product']

    # Display product metrics as a table
    st.subheader("Average Time in Progress per Story Point per Product")
    st.dataframe(product_metrics)

    # Plot average time per story point per product
    fig_product = px.bar(product_metrics, x='product', y='avg_time_per_story_point_product',
                         title="Average Time in Progress per Story Point per Product",
                         labels={'avg_time_per_story_point_product': 'Average Time (hours)', 'product': 'Product'})
    st.plotly_chart(fig_product)

if __name__ == "__main__":
    main()
