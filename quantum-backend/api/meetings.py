"""
Meeting Management API Endpoints
Handles meeting data and transcripts
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from services.vexa_client import VexaClient
from database import get_db, Transcript
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Vexa client
vexa_client = VexaClient(api_key=settings.vexa_api_key, base_url=settings.vexa_base_url)


class UpdateMeetingRequest(BaseModel):
    """Request to update meeting metadata"""
    name: Optional[str] = None
    participants: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    notes: Optional[str] = None


@router.get("/")
async def list_meetings():
    """
    List all meetings
    """
    try:
        meetings = await vexa_client.list_meetings()
        
        return {
            "success": True,
            "count": len(meetings) if isinstance(meetings, list) else 0,
            "meetings": meetings
        }
        
    except Exception as e:
        logger.error(f"Failed to list meetings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/{meeting_id}/transcript")
async def get_transcript(
    platform: str, 
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    Get real-time transcript for a meeting
    Can be called during or after the meeting.
    Falls back to local database if Vexa returns empty or 404.
    """
    try:
        # 1. Try Vexa first for real-time data
        transcript_result = await vexa_client.get_transcript(platform, meeting_id)
        
        # Check if we got actual data from Vexa
        if transcript_result and 'transcript' in transcript_result and transcript_result['transcript']:
            return {
                "success": True,
                "platform": platform,
                "meeting_id": meeting_id,
                "source": "vexa",
                "transcript": transcript_result['transcript']
            }
        
        # 2. Fallback to local database for processed meetings
        logger.info(f"Vexa transcript empty for {meeting_id}, falling back to local DB")
        db_transcripts = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).all()
        
        if db_transcripts:
            formatted_transcript = [
                {
                    "speaker": t.speaker,
                    "timestamp": t.timestamp,
                    "text": t.text
                }
                for t in db_transcripts
            ]
            return {
                "success": True,
                "platform": platform,
                "meeting_id": meeting_id,
                "source": "database",
                "transcript": formatted_transcript
            }
            
        return {
            "success": True,
            "platform": platform,
            "meeting_id": meeting_id,
            "source": "none",
            "transcript": [],
            "message": "No transcript available in Vexa or local database"
        }
        
    except Exception as e:
        logger.error(f"Failed to get transcript: {str(e)}")
        # Even on Vexa error, try local DB as last resort
        try:
            db_transcripts = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).all()
            if db_transcripts:
                return {
                    "success": True,
                    "platform": platform,
                    "meeting_id": meeting_id,
                    "source": "database_recovery",
                    "transcript": [
                        {"speaker": t.speaker, "timestamp": t.timestamp, "text": t.text}
                        for t in db_transcripts
                    ]
                }
        except:
            pass
            
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{platform}/{meeting_id}")
async def update_meeting(
    platform: str,
    meeting_id: str,
    request: UpdateMeetingRequest
):
    """
    Update meeting metadata
    """
    try:
        result = await vexa_client.update_meeting_data(
            platform=platform,
            native_meeting_id=meeting_id,
            name=request.name,
            participants=request.participants,
            languages=request.languages,
            notes=request.notes
        )
        
        return {
            "success": True,
            "message": "Meeting updated successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to update meeting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{platform}/{meeting_id}")
async def delete_meeting_transcripts(platform: str, meeting_id: str):
    """
    Delete meeting transcripts and anonymize data
    Only works for completed or failed meetings
    """
    try:
        result = await vexa_client.delete_meeting_transcripts(platform, meeting_id)
        
        return {
            "success": True,
            "message": "Meeting transcripts deleted and data anonymized",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to delete meeting transcripts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
