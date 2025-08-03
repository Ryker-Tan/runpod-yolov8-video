import runpod
import subprocess
from ultralytics import YOLO
import os
import requests

# Load your YOLOv8 model from weights
model = YOLO("weights.pt")

def download_file(url, local_path):
    response = requests.get(url, stream=True)
    with open(local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def extract_frame(video_path, frame_path):
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", "fps=1", "-frames:v", "1", frame_path
    ], check=True)

def handler(event):
    video_url = event["input"]["video_url"]

    # Step 1: Download video
    video_path = "/tmp/input.mp4"
    frame_path = "/tmp/frame.jpg"
    download_file(video_url, video_path)

    # Step 2: Extract one frame using ffmpeg
    extract_frame(video_path, frame_path)

    # Step 3: Run YOLOv8 inference on the frame
    results = model(frame_path)

    detections = []
    for box in results[0].boxes:
        b = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
        c = int(box.cls[0])       # class id
        conf = float(box.conf[0]) # confidence
        detections.append({
            "bbox": b,
            "class": int(c),
            "confidence": conf
        })

    return {"detections": detections}

# Start the RunPod serverless function
runpod.serverless.start({"handler": handler})
