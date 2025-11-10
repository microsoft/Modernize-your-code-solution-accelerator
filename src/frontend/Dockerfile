# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY . .

# Build the app
RUN npm run build

# Runtime stage
# ARCHITECTURAL DECISION: Using Python/uvicorn instead of nginx for frontend serving
# Reasons:
# 1. Unified deployment model with backend (both use Python/uvicorn)
# 2. Consistent container app configuration in Azure
# 3. Simplified orchestration and monitoring
# 4. frontend_server.py may handle API proxying or server-side logic
FROM python:3.11-slim

WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built assets from build stage
COPY --from=build /app/dist ./dist
COPY frontend_server.py .

EXPOSE 3000

CMD ["uvicorn", "frontend_server:app", "--host", "0.0.0.0", "--port", "3000"]