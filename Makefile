.PHONY: start-dev start-prod start-test deploy deploy-test rollback backup logs-dev logs-prod logs-test stop-dev stop-prod stop-test status status-dev status-prod status-test clean-logs test-unit-dev test-unit-test test-unit-prod test-integration-dev test-integration-test test-integration-prod test-smoke-dev test-smoke-test test-smoke-prod test-all-dev test-all-test test-all-prod check-db-dev check-db-test check-db-prod create-db-dev create-db-test create-db-prod ensure-db-dev ensure-db-test ensure-db-prod

# Database check commands - FIXED with -d postgres
check-db-dev:
	@echo "Checking if development database exists..."
	@source .env.dev && \
	docker exec postgres psql -U $${DB_USER} -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$${DB_NAME}'" | grep -q 1 || \
	(echo "❌ Database $${DB_NAME} does not exist! Run: make create-db-dev" && exit 1)
	@echo "✅ Database exists"

check-db-test:
	@echo "Checking if test database exists..."
	@source .env.test && \
	docker exec postgres-test psql -U $${DB_USER} -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$${DB_NAME}'" | grep -q 1 || \
	(echo "❌ Database $${DB_NAME} does not exist! Run: make create-db-test" && exit 1)
	@echo "✅ Database exists"

check-db-prod:
	@echo "Checking if production database exists..."
	@source .env.prod && \
	docker exec postgres-prod psql -U $${DB_USER} -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$${DB_NAME}'" | grep -q 1 || \
	(echo "❌ Database $${DB_NAME} does not exist! Run: make create-db-prod" && exit 1)
	@echo "✅ Database exists"

# Database creation commands - Already correct with -d postgres
create-db-dev:
	@echo "Creating development database..."
	@source .env.dev && \
	docker exec postgres psql -U $${DB_USER} -d postgres -c "CREATE DATABASE $${DB_NAME};" && \
	echo "✅ Database $${DB_NAME} created successfully" || \
	echo "⚠️  Database might already exist or creation failed"

create-db-test:
	@echo "Creating test database..."
	@source .env.test && \
	docker exec postgres-test psql -U $${DB_USER} -d postgres -c "CREATE DATABASE $${DB_NAME};" && \
	echo "✅ Database $${DB_NAME} created successfully" || \
	echo "⚠️  Database might already exist or creation failed"

create-db-prod:
	@echo "Creating production database..."
	@source .env.prod && \
	docker exec postgres-prod psql -U $${DB_USER} -d postgres -c "CREATE DATABASE $${DB_NAME};" && \
	echo "✅ Database $${DB_NAME} created successfully" || \
	echo "⚠️  Database might already exist or creation failed"

# Ensure database exists commands - FIXED with -d postgres
ensure-db-dev:
	@echo "Ensuring development database exists..."
	@source .env.dev && \
	if docker exec postgres psql -U $${DB_USER} -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$${DB_NAME}'" | grep -q 1; then \
		echo "✅ Database already exists"; \
	else \
		echo "📦 Creating database..."; \
		docker exec postgres psql -U $${DB_USER} -d postgres -c "CREATE DATABASE $${DB_NAME};" && \
		echo "✅ Database created successfully"; \
	fi

ensure-db-test:
	@echo "Ensuring test database exists..."
	@source .env.test && \
	if docker exec postgres-test psql -U $${DB_USER} -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$${DB_NAME}'" | grep -q 1; then \
		echo "✅ Database already exists"; \
	else \
		echo "📦 Creating database..."; \
		docker exec postgres-test psql -U $${DB_USER} -d postgres -c "CREATE DATABASE $${DB_NAME};" && \
		echo "✅ Database created successfully"; \
	fi

ensure-db-prod:
	@echo "Ensuring production database exists..."
	@source .env.prod && \
	if docker exec postgres-prod psql -U $${DB_USER} -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$${DB_NAME}'" | grep -q 1; then \
		echo "✅ Database already exists"; \
	else \
		echo "📦 Creating database..."; \
		docker exec postgres-prod psql -U $${DB_USER} -d postgres -c "CREATE DATABASE $${DB_NAME};" && \
		echo "✅ Database created successfully"; \
	fi

