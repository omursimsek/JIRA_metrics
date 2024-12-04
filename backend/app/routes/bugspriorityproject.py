from fastapi import FastAPI, HTTPException, APIRouter
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, func, select, cast, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
import config


DATABASE_URL = config.DATABASE_URL

# Database setup
DATABASE_URL = config.DATABASE_URL
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter()

# Define the Issue model
class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String, unique=True, index=True, nullable=False)  # Unique ID to link with Bug
    key = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    owner = Column(String, nullable=False)
    issue_type = Column(String, nullable=False)
    project = Column(String, nullable=False)
    created = Column(TIMESTAMP, nullable=False)
    resolutiondate = Column(TIMESTAMP)
    resolution = Column(String)

    # Establish a one-to-one or one-to-many relationship with Bug
    bugs = relationship("Bug", back_populates="issue", cascade="all, delete-orphan")


# Define the Bug model
class Bug(Base):
    __tablename__ = "bugs"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String, ForeignKey("issues.issue_id"), unique=True, index=True, nullable=False)  # Foreign key to Issue
    status = Column(String)
    assignee = Column(String)
    bug_root_cause = Column(Text)
    priority = Column(String)

    # Reference back to the Issue model
    issue = relationship("Issue", back_populates="bugs")


# Routes
@router.get("/priority")
def get_bugs_per_day():
    session = SessionLocal()
    try:
        # bugs root causes by project
        # created_query = select(
        #     cast(Issue.project, String).label("project"),
        #     cast(Bug.bug_root_cause, String).label("root_cause"),
        #     func.count().label("created_count")
        # ).group_by( 
        #     cast(Issue.project, String),
        #     cast(Bug.bug_root_cause, String)
        # )

        created_query = select(
            cast(Issue.project, String).label("project"),
            cast(Bug.priority, String).label("priority"),
            func.count().label("created_count")
        ).select_from(
            Bug
        ).join(
            Issue, isouter=True  # Uses the defined relationship
        ).group_by(
            cast(Issue.project, String),
            cast(Bug.priority, String)
        )

        priorities = session.execute(created_query).fetchall()

        # Format results into dictionaries
        priorities = [{"project": row[0], "priority": row[1], "count": row[2] } for row in priorities]

        return {"priorities": priorities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
    finally:
        session.close()
