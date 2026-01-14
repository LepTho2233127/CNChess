# 1. Start with a base image (using slim for smaller size)
FROM python:3.12-slim

# 2. Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Install dependencies
# Copy only requirements first to leverage Docker cache

# Install system dependencies required by Pygame (SDL libraries)
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libfreetype6-dev \
    pkg-config


COPY /python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Define the command to run your app
# Replace 'main.py' with your script's entry point
CMD ["bash"]