# Development commands with database checks
start-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d postgres pgbouncer
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@for i in $$(seq 1 30); do \
		docker exec postgres pg_isready -U $$(grep DB_USER .env.dev | cut -d '=' -f2) > /dev/null 2>&1 && break || \
		([ $$i -eq 30 ] && echo "❌ PostgreSQL failed to start" && exit 1) || \
		sleep 1; \
	done
	@$(MAKE) ensure-db-dev
	docker-compose -f docker-compose.dev.yml --env-file .env.dev up

stop-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev down

logs-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev logs -f

build-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev build

status-dev:
	@docker-compose -f docker-compose.dev.yml --env-file .env.dev ps

health-check-dev:
	@echo "Checking development health endpoints..."
	@$(MAKE) check-db-dev
	@$(MAKE) check-migrations-dev
	@source .env.dev && \
	curl -s http://localhost:$${PATIENT_SERVICE_PORT}/health | jq '.' || echo "Patient service not responding" && \
	curl -s http://localhost:$${THERAPIST_SERVICE_PORT}/health | jq '.' || echo "Therapist service not responding" && \
	curl -s http://localhost:$${MATCHING_SERVICE_PORT}/health | jq '.' || echo "Matching service not responding" && \
	curl -s http://localhost:$${COMMUNICATION_SERVICE_PORT}/health | jq '.' || echo "Communication service not responding" && \
	curl -s http://localhost:$${GEOCODING_SERVICE_PORT}/health | jq '.' || echo "Geocoding service not responding"

# Test environment commands with database checks
start-test:
	docker-compose -f docker-compose.test.yml --env-file .env.test up -d postgres-test
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@for i in $$(seq 1 30); do \
		docker exec postgres-test pg_isready -U $$(grep DB_USER .env.test | cut -d '=' -f2) > /dev/null 2>&1 && break || \
		([ $$i -eq 30 ] && echo "❌ PostgreSQL failed to start" && exit 1) || \
		sleep 1; \
	done
	@$(MAKE) ensure-db-test
	docker-compose -f docker-compose.test.yml --env-file .env.test up -d

start-test-db-only:
	docker-compose -f docker-compose.test.yml --env-file .env.test up -d postgres-test

start-test-pgbouncer-only:
	docker-compose -f docker-compose.test.yml --env-file .env.test up -d pgbouncer-test

stop-test:
	docker-compose -f docker-compose.test.yml --env-file .env.test down

logs-test:
	docker-compose -f docker-compose.test.yml --env-file .env.test logs -f

build-test:
	docker-compose -f docker-compose.test.yml --env-file .env.test build

status-test:
	docker-compose -f docker-compose.test.yml --env-file .env.test ps

health-check-test:
	@echo "Checking test environment health endpoints..."
	@$(MAKE) check-db-test
	@$(MAKE) check-migrations-test
	@source .env.test && \
	curl -s http://localhost:$${PATIENT_SERVICE_PORT}/health | jq '.' || echo "Patient service not responding" && \
	curl -s http://localhost:$${THERAPIST_SERVICE_PORT}/health | jq '.' || echo "Therapist service not responding" && \
	curl -s http://localhost:$${MATCHING_SERVICE_PORT}/health | jq '.' || echo "Matching service not responding" && \
	curl -s http://localhost:$${COMMUNICATION_SERVICE_PORT}/health | jq '.' || echo "Communication service not responding" && \
	curl -s http://localhost:$${GEOCODING_SERVICE_PORT}/health | jq '.' || echo "Geocoding service not responding"

# Production commands with database checks
start-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d postgres-prod
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@for i in $$(seq 1 30); do \
		docker exec postgres-prod pg_isready -U $$(grep DB_USER .env.prod | cut -d '=' -f2) > /dev/null 2>&1 && break || \
		([ $$i -eq 30 ] && echo "❌ PostgreSQL failed to start" && exit 1) || \
		sleep 1; \
	done
	@$(MAKE) ensure-db-prod
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

