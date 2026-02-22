FROM python:3.10

WORKDIR /app
COPY . .

# System packages required for OCR and image processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8080

EXPOSE 8080

# Production server for Cloud Run
CMD exec gunicorn --bind :$PORT app:app