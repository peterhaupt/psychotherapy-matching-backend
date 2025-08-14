# Backup & Recovery Test Procedure
**Curavani Platform - Complete Disaster Recovery Documentation**

Last Updated: August 2025

---

## 📋 Daily Backup Operations

### 1.1 External Disk Rotation
- [ ] **Time**: Every day at [SPECIFY TIME]
- [ ] Remove current external disk from server
- [ ] Label with date: `BACKUP_YYYY-MM-DD`
- [ ] Connect fresh external disk
- [ ] Verify backup service recognizes new disk
- [ ] Store removed disk in secure location

### 1.2 Backup Verification
```bash
# Check backup service status
curl http://localhost:8081/health

# Trigger manual backup if needed
curl -X POST http://localhost:8081/backup

# Verify backup files exist
ls -la /backups/postgres/prod/
```

---

## 🏦 Weekly Offsite Storage

### 2.1 Bank Safe Deposit Schedule
**Every Friday:**
- [ ] Collect last 7 daily backup disks
- [ ] Document disk labels in logbook
- [ ] Transport to bank in secure case
- [ ] Store in safe deposit box
- [ ] Retrieve oldest set of disks (if rotation needed)
- [ ] Update offsite backup log

### 2.2 Backup Log Template
```
Date: ________
Disks Deposited: ________ to ________
Disks Retrieved: ________ to ________
Verified By: ________
Next Rotation: ________
```

---

## 🧹 Pre-Recovery Environment Cleanup

### 3.1 Complete VM Reset
```bash
# Connect to VM
ssh testcomputer@192.168.64.5

# Stop all containers
cd ~/curavani_backend
docker compose -f docker-compose.test.yml down
cd ~/curavani_frontend_internal
docker compose -f docker-compose.test.yml down

# List what's running (should be empty)
docker ps -a

# Nuclear cleanup - removes EVERYTHING
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker network prune -f
docker volume prune -f
docker system prune -a --volumes -f

# Verify clean state
docker ps -a      # Should show NO containers
docker volume ls  # Should show NO volumes
docker network ls # Should show only default networks

# Remove old project files
rm -rf ~/curavani_backend/*
rm -rf ~/curavani_frontend_internal/*
rm -rf ~/Recovery_Test/*
```

### 3.2 Verify Clean Database State
```bash
# Ensure no postgres data remains
docker volume ls | grep postgres
# Should return nothing

# Clear any remaining data directories
sudo rm -rf /var/lib/docker/volumes/*postgres*
```

---

## 🔄 Recovery Test Procedure

### 4.1 Transfer Recovery Files
**From Mac Host:**
```bash
# Copy all recovery files to VM
scp -r ~/Documents/Recovery_Test/* testcomputer@192.168.64.5:~/

# Verify transfer
ssh testcomputer@192.168.64.5 "ls -la ~/"
```

### 4.2 Access Linux VM
```bash
ssh testcomputer@192.168.64.5
```

### 4.3 Deploy Test Environment

#### Backend Deployment
```bash
cd ~/curavani_backend

# Create necessary Docker volumes
docker volume create curavani_backend_postgres_test_data

# Fix Makefile for bash
sed -i '1i SHELL := /bin/bash' Makefile

# Create .env.test if missing
cp .env .env.test

# Deploy backend services
make deploy-test

# If migrations fail, skip them (we'll restore from backup)
# Or run: docker compose -f docker-compose.test.yml up -d

# Verify services are running
docker ps
docker compose -f docker-compose.test.yml logs --tail=50
```

#### Frontend Deployment
```bash
cd ~/curavani_frontend_internal

# Create .dockerignore
cat > .dockerignore << 'EOF'
node_modules
npm-debug.log
build
dist
.env.local
EOF

# Fix Makefile if needed
sed -i '1i SHELL := /bin/bash' Makefile

# Deploy frontend
make deploy-test

# Verify frontend is running
docker ps | grep frontend-test
curl http://localhost:3001
```

### 4.4 Restore Backup Data

#### Locate and Copy Backup File
```bash
# Find latest backup file
ls -la ~/curavani_backend/backups/

# Copy backup file from external disk (adjust path as needed)
# Example: cp /media/backup_disk/backup_2025-08-14.sql ~/restore_backup.sql
```

#### Perform Database Restore
```bash
# Stop application services (keep database running)
cd ~/curavani_backend
docker compose -f docker-compose.test.yml stop patient_service-test therapist_service-test matching_service-test communication_service-test geocoding_service-test

# Restore database from backup
docker exec -i postgres-test psql -U postgres < ~/restore_backup.sql

# Or if backup is compressed:
gunzip < ~/restore_backup.sql.gz | docker exec -i postgres-test psql -U postgres

# Verify restore
docker exec postgres-test psql -U postgres -c "\dt"
docker exec postgres-test psql -U postgres -c "SELECT COUNT(*) FROM patients;"
docker exec postgres-test psql -U postgres -c "SELECT COUNT(*) FROM therapists;"

# Restart all services
docker compose -f docker-compose.test.yml start
```

---

## ✅ Verification Testing

### 5.1 Setup SSH Tunnels
**From Mac Host (New Terminal):**
```bash
# Create SSH tunnels for all services
ssh -L 8011:localhost:8011 -L 8012:localhost:8012 -L 8013:localhost:8013 -L 8014:localhost:8014 -L 8015:localhost:8015 testcomputer@192.168.64.5

# Keep this terminal open during testing
```

### 5.2 Manual Data Verification

