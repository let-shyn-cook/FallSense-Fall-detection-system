from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
from collections import defaultdict

class DashboardData:
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

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Generate dashboard data from events"""
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Calculate total falls and today's falls
        total_falls = len([e for e in self.events if e.get('fall_detected', False)])
        today_falls = len([
            e for e in self.events 
            if e.get('fall_detected', False) and 
            datetime.fromisoformat(e['timestamp']).date() == today
        ])

        # Get unique cameras
        cameras = set(e['camera'] for e in self.events)
        active_cameras = len(cameras)  # Assuming all cameras in events are active

        # Generate timeline data (last 24 hours)
        timeline_data = self._generate_timeline_data()

        # Generate camera distribution data
        camera_distribution = self._generate_camera_distribution()

        # Get recent events (last 10)
        recent_events = self._get_recent_events()

        # Generate camera status
        camera_status = self._generate_camera_status()

        return {
            "total_falls": total_falls,
            "today_falls": today_falls,
            "active_cameras": active_cameras,
            "total_cameras": len(cameras),
            "timeline": timeline_data,
            "camera_distribution": camera_distribution,
            "recent_events": recent_events,
            "cameras": camera_status
        }

    def _generate_timeline_data(self) -> Dict[str, List]:
        """Generate timeline data for the last 24 hours"""
        now = datetime.now()
        start_time = now - timedelta(hours=24)
        
        # Initialize hourly buckets
        hourly_data = defaultdict(int)
        for hour in range(24):
            time_key = (start_time + timedelta(hours=hour)).strftime("%H:00")
            hourly_data[time_key] = 0

        # Count falls in each hour
        for event in self.events:
            if not event.get('fall_detected', False):
                continue
                
            event_time = datetime.fromisoformat(event['timestamp'])
            if start_time <= event_time <= now:
                hour_key = event_time.strftime("%H:00")
                hourly_data[hour_key] += 1

        # Convert to lists for chart.js
        labels = list(hourly_data.keys())
        values = list(hourly_data.values())
        
        return {
            "labels": labels,
            "values": values
        }

    def _generate_camera_distribution(self) -> Dict[str, List]:
        """Generate camera distribution data"""
        camera_counts = defaultdict(int)
        
        for event in self.events:
            if event.get('fall_detected', False):
                camera_counts[event['camera']] += 1

        return {
            "labels": list(camera_counts.keys()),
            "values": list(camera_counts.values())
        }

    def _get_recent_events(self, limit: int = 10) -> List[Dict]:
        """Get recent events with fall detection"""
        fall_events = [
            event for event in self.events 
            if event.get('fall_detected', False)
        ]
        
        # Sort by timestamp descending
        fall_events.sort(
            key=lambda x: datetime.fromisoformat(x['timestamp']),
            reverse=True
        )
        
        return fall_events[:limit]

    def _generate_camera_status(self) -> List[Dict]:
        """Generate camera status data"""
        # Get unique cameras from events
        cameras = set(e['camera'] for e in self.events)
        
        # For each camera, check if it has events in the last 5 minutes
        now = datetime.now()
        five_minutes_ago = now - timedelta(minutes=5)
        
        camera_status = []
        for camera in cameras:
            recent_events = [
                e for e in self.events 
                if e['camera'] == camera and 
                datetime.fromisoformat(e['timestamp']) >= five_minutes_ago
            ]
            
            camera_status.append({
                "name": camera,
                "status": "online" if recent_events else "offline"
            })
            
        return camera_status 