FROM python:3.11-slim

WORKDIR /app

# Install system deps for PDF/ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (retries for flaky networks)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 300 -r requirements.txt

# Copy backend code
COPY backend/ .

# Run from backend dir so app module resolves
WORKDIR /app
ENV PYTHONPATH=/app
EXPOSE 8000

# Use PORT from env (Render, Railway, etc. set this)
ENV PORT=8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
