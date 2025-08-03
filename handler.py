import runpod
import subprocess
from ultralytics import YOLO
import os
import requests
import cv2
import numpy as np
from supabase import create_client, Client

# === Load your YOLOv8 weights ===
model = YOLO("weights.pt")  # Your custom model file already in your repo

# === Supabase credentials ===
SUPABASE_URL = "https://uejwgamhhbptifvbcpjg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVlandnYW1oaGJwdGlmdmJjcGpnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE0NTg3NjcsImV4cCI6MjA2NzAzNDc2N30.3TzBwfwYZZTFQs2YlA6kWnBuTW_YmPHrUMe__o6i720"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def download_file(url, local_path):
    response = requests.get(url, stream=True)
    with open(local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def handler(event):
    video_url = event["input"]["video_url"]
    video_name = video_url.split("/")[-1]
    input_path = f"/tmp/{video_name}"
    output_path = f"/tmp/annotated_{video_name}"

    # Step 1: Download the input video
    download_file(video_url, input_path)

    # Step 2: Annotate frames and write new video
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)[0]
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            label = model.names[cls]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        out.write(frame)

    cap.release()
    out.release()

    # Step 3: Upload the annotated video to Supabase
    with open(output_path, "rb") as f:
        supabase.storage.from_("sprint-clips").upload(f"annotated/{video_name}", f, {"cacheControl": "3600", "upsert": True})

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/sprint-clips/annotated/{video_name}"
    return {"output_video_url": public_url}
