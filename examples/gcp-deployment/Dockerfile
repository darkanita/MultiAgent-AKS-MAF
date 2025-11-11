FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY gcp_agent_wrapper.py .

# Cloud Run expects PORT environment variable
ENV PORT=8080

# Run the application
CMD ["python", "gcp_agent_wrapper.py"]
