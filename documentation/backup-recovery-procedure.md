# Backup & Recovery Test Procedure
**Curavani Platform - Complete Disaster Recovery Documentation**

Last Updated: August 2025

---

## 📋 Daily Backup Operations

### 1.1 External Disk Rotation
- [ ] **Time**: Every day as last task
- [ ] Remove current external disk
- [ ] Document in list
- [ ] Connect fresh external disk
- [ ] Verify backup service recognizes new disk
- [ ] Store removed disk in secure location

### 1.2 Backup Verification
```bash
# Check backup service status
curl http://localhost:8082/health

# Verify backup files exist
ls -la curavani_backend/backups/postgres/hourly
```

---

## 🏦 Weekly Offsite Storage

### 2.1 Bank Safe Deposit Schedule
**Every Friday:**
- [ ] Collect last daily backup disk
- [ ] Document disk labels in logbook
- [ ] Transport to bank in secure case
- [ ] Store in safe deposit box
- [ ] Retrieve disk from bank deposit
- [ ] Update offsite backup log

---

## 🧹 Pre-Recovery Environment Cleanup


### 3.1 Complete VM Reset
```bash

# Connect to VM
ssh testcomputer@192.168.64.5

# Run cleanup script
bash cleanup.sh
```
---

## 🔄 Weekly Recovery Test Procedure

### 4.1 Transfer Recovery Files
**From Mac Host:**
```bash
# Copy all recovery files to VM from separate terminal on MacOS
scp -r ~/Documents/Recovery_Test/* testcomputer@192.168.64.5:~/
```

### 4.2 Deploy Test Environment

#### Backend Deployment
```bash
cd ~/curavani_backend

# Deploy backend services
# make deploy-test cannot be used at the moment because not all tests e.g. email work properly on the VM
make build-test
make start-test
```

#### Frontend Deployment
```bash
cd ~/curavani_frontend_internal

# Deploy frontend
make deploy-test
```

### 4.4 Restore Backup Data

#### Perform Database Restore
```bash
cd ~/curavani_backend

# get list of backups
make list-backups

# restore production backup to test environment
make restore-test BACKUP=timestamp FROM=prod

# currently also needed, because makefile is not fully working on Linux VM
make start-test
```

---

## ✅ Verification Testing

### 5.1 Setup SSH Tunnels
**From Mac Host (New Terminal):**
```bash
# Create SSH tunnels for all services // needed to run front on host Mac OS
ssh -L 8011:localhost:8011 -L 8012:localhost:8012 -L 8013:localhost:8013 -L 8014:localhost:8014 -L 8015:localhost:8015 testcomputer@192.168.64.5

# Keep this terminal open during testing
```

### 5.2 Manual Data Verification

http://192.168.64.5:3001

#### Check Three Patients

#### Check Three Therapists

#### Check Therapeutenanfragen

#### Check Platzsuchen

#### Check E-Mail and Phone Calls

#### 5.3 Shut Down VM

```bash
# shut down VM
sudo shutdown -h now
```

---

## 📚 Appendix

### A. Common Issues and Solutions

**Issue: Backup file not found**
```bash
# production patient-service needs to be restarted after backup recovery
# know issue with Docker Desktop on Mac OS
docker restart patient_service-prod
```

---

**Document Version**: 1.1  
**Last Review**: August 2025  
**Next Review**: September 2025