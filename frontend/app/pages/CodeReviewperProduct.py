import streamlit as st
import pandas as pd
import plotly.express as px
import requests

API_URL = "http://backend:8000/code-review-history"

# Product mapping moved to frontend
PRODUCT_MAPPING = {
    "RTMS": ["FFF", "SLY", "EXW"],
    "PTM/ROM": ["PB", "SMY"],
    "RSB/FLEET": ["AAV"],
    "Integration": ["ISY"]
}


def fetch_code_review_data():
    """Fetch raw code review data from the FastAPI backend."""
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data from backend.")
        return []


def group_and_count_by_product(data):
    """Group raw data by product and calculate counts."""
    # Convert raw data into a DataFrame
    df = pd.DataFrame(data)
    
    # Map projects to products
    df["product"] = df["project"].map(
        lambda x: next((product for product, projects in PRODUCT_MAPPING.items() if x in projects), None)
    )

    # Remove rows where product mapping was not found
    df = df.dropna(subset=["product"])

    # Group and count by product and review_result
    grouped = df.groupby(["product", "code_review_status"]).size().reset_index(name="count")
    return grouped


def main():
    st.title("Code Review Results by Product")

    # Fetch raw data from the API
    st.write("Loading data...")
    raw_data = fetch_code_review_data()
    if not raw_data:
        return

    # Sidebar filter for products
    st.sidebar.header("Filters")
    all_products = sorted(PRODUCT_MAPPING.keys())
    selected_products = st.sidebar.multiselect("Select Products:", options=all_products, default=all_products)

    # Process raw data to calculate counts
    grouped_data = group_and_count_by_product(raw_data)

    # Filter grouped data by selected products
    filtered_data = grouped_data[grouped_data["product"].isin(selected_products)]

    # Visualization: Bar chart
    st.subheader("Bar Chart of Code Review Results by Product")
    fig = px.bar(
        filtered_data,
        x="product",
        y="count",
        color="code_review_status",
        title="Code Review Results by Product",
        labels={"product": "Product", "count": "Count", "review_result": "Review Result"}
    )
    st.plotly_chart(fig)


if __name__ == "__main__":
    main()
