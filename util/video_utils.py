import cv2
import os

def extract_frames(video_path, output_folder):
    """
    Tách các frame từ video và lưu vào thư mục đầu ra, với video 30 FPS sẽ lấy mẫu cách 1 frame.
    
    Args:
        video_path (str): Đường dẫn đến file video
        output_folder (str): Đường dẫn đến thư mục lưu các frame
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        # Kiểm tra đường dẫn video
        if not os.path.exists(video_path):
            print(f"Không tìm thấy file video: {video_path}")
            return False
        
        # Tạo thư mục đầu ra nếu chưa tồn tại
        os.makedirs(output_folder, exist_ok=True)
        
        # Đọc video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Không thể mở video")
            return False
        
        # Lấy thông tin video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"Tổng số frame: {total_frames}")
        print(f"FPS video nguồn: {source_fps}")
        
        if source_fps <= 0:
            print("Không thể xác định FPS của video nguồn")
            return False
            
        # Với video 30 FPS, lấy mẫu cách 1 frame (skip 1 frame)
        frame_interval = 2 if round(source_fps) == 30 else 1
        target_fps = source_fps / frame_interval
        print(f"Khoảng cách lấy mẫu: {frame_interval} frame (skip {frame_interval-1} frame)")
        print(f"FPS đích dự kiến: {target_fps:.2f}")
        
        # Đọc và lưu frame theo khoảng cách đã tính
        frame_count = 0
        actual_frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Chỉ lưu frame theo khoảng cách đã tính
            if frame_count % frame_interval == 0:
                frame_path = os.path.join(output_folder, f"frame_{actual_frame_count:06d}.jpg")
                cv2.imwrite(frame_path, frame)
                actual_frame_count += 1
                
                if actual_frame_count % 100 == 0:
                    print(f"Đã xử lý {actual_frame_count} frames")
                    
            frame_count += 1
        
        actual_fps = (actual_frame_count / (total_frames / source_fps))
        print(f"\nHoàn thành! Đã lưu {actual_frame_count} frames vào {output_folder}")
        print(f"FPS thực tế đạt được: {actual_fps:.2f}")
        cap.release()
        return True
        
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        return False

if __name__ == "__main__":
    # Ví dụ sử dụng
    video_path = "0405.mp4"
    output_folder = "test_acc"
    extract_frames(video_path, output_folder)