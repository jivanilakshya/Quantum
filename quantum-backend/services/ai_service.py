"""
AI Service for meeting intelligence processing
Uses Google Gemini for summarization and extraction
"""

import google.generativeai as genai
from config import settings
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel('gemini-pro')


class AIService:
    """AI service for processing meeting transcripts"""
    
    @staticmethod
    def generate_summary(transcript_text: str) -> Dict[str, Any]:
        """
        Generate meeting summary from transcript
        
        Args:
            transcript_text: Full meeting transcript
            
        Returns:
            Dict with summary, key_points, and decisions
        """
        try:
            prompt = f"""
Analyze this meeting transcript and provide:
1. A concise summary (2-3 sentences)
2. Key discussion points (as a bullet list)
3. Important decisions made (as a bullet list)

Format your response as JSON:
{{
    "summary": "Brief summary here",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "decisions": ["Decision 1", "Decision 2"]
}}

Transcript:
{transcript_text}

Respond ONLY with valid JSON, no additional text.
"""
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result = json.loads(result_text.strip())
            logger.info("Summary generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            return {
                "summary": "Failed to generate summary",
                "key_points": [],
                "decisions": []
            }
    
    @staticmethod
    def extract_action_items(transcript_text: str) -> List[Dict[str, str]]:
        """
        Extract action items from transcript
        
        Args:
            transcript_text: Full meeting transcript
            
        Returns:
            List of action items with task, owner, due_date, priority
        """
        try:
            prompt = f"""
Extract action items from this meeting transcript.
For each action item, identify:
- task: What needs to be done
- owner: Who is responsible (extract from transcript)
- due_date: When it's due (extract or estimate as YYYY-MM-DD)
- priority: high, medium, or low

Format as JSON array:
[
    {{
        "task": "Complete Jira integration API design",
        "owner": "Alex Kumar",
        "due_date": "2026-01-12",
        "priority": "high"
    }}
]

Transcript:
{transcript_text}

Respond ONLY with valid JSON array, no additional text.
If no action items found, return empty array [].
"""
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result = json.loads(result_text.strip())
            logger.info(f"Extracted {len(result)} action items")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract action items: {str(e)}")
            return []
    
    @staticmethod
    def detect_participants(transcript_segments: List[Dict[str, str]]) -> List[str]:
        """
        Detect unique participants from transcript
        
        Args:
            transcript_segments: List of transcript segments with speaker field
            
        Returns:
            List of unique participant names
        """
        try:
            participants = set()
            for segment in transcript_segments:
                if 'speaker' in segment and segment['speaker']:
                    participants.add(segment['speaker'])
            
            result = list(participants)
            logger.info(f"Detected {len(result)} participants")
            return result
            
        except Exception as e:
            logger.error(f"Failed to detect participants: {str(e)}")
            return []
    
    @staticmethod
    def analyze_emotions(transcript_text: str) -> List[Dict[str, Any]]:
        """
        Analyze emotions from transcript
        
        Args:
            transcript_text: Full meeting transcript
            
        Returns:
            List of emotion data points
        """
        try:
            prompt = f"""
Analyze the emotional tone of this meeting transcript.
For key moments, identify:
- timestamp: Time in format "MM:SS"
- emotion: happy, neutral, concerned, or frustrated
- intensity: 0.0 to 1.0

Format as JSON array (max 5 key moments):
[
    {{
        "timestamp": "00:00",
        "emotion": "neutral",
        "intensity": 0.5
    }}
]

Transcript:
{transcript_text}

Respond ONLY with valid JSON array, no additional text.
"""
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result = json.loads(result_text.strip())
            logger.info(f"Analyzed {len(result)} emotion points")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze emotions: {str(e)}")
            return []
    
    @staticmethod
    def calculate_overall_emotion_score(emotions: List[Dict[str, Any]]) -> float:
        """
        Calculate overall emotion score from emotion data
        
        Args:
            emotions: List of emotion data points
            
        Returns:
            Overall score from 0.0 to 10.0
        """
        if not emotions:
            return 7.0  # Default neutral-positive score
        
        # Map emotions to scores
        emotion_scores = {
            "happy": 9.0,
            "neutral": 7.0,
            "concerned": 5.0,
            "frustrated": 3.0
        }
        
        total_score = 0
        total_weight = 0
        
        for emotion in emotions:
            base_score = emotion_scores.get(emotion.get("emotion", "neutral"), 7.0)
            intensity = emotion.get("intensity", 0.5)
            weight = intensity
            
            total_score += base_score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 7.0
        
        return round(total_score / total_weight, 1)
