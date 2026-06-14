FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg libjpeg-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir setuptools

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper base model during build (avoids slow first-start)
RUN python -c "import whisper; whisper.load_model('base')"

COPY app/ app/
COPY frontend/ frontend/
COPY lessons/ lessons/

ENV DATA_DIR=/data
ENV CONFIG_DIR=/config
ENV PORT=13200

EXPOSE 13200

CMD ["python", "-m", "app.main"]
