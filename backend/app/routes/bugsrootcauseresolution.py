from fastapi import FastAPI, HTTPException, APIRouter
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, func, select, cast, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
import config


DATABASE_URL = config.DATABASE_URL

# Database setup
#DATABASE_URL = "sqlite:///./test.db"  # Replace with your actual database URL
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

    # Reference back to the Issue model
    issue = relationship("Issue", back_populates="bugs")


# Routes
@router.get("/rootcausewithrd")
def get_bugs_per_day():
    session = SessionLocal()
    try:
        created_query = select(
            cast(Issue.project, String).label("project"),
            cast(Bug.bug_root_cause, String).label("root_cause"),
            func.date(Issue.resolutiondate).label("date"),
            func.count().label("created_count")
        ).select_from(
            Bug
        ).join(
            Issue, isouter=True  # Uses the defined relationship
        ).group_by(
            cast(Issue.project, String),
            cast(Bug.bug_root_cause, String),
            func.date(Issue.resolutiondate).label("date")
        )

        root_causes = session.execute(created_query).fetchall()

        # Format results into dictionaries
        root_causes = [{"project": row[0], "root_Cause": row[1], "date": row[2], "count": row[3] } for row in root_causes]

        return {"root_causes": root_causes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
    finally:
        session.close()
