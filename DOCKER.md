# Docker Setup

## Quick Start (Single Container - Recommended)

This runs both frontend and backend in a single container with nginx serving the frontend and proxying API calls:

```bash
# Build and run
docker-compose -f docker-compose.single.yml up -d

# Access the app
open http://localhost:8080
```

## Development Setup (Two Containers)

For development with hot-reloading:

```bash
# Start both services
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Production Setup (Separate Containers)

```bash
# Using production compose
docker-compose -f docker-compose.prod.yml up -d

# Frontend: http://localhost:80
# Backend: http://localhost:8000
```

## Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up --build
```

## Volume Mounts

Data folders are mounted from `./data`:
- `./data/watch` - Watch folder for new audiobooks
- `./data/output` - Output folder for processed files

## Environment Variables

- `PYTHONUNBUFFERED=1` - Ensure Python output is not buffered
- `ALLOWED_ORIGINS=*` - CORS configuration (default: allow all)

## Troubleshooting

### Container won't start
```bash
docker-compose logs
```

### Port already in use
```bash
# Kill existing containers
docker-compose down

# Check for other processes on the port
lsof -i :8080
```

### Rebuild from scratch
```bash
docker-compose down --rmi local
docker-compose build --no-cache
docker-compose up -d
```