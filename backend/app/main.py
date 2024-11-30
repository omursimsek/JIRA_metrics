import os
import requests
import asyncio
from fastapi import FastAPI, HTTPException
import asyncpg
from datetime import datetime

app = FastAPI()

# Load environment variables
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
DATABASE_URL = os.getenv("DATABASE_URL")

# Database connection pool
db_pool = None


@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)


@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()


async def insert_issue_data(issue):
    async with db_pool.acquire() as connection:
        # Insert issue data
        await connection.execute(
            """
            INSERT INTO issues (issue_id, summary, status, assignee)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (issue_id) DO UPDATE
            SET status = EXCLUDED.status, assignee = EXCLUDED.assignee
            """,
            issue["id"],
            issue["fields"]["summary"],
            issue["fields"]["status"]["name"],
            issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else None,
        )

        # Insert status history
        for history in issue["changelog"]["histories"]:
            for item in history["items"]:
                if item["field"] == "status":
                    changed_at = parse_jira_timestamp(history["created"])
                    await connection.execute(
                        """
                        INSERT INTO issue_status_history (issue_id, status, changed_at)
                        VALUES ($1, $2, $3)
                        """,
                        issue["id"],
                        item["toString"],
                        changed_at,
                    )

        # Insert assignee history
        for history in issue["changelog"]["histories"]:
            for item in history["items"]:
                if item["field"] == "assignee":
                    changed_at = parse_jira_timestamp(history["created"])
                    await connection.execute(
                        """
                        INSERT INTO issue_assignee_history (issue_id, assignee, changed_at)
                        VALUES ($1, $2, $3)
                        """,
                        issue["id"],
                        item["toString"],
                        changed_at,
                    )

def parse_jira_timestamp(timestamp_str):
    """
    Parse Jira's timestamp string into a naive datetime object.
    Example input: '2024-11-29T16:08:46.319+0100'
    """
    dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")  # Parse as timezone-aware
    return dt.replace(tzinfo=None)  # Convert to timezone-naive


@app.get("/fetch-jira-data/{project_key}")
async def fetch_jira_data(project_key: str):
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    params = {
        "jql": f"project={project_key} AND (issuetype=Story OR issuetype=Bug)",
        "fields": "summary,status,assignee",
        "expand": "changelog",
        "maxResults": 100,
    }

    response = requests.get(url, auth=auth, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    issues = response.json().get("issues", [])
    for issue in issues:
        await insert_issue_data(issue)

    return {"message": f"Fetched and stored data for {len(issues)} issues in project {project_key}"}
