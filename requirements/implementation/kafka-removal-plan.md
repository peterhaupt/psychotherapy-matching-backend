# Kafka Removal Migration Plan
**Version:** 1.0  
**Date:** January 2025  
**Objective:** Complete removal of Apache Kafka from the microservices architecture

---

## Executive Summary

This plan outlines the systematic removal of Apache Kafka from the Curavani backend architecture, replacing event-driven communication with direct synchronous API calls. The migration focuses on three core event patterns that need replacement and ensures system consistency through blocking operations with proper error handling.

---

## Phase 1: Test Creation (Tests That Will Initially Fail)

### 1.1 Unit Tests for New API Endpoints

#### Patient Service Tests
**File:** `tests/unit/test_patient_last_contact_api.py`

```python
# Test new endpoint: PATCH /patients/{id}/last-contact
- test_update_last_contact_success()
- test_update_last_contact_patient_not_found()
- test_update_last_contact_invalid_date()
- test_update_last_contact_idempotent()
```

**File:** `tests/unit/test_patient_deletion_cascade.py`

```python
# Test deletion with Matching API cascade
- test_delete_patient_calls_matching_api()
- test_delete_patient_rollback_on_matching_failure()
- test_delete_patient_retries_on_network_error()
- test_delete_patient_blocks_on_matching_unavailable()
```

#### Therapist Service Tests
**File:** `tests/unit/test_therapist_blocking_cascade.py`

```python
# Test blocking with Matching API cascade
- test_block_therapist_calls_matching_api()
- test_block_therapist_rollback_on_matching_failure()
- test_unblock_therapist_calls_matching_api()
- test_block_therapist_retries_on_network_error()
```

#### Matching Service Tests
**File:** `tests/unit/test_matching_cascade_endpoints.py`

```python
# Test new endpoints for cascade operations
- test_cancel_searches_for_patient()
- test_handle_therapist_blocked()
- test_handle_therapist_unblocked()
- test_cascade_operations_transactional()
```

#### Communication Service Tests
**File:** `tests/unit/test_communication_patient_updates.py`

```python
# Test direct Patient API calls
- test_email_sent_updates_patient_last_contact()
- test_email_response_updates_patient_last_contact()
- test_phone_call_completed_updates_patient_last_contact()
- test_patient_api_retry_logic()
- test_patient_api_failure_handling()
```

### 1.2 Integration Tests

**File:** `tests/integration/test_kafka_removal_cascades.py`

```python
def test_patient_deletion_cascade_integration():
    """End-to-end test of patient deletion with matching cascade."""
    # 1. Create patient
    # 2. Create active search (platzsuche)
    # 3. Delete patient via API
    # 4. Verify search is cancelled
    # 5. Verify patient is deleted

def test_therapist_blocking_cascade_integration():
    """End-to-end test of therapist blocking with matching cascade."""
    # 1. Create therapist
    # 2. Create unsent anfragen
    # 3. Block therapist via API
    # 4. Verify anfragen are cancelled
    # 5. Verify therapist status is updated

def test_communication_patient_update_integration():
    """End-to-end test of communication updating patient."""
    # 1. Create patient
    # 2. Send email via Communication API
    # 3. Verify patient last_contact is updated
    # 4. Complete phone call
    # 5. Verify patient last_contact is updated again

def test_cascade_failure_rollback():
    """Test that primary operations rollback on cascade failure."""
    # 1. Shutdown Matching service
    # 2. Attempt patient deletion
    # 3. Verify deletion fails with appropriate error
    # 4. Verify patient still exists
    # 5. Start Matching service
    # 6. Retry deletion - should succeed
```

---

## Phase 2: Implementation of New Functionality

### 2.1 New API Endpoints

