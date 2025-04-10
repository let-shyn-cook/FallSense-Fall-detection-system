import os
import cv2
import shutil
import json
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk

class ImageLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("Manual Image Labeling Tool")
        
        # Định nghĩa các nhãn và thư mục
        self.labels = {
            '1': 'Fall Down',
            '2': 'Lying Down',
            '3': 'Sit down',
            '4': 'Sitting',
            '5': 'Stand up',
            '6': 'Standing',
            '7': 'Walking'
        }
        
        # Đường dẫn thư mục
        self.test_acc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_acc')
        
        # Tạo các thư mục con nếu chưa tồn tại
        for label in self.labels.values():
            label_dir = os.path.join(self.test_acc_dir, label)
            if not os.path.exists(label_dir):
                os.makedirs(label_dir)
        
        # Lấy danh sách ảnh
        self.image_files = [f for f in os.listdir(self.test_acc_dir) 
                          if f.endswith('.jpg') and os.path.isfile(os.path.join(self.test_acc_dir, f))]
        self.image_files.sort()
        self.current_index = 0
        
        # Dictionary để lưu thông tin annotation
        self.annotations = {}
        self.current_video = 1
        self.video_start = 0
        
        # Tạo giao diện
        self.setup_gui()
        
        # Hiển thị ảnh đầu tiên
        if self.image_files:
            self.show_image()
    
    def setup_gui(self):
        # Frame cho ảnh
        self.image_frame = Frame(self.root)
        self.image_frame.pack(pady=10)
        
        self.image_label = Label(self.image_frame)
        self.image_label.pack()
        
        # Frame cho các nút điều khiển
        control_frame = Frame(self.root)
        control_frame.pack(pady=10)
        
        # Hiển thị thông tin file hiện tại
        self.info_label = Label(control_frame, text="")
        self.info_label.pack(pady=5)
        
        # Các nút nhãn
        label_frame = Frame(self.root)
        label_frame.pack(pady=5)
        
        for key, label in self.labels.items():
            btn = Button(label_frame, text=f"{key}: {label}",
                        command=lambda k=key: self.label_image(k))
            btn.pack(side=LEFT, padx=5)
        
        # Nút đánh dấu video mới
        Button(control_frame, text="New Video",
               command=self.mark_new_video).pack(pady=5)
        
        # Nút lưu annotation
        Button(control_frame, text="Save Annotations",
               command=self.save_annotations).pack(pady=5)
    
    def show_image(self):
        if 0 <= self.current_index < len(self.image_files):
            image_path = os.path.join(self.test_acc_dir, self.image_files[self.current_index])
            # Đọc và hiển thị ảnh
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (800, 600))
            photo = ImageTk.PhotoImage(Image.fromarray(image))
            
            self.image_label.config(image=photo)
            self.image_label.image = photo
            
            # Cập nhật thông tin
            self.info_label.config(
                text=f"Image {self.current_index + 1}/{len(self.image_files)}: "
                     f"{self.image_files[self.current_index]}")
    
    def label_image(self, label_key):
        if self.current_index < len(self.image_files):
            # Di chuyển ảnh vào thư mục tương ứng
            src = os.path.join(self.test_acc_dir, self.image_files[self.current_index])
            dst_dir = os.path.join(self.test_acc_dir, self.labels[label_key])
            dst = os.path.join(dst_dir, self.image_files[self.current_index])
            shutil.move(src, dst)
            
            # Chuyển sang ảnh tiếp theo
            self.current_index += 1
            if self.current_index < len(self.image_files):
                self.show_image()
            else:
                self.image_label.config(image='')
                self.info_label.config(text="All images have been labeled!")
    
    def mark_new_video(self):
        # Lưu thông tin video hiện tại
        if self.current_index > self.video_start:
            self.annotations[f"video_{self.current_video}"] = {
                "start_frame": self.video_start,
                "end_frame": self.current_index - 1
            }
            
            # Chuẩn bị cho video mới
            self.current_video += 1
            self.video_start = self.current_index
    
    def save_annotations(self):
        # Lưu video cuối cùng nếu chưa được lưu
        if self.current_index > self.video_start:
            self.annotations[f"video_{self.current_video}"] = {
                "start_frame": self.video_start,
                "end_frame": self.current_index - 1
            }
        
        # Lưu vào file JSON
        annotation_file = os.path.join(self.test_acc_dir, 'video_annotations.json')
        with open(annotation_file, 'w') as f:
            json.dump(self.annotations, f, indent=4)
        
        print(f"Annotations saved to {annotation_file}")

def main():
    root = Tk()
    app = ImageLabeler(root)
    root.mainloop()

if __name__ == '__main__':
    main()