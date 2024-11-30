import asyncio
import asyncpg
import pandas as pd

# Database configuration
DB_CONFIG = {
    "user": "postgres",
    "password": "password",
    "database": "jira_data",
    "host": "db",
    "port": 5432,
}

# Helper function to create a database connection
async def get_db_connection():
    return await asyncpg.connect(**DB_CONFIG)

# Fetch issues data
async def fetch_issues_data(project_filter=None, status_filter=None, assignee_filter=None):
    query = "SELECT * FROM issues WHERE 1=1"
    params = []
    
    if project_filter:
        query += " AND project = $1"
        params.append(project_filter)
    if status_filter:
        query += f" AND status = ${len(params) + 1}"
        params.append(status_filter)
    if assignee_filter:
        query += f" AND assignee = ${len(params) + 1}"
        params.append(assignee_filter)

    conn = await get_db_connection()
    rows = await conn.fetch(query, *params)
    await conn.close()
    
    return pd.DataFrame(rows)

# Fetch status history data
async def fetch_status_history(project_filter=None):
    query = """
        SELECT h.issue_id, h.status, h.changed_at
        FROM issue_status_history h
        JOIN issues i ON h.issue_id = i.issue_id
        WHERE 1=1
    """
    params = []
    if project_filter:
        query += " AND i.project = $1"
        params.append(project_filter)
    
    conn = await get_db_connection()
    rows = await conn.fetch(query, *params)
    await conn.close()
    
    return pd.DataFrame(rows,columns=["issue_id","status","changed_at"])

# Fetch assignee history data
async def fetch_assignee_history(project_filter=None):
    query = """
        SELECT h.issue_id, h.assignee, h.changed_at
        FROM issue_assignee_history h
        JOIN issues i ON h.issue_id = i.issue_id
        WHERE 1=1
    """
    params = []
    if project_filter:
        query += " AND i.project = $1"
        params.append(project_filter)
    
    conn = await get_db_connection()
    rows = await conn.fetch(query, *params)
    await conn.close()
    
    return pd.DataFrame(rows)