#### Patient Service
**Endpoint:** `PATCH /api/patients/{id}/last-contact`
```python
# patient_service/api/patients.py

class PatientLastContactResource(Resource):
    def patch(self, patient_id):
        """Update only the last contact date for a patient."""
        parser = reqparse.RequestParser()
        parser.add_argument('date', type=str, required=False)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {"message": "Patient not found"}, 404
            
            # Use provided date or today
            contact_date = args.get('date') or date.today().isoformat()
            patient.letzter_kontakt = contact_date
            
            db.commit()
            return {"message": "Last contact updated", "letzter_kontakt": contact_date}, 200
        finally:
            db.close()
```

#### Matching Service
**Endpoint:** `POST /api/matching/cascade/patient-deleted`
```python
# matching_service/api/cascade_operations.py

class PatientDeletedCascadeResource(Resource):
    def post(self):
        """Handle cascading operations for patient deletion."""
        parser = reqparse.RequestParser()
        parser.add_argument('patient_id', type=int, required=True)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Cancel all active searches for the patient
            active_searches = db.query(Platzsuche).filter(
                Platzsuche.patient_id == args['patient_id'],
                Platzsuche.status == SuchStatus.aktiv
            ).all()
            
            cancelled_count = 0
            for search in active_searches:
                search.status = SuchStatus.abgebrochen
                search.notizen = f"Cancelled: Patient deleted from system"
                cancelled_count += 1
            
            db.commit()
            return {
                "message": f"Cancelled {cancelled_count} active searches",
                "cancelled_searches": cancelled_count
            }, 200
        except Exception as e:
            db.rollback()
            return {"message": f"Failed to cancel searches: {str(e)}"}, 500
        finally:
            db.close()
```

**Endpoint:** `POST /api/matching/cascade/therapist-blocked`
```python
class TherapistBlockedCascadeResource(Resource):
    def post(self):
        """Handle cascading operations for therapist blocking."""
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int, required=True)
        parser.add_argument('reason', type=str, required=False)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Cancel unsent anfragen
            unsent_anfragen = db.query(Therapeutenanfrage).filter(
                Therapeutenanfrage.therapist_id == args['therapist_id'],
                Therapeutenanfrage.gesendet_datum.is_(None)
            ).all()
            
            cancelled_count = 0
            for anfrage in unsent_anfragen:
                anfrage.notizen = f"Cancelled: {args.get('reason', 'Therapist blocked')}"
                cancelled_count += 1
            
            # Add therapist to exclusion lists for affected patients
            # ... implementation details ...
            
            db.commit()
            return {
                "message": f"Processed therapist blocking",
                "cancelled_anfragen": cancelled_count
            }, 200
        except Exception as e:
            db.rollback()
            return {"message": f"Failed to process blocking: {str(e)}"}, 500
        finally:
            db.close()
```

**Endpoint:** `POST /api/matching/cascade/therapist-unblocked`
```python
class TherapistUnblockedCascadeResource(Resource):
    def post(self):
        """Handle cascading operations for therapist unblocking."""
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int, required=True)
        args = parser.parse_args()
        
        # Currently minimal implementation - can be extended
        return {"message": "Therapist unblocking processed"}, 200
```

### 2.2 API Client Utilities

**File:** `shared/api/retry_client.py`
```python
import requests
from time import sleep
from typing import Optional, Dict, Any

class RetryAPIClient:
    """API client with automatic retry logic."""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    @classmethod
    def call_with_retry(cls, method: str, url: str, 
                       json: Optional[Dict] = None,
                       timeout: int = 10) -> requests.Response:
        """
        Make an API call with automatic retry on failure.
        
        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Full URL to call
            json: JSON payload (optional)
            timeout: Request timeout in seconds
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException after all retries exhausted
        """
        last_exception = None
        
        for attempt in range(cls.MAX_RETRIES):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=json,
                    timeout=timeout
                )
                
                # Success or client error (4xx) - don't retry
                if response.status_code < 500:
                    return response
                    
                # Server error - will retry
                last_exception = requests.HTTPError(
                    f"Server error: {response.status_code}"
                )
                
            except requests.RequestException as e:
                last_exception = e
            
            # Wait before retry (except on last attempt)
            if attempt < cls.MAX_RETRIES - 1:
                sleep(cls.RETRY_DELAY * (attempt + 1))  # Exponential backoff
        
        # All retries exhausted
        raise last_exception
```

