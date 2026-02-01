"""
Script to check and stop all active Vexa bots
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

def get_bot_status():
    """Get status of all bots"""
    try:
        response = requests.get(f"{API_BASE}/bots/status")
        return response.json()
    except Exception as e:
        print(f"Error getting bot status: {e}")
        return None

def stop_bot(platform, meeting_id):
    """Stop a specific bot"""
    try:
        response = requests.post(
            f"{API_BASE}/bots/stop",
            json={
                "platform": platform,
                "native_meeting_id": meeting_id
            }
        )
        return response.json()
    except Exception as e:
        print(f"Error stopping bot: {e}")
        return None

if __name__ == "__main__":
    print("Checking active bots...")
    status = get_bot_status()
    
    if status:
        print(f"\nBot Status: {json.dumps(status, indent=2)}")
        
        if status.get("bots") and len(status["bots"]) > 0:
            print(f"\nFound {len(status['bots'])} active bot(s)")
            
            for bot in status["bots"]:
                platform = bot.get("platform")
                meeting_id = bot.get("native_meeting_id")
                
                print(f"\nStopping bot: {platform} - {meeting_id}")
                result = stop_bot(platform, meeting_id)
                
                if result and result.get("success"):
                    print(f"✓ Bot stopped successfully")
                else:
                    print(f"✗ Failed to stop bot: {result}")
        else:
            print("\nNo active bots found")
    else:
        print("Failed to get bot status")