stop-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod down

logs-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod logs -f

build-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod build

status-prod:
	@docker-compose -f docker-compose.prod.yml --env-file .env.prod ps

health-check:
	@echo "Checking production health endpoints..."
	@$(MAKE) check-db-prod
	@$(MAKE) check-migrations-prod
	@source .env.prod && \
	curl -s http://localhost:$${PATIENT_SERVICE_PORT}/health | jq '.' || echo "Patient service not responding" && \
	curl -s http://localhost:$${THERAPIST_SERVICE_PORT}/health | jq '.' || echo "Therapist service not responding" && \
	curl -s http://localhost:$${MATCHING_SERVICE_PORT}/health | jq '.' || echo "Matching service not responding" && \
	curl -s http://localhost:$${COMMUNICATION_SERVICE_PORT}/health | jq '.' || echo "Communication service not responding" && \
	curl -s http://localhost:$${GEOCODING_SERVICE_PORT}/health | jq '.' || echo "Geocoding service not responding"

# Database commands - FIXED db-dev to use environment variables
db-dev:
	docker exec -it postgres psql -U $(shell grep DB_USER .env.dev | cut -d '=' -f2) $(shell grep DB_NAME .env.dev | cut -d '=' -f2)

db-test:
	docker exec -it postgres-test psql -U $(shell grep DB_USER .env.test | cut -d '=' -f2) $(shell grep DB_NAME .env.test | cut -d '=' -f2)

db-prod:
	docker exec -it postgres-prod psql -U $(shell grep DB_USER .env.prod | cut -d '=' -f2) $(shell grep DB_NAME .env.prod | cut -d '=' -f2)

# Database migration commands - WITH SUCCESS VERIFICATION
migrate-dev:
	@echo "Running Alembic migrations for development..."
	@$(MAKE) check-db-dev
	@cd migrations && alembic upgrade head && \
	echo "✅ Migrations completed successfully" || \
	(echo "❌ Migration failed!" && exit 1)

migrate-test:
	@echo "Running Alembic migrations for test environment..."
	@$(MAKE) check-db-test
	@cd migrations && ENV=test alembic upgrade head && \
	echo "✅ Migrations completed successfully" || \
	(echo "❌ Migration failed!" && exit 1)

migrate-prod:
	@echo "Running Alembic migrations for production..."
	@$(MAKE) check-db-prod
	@cd migrations && ENV=prod alembic upgrade head && \
	echo "✅ Migrations completed successfully" || \
	(echo "❌ Migration failed!" && exit 1)

# Check if migrations are up to date - WITH BETTER ERROR HANDLING
check-migrations-dev:
	@echo "Checking development database migrations..."
	@cd migrations && alembic current || \
	echo "⚠️  Could not check migration status - database might not be migrated"

check-migrations-test:
	@echo "Checking test database migrations..."
	@cd migrations && ENV=test alembic current || \
	echo "⚠️  Could not check migration status - database might not be migrated"

check-migrations-prod:
	@echo "Checking production database migrations..."
	@cd migrations && ENV=prod alembic current || \
	echo "⚠️  Could not check migration status - database might not be migrated"

# Test database management
reset-test-db:
	@echo "Resetting test database..."
	@source .env.test && \
	docker exec -it postgres-test psql -U $${DB_USER} -d postgres -c "DROP DATABASE IF EXISTS $${DB_NAME};" && \
	docker exec -it postgres-test psql -U $${DB_USER} -d postgres -c "CREATE DATABASE $${DB_NAME};" && \
	echo "Test database reset complete"

# Development Environment Testing Commands - WITH --env=dev
test-unit-dev:
	@echo "Running unit tests against development..."
	@source .env.dev && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests/unit -v --env=dev

test-integration-dev:
	@echo "Running integration tests against development..."
	@source .env.dev && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests/integration -v --env=dev

