FROM python:3.11-slim

# This is required by the executable called by the Syntax Checker agent
RUN apt-get update && \
    apt-get install -y libicu-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
