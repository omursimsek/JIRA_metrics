import streamlit as st
import requests
import pandas as pd
import plotly.express as px

def fetch_data(api_url):
    """Fetch data from the backend API."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

def prepare_data(data):
    """Convert API data to a DataFrame for plotting."""
    if "priorities" not in data:
        st.error("Invalid data format from API.")
        return None

    # Convert the data to a DataFrame
    df = pd.DataFrame(data["priorities"])
    return df

def main():
    st.title("Stacked Bar Chart per Project")

    # API endpoint URL
    api_url = st.text_input("Enter the API endpoint URL:", "http://backend:8000/bugspriorityproject/priority")

    if api_url:
        # Fetch data from the API
        data = fetch_data(api_url)

        if data:
            # Prepare the data for visualization
            df = prepare_data(data)

            if df is not None:
                # Create the stacked bar chart
                fig = px.bar(
                    df,
                    x="project",
                    y="count",
                    color="priority",
                    title="Priorities per Project",
                    labels={"count": "Count", "project": "Project", "priority": "Priority"},
                    text="count",
                )

                # Update the layout for better readability
                fig.update_layout(
                    barmode="stack",
                    xaxis_title="Project",
                    yaxis_title="Count",
                    legend_title="Priority",
                    title_x=0.5,
                )

                # Display the chart
                st.plotly_chart(fig)

if __name__ == "__main__":
    main()
