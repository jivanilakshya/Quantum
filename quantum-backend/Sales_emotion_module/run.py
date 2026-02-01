"""
Google Meet Emotion Analyzer - Main Entry Point

Captures Google Meet window and analyzes emotions of all participants in real-time.
Works by capturing the Google Meet browser window and processing video frames.

Usage:
    python run.py --duration 300
    python run.py --region 100,100,800,600 --duration 600
    python run.py --save-output --output result.mp4
"""

import cv2
import numpy as np
import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meeting_emotion_analyzer import MeetingEmotionAnalyzer
from config import MODEL_PATH, MODEL_TYPE_PROD

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("Warning: 'mss' library not available. Install it with: pip install mss")
    print("Alternative: Will try PIL ImageGrab (slower)")

try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class GoogleMeetCapture:
    """Captures frames from Google Meet window."""
    
    def __init__(self, window_name=None, monitor_region=None):
        """
        Initialize Google Meet capture.
        
        Args:
            window_name: Name of the browser window (e.g., "Google Meet - Chrome")
            monitor_region: Region to capture as (left, top, width, height)
        """
        self.window_name = window_name or "Google Meet"
        self.monitor_region = monitor_region
        self.sct = None
        
        # Try to initialize mss (fastest)
        if MSS_AVAILABLE:
            try:
                self.sct = mss.mss()
                print("[OK] Using mss for screen capture (fast)")
            except Exception as e:
                print(f"Warning: Could not initialize mss: {e}")
        
        # Fallback to PIL if mss not available
        if self.sct is None and PIL_AVAILABLE:
            print("[OK] Using PIL ImageGrab for screen capture (slower)")
        
        if self.sct is None and not PIL_AVAILABLE:
            raise ImportError("No screen capture library available. Install 'mss' or 'PIL'")
    
    def capture_frame(self) -> np.ndarray:
        """Capture current frame from Google Meet window."""
        if self.sct is not None:
            # Use mss (faster)
            if self.monitor_region:
                monitor = {
                    "top": self.monitor_region[1],
                    "left": self.monitor_region[0],
                    "width": self.monitor_region[2],
                    "height": self.monitor_region[3]
                }
            else:
                # Capture entire screen
                monitor = self.sct.monitors[1]  # Primary monitor
            
            screenshot = self.sct.grab(monitor)
            frame = np.array(screenshot)
            # Convert BGRA to BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        elif PIL_AVAILABLE:
            # Use PIL ImageGrab (slower)
            if self.monitor_region:
                bbox = (
                    self.monitor_region[0],
                    self.monitor_region[1],
                    self.monitor_region[0] + self.monitor_region[2],
                    self.monitor_region[1] + self.monitor_region[3]
                )
            else:
                bbox = None
            
            screenshot = ImageGrab.grab(bbox=bbox)
            frame = np.array(screenshot)
            # Convert RGB to BGR for OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        else:
            raise RuntimeError("No capture method available")
        
        return frame
    
    def get_window_region(self):
        """
        Try to find Google Meet window and return its region.
        This is a helper function - you may need to adjust for your setup.
        """
        if PYAUTOGUI_AVAILABLE:
            try:
                # Try to find window by name
                # Note: This requires additional libraries on some systems
                # For now, return None to use full screen or manual region
                pass
            except:
                pass
        
        return None  # Will use full screen or manual region


