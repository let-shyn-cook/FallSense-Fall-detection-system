from typing import List, Dict, Optional
from datetime import datetime
import json

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

class GraphData:
    def __init__(self, data_file: str = "fall_events.json"):
        self.query = FallEventQuery(data_file)
        self._events_data: List[Dict] = []
        
    def load_all_data(self) -> None:
        """Load all events data into memory"""
        self._events_data = self.query.query_events()
        
    def get_events_data(self) -> List[Dict]:
        """Get all loaded events data"""
        return self._events_data
        
    def clear_data(self) -> None:
        """Clear all stored data"""
        self._events_data = []
        
    def print_results(self) -> None:
        """Print all stored data in a formatted way"""
        print("\n" + "="*50)
        print("Printing All Events")
        print("="*50)
        
        if not self._events_data:
            print("No events data available. Please load data first.")
            return
            
        print(f"\nTotal number of events: {len(self._events_data)}")
        print("-"*50)
        
        for event in self._events_data:
            self._print_event_details(event)
                
    def _print_event_details(self, event: Dict) -> None:
        """Helper method to print event details"""
        print(f"\nTimestamp: {event.get('timestamp', 'N/A')}")
        print(f"Camera: {event.get('camera', 'N/A')}")
        print(f"Track ID: {event.get('track_id', 'N/A')}")
        print(f"Action: {event.get('action', 'N/A')}")
        print(f"Fall Detected: {'Yes' if event.get('fall_detected', False) else 'No'}")
        print(f"Status: {event.get('status', 'N/A')}")
        print(f"Location: {event.get('location', 'N/A')}")
        print(f"Snapshot URL: {event.get('snapshot_url', 'N/A')}")
        print(f"Video URL: {event.get('video_url', 'N/A')}")
        print(f"Reset Flag: {'Yes' if event.get('reset_flag', False) else 'No'}")
        print("-"*50)

if __name__ == "__main__":
    graph_data = GraphData()
    graph_data.load_all_data()
    graph_data.print_results()
