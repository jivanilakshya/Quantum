"""
Vexa AI Client for Meeting Bot Management and Transcription
Handles all interactions with the Vexa AI API
"""

import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class BotRequest(BaseModel):
    """Request model for creating a bot"""
    platform: str  # "google_meet" or "teams"
    native_meeting_id: str
    passcode: Optional[str] = None  # Required for Teams
    language: Optional[str] = "en"
    bot_name: Optional[str] = "Quantum AI Bot"


class VexaClient:
    """Client for interacting with Vexa AI API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.cloud.vexa.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    async def request_bot(self, bot_request: BotRequest) -> Dict[str, Any]:
        """
        Request a bot to join a meeting
        """
        url = f"{self.base_url}/bots"
        payload = bot_request.model_dump(exclude_none=True)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                logger.info(f"Bot requested successfully for meeting {bot_request.native_meeting_id}")
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 409:
                    logger.warning(f"Bot already exists for meeting {bot_request.native_meeting_id}")
                    return {"message": "Bot already exists for this meeting", "already_running": True}
                
                logger.error(f"HTTP error requesting bot: {str(e)} - Response: {e.response.text}")
                raise Exception(f"Failed to request bot: {str(e)}")
            except httpx.RequestError as e:
                logger.error(f"Request error requesting bot: {str(e)}")
                raise Exception(f"Failed to request bot: {str(e)}")
    
    async def get_transcript(self, platform: str, native_meeting_id: str) -> Dict[str, Any]:
        """
        Get real-time transcript for a meeting
        """
        url = f"{self.base_url}/transcripts/{platform}/{native_meeting_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                # Validation: Ensure transcript field exists
                if not data or 'transcript' not in data:
                    logger.warning(f"Vexa returned empty or invalid transcript for {native_meeting_id}")
                    return {"transcript": [], "message": "No transcript available yet"}
                    
                return data
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting transcript: {str(e)} - Response: {e.response.text}")
                if e.response.status_code == 404:
                    return {"transcript": [], "message": "Transcript not found"}
                raise Exception(f"Failed to get transcript: {str(e)}")
            except httpx.RequestError as e:
                logger.error(f"Request error getting transcript: {str(e)}")
                raise Exception(f"Failed to get transcript: {str(e)}")
    
    async def get_bot_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all running bots
        """
        url = f"{self.base_url}/bots/status"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to get bot status: {str(e)}")
                raise Exception(f"Failed to get bot status: {str(e)}")
    
    async def update_bot_config(
        self, 
        platform: str, 
        native_meeting_id: str, 
        language: str
    ) -> Dict[str, Any]:
        """
        Update bot configuration (e.g., change language)
        """
        url = f"{self.base_url}/bots/{platform}/{native_meeting_id}/config"
        payload = {"language": language}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.put(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to update bot config: {str(e)}")
                raise Exception(f"Failed to update bot config: {str(e)}")
    
    async def stop_bot(self, platform: str, native_meeting_id: str) -> Dict[str, Any]:
        """
        Stop a bot and remove it from the meeting
        """
        url = f"{self.base_url}/bots/{platform}/{native_meeting_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.delete(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to stop bot: {str(e)}")
                raise Exception(f"Failed to stop bot: {str(e)}")
    
    async def list_meetings(self) -> List[Dict[str, Any]]:
        """
        List all meetings associated with the API key
        """
        url = f"{self.base_url}/meetings"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to list meetings: {str(e)}")
                raise Exception(f"Failed to list meetings: {str(e)}")
    
    async def update_meeting_data(
        self,
        platform: str,
        native_meeting_id: str,
        name: Optional[str] = None,
        participants: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update meeting metadata
        """
        url = f"{self.base_url}/meetings/{platform}/{native_meeting_id}"
        data = {}
        
        if name: data["name"] = name
        if participants: data["participants"] = participants
        if languages: data["languages"] = languages
        if notes: data["notes"] = notes
        
        payload = {"data": data}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.patch(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to update meeting data: {str(e)}")
                raise Exception(f"Failed to update meeting data: {str(e)}")
    
    async def delete_meeting_transcripts(
        self, 
        platform: str, 
        native_meeting_id: str
    ) -> Dict[str, Any]:
        """
        Delete meeting transcripts and anonymize data
        """
        url = f"{self.base_url}/meetings/{platform}/{native_meeting_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.delete(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to delete meeting transcripts: {str(e)}")
                raise Exception(f"Failed to delete meeting transcripts: {str(e)}")

