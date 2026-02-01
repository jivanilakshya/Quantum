"""
Multi-Person Meeting Emotion Analyzer

This module provides functionality to detect and track emotions of multiple people
in a meeting, with support for speaker detection and per-person emotion summaries.
"""

import cv2
import numpy as np
import time
from collections import defaultdict, deque
from typing import List, Dict, Tuple, Optional
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.detect_emotions import SalesCallAnalyzer
from models.emotion_model import load_model, predict_emotion, KerasEmotionModel
from config import MODEL_PATH, MODEL_TYPE_PROD, CONFIDENCE_THRESHOLD


class SpeakingSession:
    """Tracks a single speaking session for a person."""
    
    def __init__(self, session_id: int, start_time: float):
        self.session_id = session_id
        self.start_time = start_time
        self.end_time = None
        self.emotions = []  # Store emotions during this session
        self.emotion_counts = defaultdict(int)
        self.total_duration = 0.0
        self.is_active = True
    
    def add_emotion(self, emotion: str, confidence: float, timestamp: float):
        """Add emotion to this speaking session."""
        self.emotions.append({
            'emotion': emotion,
            'confidence': confidence,
            'timestamp': timestamp
        })
        self.emotion_counts[emotion] += 1
    
    def end_session(self, end_time: float):
        """End the speaking session."""
        self.end_time = end_time
        self.total_duration = end_time - self.start_time
        self.is_active = False
    
    def get_session_summary(self) -> Optional[Dict]:
        """Get summary for this speaking session."""
        if not self.emotions:
            return None
        
        # Calculate dominant emotion
        dominant_emotion = max(self.emotion_counts.items(), key=lambda x: x[1])[0] if self.emotion_counts else None
        
        # Calculate emotion percentages
        total_emotions = len(self.emotions)
        emotion_percentages = {
            emotion: (count / total_emotions) * 100
            for emotion, count in self.emotion_counts.items()
        }
        
        # Calculate average confidence
        avg_confidence = np.mean([e['confidence'] for e in self.emotions]) if self.emotions else 0.0
        
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.total_duration,
            'dominant_emotion': dominant_emotion,
            'emotion_counts': dict(self.emotion_counts),
            'emotion_percentages': emotion_percentages,
            'average_confidence': avg_confidence,
            'total_emotions': total_emotions
        }


