# 1. Start with a base image (using slim for smaller size)
FROM python:3.12-slim

# 2. Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /python

# 4. Install dependencies
# Copy only requirements first to leverage Docker cache

# Install system dependencies required by Pygame (SDL libraries) and Qt/PyQt
RUN apt-get update && apt-get install -y \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    stockfish \
    libxcb-cursor0 \
    libxcb1 \
    libxcb-render0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-render-util0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-util1 \
    libxcb-xinput0 \
    libxcb-randr0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libxkbcommon0 \
    libdbus-1-3 \
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


COPY /python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set up Qt environment variables
ENV QT_QPA_PLATFORM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt6/plugins
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# 6. Define the command to run your app
# Replace 'main.py' with your script's entry point
CMD ["python", "main.py"]