### 2.3 Service Modifications

#### Patient Service - Delete Operation
**File:** `patient_service/api/patients.py`
```python
from shared.api.retry_client import RetryAPIClient

class PatientResource(Resource):
    def delete(self, patient_id):
        """Delete patient with cascade to Matching service."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {"message": "Patient not found"}, 404
            
            # Call Matching service BEFORE deleting patient
            matching_url = f"{MATCHING_SERVICE_URL}/api/matching/cascade/patient-deleted"
            
            try:
                response = RetryAPIClient.call_with_retry(
                    method="POST",
                    url=matching_url,
                    json={"patient_id": patient_id}
                )
                
                if response.status_code != 200:
                    # Matching service couldn't process cascade
                    return {
                        "message": f"Cannot delete patient: Matching service error: {response.text}"
                    }, 500
                    
            except requests.RequestException as e:
                # Network or timeout error after retries
                return {
                    "message": f"Cannot delete patient: Matching service unavailable: {str(e)}"
                }, 503
            
            # Now safe to delete patient
            db.delete(patient)
            db.commit()
            
            return {"message": "Patient deleted successfully"}, 200
            
        except Exception as e:
            db.rollback()
            return {"message": f"Database error: {str(e)}"}, 500
        finally:
            db.close()
```

#### Therapist Service - Block Operation
**File:** `therapist_service/api/therapists.py`
```python
from shared.api.retry_client import RetryAPIClient

class TherapistResource(Resource):
    def put(self, therapist_id):
        """Update therapist with cascade for status changes."""
        # ... existing code ...
        
        # Check if status is changing to "gesperrt"
        if args.get('status') == 'gesperrt' and therapist.status != 'gesperrt':
            # Call Matching service BEFORE updating status
            matching_url = f"{MATCHING_SERVICE_URL}/api/matching/cascade/therapist-blocked"
            
            try:
                response = RetryAPIClient.call_with_retry(
                    method="POST",
                    url=matching_url,
                    json={
                        "therapist_id": therapist_id,
                        "reason": args.get('sperrgrund', 'Status changed to blocked')
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "message": f"Cannot block therapist: Matching service error: {response.text}"
                    }, 500
                    
            except requests.RequestException as e:
                return {
                    "message": f"Cannot block therapist: Matching service unavailable: {str(e)}"
                }, 503
        
        # Check if status is changing from "gesperrt" to "aktiv"
        elif args.get('status') == 'aktiv' and therapist.status == 'gesperrt':
            # Call Matching service for unblocking
            matching_url = f"{MATCHING_SERVICE_URL}/api/matching/cascade/therapist-unblocked"
            
            try:
                response = RetryAPIClient.call_with_retry(
                    method="POST",
                    url=matching_url,
                    json={"therapist_id": therapist_id}
                )
            except:
                pass  # Unblocking cascade is non-critical
        
        # ... continue with normal update ...
```

#### Communication Service - Patient Updates
**File:** `communication_service/api/emails.py`
```python
from shared.api.retry_client import RetryAPIClient

class EmailResource(Resource):
    def put(self, email_id):
        """Update email and notify patient service if needed."""
        # ... existing code ...
        
        # If email was sent or response received, update patient
        if email.patient_id and (
            args.get('status') == 'Gesendet' or 
            args.get('antwort_erhalten') == True
        ):
            patient_url = f"{PATIENT_SERVICE_URL}/api/patients/{email.patient_id}/last-contact"
            
            try:
                RetryAPIClient.call_with_retry(
                    method="PATCH",
                    url=patient_url,
                    json={"date": date.today().isoformat()}
                )
            except:
                # Log error but don't fail the email update
                logger.error(f"Failed to update patient last contact for patient {email.patient_id}")
        
        # ... continue with email update ...
```

