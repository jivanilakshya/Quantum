"""
Bot Management API Endpoints
Handles Vexa AI bot operations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from services.vexa_client import VexaClient, BotRequest
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Vexa client
vexa_client = VexaClient(api_key=settings.vexa_api_key, base_url=settings.vexa_base_url)


class StartBotRequest(BaseModel):
    """Request to start a bot"""
    platform: str  # "google_meet" or "teams"
    meeting_url: str  # Full meeting URL
    language: Optional[str] = "en"
    bot_name: Optional[str] = "Quantum AI Bot"


class StopBotRequest(BaseModel):
    """Request to stop a bot"""
    platform: str
    native_meeting_id: str


class UpdateBotLanguageRequest(BaseModel):
    """Request to update bot language"""
    language: str


def extract_meeting_id(platform: str, meeting_url: str) -> tuple[str, Optional[str]]:
    """
    Extract meeting ID and passcode from URL
    
    Args:
        platform: Meeting platform
        meeting_url: Full meeting URL
        
    Returns:
        Tuple of (meeting_id, passcode)
    """
    if platform == "google_meet":
        # Extract from https://meet.google.com/abc-defg-hij
        meeting_id = meeting_url.split("/")[-1].split("?")[0]
        return meeting_id, None
    
    elif platform == "teams":
        # Extract from https://teams.live.com/meet/9366473044740?p=xxx
        parts = meeting_url.split("/")[-1].split("?")
        meeting_id = parts[0]
        passcode = None
        
        if len(parts) > 1:
            # Extract passcode from query params
            params = parts[1].split("&")
            for param in params:
                if param.startswith("p="):
                    passcode = param.split("=")[1]
                    break
        
        return meeting_id, passcode
    
    else:
        raise ValueError(f"Unsupported platform: {platform}")


@router.post("/start")
async def start_bot(request: StartBotRequest):
    """
    Start a bot for a meeting
    
    This endpoint:
    1. Extracts meeting ID from URL
    2. Requests Vexa bot to join the meeting
    3. Returns bot and meeting details
    """
    try:
        # Extract meeting ID and passcode
        meeting_id, passcode = extract_meeting_id(request.platform, request.meeting_url)
        
        # Create bot request
        bot_request = BotRequest(
            platform=request.platform,
            native_meeting_id=meeting_id,
            passcode=passcode,
            language=request.language,
            bot_name=request.bot_name
        )
        
        # Request bot from Vexa
        result = vexa_client.request_bot(bot_request)
        
        logger.info(f"Bot started for meeting {meeting_id}")
        
        return {
            "success": True,
            "message": "Bot requested successfully. It will join the meeting in ~10 seconds.",
            "meeting_id": meeting_id,
            "platform": request.platform,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_bot(request: StopBotRequest):
    """
    Stop a bot and remove it from the meeting
    IMPORTANT: This frees up API credits
    """
    try:
        result = vexa_client.stop_bot(request.platform, request.native_meeting_id)
        
        logger.info(f"Bot stopped for meeting {request.native_meeting_id}")
        
        return {
            "success": True,
            "message": "Bot stopped successfully. API credits freed.",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to stop bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_bot_status():
    """
    Get status of all running bots
    """
    try:
        bots = vexa_client.get_bot_status()
        
        return {
            "success": True,
            "active_bots": len(bots) if isinstance(bots, list) else 0,
            "bots": bots
        }
        
    except Exception as e:
        logger.error(f"Failed to get bot status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{platform}/{meeting_id}/language")
async def update_bot_language(
    platform: str,
    meeting_id: str,
    request: UpdateBotLanguageRequest
):
    """
    Update bot language during a meeting
    """
    try:
        result = vexa_client.update_bot_config(
            platform=platform,
            native_meeting_id=meeting_id,
            language=request.language
        )
        
        return {
            "success": True,
            "message": f"Bot language updated to {request.language}",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to update bot language: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
