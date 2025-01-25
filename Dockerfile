FROM python:3.11-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY . .
RUN pip install --no-cache-dir -Ur requirements.txt

# Create a non-root user and switch to it
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the default port that will be used by most agents
EXPOSE 8001

# Start the StreamBuzz server
CMD ["uvicorn", "streambuzz:app", "--host", "0.0.0.0", "--port", "8001"]