**File:** `communication_service/api/phone_calls.py`
```python
class PhoneCallResource(Resource):
    def put(self, call_id):
        """Update phone call and notify patient service if needed."""
        # ... existing code ...
        
        # If call was completed, update patient
        if call.patient_id and args.get('status') == 'abgeschlossen':
            patient_url = f"{PATIENT_SERVICE_URL}/api/patients/{call.patient_id}/last-contact"
            
            try:
                RetryAPIClient.call_with_retry(
                    method="PATCH",
                    url=patient_url,
                    json={"date": date.today().isoformat()}
                )
            except:
                logger.error(f"Failed to update patient last contact for patient {call.patient_id}")
        
        # ... continue with call update ...
```

### 2.4 URL Registration

#### Patient Service
```python
# patient_service/app.py
api.add_resource(PatientLastContactResource, '/api/patients/<int:patient_id>/last-contact')
```

#### Matching Service
```python
# matching_service/app.py
api.add_resource(PatientDeletedCascadeResource, '/api/matching/cascade/patient-deleted')
api.add_resource(TherapistBlockedCascadeResource, '/api/matching/cascade/therapist-blocked')
api.add_resource(TherapistUnblockedCascadeResource, '/api/matching/cascade/therapist-unblocked')
```

---

## Phase 3: Verification - Run Tests

### 3.1 Run Unit Tests
```bash
# Run new unit tests - should all pass
pytest tests/unit/test_patient_last_contact_api.py -v
pytest tests/unit/test_patient_deletion_cascade.py -v
pytest tests/unit/test_therapist_blocking_cascade.py -v
pytest tests/unit/test_matching_cascade_endpoints.py -v
pytest tests/unit/test_communication_patient_updates.py -v
```

### 3.2 Run Integration Tests
```bash
# Run integration tests - should all pass
pytest tests/integration/test_kafka_removal_cascades.py -v
```

### 3.3 Run Existing Tests
```bash
# Ensure existing functionality still works
pytest tests/ -v
```

---

## Phase 4: Remove All Kafka Code

### 4.1 Remove Kafka Dependencies

#### Remove from requirements.txt files
```diff
# All services: requirements/requirements.txt
- kafka-python==2.0.2
- confluent-kafka==2.3.0
```

### 4.2 Remove Kafka Code Files

#### Delete Event Producers/Consumers
```bash
# In each service directory:
rm -rf patient_service/events/
rm -rf therapist_service/events/
rm -rf matching_service/events/
rm -rf communication_service/events/
rm -rf geocoding_service/events/
```

#### Delete Shared Kafka Utilities
```bash
rm -rf shared/kafka/
```

### 4.3 Remove Kafka Initialization Code

#### Patient Service
**File:** `patient_service/app.py`
```python
# REMOVE these lines:
# from events.consumers import start_consumers
# import threading

# REMOVE from if __name__ == "__main__":
# consumer_thread = threading.Thread(target=start_consumers, daemon=True)
# consumer_thread.start()
```

#### Therapist Service
**File:** `therapist_service/app.py`
```python
# REMOVE similar Kafka initialization code
```

#### Matching Service
**File:** `matching_service/app.py`
```python
# REMOVE Kafka consumers and background workers
# REMOVE follow-up call scheduler that relied on events
```

#### Communication Service
**File:** `communication_service/app.py`
```python
# REMOVE email queue processor
# REMOVE Kafka event publishers
```

### 4.4 Remove Kafka from Docker Compose

**File:** `docker-compose.dev.yml`
```yaml
# REMOVE these services entirely:
# - zookeeper
# - kafka

# REMOVE from each service's environment variables:
# - KAFKA_BOOTSTRAP_SERVERS
# - KAFKA_LOG_LEVEL

# REMOVE from each service's depends_on:
# - kafka:
#     condition: service_healthy
```

