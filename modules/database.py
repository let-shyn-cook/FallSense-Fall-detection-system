from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import json
import os
from flask_socketio import SocketIO

class Database:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.client = None
        self.db = None
        self.fall_events = None
        self.users = None
        self.connect_mongodb()

    def connect_mongodb(self):
        try:
            # Kết nối MongoDB sử dụng URI từ biến môi trường
            self.client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=5000)
            # Kiểm tra kết nối
            self.client.admin.command('ping')
            self.db = self.client[os.getenv('MONGODB_DB')]
            self.fall_events = self.db['fall_events']
            self.users = self.db['users']
            print("Kết nối MongoDB thành công")
            return True
        except ConnectionFailure as e:
            print(f"Không thể kết nối đến MongoDB. Đảm bảo MongoDB đang chạy. Lỗi: {str(e)}")
            return False
    
    def save_fall_event(self, event):
        try:
            # Kiểm tra và chuẩn hóa dữ liệu sự kiện
            if 'track_id' not in event:
                print("Warning: Thiếu track_id trong sự kiện")
                return
            
            # Thử kết nối lại MongoDB nếu chưa kết nối
            if self.fall_events is None:
                if not self.connect_mongodb():
                    print("Không thể kết nối MongoDB, chỉ lưu vào file JSON")
            
            # Thêm trạng thái té ngã, timestamp và reset_flag
            event['fall_detected'] = True
            event['timestamp'] = datetime.now().isoformat()
            event['reset_flag'] = False
            
            # Lưu vào MongoDB
            if self.fall_events is not None:
                try:
                    # Chuyển đổi ObjectId thành string trước khi lưu
                    event_copy = event.copy()
                    result = self.fall_events.insert_one(event_copy)
                    event_copy['_id'] = str(result.inserted_id)
                    
                    # Gửi sự kiện qua WebSocket
                    if self.socketio:
                        self.socketio.emit('history_update', [event_copy])
                except Exception as mongo_error:
                    print(f"Lỗi khi lưu vào MongoDB: {str(mongo_error)}")
                    # Thử kết nối lại MongoDB
                    if self.connect_mongodb():
                        try:
                            result = self.fall_events.insert_one(event_copy)
                            event_copy['_id'] = str(result.inserted_id)
                            if self.socketio:
                                self.socketio.emit('history_update', [event_copy])
                        except Exception as retry_error:
                            print(f"Vẫn không thể lưu vào MongoDB sau khi thử kết nối lại: {str(retry_error)}")

            # Lưu vào file JSON để tương thích ngược
            try:
                events = []
                if os.path.exists('fall_events.json'):
                    with open('fall_events.json', 'r', encoding='utf-8') as f:
                        events = json.load(f)
                events.append(event)
                with open('fall_events.json', 'w', encoding='utf-8') as f:
                    json.dump(events, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Lỗi khi lưu vào file JSON: {str(e)}")
                # Tạo file mới nếu có lỗi
                with open('fall_events.json', 'w', encoding='utf-8') as f:
                    json.dump([event], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Lỗi khi lưu sự kiện té ngã: {str(e)}")
            # Đảm bảo luôn lưu được vào file JSON
            try:
                with open('fall_events.json', 'w', encoding='utf-8') as f:
                    json.dump([event], f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Lỗi nghiêm trọng khi lưu file: {str(e)}")
    
    def get_fall_events(self):
        try:
            # Lấy dữ liệu từ MongoDB
            if hasattr(self, 'fall_events') and self.fall_events is not None:
                # Chỉ lấy các sự kiện chưa được reset
                events = list(self.fall_events.find({'reset_flag': False}))
                # Chuyển đổi ObjectId thành string
                for event in events:
                    event['_id'] = str(event['_id'])
                return events
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu từ MongoDB: {str(e)}")
        
        # Fallback về file JSON nếu MongoDB thất bại
        try:
            with open('fall_events.json', 'r') as f:
                events = json.load(f)
                # Chỉ trả về các sự kiện chưa được reset
                return [event for event in events if not event.get('reset_flag', False)]
        except FileNotFoundError:
            return []
    
    def find_user(self, username):
        if self.users:
            return self.users.find_one({'username': username})
        return None
    
    def create_user(self, user_data):
        if self.users:
            return self.users.insert_one(user_data)
        return None
        
    def reset_fall_events(self):
        """Đặt reset_flag=True cho tất cả các sự kiện khi camera dừng"""
        try:
            # Reset trong MongoDB
            if hasattr(self, 'fall_events'):
                try:
                    self.fall_events.update_many(
                        {'reset_flag': False},
                        {'$set': {'reset_flag': True}}
                    )
                except Exception as mongo_error:
                    print(f"Lỗi khi cập nhật MongoDB: {str(mongo_error)}")
                
            # Reset trong file JSON
            try:
                if os.path.exists('fall_events.json'):
                    with open('fall_events.json', 'r', encoding='utf-8') as f:
                        events = json.load(f)
                    for event in events:
                        event['reset_flag'] = True
                    with open('fall_events.json', 'w', encoding='utf-8') as f:
                        json.dump(events, f, ensure_ascii=False, indent=2)
                    
                    # Gửi sự kiện qua WebSocket
                    if self.socketio:
                        self.socketio.emit('history_update', [])
                        
            except Exception as json_error:
                print(f"Lỗi khi cập nhật file JSON: {str(json_error)}")
                
        except Exception as e:
            print(f"Lỗi khi reset các sự kiện té ngã: {str(e)}")
            
    def delete_fall_events(self):
        """Xóa tất cả các sự kiện té ngã"""
        try:
            if hasattr(self, 'fall_events') and self.fall_events is not None:
                self.fall_events.delete_many({})
                
            # Xóa cả trong file JSON
            try:
                if os.path.exists('fall_events.json'):
                    with open('fall_events.json', 'w', encoding='utf-8') as f:
                        json.dump([], f)
                        
                # Gửi sự kiện qua WebSocket
                if self.socketio:
                    self.socketio.emit('history_update', [])
                    
            except Exception as e:
                print(f"Lỗi khi xóa file JSON: {str(e)}")
                
        except Exception as e:
            print(f"Lỗi khi xóa các sự kiện té ngã: {str(e)}")