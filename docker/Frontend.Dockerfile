# Build stage
FROM node:20.19 AS build

WORKDIR /app

# Copy package files
COPY src/frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY src/frontend/ .

# Build the app
RUN npm run build

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python requirements and install
COPY src/frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built assets from build stage
COPY --from=build /app/dist ./dist
COPY src/frontend/frontend_server.py .

EXPOSE 3000

CMD ["uvicorn", "frontend_server:app", "--host", "0.0.0.0", "--port", "3000"]