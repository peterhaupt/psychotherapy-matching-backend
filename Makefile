.PHONY: dev prod test deploy deploy-test rollback backup logs-dev logs-prod logs-test stop-dev stop-prod stop-test status clean-logs test-unit-dev test-unit-test test-unit-prod test-integration-dev test-integration-test test-integration-prod test-smoke-dev test-smoke-test test-smoke-prod test-all-dev test-all-test test-all-prod

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

test-start-db-only:
	docker-compose -f docker-compose.test.yml --env-file .env.test up -d postgres-test

test-start-pgbouncer-only:
	docker-compose -f docker-compose.test.yml --env-file .env.test up -d pgbouncer-test

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

# Database migration commands - UPDATED FOR SIMPLE ENVIRONMENT DETECTION
migrate-dev:
	@echo "Running Alembic migrations for development..."
	cd migrations && alembic upgrade head

migrate-test:
	@echo "Running Alembic migrations for test environment..."
	cd migrations && ENV=test alembic upgrade head

migrate-prod:
	@echo "Running Alembic migrations for production..."
	cd migrations && ENV=prod alembic upgrade head

# Check if migrations are up to date - UPDATED FOR SIMPLE ENVIRONMENT DETECTION
check-migrations-dev:
	@echo "Checking development database migrations..."
	cd migrations && alembic current

check-migrations-test:
	@echo "Checking test database migrations..."
	cd migrations && ENV=test alembic current

check-migrations-prod:
	@echo "Checking production database migrations..."
	cd migrations && ENV=prod alembic current

# Test database management
reset-test-db:
	@echo "Resetting test database..."
	@source .env.test && \
	docker exec -it postgres-test psql -U $${DB_USER} -d postgres -c "DROP DATABASE IF EXISTS $${DB_NAME};" && \
	docker exec -it postgres-test psql -U $${DB_USER} -d postgres -c "CREATE DATABASE $${DB_NAME};" && \
	echo "Test database reset complete"

# Development Environment Testing Commands
test-unit-dev:
	@echo "Running unit tests against development..."
	@export PATIENT_API_URL=http://localhost:8001/api && \
	export THERAPIST_API_URL=http://localhost:8002/api && \
	export MATCHING_API_URL=http://localhost:8003/api && \
	export COMMUNICATION_API_URL=http://localhost:8004/api && \
	export GEOCODING_API_URL=http://localhost:8005/api && \
	export PATIENT_HEALTH_URL=http://localhost:8001/health && \
	export THERAPIST_HEALTH_URL=http://localhost:8002/health && \
	export MATCHING_HEALTH_URL=http://localhost:8003/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:8004/health && \
	export GEOCODING_HEALTH_URL=http://localhost:8005/health && \
	pytest tests/unit -v

test-integration-dev:
	@echo "Running integration tests against development..."
	@export PATIENT_API_URL=http://localhost:8001/api && \
	export THERAPIST_API_URL=http://localhost:8002/api && \
	export MATCHING_API_URL=http://localhost:8003/api && \
	export COMMUNICATION_API_URL=http://localhost:8004/api && \
	export GEOCODING_API_URL=http://localhost:8005/api && \
	export PATIENT_HEALTH_URL=http://localhost:8001/health && \
	export THERAPIST_HEALTH_URL=http://localhost:8002/health && \
	export MATCHING_HEALTH_URL=http://localhost:8003/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:8004/health && \
	export GEOCODING_HEALTH_URL=http://localhost:8005/health && \
	pytest tests/integration -v

test-smoke-dev:
	@echo "Running smoke tests against development..."
	@export PATIENT_API_URL=http://localhost:8001/api && \
	export THERAPIST_API_URL=http://localhost:8002/api && \
	export MATCHING_API_URL=http://localhost:8003/api && \
	export COMMUNICATION_API_URL=http://localhost:8004/api && \
	export GEOCODING_API_URL=http://localhost:8005/api && \
	export PATIENT_HEALTH_URL=http://localhost:8001/health && \
	export THERAPIST_HEALTH_URL=http://localhost:8002/health && \
	export MATCHING_HEALTH_URL=http://localhost:8003/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:8004/health && \
	export GEOCODING_HEALTH_URL=http://localhost:8005/health && \
	pytest tests/smoke -v

test-all-dev: test-unit-dev test-integration-dev test-smoke-dev
	@echo "All development tests completed"

