FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Copy all code and weights
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Runpod template setup
ENV RP_HANDLER=handler
CMD ["python3", "-m", "runpod"]
