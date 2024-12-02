
from fastapi import APIRouter
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List
import asyncpg
import config
import pandas as pd

router = APIRouter()

# Load environment variables
JIRA_BASE_URL = config.JIRA_BASE_URL
JIRA_API_TOKEN = config.JIRA_API_TOKEN
JIRA_EMAIL = config.JIRA_EMAIL
DATABASE_URL = config.DATABASE_URL

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
WORKING_HOURS_END = 18  # End of the working day
LUNCH_START = 12         # 12:00 PM
LUNCH_END = 13           # 1:00 PM

# Product mapping moved to frontend
PRODUCT_MAPPING = {
    "RTMS": ["FFF", "SLY", "EXW"],
    "PTM/ROM": ["PB", "SMY"],
    "RSB/FLEET": ["AAV"],
    "Integration": ["ISY"]
}

class TimeStatusStory(BaseModel):
    issue_id: str
    key: str
    project: str
    status: str
    #from_status: str
    #changed_at_start: datetime
    #changed_at_end: datetime
    story_points: int
    owner: str
    current_status: str
    working_hours: float
    product: str

async def fetch_from_db(query: str):
    conn = await asyncpg.connect(DATABASE_URL)
    data = await conn.fetch(query)
    await conn.close()
    return data

@router.get("/stories", response_model=List[TimeStatusStory])
async def get_average_times():
    query = """
            SELECT
            s.issue_id,
            i.key,
            i.project,
            sh.from_status AS from_status,
            sh.to_status AS status,
            sh.changed_at AS changed_at_start,
            COALESCE(LEAD(sh.changed_at) OVER (PARTITION BY s.issue_id ORDER BY sh.changed_at), NOW()) AS changed_at_end,
            s.story_points,
            i.owner,
            s.status AS current_status
        FROM
            status_history sh
        JOIN issues i ON sh.issue_id = i.issue_id
        JOIN stories s ON s.issue_id = i.issue_id
        where s.status = 'Closed'
    """
    data = await fetch_from_db(query)

    df = pd.DataFrame(data, columns=["issue_id","key","project","from_status","status","changed_at_start","changed_at_end","story_points","owner","current_status"])
    df = df[df["status"] == "in progress"]
    df = df[df["owner"] != "None"]
    
     # Ensure necessary datetime columns exist
    if "changed_at_start" not in df.columns or "changed_at_end" not in df.columns:
        return "Data does not contain required time columns."

    # Convert time columns to datetime
    df["changed_at_start"] = pd.to_datetime(df["changed_at_start"], utc=True, format='mixed')
    df["changed_at_end"] = pd.to_datetime(df["changed_at_end"], utc=True, format='mixed')

    # Calculate working hours for each row
    df["working_hours"] = df.apply(
        lambda row: calculate_working_hours(row["changed_at_start"], row["changed_at_end"]), axis=1
    )

    df["product"] = df["project"].map(
        lambda x: next((product for product, projects in PRODUCT_MAPPING.items() if x in projects), None)
    )

    # Remove rows where product mapping was not found
    df = df.dropna(subset=["product"])

    #df.drop(["changed_at_start"], axis=1);
    grouped_df = (
        df.groupby(["issue_id", "key", "project", "status", "story_points", "owner", "current_status","product"], as_index=False)
        .agg({"working_hours": "sum"})
    )
    grouped_df["working_hours"] = grouped_df["working_hours"].round(2)
    return grouped_df.to_dict(orient="records")

    #return data
    return [
        {
            "issue_id": record["issue_id"],
            "key":record["key"],
            "project":record["project"],
            "status": record["status"],
            "from_status": record["from_status"],
            "changed_at_start": record["changed_at_start"],
            "changed_at_end": record["changed_at_end"],
            "story_points": record["story_points"],
            "owner": record["owner"],
            "current_status": record["current_status"]
        }
        for record in data
    ]

