"""
Meeting Management API Endpoints
Handles meeting data and transcripts
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.vexa_client import VexaClient
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
        meetings = vexa_client.list_meetings()
        
        return {
            "success": True,
            "count": len(meetings) if isinstance(meetings, list) else 0,
            "meetings": meetings
        }
        
    except Exception as e:
        logger.error(f"Failed to list meetings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/{meeting_id}/transcript")
async def get_transcript(platform: str, meeting_id: str):
    """
    Get real-time transcript for a meeting
    Can be called during or after the meeting
    """
    try:
        transcript = vexa_client.get_transcript(platform, meeting_id)
        
        return {
            "success": True,
            "platform": platform,
            "meeting_id": meeting_id,
            "transcript": transcript
        }
        
    except Exception as e:
        logger.error(f"Failed to get transcript: {str(e)}")
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
        result = vexa_client.update_meeting_data(
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
        result = vexa_client.delete_meeting_transcripts(platform, meeting_id)
        
        return {
            "success": True,
            "message": "Meeting transcripts deleted and data anonymized",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to delete meeting transcripts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
