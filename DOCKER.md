# Docker Setup

## Remote Server Deployment (Recommended)

The simplest way to deploy to a remote server using a single container.

### 1. Clone the repository on your server

```bash
git clone https://github.com/curtis-winter/audiobook-renamer.git
cd audiobook-renamer/audiobook-manager
```

### 2. Configure environment

```bash
cp .env.docker.example .env
```

Edit `.env` with your server's paths:

```bash
# Port to expose the web interface
APP_PORT=3000

# CORS origins - use * for open access
ALLOWED_ORIGINS=*
```

The host directory `/mnt/plex-media` is automatically mounted as `/mnt/media` inside the container. Use the app's Settings page to pick your watch and output folders from anywhere under `/mnt/media`.

### 3. Build and start

```bash
docker compose -f docker-compose.single.yml up -d --build
```

### 4. Access the application

Open `http://your-server-ip:3000` in your browser.

---

## Quick Start (Local Development)

```bash
docker compose -f docker-compose.single.yml up -d --build
# Access at http://localhost:3000
```

## Production Setup (Separate Containers)

For running frontend and backend in separate containers:

```bash
docker compose -f docker-compose.prod.yml up -d --build
# Frontend: http://localhost:80
# Backend:  http://localhost:8000
```

## Docker Commands

```bash
# Build images
docker compose -f docker-compose.single.yml build

# Start services
docker compose -f docker-compose.single.yml up -d

# View logs
docker compose -f docker-compose.single.yml logs -f

# Stop services
docker compose -f docker-compose.single.yml down

# Rebuild after changes
docker compose -f docker-compose.single.yml up --build -d

# Check container health
docker compose -f docker-compose.single.yml ps
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | `3000` | Port to expose the web interface |
| `ALLOWED_ORIGINS` | `*` | CORS origins (comma-separated or `*`) |
| `CONFIG_PATH` | `/config/config.json` | Path to config file inside container |
| `PYTHONUNBUFFERED` | `1` | Disable Python output buffering |

### Persistent Storage

The following data is persisted using Docker volumes:

| Volume | Description |
|--------|-------------|
| `audiobook-config` | Application configuration (templates, settings) |

### File System Mounts

Your host directories are mounted into the container:

| Host Path | Container Path | Description |
|-----------|---------------|-------------|
| `/mnt/plex-media` | `/mnt/media` | All audiobook media (use Settings in the app to pick watch/output subfolders) |

## Docker Files

| File | Description |
|------|-------------|
| `Dockerfile` | Single container with frontend + backend + nginx |
| `docker-compose.single.yml` | Single container compose (recommended) |
| `docker-compose.prod.yml` | Production setup with 2 containers |
| `nginx.docker.conf` | Nginx config for single-container mode |

## Troubleshooting

### Container won't start

```bash
docker compose -f docker-compose.single.yml logs
```

### Port already in use

```bash
# Kill existing containers
docker compose -f docker-compose.single.yml down

# Check for other processes on the port
lsof -i :3000
```

### Permission denied on mounted volumes

Ensure your host directories are accessible by the container:

```bash
# Check permissions
ls -la /path/to/your/audiobooks

# If needed, adjust permissions
chmod -R 755 /path/to/your/audiobooks
```

### Rebuild from scratch

```bash
docker compose -f docker-compose.single.yml down
docker compose -f docker-compose.single.yml build --no-cache
docker compose -f docker-compose.single.yml up -d
```

### Check container health

```bash
docker compose -f docker-compose.single.yml ps
# Should show "healthy" status

# Manual health check
curl http://localhost:3000/api/config
```
