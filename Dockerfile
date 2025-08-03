FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg libgl1

# Set working directory
WORKDIR /app

# Copy code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# RunPod handler setup
ENV RP_HANDLER=handler
CMD ["python", "-m", "runpod"]