class PersonTracker:
    """Tracks a single person across frames with their emotion history and speaking sessions."""
    
    def __init__(self, person_id: int, initial_location: Tuple[int, int, int, int]):
        """
        Initialize person tracker.
        
        Args:
            person_id: Unique identifier for this person
            initial_location: Initial face location (x, y, w, h)
        """
        self.person_id = person_id
        self.location = initial_location
        self.emotion_history = deque(maxlen=100)  # Store last 100 emotions
        self.speaking_history = deque(maxlen=100)  # Track speaking status
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.total_frames = 0
        
        # Emotion metrics
        self.emotion_counts = defaultdict(int)
        self.emotion_durations = defaultdict(float)
        self.last_emotion = None
        self.last_emotion_time = None
        
        # Speaking session tracking
        self.speaking_sessions: List[SpeakingSession] = []
        self.current_session: Optional[SpeakingSession] = None
        self.next_session_id = 0
        self.was_speaking = False  # Track previous speaking state
        
        # Store last speaking state separately for tracking
        self._last_speaking_state = False
        
    def update_location(self, location: Tuple[int, int, int, int]):
        """Update person's face location."""
        self.location = location
        self.last_seen = time.time()
        
    def add_emotion(self, emotion: str, confidence: float, is_speaking: bool = False, only_when_speaking: bool = False):
        """
        Add emotion prediction for this person.
        
        Args:
            emotion: Detected emotion
            confidence: Confidence score
            is_speaking: Whether person is currently speaking
            only_when_speaking: If True, only store emotions when speaking
        """
        self.total_frames += 1
        self.last_seen = time.time()
        current_time = time.time()
        
        # Only analyze emotions when speaking if only_when_speaking is True
        if only_when_speaking and not is_speaking:
            # Still update location and last_seen, but don't store emotions
            return
        
        # Handle speaking session tracking
        if is_speaking and not self._last_speaking_state:
            # Started speaking - create new session
            self.current_session = SpeakingSession(self.next_session_id, current_time)
            self.next_session_id += 1
            self.speaking_sessions.append(self.current_session)
            # Get person name from tracker if available
            person_name = getattr(self, '_person_name', None)
            if person_name is None:
                person_name = f"Person {self.person_id}"
            print(f"\n🎤 {person_name} started speaking (Session {self.current_session.session_id})")
        
        elif not is_speaking and self._last_speaking_state and self.current_session:
            # Stopped speaking - end current session
            self.current_session.end_session(current_time)
            session_summary = self.current_session.get_session_summary()
            if session_summary:
                print(f"\n{'='*70}")
                # Get person name from tracker if available
                person_name = getattr(self, '_person_name', None)
                if person_name is None:
                    person_name = f"Person {self.person_id}"
                print(f"✅ {person_name} finished speaking - Session {self.current_session.session_id}")
                print(f"{'='*70}")
                print(f"Duration: {session_summary['duration']:.2f} seconds")
                print(f"Dominant emotion: {session_summary['dominant_emotion']}")
                print(f"Emotion distribution:")
                for emo, pct in sorted(session_summary['emotion_percentages'].items(), 
                                      key=lambda x: x[1], reverse=True):
                    print(f"  {emo}: {pct:.1f}%")
                print(f"Average confidence: {session_summary['average_confidence']:.2f}")
                print(f"{'='*70}\n")
            self.current_session = None
        
        # Store emotion in current session if speaking
        if is_speaking and self.current_session:
            self.current_session.add_emotion(emotion, confidence, current_time)
        
        # Store emotion in general history
        self.emotion_history.append({
            'emotion': emotion,
            'confidence': confidence,
            'timestamp': current_time,
            'is_speaking': is_speaking
        })
        self.speaking_history.append(is_speaking)
        
        # Update metrics (only count speaking emotions if only_when_speaking)
        if not only_when_speaking or is_speaking:
            if self.last_emotion and self.last_emotion_time:
                # Add duration to previous emotion
                duration = current_time - self.last_emotion_time
                self.emotion_durations[self.last_emotion] += duration
            
            self.last_emotion = emotion
            self.last_emotion_time = current_time
            self.emotion_counts[emotion] += 1
        
        self._last_speaking_state = is_speaking
        self.was_speaking = is_speaking
    
    def get_metrics(self) -> Dict:
        """Get summary metrics for this person."""
        total_duration = sum(self.emotion_durations.values())
        
        # Calculate percentages
        emotion_percentages = {}
        if total_duration > 0:
            for emotion, duration in self.emotion_durations.items():
                emotion_percentages[emotion] = (duration / total_duration) * 100
        
        # Speaking percentage
        if len(self.speaking_history) > 0:
            speaking_count = sum(self.speaking_history)
            speaking_percentage = (speaking_count / len(self.speaking_history)) * 100
        else:
            speaking_percentage = 0.0
        
        # Dominant emotion
        dominant_emotion = max(self.emotion_counts.items(), key=lambda x: x[1])[0] if self.emotion_counts else None
        
        # End current session if still active
        if self.current_session and self.current_session.is_active:
            self.current_session.end_session(time.time())
        
        # Get all completed session summaries
        session_summaries = []
        for session in self.speaking_sessions:
            if session.end_time:  # Only completed sessions
                summary = session.get_session_summary()
                if summary:
                    session_summaries.append(summary)
        
        return {
            'person_id': self.person_id,
            'total_frames': self.total_frames,
            'total_duration': total_duration,
            'dominant_emotion': dominant_emotion,
            'emotion_counts': dict(self.emotion_counts),
            'emotion_percentages': emotion_percentages,
            'speaking_percentage': speaking_percentage,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'total_speaking_sessions': len(self.speaking_sessions),
            'speaking_sessions': session_summaries  # Per-session summaries
        }