def calculate_working_hours(start_time, end_time):
    """
    Calculate the working hours between two datetime objects,
    excluding weekends, Turkish holidays, and a lunch break.
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
            lunch_start = current.replace(hour=LUNCH_START, minute=0, second=0, microsecond=0)
            lunch_end = current.replace(hour=LUNCH_END, minute=0, second=0, microsecond=0)

            if end_time < start_of_day:
                break;

            # Adjust current time to the start of the working day if before start
            if current < start_of_day:
                current = min(end_time, start_of_day)

            # Skip to the next day if the current time is beyond the end of the working day
            if current >= end_of_day:
                current += timedelta(days=1)
                current = current.replace(hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0)
                continue

            # Calculate working hours for the current day
            effective_end_time = min(end_of_day, end_time)

            if current < lunch_start:  # Before lunch
                total_hours += (min(lunch_start, effective_end_time) - current).total_seconds() / 3600.0
                current = min(effective_end_time, lunch_end)  # Skip to after lunch if necessary
            if current >= lunch_end:  # After lunch
                total_hours += (effective_end_time - max(current, lunch_end)).total_seconds() / 3600.0

        # Move to the next day
        current += timedelta(days=1)
        current = current.replace(hour=WORKING_HOURS_START, minute=0, second=0, microsecond=0)

    # Convert total hours from timedelta to float hours
    total_hours_in_hours = total_hours.total_seconds() / 3600 if isinstance(total_hours, timedelta) else total_hours
    return total_hours_in_hours

class TimeStatusBug(BaseModel):
    issue_id: str
    key: str
    project: str
    status: str
    #from_status: str
    #changed_at_start: datetime
    #changed_at_end: datetime
    #story_points: int
    owner: str
    current_status: str
    working_hours: float
    product: str

@router.get("/bugs", response_model=List[TimeStatusBug])
async def get_average_times():
    query = """
            SELECT
            s.issue_id,
            i.key,
            i.project,
            sh.from_status AS from_status,
            sh.to_status AS status,
            sh.changed_at AS changed_at_start,
            COALESCE(LEAD(sh.changed_at) OVER (PARTITION BY s.issue_id ORDER BY sh.changed_at), NOW()) AS changed_at_end,
            i.owner,
            s.status AS current_status
        FROM
            status_history sh
        JOIN issues i ON sh.issue_id = i.issue_id
        JOIN bugs s ON s.issue_id = i.issue_id
        where s.status = 'Closed'
    """
    data = await fetch_from_db(query)

    df = pd.DataFrame(data, columns=["issue_id","key","project","from_status","status","changed_at_start","changed_at_end","owner","current_status"])
    df = df[df["status"] == "in progress"]
    df = df[df["owner"] != "None"]
    
     # Ensure necessary datetime columns exist
    if "changed_at_start" not in df.columns or "changed_at_end" not in df.columns:
        return "Data does not contain required time columns."

    # Convert time columns to datetime
    df["changed_at_start"] = pd.to_datetime(df["changed_at_start"], utc=True, format='mixed')
    df["changed_at_end"] = pd.to_datetime(df["changed_at_end"], utc=True, format='mixed')

    # Calculate working hours for each row
    df["working_hours"] = df.apply(
        lambda row: calculate_working_hours(row["changed_at_start"], row["changed_at_end"]), axis=1
    )

    df["product"] = df["project"].map(
        lambda x: next((product for product, projects in PRODUCT_MAPPING.items() if x in projects), None)
    )

    # Remove rows where product mapping was not found
    df = df.dropna(subset=["product"])

    #df.drop(["changed_at_start"], axis=1);
    grouped_df = (
        df.groupby(["issue_id", "key", "project", "status", "owner", "current_status","product"], as_index=False)
        .agg({"working_hours": "sum"})
    )
    grouped_df["working_hours"] = grouped_df["working_hours"].round(2)
    return grouped_df.to_dict(orient="records")