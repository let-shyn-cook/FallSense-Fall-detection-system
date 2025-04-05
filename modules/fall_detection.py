import cv2
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

class FallDetectionSystem:
    def __init__(self, prob_threshold=10):
        self.memory_prob = 0
        self.prob = prob_threshold
        self.fall_detected = False
        self.prev_actions = []
        self.motion_threshold = 0.5
        self.fall_confirmed = False
        self.fall_frames = []
        self.save_images = os.getenv('SAVE_IMAGES', 'true').lower() == 'true'
        self.images_dir = os.getenv('IMAGES_DIR', 'static/fall_images')
        
    def update(self, action):
        # Lưu lịch sử hành động
        self.prev_actions.append(action)
        if len(self.prev_actions) > 5:
            self.prev_actions.pop(0)
            
        # Kiểm tra điều kiện té ngã
        if action == 'Fall Down':
            # Kiểm tra hành động trước đó có phải là đứng/đi bộ không
            prev_standing = any(act in ['Standing', 'Walking'] for act in self.prev_actions[:-1])
            
            if prev_standing:
                self.memory_prob += 1
                if self.memory_prob >= self.prob:
                    # Xác nhận té ngã
                    self.fall_detected = True
                    self.fall_confirmed = True
        elif action == 'Lying Down':
            # Giữ trạng thái té ngã nếu đã xác nhận té ngã trước đó
            if self.fall_confirmed:
                self.fall_detected = True
            # Nếu chưa xác nhận té ngã, kiểm tra chuỗi hành động trước đó
            elif len(self.prev_actions) >= 2:
                # Kiểm tra nếu có hành động Fall Down trong 2 frame gần nhất
                if any(act == 'Fall Down' for act in self.prev_actions[-2:]):
                    self.fall_detected = True
                    self.fall_confirmed = True
                # Kiểm tra trường hợp frame bị nhảy (từ đứng/đi bộ -> ngồi -> nằm)
                elif (any(act in ['Standing', 'Walking'] for act in self.prev_actions[:-2]) and
                      self.prev_actions[-2] == 'Sitting' and
                      action == 'Lying Down'):
                    self.fall_detected = True
                    self.fall_confirmed = True
        else:
            # Nếu đang đứng hoặc đi bộ bình thường
            if action in ['Standing', 'Walking']:
                self.memory_prob = 0
                self.fall_detected = False
                self.fall_confirmed = False
            # Nếu đang ngồi hoặc đứng dậy/ngồi xuống bình thường
            elif action in ['Sitting', 'Stand up', 'Sit down']:
                # Chỉ reset nếu không có dấu hiệu té ngã trong chuỗi hành động gần đây
                if not any(act == 'Fall Down' for act in self.prev_actions[-2:]):
                    self.memory_prob = 0
                    self.fall_detected = False
                    self.fall_confirmed = False
            
        return self.fall_detected