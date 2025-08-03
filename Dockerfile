FROM python:3.10

RUN apt-get update && apt-get install -y ffmpeg libgl1 curl

WORKDIR /app
COPY handler.py /app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Download YOLO weights from public link instead of bundling
RUN curl -o weights.pt https://your-link-to-weights.pt

ENV RP_HANDLER=handler
CMD ["python", "handler.py"]
