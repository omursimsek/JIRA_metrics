import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

API_URL = "http://backend:8000/average-times"

# Define Turkish public holidays
TURKISH_HOLIDAYS = [
    "2024-01-01",  # New Year's Day
    "2024-04-23",  # National Sovereignty and Children's Day
    "2024-05-01",  # Labor and Solidarity Day
    "2024-05-19",  # Commemoration of Atatürk, Youth and Sports Day
    "2024-07-15",  # Democracy and National Unity Day
    "2024-08-30",  # Victory Day
    "2024-10-29",  # Republic Day
    # Add additional holidays (e.g., religious holidays)
]

WORKING_HOURS_START = 9  # Start of the working day
WORKING_HOURS_END = 17  # End of the working day

# Product mapping moved to frontend
PRODUCT_MAPPING = {
    "RTMS": ["FFF", "SLY", "EXW"],
    "PTM/ROM": ["PB", "SMY"],
    "RSB/FLEET": ["AAV"],
    "Integration": ["ISY"]
}

def fetch_average_time():
    """Fetch raw code review data from the FastAPI backend."""
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data from backend.")
        return []

def calculate_working_hours(start_time, end_time):
    """
    Calculate the working hours between two datetime objects,
    excluding weekends and Turkish holidays.
    """
    if not start_time or not end_time:
        return 0

    holidays = [datetime.strptime(date, "%Y-%m-%d").date() for date in TURKISH_HOLIDAYS]
    total_hours = 0
    current = start_time
    while current < end_time:
        if current.weekday() < 5 and current.date() not in holidays:  # Weekday and not a holiday
            start_of_day = current.replace(hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0)
            end_of_day = current.replace(hour=WORKING_HOURS_END, minute=0, second=0, microsecond=0)
            if current < start_of_day:
                current = start_of_day
            if current > end_of_day:
                current += timedelta(days=1)
                current = current.replace(hour=WORKING_HOURS_START)
                continue
            total_hours += (min(end_of_day, end_time) - current).total_seconds() / 3600.0
        current += timedelta(days=1)
        current = current.replace(hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0)
    return total_hours

def main():
    st.title("Time Spent in 'In Progress' Status")

    # Fetch raw data from the API
    st.write("Loading data...")
    raw_data = fetch_average_time()
    if not raw_data:
        return

    # Convert raw data to DataFrame
    df = pd.DataFrame(raw_data)

    # Filter only for "In Progress" status
    df = df[df["status"] == "in progress"]
    st.dataframe(df)

    # Ensure necessary datetime columns exist
    if "changed_at_start" not in df.columns or "changed_at_end" not in df.columns:
        st.error("Data does not contain required time columns.")
        return

    # Convert time columns to datetime
    df["changed_at_start"] = pd.to_datetime(df["changed_at_start"], utc=True, format='mixed')
    df["changed_at_end"] = pd.to_datetime(df["changed_at_end"], utc=True, format='mixed')

    # Calculate working hours for each row
    df["working_hours"] = df.apply(
        lambda row: calculate_working_hours(row["changed_at_start"], row["changed_at_end"]), axis=1
    )

    # Add weekly breakdown
    df["week"] = df["changed_at_start"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly_aggregated = df.groupby(["project", "week"])["working_hours"].sum().reset_index()

    # Visualization: Line Chart for Weekly Data by Project
    st.subheader("Weekly 'In Progress' Times by Project")
    fig = px.line(
        weekly_aggregated, 
        x="week", 
        y="working_hours", 
        color="project", 
        title="Weekly 'In Progress' Times by Project",
        labels={"week": "Week", "working_hours": "Working Hours", "project": "Project"}
    )
    fig.update_layout(xaxis_title="Week", yaxis_title="Working Hours", legend_title="Project")
    st.plotly_chart(fig)

    df["product"] = df["project"].map(
        lambda x: next((product for product, projects in PRODUCT_MAPPING.items() if x in projects), None)
    )

    # Remove rows where product mapping was not found
    df = df.dropna(subset=["product"])

    # Add weekly breakdown
    df["week"] = df["changed_at_start"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly_aggregated = df.groupby(["product", "week"])["working_hours"].sum().reset_index()

    # # Generate a complete range of weeks within the data's date range
    # start_date = df["changed_at_start"].min().date()
    # end_date = df["changed_at_end"].max().date()
    # all_weeks = pd.date_range(start=start_date, end=end_date, freq='W')

    # # Create a DataFrame for all possible weeks and merge it with the data
    # all_weeks_df = pd.DataFrame({
    #     "week": all_weeks,
    #     "product": df["product"].unique()
    # })
    # all_weeks_df["week"] = all_weeks_df["week"].dt.date

    # # Merge and fill missing data with zero
    # complete_df = pd.merge(all_weeks_df, weekly_aggregated, on=["product", "week"], how="left").fillna(0)


    # Visualization: Line Chart for Weekly Data by Product
    st.subheader("Weekly 'In Progress' Times by Product")
    fig = px.line(
        weekly_aggregated, 
        x="week", 
        y="working_hours", 
        color="product", 
        title="Weekly 'In Progress' Times by Product",
        labels={"week": "Week", "working_hours": "Working Hours", "product": "Product"}
    )
    fig.update_layout(xaxis_title="Week", yaxis_title="Working Hours", legend_title="Product")
    st.plotly_chart(fig)

if __name__ == "__main__":
    main()