# Test Environment Testing Commands
test-unit-test:
	@echo "Running unit tests against test environment..."
	@export PATIENT_API_URL=http://localhost:8011/api && \
	export THERAPIST_API_URL=http://localhost:8012/api && \
	export MATCHING_API_URL=http://localhost:8013/api && \
	export COMMUNICATION_API_URL=http://localhost:8014/api && \
	export GEOCODING_API_URL=http://localhost:8015/api && \
	export PATIENT_HEALTH_URL=http://localhost:8011/health && \
	export THERAPIST_HEALTH_URL=http://localhost:8012/health && \
	export MATCHING_HEALTH_URL=http://localhost:8013/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:8014/health && \
	export GEOCODING_HEALTH_URL=http://localhost:8015/health && \
	pytest tests/unit -v

test-integration-test:
	@echo "Running integration tests against test environment..."
	@export PATIENT_API_URL=http://localhost:8011/api && \
	export THERAPIST_API_URL=http://localhost:8012/api && \
	export MATCHING_API_URL=http://localhost:8013/api && \
	export COMMUNICATION_API_URL=http://localhost:8014/api && \
	export GEOCODING_API_URL=http://localhost:8015/api && \
	export PATIENT_HEALTH_URL=http://localhost:8011/health && \
	export THERAPIST_HEALTH_URL=http://localhost:8012/health && \
	export MATCHING_HEALTH_URL=http://localhost:8013/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:8014/health && \
	export GEOCODING_HEALTH_URL=http://localhost:8015/health && \
	pytest tests/integration -v

test-smoke-test:
	@echo "Running smoke tests against test environment..."
	@export PATIENT_API_URL=http://localhost:8011/api && \
	export THERAPIST_API_URL=http://localhost:8012/api && \
	export MATCHING_API_URL=http://localhost:8013/api && \
	export COMMUNICATION_API_URL=http://localhost:8014/api && \
	export GEOCODING_API_URL=http://localhost:8015/api && \
	export PATIENT_HEALTH_URL=http://localhost:8011/health && \
	export THERAPIST_HEALTH_URL=http://localhost:8012/health && \
	export MATCHING_HEALTH_URL=http://localhost:8013/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:8014/health && \
	export GEOCODING_HEALTH_URL=http://localhost:8015/health && \
	pytest tests/smoke -v

test-all-test: test-unit-test test-integration-test test-smoke-test
	@echo "All test environment tests completed"

# Production Environment Testing Commands
test-unit-prod:
	@echo "Running unit tests against production..."
	@export PATIENT_API_URL=http://localhost:8021/api && \
	export THERAPIST_API_URL=http://localhost:8022/api && \
	export MATCHING_API_URL=http://localhost:8023/api && \
	export COMMUNICATION_API_URL=http://localhost:8024/api && \
	export GEOCODING_API_URL=http://localhost:8025/api && \
	export PATIENT_HEALTH_URL=http://localhost:8021/health && \
	export THERAPIST_HEALTH_URL=http://localhost:8022/health && \
	export MATCHING_HEALTH_URL=http://localhost:8023/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:8024/health && \
	export GEOCODING_HEALTH_URL=http://localhost:8025/health && \
	pytest tests/unit -v

test-integration-prod:
	@echo "Running integration tests against production..."
	@export PATIENT_API_URL=http://localhost:8021/api && \
	export THERAPIST_API_URL=http://localhost:8022/api && \
	export MATCHING_API_URL=http://localhost:8023/api && \
	export COMMUNICATION_API_URL=http://localhost:8024/api && \
	export GEOCODING_API_URL=http://localhost:8025/api && \
	export PATIENT_HEALTH_URL=http://localhost:8021/health && \
	export THERAPIST_HEALTH_URL=http://localhost:8022/health && \
	export MATCHING_HEALTH_URL=http://localhost:8023/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:8024/health && \
	export GEOCODING_HEALTH_URL=http://localhost:8025/health && \
	pytest tests/integration -v

