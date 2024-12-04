
import streamlit as st
import requests
import pandas as pd
import altair as alt
from datetime import datetime
import plotly.graph_objects as go

# API Base URL
API_BASE_URL = "http://backend:8000/bugs"  # Replace with your actual API base URL

# Function to fetch data from the `/bugs-per-day` endpoint
def fetch_bugs_per_day():
    try:
        response = requests.get(f"{API_BASE_URL}/bugs-per-day")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching daily data: {e}")
        return None

# Function to fetch data from the `/bugs-per-week` endpoint
def fetch_bugs_per_week():
    try:
        response = requests.get(f"{API_BASE_URL}/bugs-per-week")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weekly data: {e}")
        return None

# Function to filter data by date range
def filter_date_range(df, start_date, end_date, date_col):
    df[date_col] = pd.to_datetime(df[date_col])
    return df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]

# Main Streamlit application
def main():
    st.title("Bug Statistics")

    # Generate the date range from July 15, 2024, to the current date
    start_date = "2024-07-15"
    end_date = "2024-12-02"
    date_range = pd.date_range(start=start_date, end=end_date)

    # Create a DataFrame with all days in the date range
    date_df = pd.DataFrame({'date': date_range})

    # Tabs for daily and weekly data
    tab1, tab2 = st.tabs(["Daily Data", "Weekly Data"])

    # Daily Data Tab
    with tab1:
        #st.header("Bugs Per Day")
        daily_data = fetch_bugs_per_day()

        if daily_data:
            # Prepare dataframes for created and resolved data
            created_df = pd.DataFrame(daily_data["created_per_day"])
            resolved_df = pd.DataFrame(daily_data["resolved_per_day"])

            # Ensure that the 'date' column in date_df and the keys in created_df and resolved_df are datetime
            date_df['date'] = pd.to_datetime(date_df['date'])
            created_df['day'] = pd.to_datetime(created_df['day'])
            resolved_df['day'] = pd.to_datetime(resolved_df['day'])

            # Merge the date_df with created_df to get the count for created issues
            created_df = date_df.merge(created_df, left_on='date', right_on='day', how='left')
            created_df = created_df.rename(columns={'count': 'created_count'}).drop(columns=['day'])

            # Merge the date_df with resolved_df to get the count for resolved issues
            resolved_df = date_df.merge(resolved_df, left_on='date', right_on='day', how='left')
            resolved_df = resolved_df.rename(columns={'count': 'resolved_count'}).drop(columns=['day'])

            # Merge the created_df and resolved_df to get the final DataFrame
            final_df = pd.merge(created_df, resolved_df, on='date', how='outer')

            # Fill NaN values with 0 (no issues created or resolved on that day)
            final_df.fillna(0, inplace=True)

            # Plot the combined chart
            #st.subheader("Bugs Created and Resolved Per Day")
            # Create a Plotly figure
            fig = go.Figure()

            # Add the first data series to the plot
            fig.add_trace(
                go.Scatter(
                    x=final_df['date'],
                    y=final_df['created_count'],
                    mode='lines+markers',
                    name='Created'
                )
            )

            # Add the second data series to the plot
            fig.add_trace(
                go.Scatter(
                    x=final_df['date'],
                    y=final_df['resolved_count'],
                    mode='lines+markers',
                    name='Resolved'
                )
            )

            # Customize the chart
            fig.update_layout(
                title='',
                xaxis_title='Date',
                yaxis_title='Value',
                template='plotly_dark',  # You can change the template to 'plotly', 'ggplot2', etc.
                xaxis=dict(tickangle=45),  # Rotate x-axis labels for better readability
            )

            # Display the plot in Streamlit
            st.plotly_chart(fig)

    # Weekly Data Tab
    with tab2:
        #st.header("Bugs Per Week")
        #weekly_data = fetch_bugs_per_week()

        if daily_data:
            # Prepare dataframes for created and resolved data
            created_df = pd.DataFrame(daily_data["created_per_day"])
            resolved_df = pd.DataFrame(daily_data["resolved_per_day"])

            # Ensure that the 'date' column in date_df and the keys in created_df and resolved_df are datetime
            date_df['date'] = pd.to_datetime(date_df['date'])
            created_df['day'] = pd.to_datetime(created_df['day'])
            resolved_df['day'] = pd.to_datetime(resolved_df['day'])

            # Merge the date_df with created_df to get the count for created issues
            created_df = date_df.merge(created_df, left_on='date', right_on='day', how='left')
            created_df = created_df.rename(columns={'count': 'created_count'}).drop(columns=['day'])

            # Merge the date_df with resolved_df to get the count for resolved issues
            resolved_df = date_df.merge(resolved_df, left_on='date', right_on='day', how='left')
            resolved_df = resolved_df.rename(columns={'count': 'resolved_count'}).drop(columns=['day'])

            # Merge the created_df and resolved_df to get the final DataFrame
            final_df = pd.merge(created_df, resolved_df, on='date', how='outer')

            # Fill NaN values with 0 (no issues created or resolved on that day)
            final_df.fillna(0, inplace=True)

            # Group the data by week starting from July 15, 2024, and aggregate counts
            final_df['week_start'] = final_df['date'].dt.to_period('W').dt.start_time  # Set week start dates

            # Aggregating counts by week
            weekly_data = final_df.groupby('week_start').agg(
                created_count=('created_count', 'sum'),
                resolved_count=('resolved_count', 'sum')
            ).reset_index()

            # Streamlit title
            #st.title("Bugs Created and Resolved Per Week")

            # Create a Plotly figure
            fig = go.Figure()

            # Add the first data series (created count) to the plot
            fig.add_trace(
                go.Bar(
                    x=weekly_data['week_start'],
                    y=weekly_data['created_count'],
                    name='Created Count',
                    marker_color='blue'
                )
            )

            # Add the second data series (resolved count) to the plot
            fig.add_trace(
                go.Bar(
                    x=weekly_data['week_start'],
                    y=weekly_data['resolved_count'],
                    name='Resolved Count',
                    marker_color='orange'
                )
            )

            # Customize the chart
            fig.update_layout(
                title='',
                xaxis_title='Week Starting Date',
                yaxis_title='Count',
                template='plotly_dark',
                xaxis=dict(tickangle=45, type='category'),  # Adjust x-axis type for datetime display
            )

            # Display the plot in Streamlit
            st.plotly_chart(fig)

if __name__ == "__main__":
    main()