test-smoke-dev:
	@echo "Running smoke tests against development..."
	@source .env.dev && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests/smoke -v --env=dev

test-all-dev:
	@echo "Running all tests against development..."
	@source .env.dev && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests -v --env=dev

# Test Environment Testing Commands - WITH --env=test
test-unit-test:
	@echo "Running unit tests against test environment..."
	@source .env.test && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests/unit -v --env=test

test-integration-test:
	@echo "Running integration tests against test environment..."
	@source .env.test && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests/integration -v --env=test

test-smoke-test:
	@echo "Running smoke tests against test environment..."
	@source .env.test && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests/smoke -v --env=test

test-all-test:
	@echo "Running all tests against test environment..."
	@source .env.test && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests -v --env=test

# Production Environment Testing Commands - WITH --env=prod
test-unit-prod:
	@echo "Running unit tests against production..."
	@source .env.prod && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests/unit -v --env=prod

test-integration-prod:
	@echo "Running integration tests against production..."
	@source .env.prod && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests/integration -v --env=prod

test-smoke-prod:
	@echo "Running smoke tests against production..."
	@source .env.prod && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests/smoke -v --env=prod

test-all-prod:
	@echo "Running all tests against production..."
	@source .env.prod && \
	export PATIENT_API_URL=http://localhost:$${PATIENT_SERVICE_PORT}/api && \
	export THERAPIST_API_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/api && \
	export MATCHING_API_URL=http://localhost:$${MATCHING_SERVICE_PORT}/api && \
	export COMMUNICATION_API_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/api && \
	export GEOCODING_API_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/api && \
	export PATIENT_HEALTH_URL=http://localhost:$${PATIENT_SERVICE_PORT}/health && \
	export THERAPIST_HEALTH_URL=http://localhost:$${THERAPIST_SERVICE_PORT}/health && \
	export MATCHING_HEALTH_URL=http://localhost:$${MATCHING_SERVICE_PORT}/health && \
	export COMMUNICATION_HEALTH_URL=http://localhost:$${COMMUNICATION_SERVICE_PORT}/health && \
	export GEOCODING_HEALTH_URL=http://localhost:$${GEOCODING_SERVICE_PORT}/health && \
	pytest tests -v --env=prod

# Deployment commands WITH DATABASE AND MIGRATION CHECKS
deploy-test:
	@echo "🚀 Deploying to TEST environment..."
	@echo "===================================="
	# Build test images
	$(MAKE) build-test
	# Stop test environment
	$(MAKE) stop-test
	# Start ONLY PostgreSQL first (no PgBouncer, no apps)
	@echo "🗄️  Starting PostgreSQL..."
	$(MAKE) start-test-db-only
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
	# Ensure database exists
	@$(MAKE) ensure-db-test
	# Now start PgBouncer
	@echo "🔗 Starting PgBouncer..."
	$(MAKE) start-test-pgbouncer-only
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
	$(MAKE) start-test
	# Wait for all services to be ready
	@echo "⏳ Waiting for all services to start..."
	@sleep 15
	# Run migrations WITH SUCCESS CHECK
	@echo "📊 Running database migrations..."
	@$(MAKE) migrate-test || (echo "❌ Migration failed! Aborting deployment." && exit 1)
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
	# Shutdown test environment after successful deployment
	$(MAKE) stop-test
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

# Debug target to check environment variable loading
debug-env-urls:
	@echo "=== CHECKING ENVIRONMENT VARIABLE LOADING ==="
	@echo ""
	@echo "--- DEV Environment ---"
	@source .env.dev && \
	echo "COMMUNICATION_SERVICE_PORT: $${COMMUNICATION_SERVICE_PORT}" && \
	echo "COMMUNICATION_API_URL: http://localhost:$${COMMUNICATION_SERVICE_PORT}/api"
	@echo ""
	@echo "--- TEST Environment ---"
	@source .env.test && \
	echo "COMMUNICATION_SERVICE_PORT: $${COMMUNICATION_SERVICE_PORT}" && \
	echo "COMMUNICATION_API_URL: http://localhost:$${COMMUNICATION_SERVICE_PORT}/api"
	@echo ""
	@echo "--- PROD Environment ---"
	@source .env.prod && \
	echo "COMMUNICATION_SERVICE_PORT: $${COMMUNICATION_SERVICE_PORT}" && \
	echo "COMMUNICATION_API_URL: http://localhost:$${COMMUNICATION_SERVICE_PORT}/api"
	@echo ""
	@echo "=== END ==="

