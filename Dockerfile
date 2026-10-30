# ============================================================
# MAYA // CYBER COMPANION OS — HUGGING FACE SPACES DOCKER
# ============================================================
FROM python:3.11-slim

# Install system dependencies (curl, ffmpeg for edge-tts audio, git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ffmpeg \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user (Hugging Face Spaces standard UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    SPACE_ID="huggingface-maya"

WORKDIR $HOME/app

# Copy dependency requirements
COPY --chown=user:user requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application source code
COPY --chown=user:user . .

# Expose Hugging Face default port
EXPOSE 7860

# Launch Web_maya runtime
CMD ["python", "Web_maya/app.py"]

