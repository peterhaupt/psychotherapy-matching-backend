.PHONY: dev prod test deploy deploy-test rollback backup logs-dev logs-prod logs-test stop-dev stop-prod stop-test status clean-logs test-unit test-integration test-smoke test-all

# Development commands
dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev up

stop-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev down

logs-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev logs -f

build-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev build

# Test environment commands
test-start:
	docker-compose -f docker-compose.test.yml --env-file .env.test up -d

test-stop:
	docker-compose -f docker-compose.test.yml --env-file .env.test down

test-logs:
	docker-compose -f docker-compose.test.yml --env-file .env.test logs -f

test-build:
	docker-compose -f docker-compose.test.yml --env-file .env.test build

test-status:
	docker-compose -f docker-compose.test.yml --env-file .env.test ps

# Production commands
prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

stop-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod down

logs-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod logs -f

build-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod build

# Database commands
db-dev:
	docker exec -it postgres psql -U curavani therapy_platform

db-test:
	docker exec -it postgres-test psql -U $(shell grep DB_USER .env.test | cut -d '=' -f2) $(shell grep DB_NAME .env.test | cut -d '=' -f2)

db-prod:
	docker exec -it postgres-prod psql -U $(shell grep DB_USER .env.prod | cut -d '=' -f2) $(shell grep DB_NAME .env.prod | cut -d '=' -f2)

# Database migration commands
migrate-dev:
	@echo "Running Alembic migrations for development..."
	cd patient_service && alembic upgrade head

migrate-test:
	@echo "Running Alembic migrations for test environment..."
	@export $$(cat .env.test | grep -v '^#' | xargs) && \
	cd patient_service && alembic upgrade head

migrate-prod:
	@echo "Running Alembic migrations for production..."
	@export $$(cat .env.prod | grep -v '^#' | xargs) && \
	cd patient_service && alembic upgrade head

# Check if migrations are up to date
check-migrations-dev:
	@echo "Checking development database migrations..."
	cd patient_service && alembic current

check-migrations-test:
	@echo "Checking test database migrations..."
	@export $$(cat .env.test | grep -v '^#' | xargs) && \
	cd patient_service && alembic current

check-migrations-prod:
	@echo "Checking production database migrations..."
	@export $$(cat .env.prod | grep -v '^#' | xargs) && \
	cd patient_service && alembic current

# Test database management
reset-test-db:
	@echo "Resetting test database..."
	@source .env.test && \
	docker exec -it postgres-test psql -U $${DB_USER} -d postgres -c "DROP DATABASE IF EXISTS $${DB_NAME};" && \
	docker exec -it postgres-test psql -U $${DB_USER} -d postgres -c "CREATE DATABASE $${DB_NAME};" && \
	echo "Test database reset complete"

# Testing commands
test-unit:
	@echo "Running unit tests..."
	pytest tests/unit -v

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration -v

test-smoke:
	@echo "Running smoke tests..."
	pytest tests/smoke -v

test-all: test-unit test-integration test-smoke
	@echo "All tests completed"

# Test against specific environment
test-unit-dev:
	@echo "Running unit tests against development..."
	@export PATIENT_API_URL=http://localhost:8001/api && \
	export THERAPIST_API_URL=http://localhost:8002/api && \
	export MATCHING_API_URL=http://localhost:8003/api && \
	export COMMUNICATION_API_URL=http://localhost:8004/api && \
	export GEOCODING_API_URL=http://localhost:8005/api && \
	pytest tests/unit -v

test-unit-test:
	@echo "Running unit tests against test environment..."
	@export PATIENT_API_URL=http://localhost:8011/api && \
	export THERAPIST_API_URL=http://localhost:8012/api && \
	export MATCHING_API_URL=http://localhost:8013/api && \
	export COMMUNICATION_API_URL=http://localhost:8014/api && \
	export GEOCODING_API_URL=http://localhost:8015/api && \
	pytest tests/unit -v

test-integration-test:
	@echo "Running integration tests against test environment..."
	@export PATIENT_API_URL=http://localhost:8011/api && \
	export THERAPIST_API_URL=http://localhost:8012/api && \
	export MATCHING_API_URL=http://localhost:8013/api && \
	export COMMUNICATION_API_URL=http://localhost:8014/api && \
	export GEOCODING_API_URL=http://localhost:8015/api && \
	pytest tests/integration -v

test-smoke-test:
	@echo "Running smoke tests against test environment..."
	@export PATIENT_API_URL=http://localhost:8011/api && \
	export THERAPIST_API_URL=http://localhost:8012/api && \
	export MATCHING_API_URL=http://localhost:8013/api && \
	export COMMUNICATION_API_URL=http://localhost:8014/api && \
	export GEOCODING_API_URL=http://localhost:8015/api && \
	pytest tests/smoke -v

test-smoke-prod:
	@echo "Running smoke tests against production..."
	@export PATIENT_API_URL=http://localhost:8021/api && \
	export THERAPIST_API_URL=http://localhost:8022/api && \
	export MATCHING_API_URL=http://localhost:8023/api && \
	export COMMUNICATION_API_URL=http://localhost:8024/api && \
	export GEOCODING_API_URL=http://localhost:8025/api && \
	pytest tests/smoke -v

