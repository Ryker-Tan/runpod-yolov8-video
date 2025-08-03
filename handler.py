import runpod
import os
import requests
import cv2
from ultralytics import YOLO
import tempfile
import shutil
from supabase import create_client, Client

# Supabase setup
SUPABASE_URL = "https://uejwgamhhbptifvbcpjg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load YOLO model
print("Loading YOLO model...")
model = YOLO("weights.pt")
print("YOLO model loaded.")

def draw_boxes(results, frame):
    print("Drawing boxes...")
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return frame

def process_video(video_url):
    print(f"Downloading video from: {video_url}")
    response = requests.get(video_url, stream=True)
    if response.status_code != 200:
        raise Exception(f"Failed to download video. Status code: {response.status_code}")

    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    with open(temp_input.name, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response
    print("Video downloaded.")

    cap = cv2.VideoCapture(temp_input.name)
    if not cap.isOpened():
        raise Exception("cv2 failed to open video file.")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video properties - FPS: {fps}, Width: {width}, Height: {height}")

    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("End of video or read failed.")
            break

        try:
            results = model(frame)
            frame = draw_boxes(results, frame)
            out.write(frame)
            frame_count += 1
        except Exception as e:
            print(f"Error during inference on frame {frame_count}: {e}")
            break

    cap.release()
    out.release()
    print(f"Processed {frame_count} frames.")

    file_name = os.path.basename(output_path)
    with open(output_path, 'rb') as f:
        print("Uploading to Supabase...")
        supabase.storage.from_("sprint-clips").upload(file_name, f, {
            "content-type": "video/mp4",
            "cache-control": "max-age=0"
        }, upsert=True)

    public_url = supabase.storage.from_("sprint-clips").get_public_url(file_name)
    print(f"Public URL: {public_url}")
    return public_url

def handler(event):
    try:
        video_url = event["input"]["video_url"]
        print(f"Handler received video URL: {video_url}")
        result_url = process_video(video_url)
        print("Video processed successfully.")
        return {"output_video_url": result_url}
    except Exception as e:
        print(f"Handler failed: {e}")
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
