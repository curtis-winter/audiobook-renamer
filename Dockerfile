# Build stage for frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Final stage
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libtag1-dev \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend
COPY backend/ ./backend/
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create nginx config
RUN echo 'events { worker_connections 1024; } \
http { \
    include /etc/nginx/mime.types; \
    default_type application/octet-stream; \
    server { \
        listen 80; \
        server_name localhost; \
        root /app/frontend/dist; \
        index index.html; \
        location / { \
            try_files $uri $uri/ /index.html; \
        } \
        location /api { \
            proxy_pass http://localhost:8000; \
            proxy_set_header Host $host; \
            proxy_set_header X-Real-IP $remote_addr; \
        } \
    } \
}' > /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx and backend
CMD sh -c "nginx & cd /app/backend && uvicorn main:app --host 0.0.0.0 --port 8000"