# Deployment commands
deploy-test:
	@echo "🚀 Deploying to TEST environment..."
	@echo "===================================="
	# Build test images
	$(MAKE) test-build
	# Stop test environment
	$(MAKE) test-stop
	# Start test environment
	$(MAKE) test-start
	# Wait for services to be ready
	@echo "⏳ Waiting for test services to start..."
	@sleep 15
	# Reset test database
	$(MAKE) reset-test-db
	# Run migrations
	$(MAKE) migrate-test
	# Check migrations are current
	$(MAKE) check-migrations-test
	# Run all tests
	@echo "🧪 Running all tests in test environment..."
	$(MAKE) test-unit-test
	$(MAKE) test-integration-test
	$(MAKE) test-smoke-test
	@echo "✅ Test deployment complete!"

deploy: deploy-test
	@echo ""
	@echo "🚀 TEST PASSED - Deploying to PRODUCTION..."
	@echo "==========================================="
	# Run the production deployment script
	./scripts/deploy.sh
	# Check production migrations are current
	$(MAKE) check-migrations-prod
	# Run smoke tests on production
	$(MAKE) test-smoke-prod
	@echo "✅ Full deployment complete!"

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
	@echo "=== Backend Test Status ==="
	@docker-compose -f docker-compose.test.yml --env-file .env.test ps
	@echo ""
	@echo "=== Backend Production Status ==="
	@docker-compose -f docker-compose.prod.yml --env-file .env.prod ps

status-prod:
	@docker-compose -f docker-compose.prod.yml --env-file .env.prod ps

health-check:
	@echo "Checking production health endpoints..."
	@curl -s http://localhost:8021/health | jq '.' || echo "Patient service not responding"
	@curl -s http://localhost:8022/health | jq '.' || echo "Therapist service not responding"
	@curl -s http://localhost:8023/health | jq '.' || echo "Matching service not responding"
	@curl -s http://localhost:8024/health | jq '.' || echo "Communication service not responding"
	@curl -s http://localhost:8025/health | jq '.' || echo "Geocoding service not responding"

health-check-test:
	@echo "Checking test environment health endpoints..."
	@curl -s http://localhost:8011/health | jq '.' || echo "Patient service not responding"
	@curl -s http://localhost:8012/health | jq '.' || echo "Therapist service not responding"
	@curl -s http://localhost:8013/health | jq '.' || echo "Matching service not responding"
	@curl -s http://localhost:8014/health | jq '.' || echo "Communication service not responding"
	@curl -s http://localhost:8015/health | jq '.' || echo "Geocoding service not responding"

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
	@echo "  make dev              - Start development environment"
	@echo "  make stop-dev         - Stop development environment"
	@echo "  make logs-dev         - View development logs"
	@echo "  make build-dev        - Build development images"
	@echo "  make db-dev           - Connect to development database"
	@echo "  make migrate-dev      - Run migrations on development database"
	@echo ""
	@echo "Test Environment:"
	@echo "  make test-start       - Start test environment"
	@echo "  make test-stop        - Stop test environment"
	@echo "  make test-logs        - View test logs"
	@echo "  make test-build       - Build test images"
	@echo "  make test-status      - Show test environment status"
	@echo "  make db-test          - Connect to test database"
	@echo "  make migrate-test     - Run migrations on test database"
	@echo "  make reset-test-db    - Drop and recreate test database"
	@echo ""
	@echo "Production:"
	@echo "  make prod             - Start production environment"
	@echo "  make stop-prod        - Stop production environment"
	@echo "  make logs-prod        - View production logs"
	@echo "  make build-prod       - Build production images"
	@echo "  make db-prod          - Connect to production database"
	@echo "  make migrate-prod     - Run migrations on production database"
	@echo ""
	@echo "Testing:"
	@echo "  make test-unit        - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-smoke       - Run smoke tests"
	@echo "  make test-all         - Run all tests"
	@echo "  make test-unit-test   - Run unit tests against test environment"
	@echo "  make test-smoke-prod  - Run smoke tests against production"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-test      - Deploy to test environment only"
	@echo "  make deploy           - Full deployment (test + production)"
	@echo "  make rollback TIMESTAMP=xxx - Rollback to specific backup"
	@echo "  make backup           - Create manual backup"
	@echo ""
	@echo "Monitoring:"
	@echo "  make status           - Show all environments status"
	@echo "  make status-prod      - Show production status only"
	@echo "  make health-check     - Check production health endpoints"
	@echo "  make health-check-test - Check test environment health endpoints"
	@echo "  make list-backups     - List all backups"
	@echo ""
	@echo "Database Migrations:"
	@echo "  make check-migrations-dev  - Check dev migration status"
	@echo "  make check-migrations-test - Check test migration status"
	@echo "  make check-migrations-prod - Check production migration status"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean-logs       - Clean old logs and backups"
	@echo "  make clean-docker     - Clean Docker system"