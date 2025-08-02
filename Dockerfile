FROM ultralytics/ultralytics:latest

RUN apt-get update && apt-get install -y ffmpeg

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python3", "-m", "runpod"]
