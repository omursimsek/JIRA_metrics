import asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import fetch_issues_data, fetch_status_history, fetch_assignee_history

# Streamlit App Configuration
st.set_page_config(page_title="Jira Dashboard", layout="wide")

st.title("Jira Issue Tracker Dashboard")

# Sidebar Filters
st.sidebar.header("Filters")
project_filter = st.sidebar.text_input("Project Key (optional)", "")
status_filter = st.sidebar.text_input("Status (optional)", "")
assignee_filter = st.sidebar.text_input("Assignee (optional)", "")

# Fetch Data
issues_data = asyncio.run(fetch_issues_data(project_filter, status_filter, assignee_filter))
status_history_data = asyncio.run(fetch_status_history(project_filter))
assignee_history_data = asyncio.run(fetch_assignee_history(project_filter))

# Display Data Summary
st.header("Data Summary")
st.write(f"Total Issues: {len(issues_data)}")
st.write(f"Status History Records: {len(status_history_data)}")
st.write(f"Assignee History Records: {len(assignee_history_data)}")

# Display Data as Tables
with st.expander("Issues Table"):
    st.dataframe(issues_data)

with st.expander("Status History Table"):
    st.dataframe(status_history_data)

with st.expander("Assignee History Table"):
    st.dataframe(assignee_history_data)

# Visualization Section
st.header("Visualizations")

# Chart: Issue Count by Status
st.subheader("Issue Count by Status")
#print(issues_data)
status_count = issues_data[3].value_counts().reset_index()
status_count.columns = ["Status", "Count"]
fig1 = px.bar(status_count, x="Status", y="Count", title="Issue Count by Status", text="Count")
st.plotly_chart(fig1, use_container_width=True)

# Chart: Assignee Distribution
st.subheader("Issues by Assignee")
assignee_count = issues_data[4].value_counts().reset_index()
assignee_count.columns = ["Assignee", "Count"]
fig2 = px.pie(assignee_count, names="Assignee", values="Count", title="Issues by Assignee")
st.plotly_chart(fig2, use_container_width=True)

# Chart: Status Changes Over Time
st.write(status_history_data)
st.subheader("Status Changes Over Time")
status_history_data["changed_at"] = pd.to_datetime(status_history_data["changed_at"])
status_history_grouped = status_history_data.groupby("changed_at")["status"].count().reset_index()
#st.write(status_history_data)
fig3 = px.line(
    status_history_grouped,
    x="changed_at",
    y="status",
    title="Status Changes Over Time",
    labels={"changed_at": "Date", "status": "Change Count"}
)
st.plotly_chart(fig3, use_container_width=True)


# Chart: Assignee Changes Over Time
st.subheader("Assignee Changes Over Time")
assignee_history_data[2] = pd.to_datetime(assignee_history_data[2])
assignee_history_grouped = assignee_history_data.groupby(2)[1].count().reset_index()
fig4 = px.line(
    assignee_history_grouped,
    x="changed_at",
    y="assignee",
    title="Assignee Changes Over Time",
    labels={"changed_at": "Date", "assignee": "Change Count"}
)
st.plotly_chart(fig4, use_container_width=True)