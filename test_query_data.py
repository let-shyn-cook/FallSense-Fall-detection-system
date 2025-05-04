import json
from datetime import datetime
from typing import List, Dict, Optional, Union
from pathlib import Path

class FallEventQuery:
    def __init__(self, data_file: str = "fall_events.json"):
        self.data_file = data_file
        self.events = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """Load fall events data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File {self.data_file} not found")
            return []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {self.data_file}")
            return []

    def query_events(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        camera: Optional[str] = None,
        fall_detected: Optional[bool] = None,
        status: Optional[str] = None,
        track_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Query fall events based on various criteria
        
        Args:
            start_time: Start timestamp in ISO format (e.g., "2025-04-25T14:02:27")
            end_time: End timestamp in ISO format
            camera: Camera name to filter by
            fall_detected: Boolean to filter by fall detection status
            status: Status to filter by (e.g., "Detected")
            track_id: Track ID to filter by
            
        Returns:
            List of matching fall events
        """
        filtered_events = self.events.copy()
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            filtered_events = [
                event for event in filtered_events
                if datetime.fromisoformat(event["timestamp"]) >= start_dt
            ]
            
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            filtered_events = [
                event for event in filtered_events
                if datetime.fromisoformat(event["timestamp"]) <= end_dt
            ]
            
        if camera:
            filtered_events = [
                event for event in filtered_events
                if event["camera"] == camera
            ]
            
        if fall_detected is not None:
            filtered_events = [
                event for event in filtered_events
                if event["fall_detected"] == fall_detected
            ]
            
        if status:
            filtered_events = [
                event for event in filtered_events
                if event["status"] == status
            ]
            
        if track_id is not None:
            filtered_events = [
                event for event in filtered_events
                if event["track_id"] == track_id
            ]
            
        return filtered_events

    def get_event_by_id(self, event_id: int) -> Optional[Dict]:
        """Get a specific fall event by its index in the list"""
        if 0 <= event_id < len(self.events):
            return self.events[event_id]
        return None

    def get_latest_events(self, limit: int = 10) -> List[Dict]:
        """Get the most recent fall events"""
        sorted_events = sorted(
            self.events,
            key=lambda x: datetime.fromisoformat(x["timestamp"]),
            reverse=True
        )
        return sorted_events[:limit]

def main():
    # Example usage
    query = FallEventQuery()
    
    # Query all events
    all_events = query.query_events()
    print(f"\nTotal events: {len(all_events)}")
    
    # Print detailed information for all events
    print("\nDetailed information for all events:")
    print("-" * 100)
    for idx, event in enumerate(all_events, 1):
        print(f"\nEvent #{idx}:")
        print(f"Timestamp: {event['timestamp']}")
        print(f"Camera: {event['camera']}")
        print(f"Track ID: {event['track_id']}")
        print(f"Action: {event['action']}")
        print(f"Fall Detected: {'Yes' if event['fall_detected'] else 'No'}")
        print(f"Status: {event['status']}")
        print(f"Location: {event['location']}")
        print(f"Snapshot URL: {event['snapshot_url']}")
        print(f"Video URL: {event['video_url']}")
        print(f"Reset Flag: {'Yes' if event['reset_flag'] else 'No'}")
        print("-" * 100)
    
    # Query events within a time range
    time_filtered = query.query_events(
        start_time="2025-04-25T14:02:00",
        end_time="2025-04-25T14:03:00"
    )
    print(f"\nEvents in time range (2025-04-25T14:02:00 to 2025-04-25T14:03:00): {len(time_filtered)}")
    
    # Query events from specific camera
    camera_events = query.query_events(camera="Camera 1")
    print(f"\nEvents from Camera 1: {len(camera_events)}")
    
    # Query only detected falls
    fall_events = query.query_events(fall_detected=True)
    print(f"\nDetected falls: {len(fall_events)}")
    
    # Get latest 5 events with detailed information
    latest_events = query.get_latest_events(limit=5)
    print("\nLatest 5 events with detailed information:")
    print("-" * 100)
    for idx, event in enumerate(latest_events, 1):
        print(f"\nLatest Event #{idx}:")
        print(f"Timestamp: {event['timestamp']}")
        print(f"Camera: {event['camera']}")
        print(f"Track ID: {event['track_id']}")
        print(f"Action: {event['action']}")
        print(f"Fall Detected: {'Yes' if event['fall_detected'] else 'No'}")
        print(f"Status: {event['status']}")
        print(f"Location: {event['location']}")
        print(f"Snapshot URL: {event['snapshot_url']}")
        print(f"Video URL: {event['video_url']}")
        print(f"Reset Flag: {'Yes' if event['reset_flag'] else 'No'}")
        print("-" * 100)

if __name__ == "__main__":
    main()