### 4.5 Remove Kafka Environment Variables

**File:** `.env`
```diff
# REMOVE all Kafka-related variables:
- KAFKA_BOOTSTRAP_SERVERS=kafka:9092
- KAFKA_LOG_LEVEL=INFO
- ZOOKEEPER_CLIENT_PORT=2181
- ZOOKEEPER_TICK_TIME=2000
- KAFKA_BROKER_ID=1
- KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
- KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9093
- KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
- KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,PLAINTEXT_HOST://0.0.0.0:9093
- KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT
- KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
- KAFKA_AUTO_CREATE_TOPICS_ENABLE=true
- ZOOKEEPER_EXTERNAL_PORT=2181
```

### 4.6 Clean Up Import Code

#### Patient Service Import Monitor
**File:** `patient_service/imports/gcs_monitor.py`
```python
# REMOVE all event publishing:
# from events.producers import publish_patient_created
# publish_patient_created(patient_id, patient_data)  # REMOVE this line
```

#### Therapist Service Import Monitor
**File:** `therapist_service/imports/file_monitor.py`
```python
# REMOVE all event publishing:
# from events.producers import publish_therapist_created
# publish_therapist_created(therapist_id, therapist_data)  # REMOVE this line
```

### 4.7 Remove Kafka Documentation

```bash
rm requirements/technical/kafka-*.md
```

---

## Phase 5: Final Verification

### 5.1 Run All Tests Again
```bash
# Full test suite should pass without Kafka
pytest tests/ -v --tb=short

# Specific verification that Kafka is gone
grep -r "kafka" . --exclude-dir=.git --exclude-dir=__pycache__ 
# Should return no results except this migration plan

grep -r "Kafka" . --exclude-dir=.git --exclude-dir=__pycache__
# Should return no results except this migration plan
```

### 5.2 Test Service Health
```bash
# Start all services locally
docker-compose -f docker-compose.dev.yml up -d

# Run health checks
pytest tests/smoke/test_health_of_all_services.py -v

# Verify no Kafka containers running
docker ps | grep kafka
# Should return empty

docker ps | grep zookeeper  
# Should return empty
```

### 5.3 Manual Integration Testing

1. **Test Patient Flow:**
   - Create patient
   - Send email to patient
   - Verify last_contact updated
   - Delete patient
   - Verify platzsuche cancelled

2. **Test Therapist Flow:**
   - Create therapist
   - Create anfragen
   - Block therapist
   - Verify anfragen cancelled
   - Unblock therapist

3. **Test Communication Flow:**
   - Send emails
   - Complete phone calls
   - Verify patient records updated

---

## Phase 6: Production Deployment

### 6.1 Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] No Kafka references in codebase
- [ ] Docker images built without Kafka
- [ ] Environment variables updated for production
- [ ] Database backups completed
- [ ] Team notified of deployment window

### 6.2 Deployment Steps

1. **Schedule Maintenance Window**
   - Duration: 30 minutes
   - Time: During low-traffic period

2. **Stop All Services**
   ```bash
   kubectl scale deployment --all --replicas=0 -n curavani-prod
   ```

3. **Deploy Database Migrations** (if any)
   ```bash
   # No database changes needed for this migration
   ```

4. **Update ConfigMaps/Secrets**
   ```bash
   # Remove Kafka-related environment variables
   kubectl apply -f k8s/configmap-prod.yaml
   ```

5. **Deploy New Service Versions**
   ```bash
   # Deploy all services simultaneously
   kubectl apply -f k8s/patient-service-deployment.yaml
   kubectl apply -f k8s/therapist-service-deployment.yaml
   kubectl apply -f k8s/matching-service-deployment.yaml
   kubectl apply -f k8s/communication-service-deployment.yaml
   kubectl apply -f k8s/geocoding-service-deployment.yaml
   ```

