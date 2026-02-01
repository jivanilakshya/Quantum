"""
Meeting Processing API Endpoints
Handles AI processing and data retrieval
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from services.vexa_client import VexaClient
from services.ai_service import AIService
from database import get_db, Meeting, Transcript, Summary, ActionItem, Participant, Emotion, init_db
from config import settings
import logging
import json
import os
import tempfile
from datetime import datetime
import sys
import threading
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Vexa client and AI service
vexa_client = VexaClient(api_key=settings.vexa_api_key, base_url=settings.vexa_base_url)
ai_service = AIService()

# Initialize database on startup
init_db()

# Store active emotion analyzers for real-time processing
active_emotion_analyzers: Dict[str, Any] = {}
emotion_analysis_lock = threading.Lock()
init_db()


class ProcessMeetingRequest(BaseModel):
    """Request to process a meeting"""
    title: Optional[str] = None


@router.post("/{platform}/{meeting_id}/process")
async def process_meeting(
    platform: str,
    meeting_id: str,
    request: ProcessMeetingRequest,
    db: Session = Depends(get_db)
):
    """
    Process a meeting with AI
    Fetches transcript, generates summary, extracts action items, etc.
    """
    try:
        logger.info(f"Processing meeting {meeting_id}")
        
        # 1. Fetch transcript from Vexa
        transcript_result = vexa_client.get_transcript(platform, meeting_id)
        
        if not transcript_result or 'transcript' not in transcript_result:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Parse transcript
        transcript_data = transcript_result['transcript']
        if isinstance(transcript_data, str):
            transcript_segments = [{"text": transcript_data}]
            transcript_text = transcript_data
        elif isinstance(transcript_data, list):
            transcript_segments = transcript_data
            transcript_text = "\n".join([
                f"{seg.get('speaker', 'Unknown')}: {seg.get('text', '')}"
                for seg in transcript_segments
            ])
        else:
            transcript_segments = []
            transcript_text = ""
        
        if not transcript_text:
            raise HTTPException(status_code=400, detail="Empty transcript")
        
        # 2. Create or update meeting record
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if not meeting:
            meeting = Meeting(
                platform=platform,
                meeting_id=meeting_id,
                title=request.title or f"Meeting {meeting_id}",
                status="processing"
            )
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
        else:
            meeting.status = "processing"
            db.commit()
        
        # 3. Save transcript segments
        # Clear existing transcripts
        db.query(Transcript).filter(Transcript.meeting_id == meeting_id).delete()
        
        for segment in transcript_segments:
            transcript_record = Transcript(
                meeting_id=meeting_id,
                speaker=segment.get('speaker'),
                timestamp=segment.get('timestamp'),
                text=segment.get('text', '')
            )
            db.add(transcript_record)
        db.commit()
        
        # 4. Generate AI summary
        summary_data = ai_service.generate_summary(transcript_text)
        
        # Save or update summary
        summary_record = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
        if summary_record:
            summary_record.summary = summary_data.get('summary', '')
            summary_record.key_points = json.dumps(summary_data.get('key_points', []))
            summary_record.decisions = json.dumps(summary_data.get('decisions', []))
        else:
            summary_record = Summary(
                meeting_id=meeting_id,
                summary=summary_data.get('summary', ''),
                key_points=json.dumps(summary_data.get('key_points', [])),
                decisions=json.dumps(summary_data.get('decisions', []))
            )
            db.add(summary_record)
        db.commit()
        
        # 5. Extract action items
        action_items_data = ai_service.extract_action_items(transcript_text)
        
        # Clear existing action items
        db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).delete()
        
        for item in action_items_data:
            action_item = ActionItem(
                meeting_id=meeting_id,
                task=item.get('task', ''),
                owner=item.get('owner', ''),
                due_date=item.get('due_date', ''),
                priority=item.get('priority', 'medium'),
                status='todo'
            )
            db.add(action_item)
        db.commit()
        
        # 6. Detect participants
        participants_list = ai_service.detect_participants(transcript_segments)
        
        # Clear existing participants
        db.query(Participant).filter(Participant.meeting_id == meeting_id).delete()
        
        for name in participants_list:
            participant = Participant(
                meeting_id=meeting_id,
                name=name
            )
            db.add(participant)
        db.commit()
        
        # 7. Analyze emotions
        emotions_data = ai_service.analyze_emotions(transcript_text)
        
        # Clear existing emotions
        db.query(Emotion).filter(Emotion.meeting_id == meeting_id).delete()
        
        for emotion in emotions_data:
            emotion_record = Emotion(
                meeting_id=meeting_id,
                timestamp=emotion.get('timestamp', ''),
                emotion=emotion.get('emotion', 'neutral'),
                intensity=emotion.get('intensity', 0.5)
            )
            db.add(emotion_record)
        db.commit()
        
        # 8. Calculate overall emotion score
        overall_score = ai_service.calculate_overall_emotion_score(emotions_data)
        
        # 9. Update meeting status
        meeting.status = "completed"
        db.commit()
        
        logger.info(f"Meeting {meeting_id} processed successfully")
        
        return {
            "success": True,
            "message": "Meeting processed successfully",
            "data": {
                "meeting_id": meeting_id,
                "summary": summary_data.get('summary'),
                "action_items_count": len(action_items_data),
                "participants_count": len(participants_list),
                "overall_emotion_score": overall_score
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to process meeting: {str(e)}")
        # Update meeting status to failed
        if 'meeting' in locals():
            meeting.status = "failed"
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/{meeting_id}/summary")
async def get_meeting_summary(
    platform: str,
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get AI-generated summary for a meeting"""
    try:
        summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
        
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found. Process the meeting first.")
        
        return {
            "success": True,
            "summary": summary.summary,
            "key_points": json.loads(summary.key_points) if summary.key_points else [],
            "decisions": json.loads(summary.decisions) if summary.decisions else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/{meeting_id}/action-items")
async def get_action_items(
    platform: str,
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get extracted action items for a meeting"""
    try:
        action_items = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
        
        return {
            "success": True,
            "action_items": [
                {
                    "id": item.id,
                    "task": item.task,
                    "owner": item.owner,
                    "due_date": item.due_date,
                    "priority": item.priority,
                    "status": item.status
                }
                for item in action_items
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get action items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/{meeting_id}/participants")
async def get_participants(
    platform: str,
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get participants for a meeting"""
    try:
        participants = db.query(Participant).filter(Participant.meeting_id == meeting_id).all()
        
        return {
            "success": True,
            "participants": [
                {
                    "id": p.id,
                    "name": p.name,
                    "email": p.email
                }
                for p in participants
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get participants: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/{meeting_id}/emotions")
async def get_emotions(
    platform: str,
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get emotion analysis for a meeting"""
    try:
        emotions = db.query(Emotion).filter(Emotion.meeting_id == meeting_id).all()
        
        emotion_data = [
            {
                "timestamp": e.timestamp,
                "emotion": e.emotion,
                "intensity": e.intensity
            }
            for e in emotions
        ]
        
        overall_score = ai_service.calculate_overall_emotion_score(emotion_data)
        
        # Calculate engagement score (same as overall_score, but named for clarity)
        engagement_score = overall_score
        
        return {
            "success": True,
            "overall_score": overall_score,
            "engagement_score": engagement_score,
            "timeline": emotion_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get emotions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/{meeting_id}/status")
async def get_meeting_status(
    platform: str,
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """Get processing status of a meeting"""
    try:
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        
        if not meeting:
            return {
                "success": True,
                "status": "not_processed",
                "message": "Meeting has not been processed yet"
            }
        
        return {
            "success": True,
            "status": meeting.status,
            "title": meeting.title,
            "date": meeting.date.isoformat() if meeting.date else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get meeting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-video-emotions")
async def analyze_video_emotions(
    file: UploadFile = File(...),
    meeting_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Analyze emotions from a video file using the emotion detection model.
    This endpoint processes video files and returns emotion analysis results.
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Check file size (limit to 500MB)
        file_size = 0
        content = b""
        async for chunk in file.stream():
            content += chunk
            file_size += len(chunk)
            if file_size > 500 * 1024 * 1024:  # 500MB limit
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 500MB.")
        
        logger.info(f"Processing video emotion analysis for file: {file.filename}, Size: {file_size / 1024 / 1024:.2f} MB")
        
        # Save uploaded file to temporary location
        video_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(content)
            video_path = tmp_file.name
        
        try:
            # Import emotion analyzer
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Sales_emotion_module'))
            from meeting_emotion_analyzer import analyze_meeting_video
            from config import MODEL_PATH, MODEL_TYPE_PROD
            
            # Analyze video
            logger.info("Starting video emotion analysis...")
            summary = analyze_meeting_video(
                video_path=video_path,
                output_path=None, 
                model_path=MODEL_PATH,
                model_type=MODEL_TYPE_PROD
            )
            
            # Filter out false positives (same as real-time analysis)
            meeting_duration = summary.get('meeting_duration', 0)
            if meeting_duration > 0:
                min_duration_seconds = max(meeting_duration * 0.05, 3.0)  # At least 5% of meeting or 3 seconds minimum
                filtered_people = []
                for person_data in summary.get('people', []):
                    person_duration = person_data.get('total_duration', 0)
                    total_frames = person_data.get('total_frames', 0)
                    if person_duration >= min_duration_seconds and total_frames >= 30:
                        filtered_people.append(person_data)
                    else:
                        logger.info(f"Filtered out person {person_data.get('person_id')} - duration: {person_duration:.1f}s, frames: {total_frames}")
                
                summary['people'] = filtered_people
                summary['total_people_active'] = len(filtered_people)
                
                # Renumber people to be sequential
                for idx, person_data in enumerate(filtered_people, 1):
                    person_data['person_id'] = idx
                    person_data['person_name'] = f"Person {idx}"
            
            # Convert summary to API response format
            emotion_timeline = []
            overall_emotion_distribution = summary.get('overall_emotion_distribution', {})
            
            # Create timeline from per-person data and speaking sessions
            # Sample emotions at regular intervals based on session data
            for person_data in summary.get('people', []):
                for session in person_data.get('speaking_sessions', []):
                    session_start = session.get('start_time', 0)
                    session_end = session.get('end_time', session_start)
                    session_duration = session.get('duration', 0)
                    dominant_emotion = session.get('dominant_emotion', 'neutral')
                    avg_confidence = session.get('average_confidence', 0.5)
                    
                    # Create timeline points for this session (sample every 5 seconds)
                    if session_duration > 0:
                        num_samples = max(1, int(session_duration / 5))
                        for i in range(num_samples):
                            timestamp_seconds = session_start + (i * session_duration / num_samples)
                            minutes = int(timestamp_seconds // 60)
                            seconds = int(timestamp_seconds % 60)
                            timestamp_str = f"{minutes:02d}:{seconds:02d}"
                            
                            emotion_timeline.append({
                                "timestamp": timestamp_str,
                                "emotion": dominant_emotion.lower() if dominant_emotion else 'neutral',
                                "intensity": avg_confidence
                            })
            
            # If no timeline created, create samples from overall distribution
            if not emotion_timeline and meeting_duration > 0:
                # Sample every 10 seconds
                num_samples = max(1, int(meeting_duration / 10))
                dominant_emotion = max(overall_emotion_distribution.items(), key=lambda x: x[1])[0] if overall_emotion_distribution else 'neutral'
                for i in range(num_samples):
                    timestamp_seconds = i * 10
                    minutes = int(timestamp_seconds // 60)
                    seconds = int(timestamp_seconds % 60)
                    timestamp_str = f"{minutes:02d}:{seconds:02d}"
                    
                    emotion_timeline.append({
                        "timestamp": timestamp_str,
                        "emotion": dominant_emotion.lower() if dominant_emotion else 'neutral',
                        "intensity": 0.7
                    })
            
            # Calculate overall engagement score
            # Map emotions to scores: happy=high, neutral=medium, others=low
            emotion_scores = {
                'happy': 0.9,
                'neutral': 0.6,
                'sad': 0.3,
                'angry': 0.2,
                'fear': 0.3,
                'surprise': 0.7,
                'disgust': 0.2
            }
            
            total_score = 0
            total_count = 0
            for emotion, count in overall_emotion_distribution.items():
                emotion_lower = emotion.lower()
                score = emotion_scores.get(emotion_lower, 0.5)
                total_score += score * count
                total_count += count
            
            engagement_score = (total_score / total_count * 10) if total_count > 0 else 5.0
            
            # Save emotions to database if meeting_id provided
            if meeting_id:
                # Clear existing emotions
                db.query(Emotion).filter(Emotion.meeting_id == meeting_id).delete()
                
                for emotion_point in emotion_timeline:
                    emotion_record = Emotion(
                        meeting_id=meeting_id,
                        timestamp=emotion_point['timestamp'],
                        emotion=emotion_point['emotion'],
                        intensity=emotion_point['intensity']
                    )
                    db.add(emotion_record)
                db.commit()
            
            # Prepare response
            response_data = {
                "success": True,
                "engagement_score": round(engagement_score, 1),
                "overall_score": round(engagement_score, 1),
                "timeline": emotion_timeline,
                "summary": {
                    "meeting_duration": summary.get('meeting_duration', 0),
                    "total_people_detected": summary.get('total_people_detected', 0),
                    "total_people_active": summary.get('total_people_active', 0),
                    "overall_emotion_distribution": overall_emotion_distribution,
                    "people": [
                        {
                            "person_id": p.get('person_id'),
                            "person_name": p.get('person_name', f"Person {p.get('person_id')}"),
                            "dominant_emotion": p.get('dominant_emotion'),
                            "emotion_percentages": p.get('emotion_percentages', {}),
                            "speaking_percentage": p.get('speaking_percentage', 0)
                        }
                        for p in summary.get('people', [])
                    ]
                }
            }
            
            logger.info(f"Video emotion analysis completed successfully")
            return response_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to analyze video emotions: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            error_detail = str(e)
            # Provide more helpful error messages
            if "No such file" in error_detail or "model" in error_detail.lower():
                error_detail = "Emotion detection model not found. Please ensure model.h5 exists in Sales_emotion_module directory."
            elif "cv2" in error_detail.lower() or "opencv" in error_detail.lower():
                error_detail = "OpenCV error. Please ensure OpenCV is properly installed."
            elif "ImportError" in error_detail or "ModuleNotFoundError" in error_detail:
                error_detail = f"Module import error: {error_detail}. Please check dependencies."
            raise HTTPException(status_code=500, detail=f"Video analysis failed: {error_detail}")
        finally:
            # Clean up temporary file
            if video_path and os.path.exists(video_path):
                os.unlink(video_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process video file: {str(e)}")
        error_detail = str(e)
        if "413" in error_detail or "too large" in error_detail.lower():
            error_detail = "File too large. Maximum size is 500MB."
        raise HTTPException(status_code=500, detail=f"Failed to process video file: {error_detail}")
    finally:
        # Ensure cleanup even if file creation fails
        if video_path and os.path.exists(video_path):
            try:
                os.unlink(video_path)
            except:
                pass


@router.post("/{platform}/{meeting_id}/start-emotion-analysis")
async def start_emotion_analysis(
    platform: str,
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    Start real-time emotion analysis for a meeting.
    This initializes the emotion analyzer and starts tracking emotions.
    """
    try:
        with emotion_analysis_lock:
            if meeting_id in active_emotion_analyzers:
                return {
                    "success": True,
                    "message": "Emotion analysis already running for this meeting",
                    "meeting_id": meeting_id
                }
            
            # Import emotion analyzer
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Sales_emotion_module'))
            from meeting_emotion_analyzer import MeetingEmotionAnalyzer
            from config import MODEL_PATH, MODEL_TYPE_PROD
            
            # Initialize analyzer with stricter settings to reduce false positives
            analyzer = MeetingEmotionAnalyzer(
                model_path=MODEL_PATH,
                model_type=MODEL_TYPE_PROD,
                max_people=5  # Limit to 5 people max
            )
            
            
            analyzer.cleanup_threshold = 1.
            analyzer.min_face_size = 40  
            analyzer.face_detection_params = {
                'scaleFactor': 1.2,
                'minNeighbors': 5, 
                'minSize': (40, 40)
            }
            
            # Store analyzer
            active_emotion_analyzers[meeting_id] = {
                'analyzer': analyzer,
                'start_time': time.time(),
                'platform': platform,
                'frames_processed': 0
            }
            
            # Create or update meeting record
            meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
            if not meeting:
                meeting = Meeting(
                    platform=platform,
                    meeting_id=meeting_id,
                    title=f"Meeting {meeting_id}",
                    status="active"
                )
                db.add(meeting)
            else:
                meeting.status = "active"
            db.commit()
            
            logger.info(f"Started emotion analysis for meeting {meeting_id}")
            
            return {
                "success": True,
                "message": "Emotion analysis started successfully",
                "meeting_id": meeting_id,
                "start_time": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to start emotion analysis: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to start emotion analysis: {str(e)}")


@router.post("/{platform}/{meeting_id}/process-emotion-frame")
async def process_emotion_frame(
    platform: str,
    meeting_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Process a single video frame for emotion analysis.
    This endpoint accepts image frames and processes them in real-time.
    """
    try:
        with emotion_analysis_lock:
            if meeting_id not in active_emotion_analyzers:
                raise HTTPException(
                    status_code=400,
                    detail="Emotion analysis not started for this meeting. Call start-emotion-analysis first."
                )
            
            analyzer_data = active_emotion_analyzers[meeting_id]
            analyzer = analyzer_data['analyzer']
            
            # Read frame data
            import cv2
            import numpy as np
            from PIL import Image
            import io
            
            content = await file.read()
            image = Image.open(io.BytesIO(content))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Process frame
            result = analyzer.process_frame(frame, detect_speakers=True)
            
            # Update frame count
            analyzer_data['frames_processed'] += 1
            
            # Save emotions to database periodically (every 10 frames or every 5 seconds)
            current_time = time.time()
            if not hasattr(analyzer_data, 'last_save_time'):
                analyzer_data['last_save_time'] = current_time
            
            if analyzer_data['frames_processed'] % 10 == 0 or (current_time - analyzer_data['last_save_time']) >= 5:
                # Save recent emotions to database
                for frame_result in result.get('frame_results', []):
                    timestamp_seconds = current_time - analyzer_data['start_time']
                    minutes = int(timestamp_seconds // 60)
                    seconds = int(timestamp_seconds % 60)
                    timestamp_str = f"{minutes:02d}:{seconds:02d}"
                    
                    emotion_record = Emotion(
                        meeting_id=meeting_id,
                        timestamp=timestamp_str,
                        emotion=frame_result.get('emotion', 'neutral').lower(),
                        intensity=frame_result.get('confidence', 0.5)
                    )
                    db.add(emotion_record)
                db.commit()
                analyzer_data['last_save_time'] = current_time
            
            return {
                "success": True,
                "frames_processed": result.get('faces_detected', 0),
                "people_tracked": result.get('people_tracked', 0),
                "frame_results": result.get('frame_results', [])
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process emotion frame: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to process frame: {str(e)}")


@router.post("/{platform}/{meeting_id}/stop-emotion-analysis")
async def stop_emotion_analysis(
    platform: str,
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    Stop emotion analysis and get the final meeting mood summary.
    """
    try:
        with emotion_analysis_lock:
            if meeting_id not in active_emotion_analyzers:
                raise HTTPException(
                    status_code=400,
                    detail="Emotion analysis not running for this meeting"
                )
            
            analyzer_data = active_emotion_analyzers[meeting_id]
            analyzer = analyzer_data['analyzer']
            
            # Get meeting summary with higher threshold to filter false positives
            # Require at least 30 frames (about 1-2 seconds at typical FPS) to be considered a real person
            summary = analyzer.get_meeting_summary(min_frames_for_summary=30)
            
            # Additional filtering: Only keep people who were seen for at least 5% of meeting duration
            # This is more aggressive to filter out false positives
            meeting_duration = summary.get('meeting_duration', 0)
            if meeting_duration > 0:
                min_duration_seconds = max(meeting_duration * 0.05, 3.0)  # At least 5% of meeting or 3 seconds minimum
                filtered_people = []
                for person_data in summary.get('people', []):
                    person_duration = person_data.get('total_duration', 0)
                    total_frames = person_data.get('total_frames', 0)
                    # Must meet both duration and frame count requirements
                    if person_duration >= min_duration_seconds and total_frames >= 30:
                        filtered_people.append(person_data)
                    else:
                        logger.info(f"Filtered out person {person_data.get('person_id')} - duration: {person_duration:.1f}s (min: {min_duration_seconds:.1f}s), frames: {total_frames} (min: 30)")
                
                summary['people'] = filtered_people
                summary['total_people_active'] = len(filtered_people)
                
                # Renumber people to be sequential (Person 1, Person 2, etc.)
                for idx, person_data in enumerate(filtered_people, 1):
                    old_id = person_data.get('person_id')
                    person_data['person_id'] = idx
                    person_data['person_name'] = f"Person {idx}"
                    logger.info(f"Renumbered person {old_id} to Person {idx}")
            
            # Calculate overall engagement score
            overall_emotion_distribution = summary.get('overall_emotion_distribution', {})
            emotion_scores = {
                'happy': 0.9,
                'neutral': 0.6,
                'sad': 0.3,
                'angry': 0.2,
                'fear': 0.3,
                'surprise': 0.7,
                'disgust': 0.2
            }
            
            total_score = 0
            total_count = 0
            for emotion, count in overall_emotion_distribution.items():
                emotion_lower = emotion.lower()
                score = emotion_scores.get(emotion_lower, 0.5)
                total_score += score * count
                total_count += count
            
            engagement_score = (total_score / total_count * 10) if total_count > 0 else 5.0
            
            # Create emotion timeline
            emotion_timeline = []
            meeting_duration = summary.get('meeting_duration', 0)
            
            for person_data in summary.get('people', []):
                for session in person_data.get('speaking_sessions', []):
                    session_start = session.get('start_time', 0)
                    session_duration = session.get('duration', 0)
                    dominant_emotion = session.get('dominant_emotion', 'neutral')
                    avg_confidence = session.get('average_confidence', 0.5)
                    
                    if session_duration > 0:
                        num_samples = max(1, int(session_duration / 5))
                        for i in range(num_samples):
                            timestamp_seconds = session_start + (i * session_duration / num_samples)
                            minutes = int(timestamp_seconds // 60)
                            seconds = int(timestamp_seconds % 60)
                            timestamp_str = f"{minutes:02d}:{seconds:02d}"
                            
                            emotion_timeline.append({
                                "timestamp": timestamp_str,
                                "emotion": dominant_emotion.lower() if dominant_emotion else 'neutral',
                                "intensity": avg_confidence
                            })
            
            # Save all emotions to database
            db.query(Emotion).filter(Emotion.meeting_id == meeting_id).delete()
            for emotion_point in emotion_timeline:
                emotion_record = Emotion(
                    meeting_id=meeting_id,
                    timestamp=emotion_point['timestamp'],
                    emotion=emotion_point['emotion'],
                    intensity=emotion_point['intensity']
                )
                db.add(emotion_record)
            
            # Update meeting status
            meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
            if meeting:
                meeting.status = "completed"
                if meeting_duration:
                    meeting.duration = int(meeting_duration / 60)  # Convert to minutes
            
            db.commit()
            
            # Remove analyzer from active list
            del active_emotion_analyzers[meeting_id]
            
            # Create formatted timeline with time ranges
            formatted_timeline = []
            for person_data in summary.get('people', []):
                person_name = person_data.get('person_name', f"Person {person_data.get('person_id')}")
                for session in person_data.get('speaking_sessions', []):
                    session_start = session.get('start_time', 0)
                    session_end = session.get('end_time', session_start)
                    session_duration = session.get('duration', 0)
                    dominant_emotion = session.get('dominant_emotion', 'neutral')
                    
                    if session_duration > 0:
                        # Create 10-second segments
                        segment_duration = 10.0
                        num_segments = max(1, int(session_duration / segment_duration))
                        
                        for i in range(num_segments):
                            segment_start = session_start + (i * segment_duration)
                            segment_end = min(session_start + ((i + 1) * segment_duration), session_end)
                            
                            def format_time(seconds: float) -> str:
                                minutes = int(seconds // 60)
                                secs = int(seconds % 60)
                                return f"{minutes:02d}:{secs:02d}"
                            
                            time_range = f"{format_time(segment_start)} to {format_time(segment_end)}"
                            formatted_timeline.append({
                                "time_range": time_range,
                                "person": person_name,
                                "emotion": dominant_emotion.capitalize() if dominant_emotion else 'Neutral',
                                "start_time": segment_start,
                                "end_time": segment_end
                            })
            
            # Sort by start time
            formatted_timeline.sort(key=lambda x: x['start_time'])
            
            # Prepare response
            response_data = {
                "success": True,
                "message": "Emotion analysis completed",
                "engagement_score": round(engagement_score, 1),
                "overall_score": round(engagement_score, 1),
                "timeline": emotion_timeline,
                "formatted_timeline": formatted_timeline,  # New formatted timeline
                "summary": {
                    "meeting_duration": meeting_duration,
                    "total_people_detected": summary.get('total_people_detected', 0),
                    "total_people_active": summary.get('total_people_active', 0),
                    "overall_emotion_distribution": overall_emotion_distribution,
                    "frames_processed": analyzer_data['frames_processed'],
                    "people": [
                        {
                            "person_id": p.get('person_id'),
                            "person_name": p.get('person_name', f"Person {p.get('person_id')}"),
                            "dominant_emotion": p.get('dominant_emotion'),
                            "emotion_percentages": p.get('emotion_percentages', {}),
                            "speaking_percentage": p.get('speaking_percentage', 0)
                        }
                        for p in summary.get('people', [])
                    ]
                }
            }
            
            logger.info(f"Stopped emotion analysis for meeting {meeting_id}")
            return response_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop emotion analysis: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to stop emotion analysis: {str(e)}")


@router.get("/{platform}/{meeting_id}/emotion-analysis-status")
async def get_emotion_analysis_status(
    platform: str,
    meeting_id: str
):
    """
    Get the current status of emotion analysis for a meeting.
    """
    try:
        with emotion_analysis_lock:
            if meeting_id not in active_emotion_analyzers:
                return {
                    "success": True,
                    "is_running": False,
                    "message": "Emotion analysis not running"
                }
            
            analyzer_data = active_emotion_analyzers[meeting_id]
            elapsed_time = time.time() - analyzer_data['start_time']
            
            return {
                "success": True,
                "is_running": True,
                "start_time": datetime.fromtimestamp(analyzer_data['start_time']).isoformat(),
                "elapsed_time_seconds": round(elapsed_time, 2),
                "frames_processed": analyzer_data['frames_processed']
            }
            
    except Exception as e:
        logger.error(f"Failed to get emotion analysis status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
