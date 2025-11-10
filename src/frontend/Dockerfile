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
# 
# This approach provides:
# 1. Unified deployment model - both frontend/backend use identical Python/uvicorn runtime
# 2. Consistent Azure Container Apps configuration and resource management
# 3. Simplified CI/CD pipeline with single container technology stack
# 4. frontend_server.py enables API proxying, authentication, or future server-side features
# 5. Reduced operational complexity - same monitoring, logging, and scaling patterns
#
# Trade-off: Larger container size vs operational simplicity benefits
# NOTE: This architecture choice addresses maintainability through unified deployment patterns
FROM python:3.11-slim

WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built assets from build stage
COPY --from=build /app/dist ./dist
COPY frontend_server.py .

EXPOSE 3000

CMD ["uvicorn", "frontend_server:app", "--host", "0.0.0.0", "--port", "3000"]