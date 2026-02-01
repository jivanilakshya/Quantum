"""
Database models for meeting intelligence
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

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
    
    # Relationships
    transcripts = relationship("Transcript", back_populates="meeting", cascade="all, delete-orphan")
    summary = relationship("Summary", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    participants = relationship("Participant", back_populates="meeting", cascade="all, delete-orphan")
    emotions = relationship("Emotion", back_populates="meeting", cascade="all, delete-orphan")


class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String, ForeignKey("meetings.meeting_id"), nullable=False)
    speaker = Column(String)
    timestamp = Column(String)
    text = Column(Text, nullable=False)
    
    meeting = relationship("Meeting", back_populates="transcripts")


class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String, ForeignKey("meetings.meeting_id"), unique=True, nullable=False)
    summary = Column(Text)
    key_points = Column(Text)  # JSON string
    decisions = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meeting = relationship("Meeting", back_populates="summary")


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

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