def analyze_google_meet_realtime(
    monitor_region=None,
    duration=300,
    model_path=None,
    model_type='keras',
    show_overlay=True,
    save_output=False,
    output_path='google_meet_analysis.mp4',
    debug_mode=False,
    test_detection=False
):
    """
    Analyze emotions in Google Meet in real-time.
    
    Args:
        monitor_region: Region to capture (left, top, width, height) or None for full screen
        duration: Duration to analyze in seconds (default: 5 minutes)
        model_path: Path to emotion model
        model_type: Model type
        show_overlay: Show visualization overlay
        save_output: Save annotated video
        output_path: Output video path
        
    Returns:
        Meeting summary dictionary
    """
    print("=" * 80)
    print("GOOGLE MEET EMOTION ANALYZER")
    print("=" * 80)
    print("\nInstructions:")
    print("1. Open Google Meet in your browser")
    print("2. Join or start a meeting")
    print("3. Make sure participants' videos are visible")
    print("4. Press Ctrl+C to stop analysis\n")
    
    try:
        # Initialize capture
        print("Initializing screen capture...")
        capture = GoogleMeetCapture(monitor_region=monitor_region)
        
        # Initialize analyzer with session-based analysis
        print("Loading emotion detection model...")
        analyzer = MeetingEmotionAnalyzer(
            model_path=model_path or MODEL_PATH,
            model_type=model_type or MODEL_TYPE_PROD,
            max_people=10,
            only_when_speaking=True  # Only analyze when person is speaking
        )
        print("[OK] Model loaded successfully")
        print("[OK] Session-based analysis enabled (analyzing only when speaking)")
        
        # Enable debug mode if requested
        if debug_mode:
            print("\nEnabling debug mode for face detection...")
            analyzer.debug_mode = True
            print("[OK] Debug mode enabled - you'll see detailed face detection information")
        
        # Ask user if they want to map names
        print("\n" + "=" * 80)
        print("PERSON NAME MAPPING")
        print("=" * 80)
        print("You can map person IDs to Google Meet usernames.")
        try:
            response = input("Do you want to map names now? (y/n, or 'auto' to try auto-detection): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            # Handle non-interactive mode or Ctrl+C
            response = 'n'
            print("Skipping name mapping (non-interactive mode).")
        
        if response == 'y':
            # Wait a bit for people to be detected, then map names
            print("\nWaiting 3 seconds for people to be detected...")
            time.sleep(3)
            analyzer.map_names_from_detected_people()
        elif response == 'auto':
            print("\nAttempting to auto-detect names from Google Meet...")
            # This will be implemented if OCR is available
            print("Auto-detection not yet implemented. Use manual mapping instead.")
            analyzer.map_names_from_detected_people()
        else:
            print("Skipping name mapping. You can map names later or they will show as 'Person 0', 'Person 1', etc.")
        
        # Test capture and face detection
        print("\nTesting screen capture and face detection...")
        test_frame = capture.capture_frame()
        print(f"[OK] Captured frame: {test_frame.shape}")
        
        # Test face detection if requested
        if test_detection:
            print("\n" + "=" * 80)
            print("FACE DETECTION TEST")
            print("=" * 80)
            print("Testing face detection on captured frame...")
            test_faces, test_gray = analyzer.detect_faces(test_frame)
            print(f"\nResult: {len(test_faces)} face(s) detected")
            
            if len(test_faces) > 0:
                print(f"\n[OK] Face detection working! Detected {len(test_faces)} face(s):")
                for i, (x, y, w, h) in enumerate(test_faces):
                    print(f"  Face {i+1}: Position=({x},{y}), Size={w}x{h} pixels")
            else:
                print("\n[WARNING] WARNING: No faces detected!")
                print("\nPossible reasons:")
                print("  1. No participants visible in Google Meet window")
                print("  2. Participants' videos are disabled/hidden")
                print("  3. Wrong capture region (try --select-region)")
                print("  4. Faces are too small or too large")
                print("  5. Poor lighting or image quality")
                print("  6. Google Meet window is minimized or not visible")
                
                print("\nTroubleshooting steps:")
                print("  1. Check Google Meet - are participant videos visible?")
                print("  2. Try --select-region to choose specific area")
                print("  3. Ensure good lighting and clear video")
                
                try:
                    response = input("\nContinue anyway? (y/n): ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    # Handle non-interactive mode
                    response = 'n'
                    print("\nAborting due to non-interactive mode.")
                
                if response != 'y':
                    print("Aborting. Please fix the issues above and try again.")
                    return None
            
            print("\n" + "=" * 80)
        
        # Setup output video if requested
        out = None
        if save_output:
            h, w = test_frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 10  # Approximate FPS for screen capture
            out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
            print(f"[OK] Saving output to: {output_path}")
        
        print(f"\n{'='*80}")
        print("STARTING ANALYSIS (Press Ctrl+C to stop)")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        frame_count = 0
        
        try:
            while (time.time() - start_time) < duration:
                # Capture frame
                frame = capture.capture_frame()
                frame_count += 1
                
                # Process frame
                result = analyzer.process_frame(frame, detect_speakers=True)
                
                # Visualize
                if show_overlay:
                    annotated_frame = analyzer.visualize_frame(frame.copy(), result)
                else:
                    annotated_frame = frame
                
                # Display
                if show_overlay:
                    # Resize if too large for display
                    display_frame = annotated_frame.copy()
                    h, w = display_frame.shape[:2]
                    if w > 1920:
                        scale = 1920 / w
                        new_w, new_h = int(w * scale), int(h * scale)
                        display_frame = cv2.resize(display_frame, (new_w, new_h))
                    
                    cv2.imshow('Google Meet Emotion Analysis', display_frame)
                    
                    # Print status
                    if result.get('processed', False) and result.get('frame_results'):
                        print(f"\nFrame {frame_count} - {time.time() - start_time:.1f}s:")
                        for person_result in result['frame_results']:
                            person_name = person_result.get('person_name', f"Person {person_result['person_id']}")
                            emotion = person_result['emotion']
                            conf = person_result['confidence']
                            speaking = "SPEAKING" if person_result['is_speaking'] else "listening"
                            print(f"  {person_name}: {emotion} ({conf:.2f}) - {speaking}")
                    
                    # Check for quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\nStopping analysis...")
                        break
                
                # Save to output video
                if out:
                    out.write(annotated_frame)
                
                # Small delay to avoid maxing out CPU
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n\nAnalysis stopped by user")
        
        # Cleanup
        if out:
            out.release()
            print(f"\n[OK] Output video saved: {output_path}")
        
        if show_overlay:
            cv2.destroyAllWindows()
        
        # Get and display summary
        print(f"\n{'='*80}")
        print("ANALYSIS SUMMARY")
        print(f"{'='*80}")
        
        summary = analyzer.get_meeting_summary()
        
        print(f"Duration: {summary['meeting_duration']:.1f} seconds")
        print(f"Frames processed: {summary['total_frames_processed']}")
        print(f"Active people: {summary['total_people_active']} (out of {summary['total_people_detected']} total detected)")
        if summary.get('total_people_detected', 0) > summary.get('total_people_active', 0):
            print(f"  Note: {summary['total_people_detected'] - summary['total_people_active']} person(s) were filtered out (likely false positives)")
        
        if summary.get('overall_emotion_distribution'):
            print(f"\nOverall Emotion Distribution:")
            for emotion, count in sorted(
                summary['overall_emotion_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"  {emotion}: {count}")
        
        print(f"\nPer-Person Statistics:")
        for person_data in summary['people']:
            person_name = person_data.get('person_name', f"Person {person_data['person_id']}")
            print(f"\n  {person_name} (ID: {person_data['person_id']}):")
            print(f"    Frames: {person_data['total_frames']}")
            print(f"    Dominant emotion: {person_data['dominant_emotion']}")
            print(f"    Speaking time: {person_data['speaking_percentage']:.1f}%")
            if person_data.get('emotion_percentages'):
                for emotion, pct in sorted(
                    person_data['emotion_percentages'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]:  # Top 3
                    print(f"      {emotion}: {pct:.1f}%")
        
        return summary
    
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def select_region_interactive():
    """
    Interactive function to select screen region for capture.
    Shows a screenshot and lets user select region.
    """
    print("\nSelecting capture region...")
    
    try:
        capture = GoogleMeetCapture()
        frame = capture.capture_frame()
        
        # Create window for selection
        cv2.namedWindow('Select Region - Press ESC when done', cv2.WINDOW_NORMAL)
        
        # Simple region selection (you can enhance this)
        print("\nInstructions:")
        print("1. Look at the full screenshot")
        print("2. Note the coordinates you want to capture")
        print("3. Press ESC to continue")
        print("4. You'll be asked to enter coordinates manually\n")
        
        # Resize if too large
        h, w = frame.shape[:2]
        if w > 1920:
            scale = 1920 / w
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        
        cv2.imshow('Select Region - Press ESC when done', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Get user input
        print("Enter capture region coordinates:")
        try:
            left = int(input("Left (x): "))
            top = int(input("Top (y): "))
            width = int(input("Width: "))
            height = int(input("Height: "))
            
            return (left, top, width, height)
        except ValueError:
            print("Invalid input. Using full screen.")
            return None
    
    except Exception as e:
        print(f"Error in region selection: {e}")
        return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze emotions in Google Meet in real-time',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze full screen for 5 minutes
  python run.py --duration 300

  # Analyze specific region
  python run.py --region 100,100,800,600 --duration 600

  # Save output video
  python run.py --save-output --output result.mp4

  # No overlay (faster)
  python run.py --no-overlay

  # Test face detection first
  python run.py --test-detection

Note: You need to have Google Meet open in your browser before starting.
        """
    )
    
    parser.add_argument('--region', type=str, help='Capture region: left,top,width,height (e.g., 100,100,800,600)')
    parser.add_argument('--duration', type=int, default=300, help='Duration in seconds (default: 300 = 5 minutes)')
    parser.add_argument('--model', type=str, default=None, help='Path to model file')
    parser.add_argument('--type', type=str, default='keras', help='Model type')
    parser.add_argument('--save-output', action='store_true', help='Save annotated output video')
    parser.add_argument('--output', type=str, default='google_meet_analysis.mp4', help='Output video path')
    parser.add_argument('--no-overlay', action='store_true', help='Disable visualization overlay (faster)')
    parser.add_argument('--select-region', action='store_true', help='Interactively select capture region')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (show detailed face detection info)')
    parser.add_argument('--test-detection', action='store_true', help='Test face detection first before full analysis')
    
    args = parser.parse_args()
    
    # Parse region if provided
    monitor_region = None
    if args.region:
        try:
            coords = [int(x.strip()) for x in args.region.split(',')]
            if len(coords) == 4:
                monitor_region = tuple(coords)
            else:
                print("ERROR: Region must be 4 numbers: left,top,width,height")
                sys.exit(1)
        except ValueError:
            print("ERROR: Invalid region format. Use: left,top,width,height")
            sys.exit(1)
    
    # Interactive region selection
    if args.select_region:
        monitor_region = select_region_interactive()
    
    # Run analysis
    summary = analyze_google_meet_realtime(
        monitor_region=monitor_region,
        duration=args.duration,
        model_path=args.model,
        model_type=args.type,
        show_overlay=not args.no_overlay,
        save_output=args.save_output,
        output_path=args.output,
        debug_mode=args.debug,
        test_detection=args.test_detection if hasattr(args, 'test_detection') else False
    )
    
    if summary:
        print("\n[OK] Analysis complete!")

