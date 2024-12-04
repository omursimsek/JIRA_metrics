from fastapi import FastAPI, HTTPException, APIRouter
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, func, select, cast
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config


DATABASE_URL = config.DATABASE_URL

# Database setup
#DATABASE_URL = "sqlite:///./test.db"  # Replace with your actual database URL
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter()

# Define models for issues and bugs
class Issue(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String, unique=True, index=True, nullable=False)
    key = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    owner = Column(String, nullable=False)
    issue_type = Column(String, nullable=False)
    project = Column(String, nullable=False)
    created = Column(TIMESTAMP, nullable=False)
    resolutiondate = Column(TIMESTAMP)
    resolution = Column(String)

class Bug(Base):
    __tablename__ = "bugs"
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String)
    assignee = Column(String)
    bug_root_cause = Column(Text)

# Routes
@router.get("/bugs-per-day")
def get_bugs_per_day():
    session = SessionLocal()
    try:
        # Query for bugs created per day
        created_query = select(
            func.date(Issue.created).label("day"),
            cast(Issue.project, String).label("project"),
            func.count().label("created_count")
        ).group_by(
            func.date(Issue.created), 
            cast(Issue.project, String)
        )

        # Query for bugs resolved per day
        resolved_query = select(
            func.date(Issue.resolutiondate).label("day"),
            cast(Issue.project, String).label("project"),
            func.count().label("resolved_count")
        ).group_by(
            func.date(Issue.resolutiondate), 
            cast(Issue.project, String)
        )

        created_per_day = session.execute(created_query).fetchall()
        resolved_per_day = session.execute(resolved_query).fetchall()

        # Format results into dictionaries
        created_per_day_data = [{"day": row[0], "created_count": row[2], "project": row[1]} for row in created_per_day]
        resolved_per_day_data = [{"day": row[0], "resolved_count": row[2], "project": row[1]} for row in resolved_per_day]

        return {"created_per_day": created_per_day_data, "resolved_per_day": resolved_per_day_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
    finally:
        session.close()
