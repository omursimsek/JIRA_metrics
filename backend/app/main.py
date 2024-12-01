import os
import requests
import asyncio
from fastapi import FastAPI, HTTPException
import asyncpg
from pydantic import BaseModel
from typing import List
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


async def insert_issue_data(issue, type):
    async with db_pool.acquire() as connection:
        # Insert issue data
        if issue["fields"]["customfield_10180"] is None:
            owner = "None"
        elif issue["fields"]["customfield_10180"]["displayName"] is None:
            owner = "None"
        else:
            owner = issue["fields"]["customfield_10180"]["displayName"]
        await connection.execute(
            """
            INSERT INTO issues (issue_id, key, summary, owner, issue_type)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (issue_id) DO NOTHING
            """,
            issue["id"],
            issue["key"],
            issue["fields"]["summary"],
            owner,
            type,
        )

        if type == "story":
            # Insert or update the story in the stories table
            customfield_value = issue["fields"].get("customfield_10026")

            try:
                customfield_int = int(customfield_value) if customfield_value is not None else None
            except ValueError:
                # Handle the case where the value cannot be converted to an integer
                customfield_int = 0
            if issue["fields"]["customfield_10202"] is None:
                code_reviewer = "None"
            elif issue["fields"]["customfield_10202"]["displayName"] is None:
                code_reviewer = "None"
            else:
                code_reviewer = issue["fields"]["customfield_10202"]["displayName"]
            if issue["fields"]["customfield_10203"] is None:
                code_review_status = "None"
            elif issue["fields"]["customfield_10203"]["value"] is None:
                code_review_status = "None"
            else:
                code_review_status = issue["fields"]["customfield_10203"]["value"]
            await connection.execute(
                """
                INSERT INTO stories (issue_id, story_points, status, assignee, code_reviewer, code_review_status)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (issue_id) DO UPDATE
                SET story_points = EXCLUDED.story_points, 
                    status = EXCLUDED.status, 
                    assignee = EXCLUDED.assignee,
                    code_reviewer = EXCLUDED.code_reviewer, 
                    code_review_status = EXCLUDED.code_review_status 
                """,
                issue["id"],
                customfield_int,  # Story points
                issue["fields"]["status"]["name"],
                issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "None",
                code_reviewer,  # Code review status
                code_review_status,  # Code review result
            )

            # Insert code review history
            for history in issue["changelog"]["histories"]:
                for item in history["items"]:
                    if item["field"] == "Code Review Results":
                        changed_at = parse_jira_timestamp(history["created"])
                        await connection.execute(
                            """
                            INSERT INTO code_review_history (issue_id, code_review_status, changed_at)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (issue_id, code_review_status, changed_at) DO NOTHING
                            """,
                            issue["id"],
                            item["toString"],
                            changed_at,
                        )
        elif type == "bug":
            # Insert or update the bug in the bugs table
            customfield_value = (
                issue["fields"].get("customfield_10104", [])
                if isinstance(issue["fields"].get("customfield_10104"), list)
                else []
            )

            # Extract the "displayName" from the first item in the list if it exists
            bug_root_cause = (
                customfield_value[0].get("displayName", "None") if customfield_value else "None"
            )

            await connection.execute(
                """
                INSERT INTO bugs (issue_id, status, assignee, bug_root_cause)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (issue_id) DO UPDATE
                SET status = EXCLUDED.status, 
                    assignee = EXCLUDED.assignee,
                    bug_root_cause = EXCLUDED.bug_root_cause 
                """,
                issue["id"],
                issue["fields"]["status"]["name"],
                issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "None",
                bug_root_cause, # Bug_root_cause
            )

        # Insert status history
        for history in issue["changelog"]["histories"]:
            for item in history["items"]:
                if item["field"] == "status":
                    changed_at = parse_jira_timestamp(history["created"])
                    await connection.execute(
                        """
                        INSERT INTO status_history (issue_id, from_status, to_status, changed_at)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (issue_id, from_status, to_status, changed_at) DO NOTHING
                        """,
                        issue["id"],
                        item["fromString"],
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
                        INSERT INTO assignee_history (issue_id, from_assignee, to_assignee, changed_at)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (issue_id, from_assignee, to_assignee, changed_at) DO NOTHING
                        """,
                        issue["id"],
                        item["fromString"] if item["fromString"] is not None else "None",
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


@app.get("/fetch-jira-data/{project_key}/story")
async def fetch_jira_data(project_key: str):
    """
    Fetch all issues from a Jira project and store them in the database.
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    start_at = 0
    max_results = 100
    total_issues = 0

    while True:
        params = {
            "jql": f"project={project_key} AND issuetype=Story",
            "fields": "summary,status,assignee,customfield_10026,customfield_10202,customfield_10203,customfield_10180", #story points, code reviewer, code review result, owner
            "expand": "changelog",
            "startAt": start_at,
            "maxResults": max_results,
        }

        response = requests.get(url, auth=auth, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        issues = data.get("issues", [])
        total_issues += len(issues)

        for issue in issues:
            await insert_issue_data(issue, "story")

        # Check if we've fetched all issues
        if start_at + len(issues) >= data.get("total", 0):
            break

        # Update startAt for the next page
        start_at += max_results

    return {"message": f"Fetched and stored data for {total_issues} issues in project {project_key}"}

@app.get("/fetch-jira-data/{project_key}/bug")
async def fetch_jira_data(project_key: str):
    """
    Fetch all issues from a Jira project and store them in the database.
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    start_at = 0
    max_results = 100
    total_issues = 0

    while True:
        params = {
            "jql": f"project={project_key} AND issuetype=Bug",
            "fields": "summary,status,assignee,customfield_10180,customfield_10104", #owner, root cause
            "expand": "changelog",
            "startAt": start_at,
            "maxResults": max_results,
        }

        response = requests.get(url, auth=auth, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        issues = data.get("issues", [])
        total_issues += len(issues)

        for issue in issues:
            await insert_issue_data(issue, "bug")

        # Check if we've fetched all issues
        if start_at + len(issues) >= data.get("total", 0):
            break

        # Update startAt for the next page
        start_at += max_results

    return {"message": f"Fetched and stored data for {total_issues} issues in project {project_key}"}

class IssueStatusHistory(BaseModel):
    issue_id: str
    status: str
    changed_at_start: datetime
    changed_at_end: datetime
    story_points: int
    owner: str

async def fetch_from_db(query: str):
    conn = await asyncpg.connect(DATABASE_URL)
    data = await conn.fetch(query)
    await conn.close()
    return data

@app.get("/average-times", response_model=List[IssueStatusHistory])
async def get_average_times():
    query = """
    SELECT
        s.issue_id,
        s.status AS status,
        sh.changed_at AS changed_at_start,
        LEAD(sh.changed_at) OVER (PARTITION BY s.issue_id ORDER BY sh.changed_at) AS changed_at_end,
        st.story_points,
        i.owner
    FROM
        status_history sh
    JOIN issues i ON sh.issue_id = i.issue_id
    JOIN stories st ON st.issue_id = s.issue_id
    """
    data = await fetch_from_db(query)
    return [
        {
            "issue_id": record["issue_id"],
            "status": record["status"],
            "changed_at_start": record["changed_at_start"],
            "changed_at_end": record["changed_at_end"],
            "story_points": record["story_points"],
            "owner": record["owner"]
        }
        for record in data
    ]