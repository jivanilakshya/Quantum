"""
Database models for meeting intelligence.

This project started with minimal tables and has grown into a persistent transcript + AI summary
pipeline. Vexa transcript response formats vary (sometimes `transcript`, sometimes `segments`),
so we store normalized segment rows and generate summaries from the merged full transcript text.

NOTE on schema evolution (SQLite):
- We keep a lightweight migration in `init_db()` for common additive changes (new columns/tables).
- For production Postgres/MySQL, migrate this logic to Alembic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)
    meeting_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    duration = Column(Integer)  # in minutes
    status = Column(String, default="active")  # active, completed, processing
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_email = Column(String, index=True, nullable=True)
    
    # Relationships
    transcripts = relationship("Transcript", back_populates="meeting", cascade="all, delete-orphan")
    summary = relationship("Summary", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    meeting_summary = relationship("MeetingSummary", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    participants = relationship("Participant", back_populates="meeting", cascade="all, delete-orphan")
    emotions = relationship("Emotion", back_populates="meeting", cascade="all, delete-orphan")


class Transcript(Base):
    __tablename__ = "transcripts"
    
    # Legacy primary key (kept for backward compatibility).
    id = Column(Integer, primary_key=True, index=True)
    # New explicit transcript_id requested by product spec (kept alongside `id`).
    transcript_id = Column(Integer, unique=True, index=True, nullable=True)
    meeting_id = Column(String, ForeignKey("meetings.meeting_id"), nullable=False)
    # Normalize naming: store speaker label as speaker_name.
    speaker = Column(String)  # legacy name
    speaker_name = Column(String, index=True, nullable=True)
    # Keep raw timestamp as text (Vexa may return ISO string or MM:SS).
    timestamp = Column(String, index=True, nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    meeting = relationship("Meeting", back_populates="transcripts")

    # Prevent accidental duplicates during incremental/live updates.
    # We consider a segment unique by meeting + timestamp + speaker + text.
    __table_args__ = (
        UniqueConstraint(
            "meeting_id",
            "timestamp",
            "speaker_name",
            "text",
            name="uq_transcripts_meeting_ts_speaker_text",
        ),
    )


class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String, ForeignKey("meetings.meeting_id"), unique=True, nullable=False)
    summary = Column(Text)
    key_points = Column(Text)  # JSON string
    decisions = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meeting = relationship("Meeting", back_populates="summary")


class MeetingSummary(Base):
    """
    Production summary model (requested by new spec).
    Stores structured Gemini output and supports regeneration/caching.
    """

    __tablename__ = "meeting_summaries"

    summary_id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String, ForeignKey("meetings.meeting_id"), unique=True, nullable=False, index=True)

    short_summary = Column(Text, nullable=True)
    detailed_summary = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)  # JSON string array
    decisions = Column(Text, nullable=True)  # JSON string array
    action_items = Column(Text, nullable=True)  # JSON string array of objects
    sentiment = Column(Text, nullable=True)  # JSON string/object
    meeting_outcome = Column(Text, nullable=True)

    generated_by = Column(String, nullable=True)  # e.g. "gemini-1.5-pro"
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)

    meeting = relationship("Meeting", back_populates="meeting_summary")


class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String, ForeignKey("meetings.meeting_id"), nullable=False)
    task = Column(String, nullable=False)
    owner = Column(String)
    due_date = Column(String)
    priority = Column(String)  # high, medium, low
    status = Column(String, default="todo")  # todo, in-progress, done
    
    meeting = relationship("Meeting", back_populates="action_items")


class Participant(Base):
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String, ForeignKey("meetings.meeting_id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String)
    
    meeting = relationship("Meeting", back_populates="participants")


class Emotion(Base):
    __tablename__ = "emotions"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String, ForeignKey("meetings.meeting_id"), nullable=False)
    timestamp = Column(String)
    emotion = Column(String)  # happy, neutral, concerned, frustrated
    intensity = Column(Float)  # 0.0 to 1.0
    
    meeting = relationship("Meeting", back_populates="emotions")


# Database setup
DATABASE_URL = "sqlite:///./quantum_meetings.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _sqlite_has_column(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)

def _sqlite_add_column_if_missing(conn, table: str, column_ddl: str, column_name: str) -> None:
    if not _sqlite_has_column(conn, table, column_name):
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_ddl}"))

def init_db():
    """
    Initialize database tables.

    We also do lightweight migrations for SQLite so developers can upgrade without manual steps.
    Only additive/low-risk changes are handled here.
    """
    Base.metadata.create_all(bind=engine)

    # SQLite additive migrations
    with engine.begin() as conn:
        # meetings.owner_email
        if conn.dialect.name == "sqlite":
            _sqlite_add_column_if_missing(conn, "meetings", "owner_email VARCHAR", "owner_email")

            # transcripts enhancements (keep legacy columns too)
            _sqlite_add_column_if_missing(conn, "transcripts", "transcript_id INTEGER", "transcript_id")
            _sqlite_add_column_if_missing(conn, "transcripts", "speaker_name VARCHAR", "speaker_name")
            _sqlite_add_column_if_missing(conn, "transcripts", "created_at DATETIME", "created_at")

            # meeting_summaries table is created by metadata.create_all above.

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
