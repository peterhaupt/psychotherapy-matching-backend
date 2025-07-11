.PHONY: dev prod test deploy rollback backup logs-dev logs-prod stop-dev stop-prod status clean-logs

# Development commands
dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev up

stop-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev down

logs-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev logs -f

build-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev build

# Production commands
prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

stop-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod down

logs-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod logs -f

build-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod build

# Testing
test:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev exec patient_service pytest tests/integration -v

smoke-test:
	pytest ./tests/smoke -v

# Deployment
deploy:
	./scripts/deploy.sh

rollback:
	@echo "Usage: make rollback TIMESTAMP=20240115_143022"
	@[ -n "$(TIMESTAMP)" ] && ./scripts/rollback.sh $(TIMESTAMP) || echo "Error: TIMESTAMP required"

backup:
	./scripts/backup-hourly.sh

# Status and monitoring
status:
	@echo "=== Backend Development Status ==="
	@docker-compose -f docker-compose.dev.yml --env-file .env.dev ps
	@echo ""
	@echo "=== Backend Production Status ==="
	@docker-compose -f docker-compose.prod.yml --env-file .env.prod ps

status-prod:
	@docker-compose -f docker-compose.prod.yml --env-file .env.prod ps

health-check:
	@echo "Checking production health endpoints..."
	@curl -s http://localhost:8011/health | jq '.' || echo "Patient service not responding"
	@curl -s http://localhost:8012/health | jq '.' || echo "Therapist service not responding"
	@curl -s http://localhost:8013/health | jq '.' || echo "Matching service not responding"
	@curl -s http://localhost:8014/health | jq '.' || echo "Communication service not responding"
	@curl -s http://localhost:8015/health | jq '.' || echo "Geocoding service not responding"

# Database commands
db-dev:
	docker exec -it postgres psql -U curavani therapy_platform

db-prod:
	docker exec -it postgres-prod psql -U $(shell grep DB_USER .env.prod | cut -d '=' -f2) $(shell grep DB_NAME .env.prod | cut -d '=' -f2)

# Utility commands
clean-logs:
	rm -f backups/*.log
	find backups/postgres/hourly -name "*.sql.gz" -mtime +7 -delete
	find backups/postgres/weekly -name "*.sql.gz" -mtime +90 -delete

list-backups:
	@echo "=== Hourly Backups ==="
	@ls -lh backups/postgres/hourly/*.sql.gz 2>/dev/null || echo "No hourly backups found"
	@echo ""
	@echo "=== Weekly Backups ==="
	@ls -lh backups/postgres/weekly/*.sql.gz 2>/dev/null || echo "No weekly backups found"

# Docker cleanup
clean-docker:
	docker system prune -f
	docker volume prune -f

# Help
help:
	@echo "Curavani Backend Makefile Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make stop-dev     - Stop development environment"
	@echo "  make logs-dev     - View development logs"
	@echo "  make build-dev    - Build development images"
	@echo "  make db-dev       - Connect to development database"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make stop-prod    - Stop production environment"
	@echo "  make logs-prod    - View production logs"
	@echo "  make build-prod   - Build production images"
	@echo "  make db-prod      - Connect to production database"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy       - Deploy to production (with backup)"
	@echo "  make rollback TIMESTAMP=xxx - Rollback to specific backup"
	@echo "  make backup       - Create manual backup"
	@echo ""
	@echo "Monitoring:"
	@echo "  make status       - Show both dev and prod status"
	@echo "  make status-prod  - Show production status only"
	@echo "  make health-check - Check production health endpoints"
	@echo "  make list-backups - List all backups"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run integration tests"
	@echo "  make smoke-test   - Run smoke tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean-logs   - Clean old logs and backups"
	@echo "  make clean-docker - Clean Docker system"