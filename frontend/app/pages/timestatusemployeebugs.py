import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

API_URL = "http://backend:8000/timestatus/bugs"

# Fetch data from the API
def fetch_average_time():
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data from backend.")
        return []

# Main function to process data and calculate metrics
def main():
    st.title("Average Time in Progress Analysis")

    # Fetch the raw data from the API
    raw_data = fetch_average_time()

    if not raw_data:
        return  # Exit if data fetch failed

    # Convert raw data to a DataFrame
    df = pd.DataFrame(raw_data)
    df["count"] = df.apply(
        lambda row: (1), axis=1
    ) 

    #st.dataframe(df)   

    # Calculate time in progress per story point per owner
    #df['time_per_bug_owner'] = df['working_hours'] / df['story_points']
    grouped_df = (
        df.groupby(["owner","product"], as_index=False)
        .agg({"working_hours": "sum", "count":"sum"})
    )
    grouped_df = grouped_df[grouped_df["working_hours"] != 0]
    grouped_df = grouped_df[grouped_df["count"] != 0]

    # Calculate working hours for each row
    grouped_df["average_time_per_bug"] = grouped_df.apply(
        lambda row: (row["working_hours"] / row["count"]), axis=1
    )

    grouped_df = grouped_df.sort_values(by='average_time_per_bug', ascending=True)

    # Display owner metrics as a table
    st.subheader("Average Time in Progress per Bug per Owner")
    st.dataframe(grouped_df)

    # Plot average time per story point per owner
    fig_owner = px.bar(grouped_df, x='owner', y='average_time_per_bug',
                       title="Average Time in Progress per Bug per Owner",
                       labels={'average_time_per_bug': 'Average Time (hours)', 'owner': 'Owner'})
    
    # Add benchmark line
    fig_owner.add_hline(
        y=grouped_df["working_hours"].sum()/grouped_df['count'].sum(),
        #line_dash="dash",
        line_color="red",
        annotation_text="Company Average",
        annotation_position="right"
    )

    prd_averages =  (
        grouped_df.groupby(["product"], as_index=False)
        .agg({"working_hours": "sum", "count":"sum"})
    )

    # Calculate working hours for each row
    prd_averages["average_time_per_product"] = prd_averages.apply(
        lambda row: (row["working_hours"] / row["count"]), axis=1
    )

    color = ["green", "yellow", "pink", "orange"]

    for i in range(4):
        fig_owner.add_hline(
            y=prd_averages.iloc[i]["average_time_per_product"],
            #line_dash="dash",
            line_color=color[i],
            annotation_text=prd_averages.iloc[i]["product"],
            annotation_position="right"
        )

    st.plotly_chart(fig_owner)

    grouped_df = grouped_df.sort_values(by='count', ascending=False)

    # Plot average time per story point per owner
    fig_owner_bug = px.bar(grouped_df, x='owner', y='count',
                       title="Total Number of Bugs per Owner",
                       labels={'count': 'Average Time (hours)', 'owner': 'Owner'})
    
    # Add benchmark line
    fig_owner_bug.add_hline(
        y=grouped_df['count'].mean(),
        #line_dash="dash",
        line_color="red",
        annotation_text="Company Average",
        annotation_position="right"
    )

    st.plotly_chart(fig_owner_bug)

    # owner_metrics = df.groupby('owner')['time_per_story_point_owner'].mean().reset_index()
    # owner_metrics.columns = ['owner', 'avg_time_per_story_point_owner']

    # # Display owner metrics as a table
    # st.subheader("Average Time in Progress per Story Point per Owner")
    # st.dataframe(owner_metrics)

    # # Plot average time per story point per owner
    # fig_owner = px.bar(owner_metrics, x='owner', y='avg_time_per_story_point_owner',
    #                    title="Average Time in Progress per Story Point per Owner",
    #                    labels={'avg_time_per_story_point_owner': 'Average Time (hours)', 'owner': 'Owner'})
    # st.plotly_chart(fig_owner)

    # Calculate overall average time in progress per story point
    overall_avg_time_per_bug = grouped_df["working_hours"].sum()/grouped_df['count'].sum()
    st.subheader("Overall Average Time in Progress per Bug")
    st.metric("Overall Average Time (hours)", f"{overall_avg_time_per_bug:.2f}")

    # Calculate time in progress per story point per product
    # product_metrics = df.groupby('product')['time_per_story_point_owner'].mean().reset_index()
    # product_metrics.columns = ['product', 'avg_time_per_story_point_product']

    # Display product metrics as a table
    st.subheader("Average Time in Progress per Bug per Product")
    st.dataframe(prd_averages)

    # Plot average time per story point per product
    fig_product = px.bar(prd_averages, x='product', y='average_time_per_product',
                         title="Average Time in Progress per Bug per Product",
                         labels={'average_time_per_product': 'Average Time (hours)', 'product': 'Product'})
    st.plotly_chart(fig_product)

if __name__ == "__main__":
    main()
