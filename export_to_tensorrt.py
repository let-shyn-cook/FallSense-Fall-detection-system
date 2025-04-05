from ultralytics import YOLO

# Load a model
model = YOLO("yolo11s-pose.pt")  # load an official model

# Export the model
model.export(format="engine",simplify=True,half=True,imgsz=640)  # export to engine format