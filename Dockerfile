FROM python:3.13-slim-bookworm

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y ffmpeg libopus0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["python", "run.py"]