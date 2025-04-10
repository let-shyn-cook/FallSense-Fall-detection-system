import os
import cv2
import numpy as np
from collections import defaultdict
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
from main import init_models, process_keypoints, predict_action

def process_video(video_path, yolo, stgcn, device, class_names):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return None

    frames_queue = []
    frame_count = 0
    valid_frame_count = 0

    # Thu thập tất cả keypoints từ video
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        results = yolo.track(frame, persist=True, conf=0.5, tracker="bytetrack.yaml")
        
        keypoints_list, _ = process_keypoints(results)
        if keypoints_list is not None:
            valid_frame_count += 1
            frames_queue.append(keypoints_list[0])

    cap.release()

    # Nếu không có frame nào hoặc hơn 30% frame không phát hiện được người, bỏ qua video này
    if frame_count == 0 or valid_frame_count / frame_count < 0.7:
        return None

    # Nếu có ít nhất 15 frame hợp lệ, dự đoán hành động
    if len(frames_queue) >= 15:
        action = predict_action(stgcn, frames_queue, device, class_names)
        if isinstance(action, str) and action != "Collecting frames...":
            return action

    return None

def balance_results(results_dict):
    # Tìm số lượng video nhỏ nhất trong các nhãn
    min_count = min(len(videos) for videos in results_dict.values())
    
    # Cân bằng số lượng video cho mỗi nhãn
    balanced_dict = {}
    for label, videos in results_dict.items():
        # Chọn ngẫu nhiên số video bằng với min_count
        balanced_dict[label] = np.random.choice(videos, min_count, replace=False).tolist()
    
    return balanced_dict

def main():
    # Khởi tạo models
    yolo, stgcn, device, class_names = init_models()

    # Đường dẫn đến thư mục test
    test_dir = "data_action/test"
    
    # Thu thập kết quả
    results = defaultdict(list)
    true_labels = []
    pred_labels = []
    videos_per_class = 10  # Số lượng video cần cho mỗi nhãn

    # Xử lý từng thư mục nhãn
    for label in os.listdir(test_dir):
        label_dir = os.path.join(test_dir, label)
        if not os.path.isdir(label_dir):
            continue

        print(f"\nProcessing {label} videos...")
        # Lấy danh sách tất cả video trong thư mục
        all_videos = [f for f in os.listdir(label_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
        if not all_videos:
            continue

        # Chọn ngẫu nhiên 10 video
        selected_videos = np.random.choice(all_videos, min(videos_per_class, len(all_videos)), replace=False)
        processed_count = 0
        remaining_videos = [v for v in all_videos if v not in selected_videos]

        # Xử lý các video đã chọn
        for video_file in selected_videos:
            video_path = os.path.join(label_dir, video_file)
            prediction = process_video(video_path, yolo, stgcn, device, class_names)
            
            if prediction is not None:
                results[label].append(prediction)
                processed_count += 1
                print(f"Video: {video_file}, Predicted: {prediction}")

        # Thêm video bổ sung nếu cần
        while processed_count < videos_per_class and remaining_videos:
            # Chọn ngẫu nhiên một video từ danh sách còn lại
            additional_video = np.random.choice(remaining_videos)
            remaining_videos.remove(additional_video)
            
            video_path = os.path.join(label_dir, additional_video)
            prediction = process_video(video_path, yolo, stgcn, device, class_names)
            
            if prediction is not None:
                results[label].append(prediction)
                processed_count += 1
                print(f"Additional video: {additional_video}, Predicted: {prediction}")

        print(f"Processed {processed_count}/{videos_per_class} videos for {label}")


    # Cân bằng số lượng kết quả giữa các nhãn
    balanced_results = balance_results(results)

    # Tạo true labels và predicted labels cho confusion matrix
    for label, predictions in balanced_results.items():
        true_labels.extend([label] * len(predictions))
        pred_labels.extend(predictions)

    # Tạo confusion matrix
    cm = confusion_matrix(true_labels, pred_labels, labels=class_names)
    
    # Vẽ confusion matrix
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names,
                yticklabels=class_names)
    plt.title('Confusion Matrix')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    plt.close()

    # In kết quả
    print("\nResults after balancing:")
    for label, predictions in balanced_results.items():
        total = len(predictions)
        correct = sum(1 for p in predictions if p == label)
        accuracy = (correct / total) * 100 if total > 0 else 0
        print(f"{label}: {correct}/{total} correct ({accuracy:.2f}% accuracy)")

if __name__ == '__main__':
    main()