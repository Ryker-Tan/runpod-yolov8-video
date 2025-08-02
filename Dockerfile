FROM python:3.10-slim

# Install dependencies
RUN apt update && apt install -y ffmpeg libgl1

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files in repo
COPY . .

# Run handler (change this if your entry file is different)
CMD ["python3", "handler.py"]