class MeetingEmotionAnalyzer:
    """
    Analyzes emotions of multiple people in a meeting.
    
    Features:
    - Multi-person face tracking
    - Per-person emotion detection
    - Speaker detection (visual or optional audio)
    - Real-time and batch processing
    - Meeting summaries and reports
    """
    
    def __init__(self, model_path=None, model_type='keras', max_people=10, only_when_speaking=False):
        """
        Initialize meeting analyzer.
        
        Args:
            model_path: Path to emotion model (defaults to config)
            model_type: Model type ('keras', 'modern', etc.)
            max_people: Maximum number of people to track
            only_when_speaking: If True, only analyze emotions when person is speaking
        """
        if model_path is None:
            model_path = MODEL_PATH
        
        # Initialize emotion model
        self.model_path = model_path
        self.model_type = model_type
        self.model, self.metadata = load_model(model_path, model_type)
        
        # Set device for PyTorch models
        if not isinstance(self.model, KerasEmotionModel):
            import torch
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
        else:
            self.device = None
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Person tracking
        self.person_trackers: Dict[int, PersonTracker] = {}
        self.next_person_id = 0
        self.max_people = max_people
        
        # Person name mapping (person_id -> name)
        self.person_names: Dict[int, str] = {}
        
        # Meeting metrics
        self.meeting_start_time = time.time()
        self.frame_count = 0
        self.analysis_interval = 0.5  # Analyze every 0.5 seconds
        self.last_analysis_time = 0
        
        # Speaker detection (can be enhanced with audio)
        self.current_speakers = set()  # Set of person IDs currently speaking
        
        # Emotion labels
        if isinstance(self.model, KerasEmotionModel):
            self.emotion_labels = self.model.emotion_labels
        else:
            self.emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        
        # Tracking stability settings
        self.min_face_size = 30  # Minimum face size (reduced for Google Meet small faces)
        self.cleanup_threshold = 3.0  # Remove person if not seen for this many seconds
        self.debug_mode = False  # Set to True for verbose debugging
        self.only_analyze_when_speaking = only_when_speaking  # Only analyze emotions when person is speaking
        
        # Face detection parameters (adjustable)
        self.face_detection_params = {
            'scaleFactor': 1.1,
            'minNeighbors': 3,
            'minSize': (30, 30)
        }
        
        print(f"Initialized MeetingEmotionAnalyzer")
        print(f"  Model: {model_path}")
        print(f"  Model type: {model_type}")
        print(f"  Max people: {max_people}")
        print(f"  Min face size: {self.min_face_size}x{self.min_face_size}")
        print(f"  Cleanup threshold: {self.cleanup_threshold}s")
        print(f"  Only analyze when speaking: {self.only_analyze_when_speaking}")
    
    def detect_faces(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], np.ndarray]:
        """Detect all faces in frame with filtering to reduce false positives."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Use configurable parameters (defaults are lenient for Google Meet)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.face_detection_params['scaleFactor'],
            minNeighbors=self.face_detection_params['minNeighbors'],
            minSize=self.face_detection_params['minSize'],
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Filter faces: remove very small or very large ones (likely false positives)
        # But be more lenient for Google Meet videos
        h, w = frame.shape[:2]
        filtered_faces = []
        
        if self.debug_mode:
            print(f"Raw face detections: {len(faces)}")
        
        for (x, y, face_w, face_h) in faces:
            # Check face size relative to frame
            face_area = face_w * face_h
            frame_area = w * h
            face_ratio = face_area / frame_area if frame_area > 0 else 0
            
            # Filter criteria (more lenient for video calls):
            # 1. Face should be at least 0.1% of frame (reduced from 0.5% for small faces)
            #    but not more than 50%
            # 2. Face should have reasonable aspect ratio (width/height between 0.4 and 2.5)
            #    (more lenient than 0.5-2.0)
            aspect_ratio = face_w / face_h if face_h > 0 else 0
            
            if 0.001 <= face_ratio <= 0.5 and 0.4 <= aspect_ratio <= 2.5:
                # Check for overlapping faces (remove if IoU > 0.6, more lenient than 0.5)
                is_duplicate = False
                for (fx, fy, fw, fh) in filtered_faces:
                    iou = self._calculate_iou((x, y, face_w, face_h), (fx, fy, fw, fh))
                    if iou > 0.6:  # More lenient - allow some overlap
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    filtered_faces.append((x, y, face_w, face_h))
                    if self.debug_mode:
                        print(f"  Accepted face: {x},{y},{face_w}x{face_h} "
                              f"(ratio={face_ratio:.3f}, aspect={aspect_ratio:.2f})")
            else:
                if self.debug_mode:
                    print(f"  Rejected face: {x},{y},{face_w}x{face_h} "
                          f"(ratio={face_ratio:.3f}, aspect={aspect_ratio:.2f})")
        
        if self.debug_mode:
            print(f"Filtered face detections: {len(filtered_faces)}")
        
        return filtered_faces, gray
    
    def _calculate_iou(self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union between two bounding boxes."""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[0] + box1[2], box2[0] + box2[2])
        y2 = min(box1[1] + box1[3], box2[1] + box2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        box1_area = box1[2] * box1[3]
        box2_area = box2[2] * box2[3]
        union = box1_area + box2_area - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def match_faces_to_people(self, faces: List[Tuple[int, int, int, int]]) -> Dict[int, Tuple[int, int, int, int]]:
        """
        Match detected faces to tracked people based on location and size similarity.
        Uses IoU (Intersection over Union) and distance for better matching.
        
        Returns:
            Dictionary mapping person_id to face location
        """
        matches = {}
        unmatched_faces = list(faces)
        current_time = time.time()
        
        # First, try to match existing people to faces using IoU and distance
        # Sort people by last seen (most recently seen first)
        sorted_trackers = sorted(
            self.person_trackers.items(),
            key=lambda x: x[1].last_seen,
            reverse=True
        )
        
        for person_id, tracker in sorted_trackers:
            if not unmatched_faces:
                break
            
            tx, ty, tw, th = tracker.location
            tracker_center = (tx + tw/2, ty + th/2)
            tracker_area = tw * th
            
            best_match = None
            best_score = -1
            
            for i, (x, y, w, h) in enumerate(unmatched_faces):
                face_center = (x + w/2, y + h/2)
                face_area = w * h
                
                # Calculate IoU
                iou = self._calculate_iou((tx, ty, tw, th), (x, y, w, h))
                
                # Calculate distance between centers
                distance = np.sqrt(
                    (tracker_center[0] - face_center[0])**2 + 
                    (tracker_center[1] - face_center[1])**2
                )
                
                # Calculate size similarity (ratio of areas)
                size_ratio = min(tracker_area, face_area) / max(tracker_area, face_area) if max(tracker_area, face_area) > 0 else 0
                
                # Combined score: IoU is most important, then distance, then size
                # IoU > 0.3 is a strong match, distance should be reasonable, size should be similar
                max_dimension = max(tw, th)
                max_distance = max_dimension * 2.0  # Allow faces to move up to 2x their size
                
                score = 0.0
                if iou > 0.1:  # At least some overlap
                    score = iou * 0.6  # IoU is 60% of score
                    if distance < max_distance:
                        distance_score = 1.0 - (distance / max_distance)
                        score += distance_score * 0.25  # Distance is 25% of score
                    if size_ratio > 0.5:  # Sizes should be similar
                        score += size_ratio * 0.15  # Size is 15% of score
                
                if score > best_score and score > 0.3:  # Minimum threshold for matching
                    best_score = score
                    best_match = i
            
            if best_match is not None:
                matches[person_id] = unmatched_faces.pop(best_match)
        
        # Remove people not seen for too long BEFORE creating new ones
        # This prevents accumulating too many person IDs
        to_remove = [
            pid for pid, tracker in self.person_trackers.items()
            if pid not in matches and (current_time - tracker.last_seen) > self.cleanup_threshold
        ]
        for pid in to_remove:
            if self.debug_mode:
                print(f"Removing person {pid} (not seen for {(current_time - self.person_trackers[pid].last_seen):.1f}s)")
            del self.person_trackers[pid]
        
        # Create new trackers ONLY for unmatched faces
        # Only create new person if face is stable (exists for multiple frames)
        for face in unmatched_faces:
            # Check if this face is too close to any existing tracker (even unmatched ones)
            # This prevents duplicate IDs for the same person
            is_duplicate = False
            for pid, tracker in self.person_trackers.items():
                if pid not in matches:  # Already checked matched ones
                    iou = self._calculate_iou(tracker.location, face)
                    if iou > 0.2:  # If 20% overlap, probably the same person
                        is_duplicate = True
                        break
            
            if not is_duplicate and len(self.person_trackers) < self.max_people:
                person_id = self.next_person_id
                self.next_person_id += 1
                self.person_trackers[person_id] = PersonTracker(person_id, face)
                matches[person_id] = face
                # Set default name if not already set
                if person_id not in self.person_names:
                    self.person_names[person_id] = f"Person {person_id}"
                # Set name in tracker
                self.person_trackers[person_id]._person_name = self.person_names[person_id]
                if self.debug_mode:
                    print(f"Created new person {person_id} at ({face[0]}, {face[1]}, {face[2]}x{face[3]})")
        
        return matches
    
    def detect_speaker_visual(self, frame: np.ndarray, face_location: Tuple[int, int, int, int]) -> bool:
        """
        Detect if a person is speaking using visual cues (mouth movement).
        
        This is a simple implementation. For better accuracy, use audio-based
        speaker detection or more sophisticated visual analysis.
        
        Args:
            frame: Video frame
            face_location: Face location (x, y, w, h)
            
        Returns:
            True if person appears to be speaking
        """
        # Simple heuristic: check if person is in the center of frame
        # (In meetings, speakers often position themselves centrally)
        # You can enhance this with mouth detection or audio analysis
        
        x, y, w, h = face_location
        frame_h, frame_w = frame.shape[:2]
        
        face_center_x = x + w/2
        face_center_y = y + h/2
        
        # Check if face is in center region (adjust thresholds as needed)
        center_region_x = (frame_w * 0.3, frame_w * 0.7)
        center_region_y = (frame_h * 0.3, frame_h * 0.7)
        
        is_center = (
            center_region_x[0] <= face_center_x <= center_region_x[1] and
            center_region_y[0] <= face_center_y <= center_region_y[1]
        )
        
        return is_center
    
    def set_speakers(self, person_ids: List[int]):
        """
        Manually set which people are currently speaking.
        
        Useful when you have audio-based speaker detection.
        
        Args:
            person_ids: List of person IDs who are speaking
        """
        self.current_speakers = set(person_ids)
    
    def set_person_name(self, person_id: int, name: str):
        """
        Set the display name for a person.
        
        Args:
            person_id: Person ID to name
            name: Display name (e.g., "John Doe" or "Alice Smith")
        """
        self.person_names[person_id] = name
        print(f"✓ Mapped Person {person_id} to '{name}'")
    
    def set_person_names(self, name_map: Dict[int, str]):
        """
        Set multiple person names at once.
        
        Args:
            name_map: Dictionary mapping person_id to name
                     Example: {0: "John Doe", 1: "Alice Smith"}
        """
        self.person_names.update(name_map)
        for pid, name in name_map.items():
            print(f"✓ Mapped Person {pid} to '{name}'")
    
    def get_person_name(self, person_id: int) -> str:
        """
        Get the display name for a person, or return default.
        
        Args:
            person_id: Person ID
            
        Returns:
            Person's name if set, otherwise "Person {person_id}"
        """
        return self.person_names.get(person_id, f"Person {person_id}")
    
    def map_names_from_detected_people(self):
        """
        Interactive function to map person IDs to names.
        Shows detected people and asks user to enter names.
        """
        if not self.person_trackers:
            print("No people detected yet. Wait for people to be detected first.")
            return
        
        print("\n" + "=" * 80)
        print("MAP PERSON IDS TO NAMES")
        print("=" * 80)
        print("\nDetected people:")
        for person_id in sorted(self.person_trackers.keys()):
            tracker = self.person_trackers[person_id]
            existing_name = self.person_names.get(person_id, "Not set")
            print(f"  Person {person_id}: {existing_name}")
        
        print("\nEnter names for each person (or press Enter to skip):")
        name_map = {}
        
        for person_id in sorted(self.person_trackers.keys()):
            current_name = self.person_names.get(person_id, "")
            prompt = f"Person {person_id} name"
            if current_name:
                prompt += f" (current: {current_name})"
            prompt += ": "
            
            name = input(prompt).strip()
            if name:
                name_map[person_id] = name
        
        if name_map:
            self.set_person_names(name_map)
            print("\n✓ Names mapped successfully!")
        else:
            print("\nNo names entered.")
    
    def preprocess_face(self, face_roi: np.ndarray):
        """Preprocess face for emotion prediction."""
        if isinstance(self.model, KerasEmotionModel):
            return face_roi
        else:
            import torchvision.transforms as transforms
            transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Grayscale(),
                transforms.Resize((48, 48)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485], std=[0.229])
            ])
            return transform(face_roi).unsqueeze(0)
    
    def process_frame(self, frame: np.ndarray, detect_speakers: bool = True) -> Dict:
        """
        Process a single frame to detect and track emotions for all people.
        
        Args:
            frame: Video frame (BGR format)
            detect_speakers: Whether to detect speakers visually
            
        Returns:
            Dictionary with frame analysis results
        """
        self.frame_count += 1
        current_time = time.time()
        
        # Skip if too soon since last analysis
        if current_time - self.last_analysis_time < self.analysis_interval:
            return {
                'processed': False,
                'reason': 'too_soon'
            }
        
        self.last_analysis_time = current_time
        
        # Detect faces
        faces, gray = self.detect_faces(frame)
        
        if len(faces) == 0:
            return {
                'processed': True,
                'faces_detected': 0,
                'people_tracked': len(self.person_trackers),
                'frame_results': []
            }
        
        # Debug: Show detected faces count
        if self.debug_mode and self.frame_count % 30 == 0:  # Print every 30 frames
            print(f"Frame {self.frame_count}: Detected {len(faces)} face(s), Tracking {len(self.person_trackers)} person(s)")
        
        # Match faces to people
        matches = self.match_faces_to_people(faces)
        
        frame_results = []
        
        # Process each matched person
        for person_id, (x, y, w, h) in matches.items():
            # Update tracker location and name
            if person_id in self.person_trackers:
                self.person_trackers[person_id].update_location((x, y, w, h))
                # Update person name in tracker if mapped
                if person_id in self.person_names:
                    self.person_trackers[person_id]._person_name = self.person_names[person_id]
            
            # Extract face
            face_roi = gray[y:y+h, x:x+w]
            if face_roi.size == 0:
                continue
            
            # Detect if speaking
            is_speaking = False
            if detect_speakers:
                if person_id in self.current_speakers:
                    is_speaking = True
                else:
                    is_speaking = self.detect_speaker_visual(frame, (x, y, w, h))
            
            # Preprocess and predict emotion
            try:
                face_input = self.preprocess_face(face_roi)
                
                if isinstance(self.model, KerasEmotionModel):
                    prediction = predict_emotion(self.model, face_input)
                    emotion = prediction['emotion']
                    confidence = prediction['confidence']
                    probabilities = prediction.get('probabilities', [])
                else:
                    face_input = face_input.to(self.device)
                    prediction = predict_emotion(self.model, face_input)
                    emotion = self.emotion_labels[prediction['emotion']]
                    confidence = prediction['confidence']
                    probabilities = prediction.get('probabilities', [])
                
                # Determine category
                if emotion in ['Happy', 'Surprise']:
                    category = 'positive'
                elif emotion in ['Angry', 'Disgust', 'Fear', 'Sad']:
                    category = 'negative'
                else:
                    category = 'neutral'
                
                # Update person tracker
                if person_id in self.person_trackers:
                    self.person_trackers[person_id].add_emotion(
                        emotion, confidence, is_speaking,
                        only_when_speaking=self.only_analyze_when_speaking
                    )
                    # Ensure name is set in tracker
                    if person_id in self.person_names:
                        self.person_trackers[person_id]._person_name = self.person_names[person_id]
                
                frame_results.append({
                    'person_id': person_id,
                    'person_name': self.get_person_name(person_id),
                    'location': (x, y, w, h),
                    'emotion': emotion,
                    'confidence': confidence,
                    'category': category,
                    'is_speaking': is_speaking,
                    'probabilities': probabilities
                })
                
            except Exception as e:
                print(f"Error processing person {person_id}: {str(e)}")
                continue
        
        return {
            'processed': True,
            'faces_detected': len(faces),
            'people_tracked': len(self.person_trackers),
            'frame_results': frame_results,
            'timestamp': current_time
        }
    
    def cleanup_inactive_people(self, min_frames=10):
        """
        Remove people who have been tracked for very few frames (likely false positives).
        
        Args:
            min_frames: Minimum number of frames a person must be tracked to be considered valid
        """
        to_remove = []
        for person_id, tracker in self.person_trackers.items():
            if tracker.total_frames < min_frames:
                to_remove.append(person_id)
        
        for pid in to_remove:
            if self.debug_mode:
                print(f"Cleaning up person {pid} (only {self.person_trackers[pid].total_frames} frames)")
            del self.person_trackers[pid]
    
    def get_meeting_summary(self, min_frames_for_summary=10) -> Dict:
        """
        Get comprehensive meeting summary with per-person statistics.
        Only includes people tracked for at least min_frames_for_summary frames.
        
        Args:
            min_frames_for_summary: Minimum frames a person must be tracked to appear in summary
        """
        # Clean up inactive people first
        self.cleanup_inactive_people(min_frames=min_frames_for_summary)
        
        # Get active people only
        active_people = {
            pid: tracker for pid, tracker in self.person_trackers.items()
            if tracker.total_frames >= min_frames_for_summary
        }
        
        summary = {
            'meeting_duration': time.time() - self.meeting_start_time,
            'total_frames_processed': self.frame_count,
            'total_people_detected': len(self.person_trackers),  # All people including inactive
            'total_people_active': len(active_people),  # Only active people
            'people': []
        }
        
        # Get metrics for each active person
        for person_id, tracker in active_people.items():
            person_metrics = tracker.get_metrics()
            # Add person name to metrics
            person_metrics['person_name'] = self.get_person_name(person_id)
            summary['people'].append(person_metrics)
        
        # Overall statistics (only from active people)
        all_emotions = []
        for tracker in active_people.values():
            all_emotions.extend([e['emotion'] for e in tracker.emotion_history])
        
        if all_emotions:
            from collections import Counter
            emotion_counts = Counter(all_emotions)
            summary['overall_emotion_distribution'] = dict(emotion_counts)
            summary['dominant_emotion'] = emotion_counts.most_common(1)[0][0] if emotion_counts else None
        
        return summary
    
    def get_person_summary(self, person_id: int) -> Optional[Dict]:
        """Get detailed summary for a specific person."""
        if person_id not in self.person_trackers:
            return None
        
        tracker = self.person_trackers[person_id]
        metrics = tracker.get_metrics()
        
        # Add recent emotion history
        metrics['recent_emotions'] = list(tracker.emotion_history)[-20:]  # Last 20
        
        return metrics
    
    def visualize_frame(self, frame: np.ndarray, frame_result: Dict) -> np.ndarray:
        """
        Draw visualization on frame showing people, emotions, and speaking status.
        
        Args:
            frame: Video frame
            frame_result: Result from process_frame()
            
        Returns:
            Annotated frame
        """
        if not frame_result.get('processed', False) or not frame_result.get('frame_results'):
            return frame
        
        for result in frame_result['frame_results']:
            person_id = result['person_id']
            person_name = result.get('person_name', self.get_person_name(person_id))
            x, y, w, h = result['location']
            emotion = result['emotion']
            confidence = result['confidence']
            is_speaking = result['is_speaking']
            category = result['category']
            
            # Choose color based on category
            if category == 'positive':
                color = (0, 255, 0)  # Green
            elif category == 'negative':
                color = (0, 0, 255)  # Red
            else:
                color = (255, 255, 0)  # Cyan
            
            # Draw face rectangle
            thickness = 3 if is_speaking else 2
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, thickness)
            
            # Draw label with person name and emotion
            label = f"{person_name}: {emotion} ({confidence:.2f})"
            if is_speaking:
                label += " [SPEAKING]"
            
            # Background for text
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x, y-text_h-10), (x+text_w, y), color, -1)
            cv2.putText(frame, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add summary info
        info_text = f"People: {frame_result['people_tracked']} | Frame: {self.frame_count}"
        cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame


def analyze_meeting_video(video_path: str, output_path: str = None, model_path=None, model_type='keras'):
    """
    Analyze emotions for all people in a meeting video.
    
    Args:
        video_path: Path to input video file
        output_path: Path to save annotated output video (optional)
        model_path: Path to emotion model
        model_type: Model type
        
    Returns:
        Meeting summary dictionary
    """
    print("=" * 80)
    print("MEETING EMOTION ANALYSIS")
    print("=" * 80)
    
    # Initialize analyzer
    analyzer = MeetingEmotionAnalyzer(model_path=model_path, model_type=model_type)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\nVideo Info:")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps:.2f}")
    print(f"  Total frames: {total_frames}")
    print(f"  Duration: {total_frames/fps:.2f} seconds")
    
    # Setup output video writer if requested
    out = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        print(f"\nOutput video: {output_path}")
    
    frame_num = 0
    
    print(f"\nProcessing video...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_num += 1
        
        # Process frame
        result = analyzer.process_frame(frame, detect_speakers=True)
        
        # Visualize
        if output_path:
            annotated_frame = analyzer.visualize_frame(frame.copy(), result)
            out.write(annotated_frame)
        
        # Progress update
        if frame_num % 30 == 0:
            progress = (frame_num / total_frames) * 100
            print(f"  Progress: {progress:.1f}% ({frame_num}/{total_frames} frames, "
                  f"{len(analyzer.person_trackers)} people tracked)")
    
    cap.release()
    if out:
        out.release()
    
    print(f"\n✓ Processing complete!")
    
    # Get and display summary
    summary = analyzer.get_meeting_summary()
    
    print(f"\n{'='*80}")
    print("MEETING SUMMARY")
    print(f"{'='*80}")
    print(f"Duration: {summary['meeting_duration']:.2f} seconds")
    print(f"Frames processed: {summary['total_frames_processed']}")
    print(f"Active people: {summary['total_people_active']} (out of {summary['total_people_detected']} total detected)")
    if summary['total_people_detected'] > summary['total_people_active']:
        print(f"  Note: {summary['total_people_detected'] - summary['total_people_active']} person(s) were filtered out (likely false positives)")
    
    if summary.get('overall_emotion_distribution'):
        print(f"\nOverall Emotion Distribution:")
        for emotion, count in sorted(
            summary['overall_emotion_distribution'].items(),
            key=lambda x: x[1], reverse=True
        ):
            print(f"  {emotion}: {count}")
    
        print(f"\nPer-Person Statistics:")
        for person_data in summary['people']:
            person_name = person_data.get('person_name', f"Person {person_data['person_id']}")
            print(f"\n  {person_name} (ID: {person_data['person_id']}):")
            print(f"    Total frames: {person_data['total_frames']}")
            print(f"    Dominant emotion: {person_data['dominant_emotion']}")
            print(f"    Speaking time: {person_data['speaking_percentage']:.1f}%")
            print(f"    Total speaking sessions: {person_data.get('total_speaking_sessions', 0)}")
            
            # Show per-session summaries
            if person_data.get('speaking_sessions'):
                print(f"\n    Speaking Sessions Summary:")
                for i, session in enumerate(person_data['speaking_sessions'], 1):
                    print(f"\n      Session {i}:")
                    print(f"        Duration: {session['duration']:.2f} seconds")
                    print(f"        Dominant emotion: {session['dominant_emotion']}")
                    print(f"        Average confidence: {session['average_confidence']:.2f}")
                    if session.get('emotion_percentages'):
                        print(f"        Emotions:")
                        for emotion, pct in sorted(
                            session['emotion_percentages'].items(),
                            key=lambda x: x[1], reverse=True
                        )[:3]:  # Top 3
                            print(f"          {emotion}: {pct:.1f}%")
            
            if person_data.get('emotion_percentages'):
                print(f"\n    Overall Emotion distribution:")
                for emotion, pct in sorted(
                    person_data['emotion_percentages'].items(),
                    key=lambda x: x[1], reverse=True
                )[:3]:  # Top 3
                    print(f"      {emotion}: {pct:.1f}%")
    
    return summary


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze emotions in meeting video')
    parser.add_argument('--video', type=str, required=True, help='Path to input video')
    parser.add_argument('--output', type=str, default=None, help='Path to output annotated video')
    parser.add_argument('--model', type=str, default=None, help='Path to model file')
    parser.add_argument('--type', type=str, default='keras', help='Model type')
    
    args = parser.parse_args()
    
    summary = analyze_meeting_video(
        video_path=args.video,
        output_path=args.output,
        model_path=args.model,
        model_type=args.type
    )
    
    print(f"\n✓ Analysis complete! Summary saved above.")

