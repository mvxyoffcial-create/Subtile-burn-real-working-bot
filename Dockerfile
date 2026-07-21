FROM python:3.11-slim

# Install system dependencies (FFmpeg with libx264/libx265 & fontconfig for multi-language subs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fontconfig \
    fonts-freefont-ttf \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose Port 8000 for Koyeb Health Check
EXPOSE 8000

# Set default PORT environment variable
ENV PORT=8000

# Run the Telegram bot
CMD ["python", "bot.py"]
