# Deployment Guide

## Overview

This guide covers deploying Fiction TikTok to various environments including local development, staging, and production.

## Prerequisites

- Docker and Docker Compose
- Domain name (for production)
- SSL certificate (for production)
- API keys for AI services

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/changshize/fiction-tiktok.git
cd fiction-tiktok
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Required API Keys

Add these to your `.env` file:

```env
# AI Services
OPENAI_API_KEY=your_openai_key
STABLE_DIFFUSION_API_KEY=your_sd_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Social Media
TIKTOK_CLIENT_KEY=your_tiktok_key
YOUTUBE_API_KEY=your_youtube_key
INSTAGRAM_ACCESS_TOKEN=your_instagram_token

# Security
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_key
```

## Local Development

### Quick Start

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Manual Setup

```bash
# Create data directories
mkdir -p data/{novels,illustrations,audio,videos,temp}

# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### Development URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5432
- Redis: localhost:6379

## Production Deployment

### 1. Server Requirements

**Minimum:**
- 4 CPU cores
- 8GB RAM
- 100GB SSD storage
- Ubuntu 20.04+ or CentOS 8+

**Recommended:**
- 8 CPU cores
- 16GB RAM
- 500GB SSD storage
- GPU for faster AI generation (optional)

### 2. Docker Compose Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: fiction_tiktok
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/fiction_tiktok
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
    volumes:
      - ./data:/app/data
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 3. Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### 4. Deploy

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## Cloud Deployment

### AWS Deployment

#### 1. EC2 Instance

```bash
# Launch EC2 instance (t3.large or larger)
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. RDS Database

```bash
# Create RDS PostgreSQL instance
# Update DATABASE_URL in .env
DATABASE_URL=postgresql://username:password@rds-endpoint:5432/fiction_tiktok
```

#### 3. ElastiCache Redis

```bash
# Create ElastiCache Redis cluster
# Update REDIS_URL in .env
REDIS_URL=redis://elasticache-endpoint:6379
```

#### 4. S3 Storage

```bash
# Create S3 bucket for file storage
# Update .env
AWS_S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Google Cloud Platform

#### 1. Cloud Run

```bash
# Build and push images
docker build -t gcr.io/PROJECT_ID/fiction-tiktok-backend ./backend
docker build -t gcr.io/PROJECT_ID/fiction-tiktok-frontend ./frontend

docker push gcr.io/PROJECT_ID/fiction-tiktok-backend
docker push gcr.io/PROJECT_ID/fiction-tiktok-frontend

# Deploy to Cloud Run
gcloud run deploy fiction-tiktok-backend \
  --image gcr.io/PROJECT_ID/fiction-tiktok-backend \
  --platform managed \
  --region us-central1

gcloud run deploy fiction-tiktok-frontend \
  --image gcr.io/PROJECT_ID/fiction-tiktok-frontend \
  --platform managed \
  --region us-central1
```

#### 2. Cloud SQL

```bash
# Create Cloud SQL PostgreSQL instance
gcloud sql instances create fiction-tiktok-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=us-central1
```

### Kubernetes Deployment

#### 1. Kubernetes Manifests

Create `k8s/` directory with:
- `namespace.yaml`
- `configmap.yaml`
- `secret.yaml`
- `postgres.yaml`
- `redis.yaml`
- `backend.yaml`
- `frontend.yaml`
- `ingress.yaml`

#### 2. Deploy

```bash
kubectl apply -f k8s/
```

## Monitoring and Logging

### 1. Health Checks

```bash
# Backend health
curl https://your-domain.com/api/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

### 2. Logging

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Log rotation
echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3"}}' | sudo tee /etc/docker/daemon.json
```

### 3. Monitoring

Add monitoring with Prometheus and Grafana:

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Backup and Recovery

### 1. Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres fiction_tiktok > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres fiction_tiktok < backup.sql
```

### 2. File Backup

```bash
# Backup data directory
tar -czf data-backup-$(date +%Y%m%d).tar.gz data/

# Sync to S3
aws s3 sync data/ s3://your-backup-bucket/data/
```

## Security

### 1. SSL/TLS

```bash
# Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### 2. Firewall

```bash
# UFW rules
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. Environment Security

- Use strong passwords
- Rotate API keys regularly
- Enable 2FA where possible
- Regular security updates

## Scaling

### 1. Horizontal Scaling

```yaml
# Scale services
docker-compose up -d --scale backend=3 --scale frontend=2
```

### 2. Load Balancing

Use nginx or cloud load balancers to distribute traffic.

### 3. Database Scaling

- Read replicas for PostgreSQL
- Redis clustering
- Connection pooling

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Memory issues**: Increase Docker memory limits
3. **API key errors**: Verify keys in .env file
4. **Database connection**: Check DATABASE_URL format

### Debug Commands

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs service_name

# Execute commands in container
docker-compose exec backend bash

# Check resource usage
docker stats
```
