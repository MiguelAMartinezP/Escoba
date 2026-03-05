FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    libgl1 \
    libglib2.0-0 \
    libmtdev1 \
    libx11-6 \
    libxcursor1 \
    libxrandr2 \
    libxinerama1 \
    libxi6 \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt