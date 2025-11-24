# Docker Deployment Guide

Complete guide for running Artify Content Backend with Docker.

## Quick Start

### Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Production Environment

```bash
# Build and start with production settings
docker-compose -f docker-compose.yml up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 2GB free RAM
- OpenAI API key

## Environment Variables

Create a `.env` file in the `content-backend` directory:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Database
POSTGRES_PASSWORD=your-secure-password

# Redis
REDIS_PASSWORD=your-redis-password

# Logging
LOG_LEVEL=INFO
ENABLE_JSON_LOGS=false
```

## Services

### 1. PostgreSQL Database

- **Port**: 5432
- **Database**: artify
- **User**: postgres
- **Data persistence**: Volume `postgres_data`

### 2. Redis Cache

- **Port**: 6379
- **Data persistence**: Volume `redis_data`
- **Authentication**: Password-protected (set via `REDIS_PASSWORD`)

### 3. FastAPI Application

- **Port**: 8000
- **Workers**: 4 (production)
- **Health check**: http://localhost:8000/health
- **API docs**: http://localhost:8000/docs

## Development Workflow

### Hot Reloading

Use the development compose file for auto-reload on code changes:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Accessing Containers

```bash
# App container
docker exec -it artify-backend bash

# Database
docker exec -it artify-postgres psql -U postgres -d artify

# Redis
docker exec -it artify-redis redis-cli
```

### Database Migrations

```bash
# Run migrations
docker exec artify-backend alembic upgrade head

# Create new migration
docker exec artify-backend alembic revision --autogenerate -m "Description"

# Rollback
docker exec artify-backend alembic downgrade -1
```

### Database Backup

```bash
# Backup
docker exec artify-backend /app/scripts/backup_db.sh

# List backups
docker exec artify-backend ls -lh /app/backups

# Copy backup to host
docker cp artify-backend:/app/backups/artify_backup_20250107_143022.sql.gz ./
```

### Database Restore

```bash
# Copy backup to container
docker cp ./backup.sql.gz artify-backend:/app/backups/

# Restore
docker exec -it artify-backend /app/scripts/restore_db.sh /app/backups/backup.sql.gz
```

## Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 app
```

### Log Files

Application logs are persisted in `./logs/` directory:

- `artify.log` - General application logs (rotated at 10MB)
- `error.log` - Error logs only (rotated daily)

## Monitoring

### Health Checks

```bash
# Check all services
docker-compose ps

# Check app health
curl http://localhost:8000/health

# Monitoring dashboard
curl http://localhost:8000/monitoring/dashboard
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## Scaling

### Horizontal Scaling

Scale the application service:

```bash
# Scale to 3 instances
docker-compose up -d --scale app=3

# With load balancer (requires nginx config)
# docker-compose up -d --scale app=3 nginx
```

### Vertical Scaling

Edit `docker-compose.yml` to set resource limits:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs app

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker exec artify-postgres pg_isready -U postgres

# Check DATABASE_URL
docker exec artify-backend env | grep DATABASE_URL
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker exec artify-redis redis-cli ping

# Check password
docker exec artify-redis redis-cli -a your-password ping
```

### Out of Disk Space

```bash
# Clean up unused images
docker image prune -a

# Clean up volumes (WARNING: deletes data)
docker volume prune

# Complete cleanup
docker system prune -a --volumes
```

## Production Deployment

### Security Checklist

- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set strong `REDIS_PASSWORD`
- [ ] Don't expose ports 5432 and 6379 publicly
- [ ] Use HTTPS with reverse proxy (nginx)
- [ ] Enable firewall rules
- [ ] Regular database backups
- [ ] Monitor logs for security events
- [ ] Keep Docker images updated

### Performance Optimization

```yaml
# docker-compose.yml
services:
  app:
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
    environment:
      LOG_LEVEL: WARNING
      ENABLE_JSON_LOGS: "true"
```

### SSL/TLS Setup

Use nginx reverse proxy:

```bash
# Uncomment nginx service in docker-compose.yml
# Create nginx.conf with SSL configuration
# docker-compose up -d nginx
```

## Backup Strategy

### Automated Backups

Set up cron job on host:

```bash
# Daily backup at 2 AM
0 2 * * * docker exec artify-backend /app/scripts/backup_db.sh
```

### Backup to Cloud

```bash
# AWS S3
docker exec artify-backend bash -c "cd /app/backups && aws s3 sync . s3://your-bucket/artify-backups/"

# Google Cloud Storage
docker exec artify-backend bash -c "cd /app/backups && gsutil rsync -r . gs://your-bucket/artify-backups/"
```

## Useful Commands

```bash
# Rebuild and restart
docker-compose up -d --build

# View environment variables
docker exec artify-backend env

# Execute Python commands
docker exec artify-backend python -c "import sys; print(sys.version)"

# Run tests (if available)
docker exec artify-backend pytest

# Shell access
docker exec -it artify-backend bash

# Stop and remove everything
docker-compose down -v --remove-orphans
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Redis Docker Hub](https://hub.docker.com/_/redis)
