import cv2
import torch
import numpy as np
from collections import deque
from ultralytics import YOLO
from models.stgcn import TwoStreamSpatialTemporalGraph
from dataloader.dataset import processing_data
from modules.fall_detection import FallDetectionSystem
import threading
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

class VideoCamera:
    def __init__(self, socketio=None):
        self.video = None
        self.is_running = False
        self.frame = None
        self.lock = threading.Lock()
        self.frames_queues = {}
        self.fall_systems = {}
        self.current_actions = {}
        self.fall_detected = {}
        self.socketio = socketio
        
        # Biến theo dõi ghi video
        self.recording = {}
        self.video_writers = {}
        self.fall_start_frames = {}
        self.fall_frame_count = {}
        
        # Biến theo dõi các track_id đã được xử lý trong phiên hiện tại
        self.processed_track_ids = set()
        
        # Tạo thư mục lưu trữ
        os.makedirs('static/fall_images', exist_ok=True)
        os.makedirs('static/fall_videos', exist_ok=True)
        
        # Khởi tạo models
        self.init_models()
        
    def init_models(self):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.yolo = YOLO(os.getenv('POSE_MODEL'))
        
        # Load ST-GCN model
        self.class_names = ['Fall Down', 'Lying Down', 'Sit down', 'Sitting', 'Stand up', 'Standing', 'Walking']
        graph_args = {'strategy': 'spatial'}
        self.stgcn = TwoStreamSpatialTemporalGraph(graph_args, len(self.class_names)).to(self.device)
        self.stgcn.load_state_dict(torch.load(os.getenv('MODEL_PATH'), map_location=self.device))
        self.stgcn.eval()
    
    def start(self):
        if not self.is_running:
            try:
                # Reset biến theo dõi track_id khi bắt đầu phiên mới
                self.processed_track_ids.clear()
                
                # Sử dụng camera source từ biến môi trường
                camera_source = os.getenv('CAMERA_SOURCE')
                # Nếu là số, chuyển thành integer
                if camera_source.isdigit():
                    camera_source = int(camera_source)
                self.video = cv2.VideoCapture(camera_source)
                
                # Kiểm tra xem camera có được mở thành công không
                if not self.video.isOpened():
                    print("Không thể mở camera. Vui lòng kiểm tra kết nối và quyền truy cập.")
                    if self.socketio:
                        self.socketio.emit('camera_error', {
                            'message': 'Không thể mở camera. Vui lòng kiểm tra kết nối và quyền truy cập.'
                        })
                    return False
                
                # Thiết lập kích thước khung hình từ biến môi trường
                self.video.set(cv2.CAP_PROP_FRAME_WIDTH, int(os.getenv('CAMERA_WIDTH')))
                self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, int(os.getenv('CAMERA_HEIGHT')))
                self.video.set(cv2.CAP_PROP_FPS, int(os.getenv('CAMERA_FPS')))
                
                # Thử đọc frame đầu tiên để kiểm tra
                ret, _ = self.video.read()
                if not ret:
                    print("Không thể đọc dữ liệu từ camera.")
                    if self.socketio:
                        self.socketio.emit('camera_error', {
                            'message': 'Không thể đọc dữ liệu từ camera.'
                        })
                    self.video.release()
                    return False
                
                self.is_running = True
                threading.Thread(target=self._capture_loop, daemon=True).start()
                return True
                
            except Exception as e:
                print(f"Lỗi khi khởi tạo camera: {str(e)}")
                if self.socketio:
                    self.socketio.emit('camera_error', {
                        'message': f'Lỗi khi khởi tạo camera: {str(e)}'
                    })
                if self.video:
                    self.video.release()
                return False
        return False
    
    def stop(self):
        self.is_running = False
        if self.video:
            self.video.release()
            self.video = None
            
        # Dừng tất cả video writers
        for track_id in list(self.video_writers.keys()):
            self.stop_recording(track_id)
            
        return True
    
    def _capture_loop(self):
        while self.is_running:
            if self.video:
                ret, frame = self.video.read()
                if ret:
                    # Xử lý frame với AI
                    processed_frame = self.process_frame(frame)
                    with self.lock:
                        self.frame = processed_frame
                else:
                    self.stop()
                    break
    
    def process_frame(self, frame):
        # Phát hiện pose với YOLO và tracking
        results = self.yolo.track(frame, persist=True, conf=0.5, tracker="bytetrack.yaml")
        
        # Xử lý keypoints
        keypoints_list, track_ids = self.process_keypoints(results)
        if keypoints_list is not None and len(results) > 0 and results[0].keypoints is not None:
            for i, (keypoints, track_id) in enumerate(zip(keypoints_list, track_ids)):
                # Khởi tạo cho người mới
                if track_id not in self.frames_queues:
                    self.frames_queues[track_id] = deque(maxlen=30)
                    self.fall_systems[track_id] = FallDetectionSystem()
                    self.current_actions[track_id] = "Waiting..."
                    self.fall_detected[track_id] = False
                
                # Thêm frame vào queue
                self.frames_queues[track_id].append(keypoints)
                
                # Dự đoán hành động
                self.current_actions[track_id] = self.predict_action(track_id)
                
                # Cập nhật trạng thái té ngã
                self.fall_detected[track_id] = self.fall_systems[track_id].update(self.current_actions[track_id])
                
                # Gửi cập nhật trạng thái qua WebSocket
                if self.socketio:
                    self.socketio.emit('status_update', {
                        'track_id': track_id,
                        'action': self.current_actions[track_id],
                        'status': 'active' if self.is_running else 'inactive',
                        'fall_detected': self.fall_detected[track_id]
                    })
                
                # Vẽ kết quả lên frame
                if results[0].keypoints is not None and len(results[0].keypoints) > i:
                    keypoints_data = results[0].keypoints[i].data[0].cpu().numpy()
                    frame = self.draw_results(frame, keypoints_data, track_id)
                
                # Lưu sự kiện té ngã
                if self.fall_detected[track_id]:
                    self.save_fall_event(track_id, frame)
        
        return frame
    
    def process_keypoints(self, results, frame_size=(640, 640)):
        if not results[0].keypoints or len(results[0].keypoints) == 0:
            return None, None
        
        processed_keypoints = []
        track_ids = []
        
        # Xử lý keypoints cho mỗi người được phát hiện
        for i in range(len(results[0].keypoints)):
            try:
                keypoints = results[0].keypoints[i].data[0].cpu().numpy()
                if keypoints.shape[0] == 0:
                    continue
                
                keypoints_reshaped = np.zeros((1, 17, 3))
                keypoints_reshaped[0, :keypoints.shape[0], :] = keypoints[:17, :3]
                # Chuẩn hóa tọa độ x, y
                keypoints_reshaped[0, :, 0] /= frame_size[0]
                keypoints_reshaped[0, :, 1] /= frame_size[1]
                
                processed_keypoints.append(keypoints_reshaped[0])
                # Lấy track_id từ kết quả tracking
                if hasattr(results[0], 'boxes') and len(results[0].boxes.id) > i:
                    track_ids.append(int(results[0].boxes.id[i]))
                else:
                    track_ids.append(i)  # Fallback nếu không có track_id
            except Exception as e:
                print(f"Error processing keypoints for person {i}: {e}")
                continue
        
        if not processed_keypoints:
            return None, None
        
        return processed_keypoints, track_ids
    
    def predict_action(self, track_id):
        if len(self.frames_queues[track_id]) < 15:
            return "Collecting frames..."
        
        # Chuẩn bị dữ liệu đầu vào
        features = np.array(list(self.frames_queues[track_id]))
        features = features[::2]  # Lấy 15 frame
        # Reshape và chuẩn hóa dữ liệu keypoints
        keypoints_data = features[:, :, :2].reshape(features.shape[0], features.shape[1], 2)
        features[:, :, :2] = processing_data(keypoints_data).reshape(features.shape[0], features.shape[1], 2)
        
        # Chuyển đổi dữ liệu sang tensor
        features = torch.tensor(features, dtype=torch.float32).unsqueeze(0).permute(0, 3, 1, 2).to(self.device)
        motion = features[:, :2, 1:, :] - features[:, :2, :-1, :]
        
        # Dự đoán
        with torch.no_grad():
            outputs = self.stgcn((features, motion))
            _, preds = torch.max(outputs, 1)
            action = self.class_names[preds.item()]
        
        return action
    
    def draw_results(self, frame, keypoints_2d, track_id):
        # Lấy vị trí để hiển thị text
        text_x = int(np.mean(keypoints_2d[:, 0]))
        text_y = int(np.mean(keypoints_2d[:, 1])) - 10
        
        # Vẽ text hành động và ID
        cv2.putText(frame, f"ID: {track_id} - {self.current_actions[track_id]}", (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Hiển thị cảnh báo té ngã
        if self.fall_detected[track_id]:
            cv2.putText(frame, f"FALL DETECTED! (ID: {track_id})", (text_x, text_y - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Vẽ các điểm keypoint
        for kp in keypoints_2d:
            x, y = int(kp[0]), int(kp[1])
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        
        # Vẽ khung xương
        skeleton = [[15,13],[13,11],[16,14],[14,12],[11,12],[5,11],[6,12],
                    [5,6],[5,7],[6,8],[7,9],[8,10],[1,2],[0,1],[0,2],
                    [1,3],[2,4],[3,5],[4,6]]
        
        for pair in skeleton:
            if keypoints_2d[pair[0]][0] != 0 and keypoints_2d[pair[1]][0] != 0:
                pt1 = (int(keypoints_2d[pair[0]][0]), int(keypoints_2d[pair[0]][1]))
                pt2 = (int(keypoints_2d[pair[1]][0]), int(keypoints_2d[pair[1]][1]))
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
        
        return frame
    
    def save_fall_event(self, track_id, frame):
        # Kiểm tra xem track_id đã tồn tại trong current_actions và chưa được xử lý trong phiên hiện tại
        if track_id not in self.current_actions:
            print(f"Warning: track_id {track_id} không tồn tại trong current_actions")
            return
            
        if track_id in self.processed_track_ids:
            return
            
        # Đánh dấu track_id đã được xử lý
        self.processed_track_ids.add(track_id)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Lưu frame hiện tại thành ảnh
        image_filename = f'static/fall_images/{timestamp}.jpg'
        image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), image_filename)
        
        # Convert frame to uint8 if needed
        frame_to_save = frame
        if isinstance(frame_to_save, np.ndarray):
            if frame_to_save.dtype != np.uint8:
                frame_to_save = (frame_to_save * 255).astype(np.uint8)
        
        cv2.imwrite(image_path, frame_to_save)
        
        # Xử lý ghi video
        if track_id not in self.recording:
            # Bắt đầu ghi video mới
            self.recording[track_id] = True
            self.fall_start_frames[track_id] = []
            self.fall_frame_count[track_id] = 0
            
            # Khởi tạo video writer với các codec khác nhau
            video_filename = f'static/fall_videos/{timestamp}.mp4'
            height, width = frame.shape[:2]
            
            # Danh sách các codec để thử
            codecs = ['avc1', 'h264', 'mp4v', 'divx', 'xvid']
            success = False
            
            for codec in codecs:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    writer = cv2.VideoWriter(video_filename, fourcc, 30.0, (width, height))
                    
                    if writer is not None and writer.isOpened():
                        self.video_writers[track_id] = writer
                        print(f"Đã khởi tạo VideoWriter thành công với codec {codec}")
                        success = True
                        break
                except Exception as e:
                    print(f"Không thể khởi tạo VideoWriter với codec {codec}: {str(e)}")
                    if writer is not None:
                        writer.release()
            
            if not success:
                print(f"Không thể tạo video writer cho {video_filename} với tất cả các codec đã thử")
                return
        
        # Lưu frame vào video
        if self.recording[track_id]:
            self.video_writers[track_id].write(frame_to_save)
            self.fall_start_frames[track_id].append(frame_to_save)
            self.fall_frame_count[track_id] += 1
            
            # Nếu đã ghi đủ 90 frames (3 giây), dừng ghi
            if self.fall_frame_count[track_id] >= 90:
                self.stop_recording(track_id)
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'camera': 'Camera 1',
            'track_id': track_id,
            'action': self.current_actions[track_id],
            'fall_detected': True,
            'snapshot_url': f'/{image_filename}',
            'video_url': f'/static/fall_videos/{timestamp}.mp4' if track_id in self.video_writers else None,
            'location': 'Camera 1',
            'status': 'Detected'
        }
        
        try:
            # Lưu vào MongoDB và file JSON thông qua Database class
            from modules.database import Database
            db = Database()
            db.save_fall_event(event)
        except Exception as e:
            print(f"Lỗi khi lưu sự kiện té ngã: {str(e)}")
    
    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                ret, jpeg = cv2.imencode('.jpg', self.frame)
                return jpeg.tobytes()
            return None
    
    def stop_recording(self, track_id):
        if track_id in self.video_writers:
            self.video_writers[track_id].release()
            del self.video_writers[track_id]
            del self.recording[track_id]
            del self.fall_start_frames[track_id]
            del self.fall_frame_count[track_id]
    
    def get_status(self):
        status = {
            'is_running': self.is_running,
            'people': []
        }
        
        # Thêm thông tin cho từng người được theo dõi
        for track_id in self.current_actions.keys():
            person_status = {
                'track_id': track_id,
                'action': self.current_actions[track_id],
                'fall_detected': self.fall_detected[track_id]
            }
            status['people'].append(person_status)
            
        return status