# Backwards compatibility aliases
dev: start-dev
prod: start-prod

# Help
help:
	@echo "Curavani Backend Makefile Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make start-dev        - Start development environment"
	@echo "  make stop-dev         - Stop development environment"
	@echo "  make logs-dev         - View development logs"
	@echo "  make build-dev        - Build development images"
	@echo "  make status-dev       - Show development environment status"
	@echo "  make health-check-dev - Check development health endpoints"
	@echo "  make db-dev           - Connect to development database"
	@echo "  make check-db-dev     - Check if development database exists"
	@echo "  make create-db-dev    - Create development database"
	@echo "  make ensure-db-dev    - Ensure development database exists (create if needed)"
	@echo "  make migrate-dev      - Run migrations on development database"
	@echo ""
	@echo "Test Environment:"
	@echo "  make start-test       - Start test environment"
	@echo "  make start-test-db-only - Start only PostgreSQL"
	@echo "  make start-test-pgbouncer-only - Start only PgBouncer"
	@echo "  make stop-test        - Stop test environment"
	@echo "  make logs-test        - View test logs"
	@echo "  make build-test       - Build test images"
	@echo "  make status-test      - Show test environment status"
	@echo "  make health-check-test - Check test environment health endpoints"
	@echo "  make db-test          - Connect to test database"
	@echo "  make check-db-test    - Check if test database exists"
	@echo "  make create-db-test   - Create test database"
	@echo "  make ensure-db-test   - Ensure test database exists (create if needed)"
	@echo "  make migrate-test     - Run migrations on test database"
	@echo "  make reset-test-db    - Drop and recreate test database"
	@echo ""
	@echo "Production:"
	@echo "  make start-prod       - Start production environment"
	@echo "  make stop-prod        - Stop production environment"
	@echo "  make logs-prod        - View production logs"
	@echo "  make build-prod       - Build production images"
	@echo "  make status-prod      - Show production environment status"
	@echo "  make health-check     - Check production health endpoints"
	@echo "  make db-prod          - Connect to production database"
	@echo "  make check-db-prod    - Check if production database exists"
	@echo "  make create-db-prod   - Create production database"
	@echo "  make ensure-db-prod   - Ensure production database exists (create if needed)"
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
	@echo "  make status-dev       - Show development status only"
	@echo "  make status-test      - Show test status only"
	@echo "  make status-prod      - Show production status only"
	@echo "  make health-check     - Check production health endpoints"
	@echo "  make health-check-dev - Check development health endpoints"
	@echo "  make health-check-test - Check test environment health endpoints"
	@echo "  make list-backups     - List all backups"
	@echo ""
	@echo "Database Management:"
	@echo "  make check-db-dev/test/prod  - Check if database exists"
	@echo "  make create-db-dev/test/prod - Create database"
	@echo "  make ensure-db-dev/test/prod - Ensure database exists (create if needed)"
	@echo ""
	@echo "Database Migrations:"
	@echo "  make check-migrations-dev  - Check dev migration status"
	@echo "  make check-migrations-test - Check test migration status"
	@echo "  make check-migrations-prod - Check production migration status"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean-logs       - Clean old logs and backups"
	@echo "  make clean-docker     - Clean Docker system"
	@echo "  make debug-env-urls   - Debug environment variable loading"
	@echo ""
	@echo "Backwards Compatibility:"
	@echo "  make dev              - Alias for start-dev"
	@echo "  make prod             - Alias for start-prod"