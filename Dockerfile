FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg libjpeg-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir setuptools

COPY requirements.txt .
# --no-build-isolation: openai-whisper (20231117) uses setup.py without declaring
# setuptools as a build dep, so pip's isolated build env can't find pkg_resources.
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

COPY app/ app/
COPY frontend/ frontend/

ENV DATA_DIR=/data
ENV CONFIG_DIR=/config
ENV PORT=13200

EXPOSE 13200

CMD ["python", "-m", "app.main"]
