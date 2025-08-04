import runpod
import os
import requests
import cv2
import tempfile
import shutil
import torch
from ultralytics import YOLO
from ultralytics.nn.tasks import DetectionModel
from supabase import create_client, Client

print("📦 Starting handler.py")

# --- Supabase Setup ---
SUPABASE_URL = "https://uejwgamhhbptifvbcpjg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVlandnYW1oaGJwdGlmdmJjcGpnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE0NTg3NjcsImV4cCI6MjA2NzAzNDc2N30.3TzBwfwYZZTFQs2YlA6kWnBuTW_YmPHrUMe__o6i720"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("✅ Supabase client initialized")

# --- Fix PyTorch global unpickling issue ---
torch.serialization.add_safe_globals([DetectionModel])
print("✅ Safe globals added for YOLOv8 loading")

# --- Load YOLOv8 model ---
model = YOLO("weights.pt")
print("✅ YOLO model loaded")

def draw_boxes(results, frame):
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return frame

def process_video(video_url):
    print("📥 Downloading video from URL:", video_url)

    # Download input video
    response = requests.get(video_url, stream=True)
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    with open(temp_input.name, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response
    print("✅ Video downloaded:", temp_input.name)

    # Setup video I/O
    cap = cv2.VideoCapture(temp_input.name)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print("🧠 Starting YOLOv8 inference on video...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        frame = draw_boxes(results, frame)
        out.write(frame)

    cap.release()
    out.release()
    print("✅ Inference and box drawing complete")

    # Upload to Supabase
    file_name = os.path.basename(output_path)
    with open(output_path, 'rb') as f:
        supabase.storage.from_("sprint-clips").upload(file_name, f, {
            "content-type": "video/mp4",
            "cache-control": "max-age=0"
        }, upsert=True)

    public_url = supabase.storage.from_("sprint-clips").get_public_url(file_name)
    print("☁️ Uploaded processed video to Supabase:", public_url)
    return public_url

def handler(event):
    print("📨 Handler received event:", event)
    video_url = event["input"]["video_url"]
    result_url = process_video(video_url)
    return {"output_video_url": result_url}

print("🚀 Calling runpod.serverless.start()")
runpod.serverless.start({"handler": handler})
