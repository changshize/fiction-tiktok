# Fiction TikTok Makefile

.PHONY: help setup build start stop restart logs clean test lint format

# Default target
help:
	@echo "Fiction TikTok - Novel to Multimedia Content Generation System"
	@echo ""
	@echo "Available commands:"
	@echo "  setup     - Initial setup and configuration"
	@echo "  build     - Build all Docker images"
	@echo "  start     - Start all services"
	@echo "  stop      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - View logs from all services"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  test      - Run tests"
	@echo "  lint      - Run linting"
	@echo "  format    - Format code"
	@echo "  backup    - Backup database and files"
	@echo "  restore   - Restore from backup"

# Setup and configuration
setup:
	@echo "🚀 Setting up Fiction TikTok..."
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

# Docker operations
build:
	@echo "🔨 Building Docker images..."
	@docker-compose build

start:
	@echo "▶️  Starting services..."
	@docker-compose up -d

stop:
	@echo "⏹️  Stopping services..."
	@docker-compose down

restart:
	@echo "🔄 Restarting services..."
	@docker-compose restart

# Logs and monitoring
logs:
	@echo "📋 Viewing logs..."
	@docker-compose logs -f

logs-backend:
	@docker-compose logs -f backend

logs-frontend:
	@docker-compose logs -f frontend

logs-db:
	@docker-compose logs -f postgres

# Development
dev:
	@echo "🛠️  Starting development environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Testing
test:
	@echo "🧪 Running tests..."
	@docker-compose exec backend python -m pytest tests/

test-backend:
	@docker-compose exec backend python -m pytest tests/ -v

test-frontend:
	@cd frontend && npm test

# Code quality
lint:
	@echo "🔍 Running linting..."
	@docker-compose exec backend flake8 .
	@docker-compose exec backend mypy .
	@cd frontend && npm run lint

format:
	@echo "✨ Formatting code..."
	@docker-compose exec backend black .
	@docker-compose exec backend isort .
	@cd frontend && npm run format

# Database operations
db-migrate:
	@echo "📊 Running database migrations..."
	@docker-compose exec backend alembic upgrade head

db-reset:
	@echo "🗑️  Resetting database..."
	@docker-compose exec backend alembic downgrade base
	@docker-compose exec backend alembic upgrade head

db-shell:
	@echo "💾 Opening database shell..."
	@docker-compose exec postgres psql -U postgres fiction_tiktok

# Backup and restore
backup:
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U postgres fiction_tiktok > backups/db-backup-$(shell date +%Y%m%d-%H%M%S).sql
	@tar -czf backups/data-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/
	@echo "✅ Backup created in backups/ directory"

restore:
	@echo "📥 Restoring from backup..."
	@read -p "Enter backup file path: " backup_file; \
	if [ -f "$$backup_file" ]; then \
		docker-compose exec -T postgres psql -U postgres fiction_tiktok < "$$backup_file"; \
		echo "✅ Database restored"; \
	else \
		echo "❌ Backup file not found"; \
	fi

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@docker system prune -f
	@docker volume prune -f

clean-all:
	@echo "🧹 Deep cleaning..."
	@docker-compose down -v --rmi all
	@docker system prune -af
	@docker volume prune -f

# Health checks
health:
	@echo "🏥 Checking service health..."
	@curl -f http://localhost:8000/health || echo "❌ Backend unhealthy"
	@curl -f http://localhost:3000 || echo "❌ Frontend unhealthy"
	@docker-compose exec postgres pg_isready -U postgres || echo "❌ Database unhealthy"
	@docker-compose exec redis redis-cli ping || echo "❌ Redis unhealthy"

# Production operations
prod-build:
	@echo "🏭 Building for production..."
	@docker-compose -f docker-compose.prod.yml build

prod-start:
	@echo "🚀 Starting production services..."
	@docker-compose -f docker-compose.prod.yml up -d

prod-stop:
	@echo "⏹️  Stopping production services..."
	@docker-compose -f docker-compose.prod.yml down

# SSL certificate setup
ssl-setup:
	@echo "🔒 Setting up SSL certificates..."
	@sudo certbot --nginx -d $(DOMAIN)

# Monitoring
monitor:
	@echo "📊 Starting monitoring stack..."
	@docker-compose -f docker-compose.monitoring.yml up -d

# Data operations
seed-data:
	@echo "🌱 Seeding sample data..."
	@docker-compose exec backend python scripts/seed_data.py

export-data:
	@echo "📤 Exporting data..."
	@mkdir -p exports
	@docker-compose exec backend python scripts/export_data.py

# API operations
api-docs:
	@echo "📚 Opening API documentation..."
	@open http://localhost:8000/docs

api-test:
	@echo "🧪 Testing API endpoints..."
	@docker-compose exec backend python scripts/test_api.py

# Frontend operations
frontend-build:
	@echo "🏗️  Building frontend..."
	@cd frontend && npm run build

frontend-dev:
	@echo "🛠️  Starting frontend development server..."
	@cd frontend && npm run dev

# Utility commands
shell-backend:
	@docker-compose exec backend bash

shell-frontend:
	@docker-compose exec frontend sh

shell-db:
	@docker-compose exec postgres bash

# Update dependencies
update-deps:
	@echo "📦 Updating dependencies..."
	@docker-compose exec backend pip install -r requirements.txt --upgrade
	@cd frontend && npm update

# Security scan
security-scan:
	@echo "🔒 Running security scan..."
	@docker-compose exec backend safety check
	@cd frontend && npm audit

# Performance test
perf-test:
	@echo "⚡ Running performance tests..."
	@docker-compose exec backend python scripts/performance_test.py

# Generate sample content
generate-sample:
	@echo "🎨 Generating sample content..."
	@docker-compose exec backend python scripts/generate_sample.py

# Status check
status:
	@echo "📊 Service Status:"
	@docker-compose ps
	@echo ""
	@echo "🏥 Health Status:"
	@make health
