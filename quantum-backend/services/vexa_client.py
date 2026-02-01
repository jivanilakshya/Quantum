"""
Vexa AI Client for Meeting Bot Management and Transcription
Handles all interactions with the Vexa AI API
"""

import requests
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
    
    def request_bot(self, bot_request: BotRequest) -> Dict[str, Any]:
        """
        Request a bot to join a meeting
        
        Args:
            bot_request: BotRequest object with meeting details
            
        Returns:
            Dict with bot and meeting details
        """
        url = f"{self.base_url}/bots"
        payload = bot_request.model_dump(exclude_none=True)
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Bot requested successfully for meeting {bot_request.native_meeting_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to request bot: {str(e)}")
            raise Exception(f"Failed to request bot: {str(e)}")
    
    def get_transcript(self, platform: str, native_meeting_id: str) -> Dict[str, Any]:
        """
        Get real-time transcript for a meeting
        
        Args:
            platform: Meeting platform (google_meet or teams)
            native_meeting_id: Meeting identifier
            
        Returns:
            Dict with transcript data
        """
        url = f"{self.base_url}/transcripts/{platform}/{native_meeting_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get transcript: {str(e)}")
            raise Exception(f"Failed to get transcript: {str(e)}")
    
    def get_bot_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all running bots
        
        Returns:
            List of active bots
        """
        url = f"{self.base_url}/bots/status"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get bot status: {str(e)}")
            raise Exception(f"Failed to get bot status: {str(e)}")
    
    def update_bot_config(
        self, 
        platform: str, 
        native_meeting_id: str, 
        language: str
    ) -> Dict[str, Any]:
        """
        Update bot configuration (e.g., change language)
        
        Args:
            platform: Meeting platform
            native_meeting_id: Meeting identifier
            language: New language code
            
        Returns:
            Dict with update confirmation
        """
        url = f"{self.base_url}/bots/{platform}/{native_meeting_id}/config"
        payload = {"language": language}
        
        try:
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Bot config updated for meeting {native_meeting_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update bot config: {str(e)}")
            raise Exception(f"Failed to update bot config: {str(e)}")
    
    def stop_bot(self, platform: str, native_meeting_id: str) -> Dict[str, Any]:
        """
        Stop a bot and remove it from the meeting
        IMPORTANT: Call this to free up API credits
        
        Args:
            platform: Meeting platform
            native_meeting_id: Meeting identifier
            
        Returns:
            Dict with bot removal confirmation
        """
        url = f"{self.base_url}/bots/{platform}/{native_meeting_id}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Bot stopped for meeting {native_meeting_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to stop bot: {str(e)}")
            raise Exception(f"Failed to stop bot: {str(e)}")
    
    def list_meetings(self) -> List[Dict[str, Any]]:
        """
        List all meetings associated with the API key
        
        Returns:
            List of meeting records
        """
        url = f"{self.base_url}/meetings"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list meetings: {str(e)}")
            raise Exception(f"Failed to list meetings: {str(e)}")
    
    def update_meeting_data(
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
        
        Args:
            platform: Meeting platform
            native_meeting_id: Meeting identifier
            name: Meeting name
            participants: List of participant names
            languages: List of language codes
            notes: Meeting notes
            
        Returns:
            Dict with updated meeting record
        """
        url = f"{self.base_url}/meetings/{platform}/{native_meeting_id}"
        data = {}
        
        if name:
            data["name"] = name
        if participants:
            data["participants"] = participants
        if languages:
            data["languages"] = languages
        if notes:
            data["notes"] = notes
        
        payload = {"data": data}
        
        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Meeting data updated for {native_meeting_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update meeting data: {str(e)}")
            raise Exception(f"Failed to update meeting data: {str(e)}")
    
    def delete_meeting_transcripts(
        self, 
        platform: str, 
        native_meeting_id: str
    ) -> Dict[str, Any]:
        """
        Delete meeting transcripts and anonymize data
        Only works for completed or failed meetings
        
        Args:
            platform: Meeting platform
            native_meeting_id: Meeting identifier
            
        Returns:
            Dict with confirmation message
        """
        url = f"{self.base_url}/meetings/{platform}/{native_meeting_id}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Meeting transcripts deleted for {native_meeting_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete meeting transcripts: {str(e)}")
            raise Exception(f"Failed to delete meeting transcripts: {str(e)}")
