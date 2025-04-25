import cv2
import torch
import numpy as np
from ultralytics import YOLO
from models.stgcn import TwoStreamSpatialTemporalGraph
from dataloader.dataset import processing_data
from collections import deque
import time

class FallDetectionSystem:
    def __init__(self, prob_threshold=5):
        self.memory_prob = {}  # Bộ đếm xác nhận té ngã cho từng người
        self.prob = prob_threshold  # Ngưỡng frame liên tiếp để xác nhận té ngã
        self.fall_detected = {}  # Trạng thái phát hiện té ngã cho từng người
        
    def update(self, action, track_id):
        # Khởi tạo nếu chưa có track_id
        if track_id not in self.memory_prob:
            self.memory_prob[track_id] = 0
            self.fall_detected[track_id] = False
            
        # Cập nhật bộ đếm dựa trên hành động
        if action == 'Fall Down':
            self.memory_prob[track_id] += 1
            # Xác nhận té ngã nếu đủ số frame liên tiếp
            if self.memory_prob[track_id] >= self.prob:
                self.fall_detected[track_id] = True
        else:
            # Reset bộ đếm nếu không phải té ngã
            self.memory_prob[track_id] = 0
            self.fall_detected[track_id] = False
            
        return self.fall_detected[track_id]

# Khởi tạo model YOLO và ST-GCN
def init_models(yolo_model='yolo11n-pose.pt', stgcn_model=r'runs\best.pt'):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    # Load YOLO model with tracking
    yolo = YOLO(yolo_model)
    
    # Load ST-GCN model
    class_names =  ['Fall Down', 'Lying Down', 'Sit down', 'Sitting', 'Stand up', 'Standing', 'Walking']
    graph_args = {'strategy': 'spatial'}
    stgcn = TwoStreamSpatialTemporalGraph(graph_args, len(class_names)).to(device)
    stgcn.load_state_dict(torch.load(stgcn_model, map_location=device))
    stgcn.eval()
    
    return yolo, stgcn, device, class_names

# Xử lý keypoints từ YOLO
def process_keypoints(results, frame_size=(640, 640)):
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

# Dự đoán hành động
def predict_action(stgcn, frames_queue, device, class_names):
    if len(frames_queue) < 15:
        return "Collecting frames..."
    
    # Chuẩn bị dữ liệu đầu vào
    features = np.array(list(frames_queue))
    
    # Lấy mẫu để có 15 frame đều đặn từ toàn bộ video
    if len(features) > 15:
        indices = np.linspace(0, len(features)-1, 15, dtype=int)
        features = features[indices]
    
    # Reshape và chuẩn hóa dữ liệu keypoints
    keypoints_data = features[:, :, :2].reshape(features.shape[0], features.shape[1], 2)
    features[:, :, :2] = processing_data(keypoints_data).reshape(features.shape[0], features.shape[1], 2)
    
    # Chuyển đổi dữ liệu sang tensor
    features = torch.tensor(features, dtype=torch.float32).unsqueeze(0).permute(0, 3, 1, 2).to(device)
    motion = features[:, :2, 1:, :] - features[:, :2, :-1, :]
    
    # Dự đoán
    with torch.no_grad():
        outputs = stgcn((features, motion))
        _, preds = torch.max(outputs, 1)
        action = class_names[preds.item()]
    
    return action

def main():
    # Khởi tạo models
    yolo, stgcn, device, class_names = init_models()
    
    # Khởi tạo hệ thống phát hiện té ngã
    fall_system = FallDetectionSystem()
    
    # Khởi tạo camera
    cap = cv2.VideoCapture('0405.mp4')
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    # Dictionary để lưu trữ frames cho từng người
    frames_queues = {}
    
    # Biến để tính FPS
    prev_time = time.time()
    fps = 0
    fps_array = deque(maxlen=30)  # Để tính trung bình FPS
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Tính FPS
        current_time = time.time()
        fps = 1 / (current_time - prev_time)
        prev_time = current_time
        fps_array.append(fps)
        avg_fps = sum(fps_array) / len(fps_array)
            
        # Phát hiện pose với YOLO và tracking
        results = yolo.track(frame, persist=True, conf=0.5, tracker="bytetrack.yaml")
        
        # Xử lý keypoints
        keypoints_list, track_ids = process_keypoints(results, frame.shape[:2])
        
        # Hiển thị FPS
        cv2.putText(frame, f"FPS: {int(avg_fps)}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 0), 3)
        
        if keypoints_list is not None:
            for i, (keypoints, track_id) in enumerate(zip(keypoints_list, track_ids)):
                # Khởi tạo queue cho người mới
                if track_id not in frames_queues:
                    frames_queues[track_id] = deque(maxlen=30)
                
                # Thêm frame vào queue
                frames_queues[track_id].append(keypoints)
                
                # Dự đoán hành động
                action = predict_action(stgcn, frames_queues[track_id], device, class_names)
                
                # Cập nhật hệ thống phát hiện té ngã
                fall_detected = fall_system.update(action, track_id)
                
                # Lấy vị trí để hiển thị text
                text_x = int(np.mean(keypoints[:, 0] * frame.shape[1]))
                text_y = int(np.mean(keypoints[:, 1] * frame.shape[0])) - 10
                
                # Vẽ text hành động và ID
                cv2.putText(frame, f"ID: {track_id} - {action}", (text_x, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Hiển thị cảnh báo té ngã
                if fall_detected:
                    cv2.putText(frame, f"FALL DETECTED! (ID: {track_id})", (text_x, text_y - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                # Vẽ khung xương
                keypoints_2d = results[0].keypoints[i].data[0].cpu().numpy()
                # Vẽ các điểm keypoint
                for kp in keypoints_2d:
                    x, y = int(kp[0]), int(kp[1])
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                
                # Định nghĩa các cặp điểm để vẽ đường nối
                skeleton = [[15,13],[13,11],[16,14],[14,12],[11,12],[5,11],[6,12],
                            [5,6],[5,7],[6,8],[7,9],[8,10],[1,2],[0,1],[0,2],
                            [1,3],[2,4],[3,5],[4,6]]
                
                # Vẽ các đường nối
                for pair in skeleton:
                    if keypoints_2d[pair[0]][0] != 0 and keypoints_2d[pair[1]][0] != 0:
                        pt1 = (int(keypoints_2d[pair[0]][0]), int(keypoints_2d[pair[0]][1]))
                        pt2 = (int(keypoints_2d[pair[1]][0]), int(keypoints_2d[pair[1]][1]))
                        cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
        
        # Resize frame để hiển thị
        display_width = 1280  # Chiều rộng mong muốn
        display_height = int(frame.shape[0] * (display_width / frame.shape[1]))  # Tính chiều cao tỷ lệ
        display_frame = cv2.resize(frame, (display_width, display_height))
        
        # Hiển thị frame
        cv2.imshow('Fall Detection', display_frame)
        
        # Thoát khi nhấn 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main() 