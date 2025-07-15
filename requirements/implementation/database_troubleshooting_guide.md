# PostgreSQL Database Connection Troubleshooting Guide

## Problem Summary
PostgreSQL is receiving connection attempts for database `"curavani"` (your username) instead of `"therapy_platform"` (your configured database name).

## Step-by-Step Testing Approach

### Step 1: Verify Core Database Setup
**Location:** Root directory

```bash
# 1.1 Check your .env.dev file values
echo "DB_USER: $DB_USER"
echo "DB_NAME: $DB_NAME"
echo "DB_PASSWORD: $DB_PASSWORD"

# 1.2 Start only PostgreSQL to isolate the issue
docker-compose -f docker-compose.dev.yml up postgres -d

# 1.3 Wait 30 seconds, then check PostgreSQL logs
docker logs postgres

# 1.4 Test direct connection with correct database name
docker exec -it postgres psql -U curavani -d therapy_platform -c "SELECT current_database();"

# 1.5 List all databases to confirm therapy_platform exists
docker exec -it postgres psql -U curavani -d postgres -c "\l"
```

**What to look for:**
- ✅ therapy_platform database should exist
- ❌ No "FATAL: database curavani does not exist" errors yet

---

### Step 2: Test PgBouncer Configuration
**Location:** Root directory

```bash
# 2.1 Start PgBouncer (depends on postgres)
docker-compose -f docker-compose.dev.yml up pgbouncer -d

# 2.2 Check PgBouncer logs immediately
docker logs pgbouncer

# 2.3 Test PgBouncer connection
docker exec -it pgbouncer psql -h localhost -p 6432 -U curavani -d therapy_platform -c "SELECT current_database();"
```

**What to look for:**
- ❌ If errors appear here, the issue is in PgBouncer config
- Check for incorrect database names in PgBouncer environment variables

---

### Step 3: Check Each Microservice Directory

#### Step 3.1: Patient Service
**Location:** `./patient_service/`

```bash
# Check for database connection code
grep -r "curavani" patient_service/
grep -r "DB_NAME\|DB_USER" patient_service/ --include="*.py"
grep -r "database.*=" patient_service/ --include="*.py"

# Look for connection strings
find patient_service/ -name "*.py" -exec grep -l "psycopg\|sqlalchemy\|connect" {} \;

# Start only patient service to test
docker-compose -f docker-compose.dev.yml up patient_service -d
docker logs patient_service
```

**What to check in code:**
- Look for hardcoded database names
- Verify environment variable usage: `os.getenv('DB_NAME')` not `os.getenv('DB_USER')`
- Check connection string format

#### Step 3.2: Therapist Service
**Location:** `./therapist_service/`

```bash
# Check for database connection code
grep -r "curavani" therapist_service/
grep -r "DB_NAME\|DB_USER" therapist_service/ --include="*.py"
grep -r "database.*=" therapist_service/ --include="*.py"

# Start only therapist service
docker-compose -f docker-compose.dev.yml up therapist_service -d
docker logs therapist_service
```

#### Step 3.3: Matching Service
**Location:** `./matching_service/`

```bash
# Check for database connection code
grep -r "curavani" matching_service/
grep -r "DB_NAME\|DB_USER" matching_service/ --include="*.py"

# Start only matching service
docker-compose -f docker-compose.dev.yml up matching_service -d
docker logs matching_service
```

#### Step 3.4: Communication Service
**Location:** `./communication_service/`

```bash
# Check for database connection code
grep -r "curavani" communication_service/
grep -r "DB_NAME\|DB_USER" communication_service/ --include="*.py"

# Start only communication service
docker-compose -f docker-compose.dev.yml up communication_service -d
docker logs communication_service
```

#### Step 3.5: Geocoding Service
**Location:** `./geocoding_service/`

```bash
# Check for database connection code
grep -r "curavani" geocoding_service/
grep -r "DB_NAME\|DB_USER" geocoding_service/ --include="*.py"

# Start only geocoding service
docker-compose -f docker-compose.dev.yml up geocoding_service -d
docker logs geocoding_service
```

---

### Step 4: Check Shared Configuration
**Location:** `./shared/`

```bash
# Check shared database utilities
find shared/ -name "*.py" -exec grep -l "database\|db\|connect" {} \;
grep -r "curavani" shared/
grep -r "DB_NAME\|DB_USER" shared/ --include="*.py"

# Look for database configuration files
find shared/ -name "*config*" -o -name "*db*" -o -name "*database*"
```

---

### Step 5: Check Application Code Patterns

**Common problematic patterns to search for:**

```bash
# Search across all service directories for these patterns:

# 1. Hardcoded database names
grep -r "curavani" */

# 2. Incorrect environment variable usage
grep -r "os\.getenv.*DB_USER.*database" */
grep -r "os\.environ.*DB_USER.*database" */

# 3. Connection string issues
grep -r "postgresql://.*curavani" */
grep -r "dbname=.*curavani" */

# 4. SQLAlchemy connection issues
grep -r "create_engine.*curavani" */

# 5. Check for default database assumptions
grep -r "default.*database" */ --include="*.py"
```

---

### Step 6: Health Check Analysis

```bash
# Check health check commands in docker-compose.dev.yml
grep -A 3 -B 1 "healthcheck" docker-compose.dev.yml

# Specifically check PgBouncer health check (most likely culprit)
grep -A 5 "pgbouncer:" docker-compose.dev.yml
```

**Pay attention to:**
- PgBouncer healthcheck command
- Any health checks that don't specify database name
- Connection attempts without explicit database parameter

---

### Step 7: Isolation Testing

```bash
# Start services one by one and monitor logs
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up postgres -d
# Wait and check logs
docker-compose -f docker-compose.dev.yml up pgbouncer -d  
# Wait and check logs
docker-compose -f docker-compose.dev.yml up patient_service -d
# Check logs after each service startup
```

---

## What Each Step Should Reveal

1. **Step 1**: Confirms PostgreSQL and database `therapy_platform` work correctly
2. **Step 2**: Identifies if PgBouncer is the culprit (very likely candidate)
3. **Step 3**: Pinpoints which microservice has incorrect database connection code
4. **Step 4**: Finds shared configuration issues
5. **Step 5**: Locates specific code patterns causing the problem
6. **Step 6**: Identifies problematic health checks
7. **Step 7**: Shows exactly when the error first appears

## Expected Findings

The issue is most likely in one of these locations:
- **PgBouncer health check** in docker-compose.dev.yml
- **Application connection code** using `DB_USER` instead of `DB_NAME`
- **Shared database utility** with hardcoded database name
- **Environment variable mixing** in application code

Run these tests in order and note exactly when the `"database curavani does not exist"` error first appears. That will pinpoint the problematic component.