# Docker Deployment Summary

## What's Created

| File | Description |
|------|-------------|
| `Dockerfile` | Single container with frontend + backend + nginx |
| `docker-compose.single.yml` | Compose file for single container |
| `docker-compose.yml` | Development setup with 2 containers |
| `docker-compose.prod.yml` | Production setup with 2 containers |
| `DOCKER.md` | Docker documentation |

## Quick Start

```bash
# Build and run (single container)
docker-compose -f docker-compose.single.yml up -d

# Access app at http://localhost:8080
```

## Directory Structure

```
audiobook-manager/
├── Dockerfile              # Single container build
├── docker-compose.single.yml   # Single container compose
├── docker-compose.yml          # Dev compose (2 services)
├── docker-compose.prod.yml     # Prod compose (2 services)
├── DOCKER.md                  # Docker documentation
├── backend/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── package.json
└── data/
    ├── watch/             # Mount for watch folder
    └── output/            # Mount for output folder
```

## Features

- ✅ Single container with nginx reverse proxy
- ✅ Frontend served from nginx
- ✅ API requests proxied to backend
- ✅ Volume mounts for data persistence
- ✅ Hot-reload support in dev mode
- ✅ Production-ready build

## Usage

1. **Build**: `docker-compose -f docker-compose.single.yml build`
2. **Run**: `docker-compose -f docker-compose.single.yml up -d`
3. **Access**: http://localhost:8080
4. **Logs**: `docker-compose -f docker-compose.single.yml logs -f`
5. **Stop**: `docker-compose -f docker-compose.single.yml down`

## Development Mode

For development with hot-reloading:

```bash
docker-compose up -d

# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```