6. **Remove Kafka Infrastructure**
   ```bash
   kubectl delete deployment kafka -n curavani-prod
   kubectl delete deployment zookeeper -n curavani-prod
   kubectl delete service kafka -n curavani-prod
   kubectl delete service zookeeper -n curavani-prod
   kubectl delete pvc kafka-data -n curavani-prod
   kubectl delete pvc zookeeper-data -n curavani-prod
   ```

7. **Scale Services Back Up**
   ```bash
   kubectl scale deployment patient-service --replicas=3 -n curavani-prod
   kubectl scale deployment therapist-service --replicas=3 -n curavani-prod
   kubectl scale deployment matching-service --replicas=3 -n curavani-prod
   kubectl scale deployment communication-service --replicas=3 -n curavani-prod
   kubectl scale deployment geocoding-service --replicas=2 -n curavani-prod
   ```

### 6.3 Post-Deployment Verification

1. **Health Checks**
   ```bash
   # Run production health checks
   for service in patient therapist matching communication geocoding; do
     curl https://api.curavani.de/$service/health
   done
   ```

2. **Functional Tests**
   - Create test patient
   - Send test email
   - Verify cascading operations
   - Delete test patient

3. **Monitor Logs**
   ```bash
   kubectl logs -f deployment/patient-service -n curavani-prod
   kubectl logs -f deployment/matching-service -n curavani-prod
   ```

4. **Performance Metrics**
   - Monitor response times
   - Check error rates
   - Verify no message queue buildup

### 6.4 No Rollback Strategy

As specified, there is no rollback strategy. The deployment is final once completed.

**In case of critical issues:**
1. Fix forward - deploy patches
2. All services must be updated together
3. Database state remains consistent due to transactional operations

---

## Appendix A: Service Dependencies After Migration

### Direct API Dependencies Created

```
Communication Service → Patient Service (new)
Patient Service → Matching Service (new)  
Therapist Service → Matching Service (new)
```

### Service Availability Requirements

- Patient deletion requires Matching service availability
- Therapist blocking requires Matching service availability
- Communication updates gracefully degrade (log errors but continue)

---

## Appendix B: Performance Impact Analysis

### Expected Latency Changes

| Operation | Before (Async) | After (Sync) | Impact |
|-----------|---------------|--------------|---------|
| Patient Deletion | ~100ms | ~300ms | +200ms |
| Therapist Blocking | ~100ms | ~300ms | +200ms |
| Email Sent | ~50ms | ~150ms | +100ms |
| Phone Call Complete | ~50ms | ~150ms | +100ms |

### Mitigation
- All operations remain under 500ms
- User experience impact minimal
- Retry logic prevents transient failures

---

## Appendix C: Error Messages for Users

### New Error Messages

**Patient Deletion Blocked:**
```
"Cannot delete patient at this time. The matching service is temporarily unavailable. Please try again in a few minutes."
```

**Therapist Blocking Failed:**
```
"Cannot update therapist status. Related services are temporarily unavailable. Please try again later."
```

**Communication Update Failed (logged only):**
```
"Warning: Failed to update patient contact information. Manual sync may be required."
```

---

## Appendix D: Monitoring and Alerts

### New Metrics to Monitor

1. **API Call Success Rate**
   - `api_calls_total{service, endpoint, status}`
   - Alert if success rate < 95%

2. **Cascade Operation Latency**
   - `cascade_operation_duration_seconds{operation}`
   - Alert if p99 > 1 second

3. **Retry Exhaustion Rate**
   - `api_retries_exhausted_total{service, endpoint}`
   - Alert if > 10 per minute

### Log Patterns to Watch

```
ERROR: "Cannot delete patient: Matching service unavailable"
ERROR: "Cannot block therapist: Matching service error"
WARNING: "Failed to update patient last contact"
INFO: "Cascade operation completed successfully"
```

---

## Sign-off

**Prepared by:** Architecture Team  
**Reviewed by:** _________________  
**Approved by:** _________________  
**Date:** _________________

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | System | Initial plan for Kafka removal |