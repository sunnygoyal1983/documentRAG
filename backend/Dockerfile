## syntax=docker/dockerfile:1.7
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements.lock ./
# OCR system dependencies (for scanned PDFs)
# - tesseract-ocr: OCR engine
# - ghostscript + qpdf: required by ocrmypdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-pan \
    ghostscript \
    qpdf \
    && rm -rf /var/lib/apt/lists/*
# Use BuildKit cache for pip downloads/wheels to speed up rebuilds.
# Note: this requires Docker BuildKit (enabled by default in Docker Desktop).
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
COPY . /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
