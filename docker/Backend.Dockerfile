FROM python:3.11-slim

# This is required by the executable called by the Syntax Checker agent
RUN apt-get update && \
apt-get install -y libicu-dev

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY src/backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY src/backend/ .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
