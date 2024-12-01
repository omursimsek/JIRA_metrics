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

def main():
    st.title("Project and Owner Timeline Viewer")

    # Fetch data from the backend
    st.write("Loading data...")
    data = fetch_data()

    if data.empty:
        return

    # Sidebar filters
    st.sidebar.header("Filters")
    project_filter = st.sidebar.text_input("Project (contains):")
    owner_filter = st.sidebar.selectbox("Owner:", options=["All"] + sorted(data['owner'].dropna().unique().tolist()))

    # Apply filters
    if project_filter:
        data = data[data['project'].str.contains(project_filter, case=False, na=False)]
    if owner_filter and owner_filter != "All":
        data = data[data['owner'] == owner_filter]

    if data.empty:
        st.warning("No data matches the selected filters.")
        return

    # Timeline visualization
    st.subheader("Timeline for Stories")
    data = data.sort_values(by="changed_at_start", ascending=False)
    fig = px.timeline(
        data,
        x_start="changed_at_start",
        x_end="changed_at_end",
        y="key",
        color="status",
        hover_data={"owner": True, "story_points": True},
        title="Timeline of Status Changes for Stories",
        labels={"key": "Story ID", "changed_at_start": "Start", "changed_at_end": "End"}
    )
    #fig.update_yaxes(categoryorder="total ascending")
    fig.update_yaxes(categoryorder="array", categoryarray=data["issue_id"].tolist())
    st.plotly_chart(fig)

if __name__ == "__main__":
    main()
