from runpod.serverless.modules.rp_logger import RunPodLogger
from runpod.serverless.modules.rp_handler import runpod_handler
import ffmpeg
import requests
from ultralytics import YOLO

logger = RunPodLogger()

def handler(event):
    video_url = event["input"]["video_url"]
    video_path = "/tmp/input.mp4"

    r = requests.get(video_url)
    with open(video_path, "wb") as f:
        f.write(r.content)

    ffmpeg.input(video_path).output("/tmp/frame.jpg", vframes=1).run()

    model = YOLO("https://universe.roboflow.com/ryker-tan/rykers-sprint-coach/2?model=best.pt&api_key=4kp6KEqeVLWBWEO3ciKC")
    results = model(video_path)

    output = []
    for r in results:
        for box in r.boxes:
            output.append({
                "x": int(box.xyxy[0][0]),
                "y": int(box.xyxy[0][1]),
                "width": int(box.xyxy[0][2] - box.xyxy[0][0]),
                "height": int(box.xyxy[0][3] - box.xyxy[0][1]),
                "label": r.names[int(box.cls[0])],
            })

    return { "output": output }

# 🔥 This is required for serverless to work properly
runpod_handler(handler)