test-smoke-prod:
	@echo "Running smoke tests against production..."
	@export PATIENT_API_URL=http://localhost:8021/api && \
	export THERAPIST_API_URL=http://localhost:8022/api && \
	export MATCHING_API_URL=http://localhost:8023/api && \
	export COMMUNICATION_API_URL=http://localhost:8024/api && \
	export GEOCODING_API_URL=http://localhost:8025/api && \
	export PATIENT_HEALTH_URL=http://localhost:8021/health && \
	export THERAPIST_HEALTH_URL=http://localhost:8022/health && \
	export MATCHING_HEALTH_URL=http://localhost:8023/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:8024/health && \
	export GEOCODING_HEALTH_URL=http://localhost:8025/health && \
	pytest tests/smoke -v

test-all-prod: test-unit-prod test-integration-prod test-smoke-prod
	@echo "All production tests completed"

# Deployment commands
deploy-test:
	@echo "🚀 Deploying to TEST environment..."
	@echo "===================================="
	# Build test images
	$(MAKE) test-build
	# Stop test environment
	$(MAKE) test-stop
	# Start ONLY PostgreSQL first (no PgBouncer, no apps)
	@echo "🗄️  Starting PostgreSQL..."
	$(MAKE) test-start-db-only
	# Wait for PostgreSQL to be ready
	@echo "⏳ Waiting for PostgreSQL to start..."
	@sleep 10
	@echo "🔍 Verifying PostgreSQL connection..."
	@for i in $$(seq 1 30); do \
		if docker exec postgres-test pg_isready -U $$(grep DB_USER .env.test | cut -d '=' -f2) > /dev/null 2>&1; then \
			echo "✅ PostgreSQL is ready"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "❌ PostgreSQL failed to start after 30 attempts"; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	# Reset test database (now 100% safe - no PgBouncer, no app connections)
	@echo "🔄 Resetting test database..."
	$(MAKE) reset-test-db
	# Now start PgBouncer
	@echo "🔗 Starting PgBouncer..."
	$(MAKE) test-start-pgbouncer-only
	# Wait for PgBouncer to be ready
	@echo "⏳ Waiting for PgBouncer to start..."
	@sleep 5
	@echo "🔍 Verifying PgBouncer connection..."
	@for i in $$(seq 1 30); do \
		if docker exec pgbouncer-test sh -c "PGPASSWORD=$$(grep DB_PASSWORD .env.test | cut -d '=' -f2) /opt/bitnami/postgresql/bin/psql -h localhost -p $$(grep PGBOUNCER_PORT .env.test | cut -d '=' -f2) -U $$(grep DB_USER .env.test | cut -d '=' -f2) -d $$(grep DB_NAME .env.test | cut -d '=' -f2) -c 'SELECT 1'" > /dev/null 2>&1; then \
			echo "✅ PgBouncer is ready"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "❌ PgBouncer failed to start after 30 attempts"; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	# Now start ALL services (PostgreSQL and PgBouncer already running, adds apps)
	@echo "🚀 Starting all application services..."
	$(MAKE) test-start
	# Wait for all services to be ready
	@echo "⏳ Waiting for all services to start..."
	@sleep 15
	# Run migrations
	@echo "📊 Running database migrations..."
	$(MAKE) migrate-test
	# Check migrations are current
	$(MAKE) check-migrations-test
	# Run all tests
	@echo "🧪 Running all tests in test environment..."
	$(MAKE) test-all-test
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
	@echo "  make test-start-db-only - Start only PostgreSQL"
	@echo "  make test-start-pgbouncer-only - Start only PgBouncer"
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
	@echo "Testing - Development Environment:"
	@echo "  make test-unit-dev        - Run unit tests against dev (ports 8001-8005)"
	@echo "  make test-integration-dev - Run integration tests against dev"
	@echo "  make test-smoke-dev       - Run smoke tests against dev"
	@echo "  make test-all-dev         - Run all tests against dev"
	@echo ""
	@echo "Testing - Test Environment:"
	@echo "  make test-unit-test        - Run unit tests against test env (ports 8011-8015)"
	@echo "  make test-integration-test - Run integration tests against test env"
	@echo "  make test-smoke-test       - Run smoke tests against test env"
	@echo "  make test-all-test         - Run all tests against test env"
	@echo ""
	@echo "Testing - Production Environment:"
	@echo "  make test-unit-prod        - Run unit tests against prod (ports 8021-8025)"
	@echo "  make test-integration-prod - Run integration tests against prod"
	@echo "  make test-smoke-prod       - Run smoke tests against prod"
	@echo "  make test-all-prod         - Run all tests against prod"
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