#### Check Three Patients
```bash
# Patient 1 - Basic Data
curl "http://localhost:8011/api/patients/1" | jq .

# Patient 1 - Communication History
curl "http://localhost:8011/api/patients/1/communication" | jq .

# Patient 2
curl "http://localhost:8011/api/patients/2" | jq .
curl "http://localhost:8011/api/patients/2/communication" | jq .

# Patient 3
curl "http://localhost:8011/api/patients/3" | jq .
curl "http://localhost:8011/api/patients/3/communication" | jq .

# Verify emails exist
curl "http://localhost:8014/api/emails?patient_id=1" | jq .

# Verify phone calls exist
curl "http://localhost:8014/api/phone-calls?patient_id=1" | jq .
```

#### Check Three Therapists
```bash
# Therapist 1 - Basic Data
curl "http://localhost:8012/api/therapists/1" | jq .

# Therapist 1 - Communication History
curl "http://localhost:8012/api/therapists/1/communication" | jq .

# Therapist 2
curl "http://localhost:8012/api/therapists/2" | jq .
curl "http://localhost:8012/api/therapists/2/communication" | jq .

# Therapist 3
curl "http://localhost:8012/api/therapists/3" | jq .
curl "http://localhost:8012/api/therapists/3/communication" | jq .
```

#### Check Therapeutenanfragen
```bash
# List all anfragen
curl "http://localhost:8013/api/therapeutenanfragen" | jq .

# Check specific anfrage with patient details
curl "http://localhost:8013/api/therapeutenanfragen/1" | jq .
```

#### Check Platzsuchen
```bash
# List all searches
curl "http://localhost:8013/api/platzsuchen" | jq .

# Check specific search with history
curl "http://localhost:8013/api/platzsuchen/1" | jq .
```

### 5.3 Verification Checklist
- [ ] **Patients Table**: All fields present, including symptome arrays
- [ ] **Therapists Table**: All contact information intact
- [ ] **Emails Table**: Historical emails with correct status
- [ ] **Phone Calls Table**: Call history with outcomes
- [ ] **Platzsuchen Table**: Active searches with correct status
- [ ] **Therapeutenanfragen Table**: Links between therapists and patients
- [ ] **Relationships**: Foreign keys properly linked
- [ ] **Date Fields**: Correct dates for all records
- [ ] **JSONB Fields**: Complex fields (zeitliche_verfuegbarkeit, etc.) intact

---

## 📝 Documentation

### 6.1 Recovery Test Log
```
Recovery Test Date: _______________
Backup File Used: _________________
Backup Date: ______________________

Data Verification Results:
- [ ] Patients: _____ records recovered
- [ ] Therapists: _____ records recovered  
- [ ] Emails: _____ records recovered
- [ ] Phone Calls: _____ records recovered
- [ ] Platzsuchen: _____ records recovered
- [ ] Therapeutenanfragen: _____ records recovered

Issues Found:
_________________________________
_________________________________
_________________________________

Recovery Time: Start: _____ End: _____
Total Duration: _____ minutes

Tested By: _______________________
Verified By: _____________________
```

### 6.2 Success Criteria
✅ **Recovery is successful if:**
- All tables contain data
- No foreign key violations
- Application services start without errors
- API endpoints return valid data
- Complex JSONB fields are intact
- Historical data (emails, calls) is complete

❌ **Recovery fails if:**
- Missing tables or columns
- Data corruption in any field
- Services fail to start
- API returns errors
- Relationships broken between tables

---

## 🧹 Post-Test Cleanup

### 7.1 Complete Environment Reset
```bash
# Stop Docker service
sudo systemctl stop docker

# Clear Docker directory (DELETES EVERYTHING)
sudo rm -rf /var/lib/docker

# Restart Docker
sudo systemctl start docker

# Re-add yourself to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker is clean
docker ps -a
docker volume ls
docker images
```

### 7.2 Final Verification
```bash
# Should return empty results
docker ps -a
docker volume ls
docker network ls

# Ready for next recovery test
echo "Environment reset complete - ready for next test"
```

---

## 📊 Recovery Metrics

### Target Recovery Objectives
- **RTO (Recovery Time Objective)**: < 4 hours
- **RPO (Recovery Point Objective)**: < 24 hours
- **Success Rate Target**: 100%

### Tracking Template
| Date | Backup Age | Recovery Time | Success | Issues | Tester |
|------|------------|---------------|---------|--------|--------|
| | | | ✅/❌ | | |
| | | | ✅/❌ | | |
| | | | ✅/❌ | | |

---

## 🚨 Emergency Contacts

**During Recovery Issues:**
- Database Admin: _______________
- System Admin: _________________
- Backup Specialist: ____________
- Manager: ______________________

**Escalation Path:**
1. Try recovery procedure 2x
2. Contact Database Admin
3. Escalate to System Admin
4. Contact backup vendor (if applicable)

---

## 📚 Appendix

### A. Common Issues and Solutions

**Issue: Backup file not found**
- Check external disk mount point
- Verify backup naming convention
- Check backup service logs

**Issue: Database restore fails**
- Ensure postgres container is running
- Check file permissions
- Verify backup file integrity

**Issue: Services won't start after restore**
- Check Docker logs: `docker logs [container-name]`
- Verify environment variables in .env files
- Check database connections

**Issue: Missing data after restore**
- Verify backup date
- Check if backup was complete
- Review backup logs for errors

### B. Backup File Naming Convention
```
backup_[environment]_[date]_[time].sql
Example: backup_prod_2025-08-14_0200.sql
```

### C. Required Tools Checklist
- [ ] SSH access to VM
- [ ] Docker and Docker Compose
- [ ] PostgreSQL client tools
- [ ] jq for JSON formatting
- [ ] External backup disks
- [ ] Secure transport case
- [ ] Access to bank safe deposit

---

**Document Version**: 1.0  
**Last Review**: August 2025  
**Next Review**: September 2025