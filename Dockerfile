FROM python:3.10

# Install system dependencies
RUN apt update && apt install -y ffmpeg libgl1 libglib2.0-0

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Start the serverless handler
CMD ["runpod", "serverless", "start"]
