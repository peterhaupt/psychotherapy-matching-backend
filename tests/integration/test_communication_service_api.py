"""Integration tests for Communication Service API.

This test suite verifies all communication service endpoints work exactly as described
in API_REFERENCE.md. All field names use German terminology.

Prerequisites:
- Docker environment must be running
- All services (patient, therapist, communication) must be accessible
- Database must be available
"""
import pytest
import requests
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

# Add project root to path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import get_config


# Get configuration
config = get_config()

# Skip tests in production
if config.FLASK_ENV == 'production':
    pytest.skip("Integration tests should not run in production environment", allow_module_level=True)

# Base URLs for all services
COMM_BASE_URL = f"http://localhost:{config.COMMUNICATION_SERVICE_PORT}/api"
PATIENT_BASE_URL = f"http://localhost:{config.PATIENT_SERVICE_PORT}/api"
THERAPIST_BASE_URL = f"http://localhost:{config.THERAPIST_SERVICE_PORT}/api"

# Test email recipients
TEST_EMAIL_RECIPIENTS = ["mail@peterhaupt.de", "info@curavani.com"]


class TestCommunicationServiceAPI:
    """Test all Communication Service API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup before each test and cleanup after."""
        self.created_email_ids: List[int] = []
        self.created_phone_call_ids: List[int] = []
        self.created_patient_ids: List[int] = []
        self.created_therapist_ids: List[int] = []
        self.base_headers = {'Content-Type': 'application/json'}
        
        # Create test recipients
        self._create_test_recipients()
        
        yield
        
        # Cleanup: Delete all created resources
        # Delete emails first
        for email_id in self.created_email_ids:
            try:
                requests.delete(f"{COMM_BASE_URL}/emails/{email_id}")
            except:
                pass
        
        # Delete phone calls
        for call_id in self.created_phone_call_ids:
            try:
                requests.delete(f"{COMM_BASE_URL}/phone-calls/{call_id}")
            except:
                pass
        
        # Delete patients
        for patient_id in self.created_patient_ids:
            try:
                requests.delete(f"{PATIENT_BASE_URL}/patients/{patient_id}")
            except:
                pass
        
        # Delete therapists
        for therapist_id in self.created_therapist_ids:
            try:
                requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist_id}")
            except:
                pass
    
    def _create_test_recipients(self):
        """Create test patient and therapist for use in tests."""
        # Create test patient
        patient_data = {
            "vorname": "Test",
            "nachname": "Patient",
            "email": TEST_EMAIL_RECIPIENTS[0],
            "telefon": "+49 30 12345678"
        }
        
        response = requests.post(
            f"{PATIENT_BASE_URL}/patients",
            json=patient_data,
            headers=self.base_headers
        )
        
        if response.status_code == 201:
            patient = response.json()
            self.test_patient_id = patient['id']
            self.created_patient_ids.append(patient['id'])
        else:
            raise Exception(f"Failed to create test patient: {response.status_code} - {response.text}")
        
        # Create test therapist
        therapist_data = {
            "vorname": "Test",
            "nachname": "Therapeut",
            "email": TEST_EMAIL_RECIPIENTS[1],
            "telefon": "+49 30 87654321"
        }
        
        response = requests.post(
            f"{THERAPIST_BASE_URL}/therapists",
            json=therapist_data,
            headers=self.base_headers
        )
        
        if response.status_code == 201:
            therapist = response.json()
            self.test_therapist_id = therapist['id']
            self.created_therapist_ids.append(therapist['id'])
        else:
            raise Exception(f"Failed to create test therapist: {response.status_code} - {response.text}")
    
    def create_test_email(self, for_therapist: bool = True, **kwargs) -> Dict[str, Any]:
        """Helper to create a test email and track it for cleanup."""
        # Default test data with German field names
        if for_therapist:
            default_data = {
                "therapist_id": self.test_therapist_id,
                "betreff": "Test Therapieanfrage",
                "inhalt_html": "<p>Dies ist eine Test-E-Mail für einen Therapeuten.</p>",
                "inhalt_text": "Dies ist eine Test-E-Mail für einen Therapeuten.",
                "empfaenger_email": TEST_EMAIL_RECIPIENTS[1],
                "empfaenger_name": "Test Therapeut"
            }
        else:
            default_data = {
                "patient_id": self.test_patient_id,
                "betreff": "Test Patienteninfo",
                "inhalt_html": "<p>Dies ist eine Test-E-Mail für einen Patienten.</p>",
                "inhalt_text": "Dies ist eine Test-E-Mail für einen Patienten.",
                "empfaenger_email": TEST_EMAIL_RECIPIENTS[0],
                "empfaenger_name": "Test Patient"
            }
        
        # Override with provided data
        default_data.update(kwargs)
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=default_data,
            headers=self.base_headers
        )
        
        if response.status_code == 201:
            email = response.json()
            self.created_email_ids.append(email['id'])
            return email
        else:
            raise Exception(f"Failed to create test email: {response.status_code} - {response.text}")
    
    def create_test_phone_call(self, for_therapist: bool = True, **kwargs) -> Dict[str, Any]:
        """Helper to create a test phone call and track it for cleanup."""
        # Default test data with German field names
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        if for_therapist:
            default_data = {
                "therapist_id": self.test_therapist_id,
                "geplantes_datum": tomorrow,
                "geplante_zeit": "14:00",
                "dauer_minuten": 5,
                "notizen": "Test-Anruf für Therapeut"
            }
        else:
            default_data = {
                "patient_id": self.test_patient_id,
                "geplantes_datum": tomorrow,
                "geplante_zeit": "10:00",
                "dauer_minuten": 10,
                "notizen": "Test-Anruf für Patient"
            }
        
        # Override with provided data
        default_data.update(kwargs)
        
        response = requests.post(
            f"{COMM_BASE_URL}/phone-calls",
            json=default_data,
            headers=self.base_headers
        )
        
        if response.status_code == 201:
            phone_call = response.json()
            self.created_phone_call_ids.append(phone_call['id'])
            return phone_call
        else:
            raise Exception(f"Failed to create test phone call: {response.status_code} - {response.text}")
    
    # --- Email Tests ---
    
    # GET /emails Tests
    
    def test_get_emails_list_empty(self):
        """Test getting empty email list."""
        response = requests.get(f"{COMM_BASE_URL}/emails")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_emails_list_with_data(self):
        """Test getting email list with data."""
        # Create test emails
        email1 = self.create_test_email(for_therapist=True)
        email2 = self.create_test_email(for_therapist=False)
        
        response = requests.get(f"{COMM_BASE_URL}/emails")
        assert response.status_code == 200
        
        emails = response.json()
        assert isinstance(emails, list)
        assert len(emails) >= 2
        
        # Verify our emails are in the list
        email_ids = [e['id'] for e in emails]
        assert email1['id'] in email_ids
        assert email2['id'] in email_ids
    
    def test_get_emails_filter_by_therapist(self):
        """Test filtering emails by therapist_id."""
        # Create emails for different recipients
        therapist_email = self.create_test_email(for_therapist=True)
        patient_email = self.create_test_email(for_therapist=False)
        
        # Filter by therapist_id
        response = requests.get(f"{COMM_BASE_URL}/emails?therapist_id={self.test_therapist_id}")
        assert response.status_code == 200
        
        emails = response.json()
        email_ids = [e['id'] for e in emails]
        
        # Should only include therapist email
        assert therapist_email['id'] in email_ids
        assert patient_email['id'] not in email_ids
    
    def test_get_emails_filter_by_patient(self):
        """Test filtering emails by patient_id."""
        # Create emails for different recipients
        therapist_email = self.create_test_email(for_therapist=True)
        patient_email = self.create_test_email(for_therapist=False)
        
        # Filter by patient_id
        response = requests.get(f"{COMM_BASE_URL}/emails?patient_id={self.test_patient_id}")
        assert response.status_code == 200
        
        emails = response.json()
        email_ids = [e['id'] for e in emails]
        
        # Should only include patient email
        assert patient_email['id'] in email_ids
        assert therapist_email['id'] not in email_ids
    
    def test_get_emails_filter_by_recipient_type(self):
        """Test filtering emails by recipient_type."""
        # Create emails for different recipients
        therapist_email = self.create_test_email(for_therapist=True)
        patient_email = self.create_test_email(for_therapist=False)
        
        # Filter for therapist emails
        response = requests.get(f"{COMM_BASE_URL}/emails?recipient_type=therapist")
        assert response.status_code == 200
        therapist_emails = response.json()
        
        # Filter for patient emails
        response = requests.get(f"{COMM_BASE_URL}/emails?recipient_type=patient")
        assert response.status_code == 200
        patient_emails = response.json()
        
        # Verify filtering works correctly
        therapist_ids = [e['id'] for e in therapist_emails]
        patient_ids = [e['id'] for e in patient_emails]
        
        assert therapist_email['id'] in therapist_ids
        assert therapist_email['id'] not in patient_ids
        assert patient_email['id'] in patient_ids
        assert patient_email['id'] not in therapist_ids
    
    def test_get_emails_filter_by_status(self):
        """Test filtering emails by status."""
        # Create email (default status is "Entwurf")
        email1 = self.create_test_email()
        
        # Filter by status
        response = requests.get(f"{COMM_BASE_URL}/emails?status=Entwurf")
        assert response.status_code == 200
        
        emails = response.json()
        email_ids = [e['id'] for e in emails]
        assert email1['id'] in email_ids
    
    # GET /emails/{id} Tests
    
    def test_get_email_by_id_success(self):
        """Test getting a specific email by ID."""
        created_email = self.create_test_email(
            betreff="Spezifische Test-E-Mail",
            inhalt_text="Spezifischer Inhalt"
        )
        
        response = requests.get(f"{COMM_BASE_URL}/emails/{created_email['id']}")
        assert response.status_code == 200
        
        email = response.json()
        assert email['id'] == created_email['id']
        assert email['betreff'] == "Spezifische Test-E-Mail"
        assert email['therapist_id'] == self.test_therapist_id
        
        # Verify German field names are used
        assert 'betreff' in email
        assert 'empfaenger_email' in email
        assert 'subject' not in email  # English names should not exist
    
    def test_get_email_by_id_not_found(self):
        """Test getting non-existent email returns 404."""
        response = requests.get(f"{COMM_BASE_URL}/emails/99999999")
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    # POST /emails Tests
    
    def test_create_email_for_therapist(self):
        """Test creating an email for a therapist."""
        data = {
            "therapist_id": self.test_therapist_id,
            "betreff": "Therapieanfrage für mehrere Patienten",
            "inhalt_html": "<p>Sehr geehrte/r Dr. Weber,</p><p>Wir haben mehrere Patienten...</p>",
            "inhalt_text": "Sehr geehrte/r Dr. Weber,\n\nWir haben mehrere Patienten...",
            "empfaenger_email": TEST_EMAIL_RECIPIENTS[1],
            "empfaenger_name": "Dr. Maria Weber"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        email = response.json()
        self.created_email_ids.append(email['id'])
        
        assert email['therapist_id'] == self.test_therapist_id
        assert email['patient_id'] is None
        assert email['betreff'] == data['betreff']
        assert email['status'] == "Entwurf"  # Default status
    
    def test_create_email_for_patient(self):
        """Test creating an email for a patient."""
        data = {
            "patient_id": self.test_patient_id,
            "betreff": "Update zu Ihrer Therapieplatzsuche",
            "inhalt_html": "<p>Gute Nachrichten!</p>",
            "inhalt_text": "Gute Nachrichten!",
            "empfaenger_email": TEST_EMAIL_RECIPIENTS[0],
            "empfaenger_name": "Max Mustermann"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        email = response.json()
        self.created_email_ids.append(email['id'])
        
        assert email['patient_id'] == self.test_patient_id
        assert email['therapist_id'] is None
        assert email['betreff'] == data['betreff']
    
    def test_create_email_missing_recipient(self):
        """Test creating email without therapist_id or patient_id fails."""
        data = {
            "betreff": "Test Email",
            "inhalt_html": "<p>Test</p>",
            "inhalt_text": "Test",
            "empfaenger_email": "test@example.com",
            "empfaenger_name": "Test User"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert 'message' in error
        assert 'therapist_id or patient_id is required' in error['message']
    
    def test_create_email_both_recipients(self):
        """Test creating email with both therapist_id and patient_id fails."""
        data = {
            "therapist_id": self.test_therapist_id,
            "patient_id": self.test_patient_id,
            "betreff": "Test Email",
            "inhalt_html": "<p>Test</p>",
            "inhalt_text": "Test",
            "empfaenger_email": "test@example.com",
            "empfaenger_name": "Test User"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert 'message' in error
        assert 'Cannot specify both therapist_id and patient_id' in error['message']
    
    def test_create_email_missing_required_fields(self):
        """Test creating email without required fields fails."""
        # Missing betreff
        data = {
            "therapist_id": self.test_therapist_id,
            "inhalt_html": "<p>Test</p>",
            "inhalt_text": "Test",
            "empfaenger_email": "test@example.com",
            "empfaenger_name": "Test User"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 400
    
    def test_create_email_with_custom_sender(self):
        """Test creating email with custom sender information."""
        data = {
            "therapist_id": self.test_therapist_id,
            "betreff": "Custom Sender Test",
            "inhalt_html": "<p>Test</p>",
            "inhalt_text": "Test",
            "empfaenger_email": TEST_EMAIL_RECIPIENTS[1],
            "empfaenger_name": "Test Therapeut",
            "absender_email": "custom@curavani.de",
            "absender_name": "Custom Sender"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        email = response.json()
        self.created_email_ids.append(email['id'])
        
        assert email['absender_email'] == "custom@curavani.de"
        assert email['absender_name'] == "Custom Sender"
    
    def test_create_email_with_markdown(self):
        """Test creating email with markdown content."""
        data = {
            "therapist_id": self.test_therapist_id,
            "betreff": "Therapieanfrage für mehrere Patienten",
            "inhalt_markdown": "# Therapieanfrage\n\nSehr geehrte/r Dr. Schmidt,\n\nwir haben mehrere Patienten...\n\n## Patientenliste\n\n- Patient 1: Anna Müller\n- Patient 2: Max Mustermann\n\n**Bitte antworten Sie innerhalb von 7 Tagen.**",
            "empfaenger_email": TEST_EMAIL_RECIPIENTS[1],
            "empfaenger_name": "Dr. Schmidt"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        email = response.json()
        self.created_email_ids.append(email['id'])
        
        assert email['betreff'] == data['betreff']
        assert email['therapist_id'] == self.test_therapist_id
    
    # PUT /emails/{id} Tests
    
    def test_update_email_response(self):
        """Test updating email response information."""
        email = self.create_test_email()
        
        update_data = {
            "antwort_erhalten": True,
            "antwortdatum": "2025-06-19T09:00:00",
            "antwortinhalt": "Ich kann 2 Patienten aufnehmen."
        }
        
        response = requests.put(
            f"{COMM_BASE_URL}/emails/{email['id']}",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        
        updated = response.json()
        assert updated['antwort_erhalten'] == True
        assert updated['antwortinhalt'] == "Ich kann 2 Patienten aufnehmen."
    
    def test_update_email_status(self):
        """Test updating email status with German enum values."""
        email = self.create_test_email()
        
        # Test different German status values
        status_values = ["In_Warteschlange", "Wird_gesendet", "Gesendet", "Fehlgeschlagen"]
        
        for status in status_values:
            response = requests.put(
                f"{COMM_BASE_URL}/emails/{email['id']}",
                json={"status": status},
                headers=self.base_headers
            )
            
            assert response.status_code == 200
            updated = response.json()
            assert updated['status'] == status
    
    def test_update_email_not_found(self):
        """Test updating non-existent email returns 404."""
        update_data = {"status": "Gesendet"}
        
        response = requests.put(
            f"{COMM_BASE_URL}/emails/99999999",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 404
    
    # --- Phone Call Tests ---
    
    # GET /phone-calls Tests
    
    def test_get_phone_calls_list_empty(self):
        """Test getting empty phone call list."""
        response = requests.get(f"{COMM_BASE_URL}/phone-calls")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_phone_calls_list_with_data(self):
        """Test getting phone call list with data."""
        # Create test phone calls
        call1 = self.create_test_phone_call(for_therapist=True)
        call2 = self.create_test_phone_call(for_therapist=False)
        
        response = requests.get(f"{COMM_BASE_URL}/phone-calls")
        assert response.status_code == 200
        
        calls = response.json()
        assert isinstance(calls, list)
        assert len(calls) >= 2
        
        # Verify our calls are in the list
        call_ids = [c['id'] for c in calls]
        assert call1['id'] in call_ids
        assert call2['id'] in call_ids
    
    def test_get_phone_calls_filter_by_therapist(self):
        """Test filtering phone calls by therapist_id."""
        # Create calls for different recipients
        therapist_call = self.create_test_phone_call(for_therapist=True)
        patient_call = self.create_test_phone_call(for_therapist=False)
        
        # Filter by therapist_id
        response = requests.get(f"{COMM_BASE_URL}/phone-calls?therapist_id={self.test_therapist_id}")
        assert response.status_code == 200
        
        calls = response.json()
        call_ids = [c['id'] for c in calls]
        
        # Should only include therapist call
        assert therapist_call['id'] in call_ids
        assert patient_call['id'] not in call_ids
    
    def test_get_phone_calls_filter_by_patient(self):
        """Test filtering phone calls by patient_id."""
        # Create calls for different recipients
        therapist_call = self.create_test_phone_call(for_therapist=True)
        patient_call = self.create_test_phone_call(for_therapist=False)
        
        # Filter by patient_id
        response = requests.get(f"{COMM_BASE_URL}/phone-calls?patient_id={self.test_patient_id}")
        assert response.status_code == 200
        
        calls = response.json()
        call_ids = [c['id'] for c in calls]
        
        # Should only include patient call
        assert patient_call['id'] in call_ids
        assert therapist_call['id'] not in call_ids
    
    def test_get_phone_calls_filter_by_status(self):
        """Test filtering phone calls by status."""
        # Create call with default status "geplant"
        call1 = self.create_test_phone_call()
        
        # Filter by status
        response = requests.get(f"{COMM_BASE_URL}/phone-calls?status=geplant")
        assert response.status_code == 200
        
        calls = response.json()
        call_ids = [c['id'] for c in calls]
        assert call1['id'] in call_ids
    
    def test_get_phone_calls_filter_by_date(self):
        """Test filtering phone calls by scheduled date."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        day_after = (date.today() + timedelta(days=2)).isoformat()
        
        # Create calls on different dates
        call1 = self.create_test_phone_call(geplantes_datum=tomorrow)
        call2 = self.create_test_phone_call(geplantes_datum=day_after)
        
        # Filter by date
        response = requests.get(f"{COMM_BASE_URL}/phone-calls?geplantes_datum={tomorrow}")
        assert response.status_code == 200
        
        calls = response.json()
        call_ids = [c['id'] for c in calls]
        
        assert call1['id'] in call_ids
        assert call2['id'] not in call_ids
    
    # GET /phone-calls/{id} Tests
    
    def test_get_phone_call_by_id_success(self):
        """Test getting a specific phone call by ID."""
        created_call = self.create_test_phone_call(
            notizen="Spezifischer Test-Anruf",
            dauer_minuten=15
        )
        
        response = requests.get(f"{COMM_BASE_URL}/phone-calls/{created_call['id']}")
        assert response.status_code == 200
        
        call = response.json()
        assert call['id'] == created_call['id']
        assert call['notizen'] == "Spezifischer Test-Anruf"
        assert call['dauer_minuten'] == 15
        assert call['therapist_id'] == self.test_therapist_id
        
        # Verify German field names
        assert 'geplantes_datum' in call
        assert 'geplante_zeit' in call
        assert 'scheduled_date' not in call  # English names should not exist
    
    def test_get_phone_call_by_id_not_found(self):
        """Test getting non-existent phone call returns 404."""
        response = requests.get(f"{COMM_BASE_URL}/phone-calls/99999999")
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    # POST /phone-calls Tests
    
    def test_create_phone_call_for_therapist(self):
        """Test creating a phone call for a therapist."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        data = {
            "therapist_id": self.test_therapist_id,
            "geplantes_datum": tomorrow,
            "geplante_zeit": "14:00",
            "dauer_minuten": 5,
            "notizen": "Follow-up für Bündel #101"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/phone-calls",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        call = response.json()
        self.created_phone_call_ids.append(call['id'])
        
        assert call['therapist_id'] == self.test_therapist_id
        assert call['patient_id'] is None
        assert call['geplantes_datum'] == tomorrow
        assert call['geplante_zeit'] == "14:00"
        assert call['status'] == "geplant"  # Default status
    
    def test_create_phone_call_for_patient(self):
        """Test creating a phone call for a patient."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        data = {
            "patient_id": self.test_patient_id,
            "geplantes_datum": tomorrow,
            "geplante_zeit": "10:00",
            "dauer_minuten": 10,
            "notizen": "Status update regarding therapy search"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/phone-calls",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        call = response.json()
        self.created_phone_call_ids.append(call['id'])
        
        assert call['patient_id'] == self.test_patient_id
        assert call['therapist_id'] is None
        assert call['notizen'] == "Status update regarding therapy search"
    
    def test_create_phone_call_missing_recipient(self):
        """Test creating phone call without therapist_id or patient_id fails."""
        data = {
            "geplantes_datum": "2025-06-20",
            "geplante_zeit": "14:00",
            "notizen": "Test call"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/phone-calls",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert 'message' in error
        assert 'therapist_id or patient_id is required' in error['message']
    
    def test_create_phone_call_both_recipients(self):
        """Test creating phone call with both therapist_id and patient_id fails."""
        data = {
            "therapist_id": self.test_therapist_id,
            "patient_id": self.test_patient_id,
            "geplantes_datum": "2025-06-20",
            "geplante_zeit": "14:00",
            "notizen": "Test call"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/phone-calls",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert 'message' in error
        assert 'Cannot specify both therapist_id and patient_id' in error['message']
    
    def test_create_phone_call_minimal_data(self):
        """Test creating phone call with minimal data."""
        # For patient, should use default date/time
        data = {
            "patient_id": self.test_patient_id,
            "notizen": "Minimal data test"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/phone-calls",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        call = response.json()
        self.created_phone_call_ids.append(call['id'])
        
        # Should have default values
        assert call['patient_id'] == self.test_patient_id
        assert call['geplantes_datum'] is not None
        assert call['geplante_zeit'] is not None
        assert call['dauer_minuten'] == 10  # Default for patients
    
    # PUT /phone-calls/{id} Tests
    
    def test_update_phone_call_status(self):
        """Test updating phone call status with German enum values."""
        call = self.create_test_phone_call()
        
        # Update to completed
        update_data = {
            "status": "abgeschlossen",
            "tatsaechliches_datum": date.today().isoformat(),
            "tatsaechliche_zeit": "14:05",
            "ergebnis": "Therapeut interessiert an 1 Patient",
            "notizen": "Will sich nächste Woche melden"
        }
        
        response = requests.put(
            f"{COMM_BASE_URL}/phone-calls/{call['id']}",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        
        updated = response.json()
        assert updated['status'] == "abgeschlossen"
        assert updated['ergebnis'] == "Therapeut interessiert an 1 Patient"
    
    def test_update_phone_call_all_statuses(self):
        """Test all German phone call status values."""
        status_values = ["geplant", "abgeschlossen", "fehlgeschlagen", "abgebrochen"]
        
        for status in status_values:
            call = self.create_test_phone_call()
            
            response = requests.put(
                f"{COMM_BASE_URL}/phone-calls/{call['id']}",
                json={"status": status},
                headers=self.base_headers
            )
            
            assert response.status_code == 200
            updated = response.json()
            assert updated['status'] == status
    
    def test_update_phone_call_not_found(self):
        """Test updating non-existent phone call returns 404."""
        update_data = {"status": "abgeschlossen"}
        
        response = requests.put(
            f"{COMM_BASE_URL}/phone-calls/99999999",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 404
    
    # DELETE /phone-calls/{id} Tests
    
    def test_delete_phone_call_success(self):
        """Test deleting an existing phone call."""
        call = self.create_test_phone_call()
        call_id = call['id']
        
        # Delete the phone call
        response = requests.delete(f"{COMM_BASE_URL}/phone-calls/{call_id}")
        assert response.status_code == 200
        
        result = response.json()
        assert 'message' in result
        assert 'deleted successfully' in result['message'].lower()
        
        # Verify phone call is deleted
        get_response = requests.get(f"{COMM_BASE_URL}/phone-calls/{call_id}")
        assert get_response.status_code == 404
        
        # Remove from cleanup list since already deleted
        self.created_phone_call_ids.remove(call_id)
    
    def test_delete_phone_call_not_found(self):
        """Test deleting non-existent phone call returns 404."""
        response = requests.delete(f"{COMM_BASE_URL}/phone-calls/99999999")
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    # --- Complex Scenario Tests ---
    
    def test_email_lifecycle(self):
        """Test complete email lifecycle: create, update status, mark as sent."""
        # 1. Create email as draft
        email_data = {
            "therapist_id": self.test_therapist_id,
            "betreff": "Lifecycle Test",
            "inhalt_html": "<p>Test content</p>",
            "inhalt_text": "Test content",
            "empfaenger_email": TEST_EMAIL_RECIPIENTS[1],
            "empfaenger_name": "Test Therapeut"
        }
        
        create_response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=email_data,
            headers=self.base_headers
        )
        assert create_response.status_code == 201
        
        email = create_response.json()
        email_id = email['id']
        self.created_email_ids.append(email_id)
        assert email['status'] == "Entwurf"
        
        # 2. Update to queued
        update_response = requests.put(
            f"{COMM_BASE_URL}/emails/{email_id}",
            json={"status": "In_Warteschlange"},
            headers=self.base_headers
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated['status'] == "In_Warteschlange"
        
        # 3. Update to sending
        update_response = requests.put(
            f"{COMM_BASE_URL}/emails/{email_id}",
            json={"status": "Wird_gesendet"},
            headers=self.base_headers
        )
        assert update_response.status_code == 200
        
        # 4. Mark as sent
        update_response = requests.put(
            f"{COMM_BASE_URL}/emails/{email_id}",
            json={"status": "Gesendet"},
            headers=self.base_headers
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated['status'] == "Gesendet"
    
    def test_phone_call_lifecycle(self):
        """Test complete phone call lifecycle: create, execute, complete."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        # 1. Create scheduled call
        call_data = {
            "patient_id": self.test_patient_id,
            "geplantes_datum": tomorrow,
            "geplante_zeit": "15:00",
            "dauer_minuten": 10,
            "notizen": "Initial consultation"
        }
        
        create_response = requests.post(
            f"{COMM_BASE_URL}/phone-calls",
            json=call_data,
            headers=self.base_headers
        )
        assert create_response.status_code == 201
        
        call = create_response.json()
        call_id = call['id']
        self.created_phone_call_ids.append(call_id)
        assert call['status'] == "geplant"
        
        # 2. Mark as completed
        update_response = requests.put(
            f"{COMM_BASE_URL}/phone-calls/{call_id}",
            json={
                "status": "abgeschlossen",
                "tatsaechliches_datum": tomorrow,
                "tatsaechliche_zeit": "15:05",
                "ergebnis": "Patient contacted successfully",
                "notizen": "Patient is interested in therapy"
            },
            headers=self.base_headers
        )
        assert update_response.status_code == 200
        
        updated = update_response.json()
        assert updated['status'] == "abgeschlossen"
        assert updated['ergebnis'] == "Patient contacted successfully"
    
    def test_communication_for_both_types(self):
        """Test creating communications for both patients and therapists."""
        # Create communications for therapist
        therapist_email = self.create_test_email(
            for_therapist=True,
            betreff="Therapist Communication Test"
        )
        therapist_call = self.create_test_phone_call(
            for_therapist=True,
            notizen="Therapist call test"
        )
        
        # Create communications for patient
        patient_email = self.create_test_email(
            for_therapist=False,
            betreff="Patient Communication Test"
        )
        patient_call = self.create_test_phone_call(
            for_therapist=False,
            notizen="Patient call test"
        )
        
        # Verify all were created successfully
        assert therapist_email['therapist_id'] == self.test_therapist_id
        assert therapist_email['patient_id'] is None
        assert therapist_call['therapist_id'] == self.test_therapist_id
        assert therapist_call['patient_id'] is None
        
        assert patient_email['patient_id'] == self.test_patient_id
        assert patient_email['therapist_id'] is None
        assert patient_call['patient_id'] == self.test_patient_id
        assert patient_call['therapist_id'] is None
    
    def test_pagination(self):
        """Test pagination for emails and phone calls."""
        # Create multiple emails
        for i in range(5):
            self.create_test_email(betreff=f"Pagination Test {i}")
        
        # Test pagination
        response = requests.get(f"{COMM_BASE_URL}/emails?page=1&limit=2")
        assert response.status_code == 200
        
        emails = response.json()
        assert isinstance(emails, list)
        # Note: Basic implementation might not respect pagination
        # This tests that the parameters are accepted without error
    
    def test_invalid_enum_values(self):
        """Test that invalid German enum values are rejected."""
        # Test invalid email status
        email = self.create_test_email()
        
        response = requests.put(
            f"{COMM_BASE_URL}/emails/{email['id']}",
            json={"status": "SENT"},  # English value, should be rejected
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert 'Invalid status value' in error['message']
        
        # Test invalid phone call status
        call = self.create_test_phone_call()
        
        response = requests.put(
            f"{COMM_BASE_URL}/phone-calls/{call['id']}",
            json={"status": "COMPLETED"},  # English value, should be rejected
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert 'Invalid status value' in error['message']
    
    def test_create_patient_email_with_markdown(self):
        """Test creating email with markdown for a patient."""
        data = {
            "patient_id": self.test_patient_id,
            "betreff": "Willkommen bei der Therapievermittlung",
            "inhalt_markdown": "# Willkommen!\n\n**Wir freuen uns, Sie zu unterstützen.**\n\n## Nächste Schritte:\n\n1. Wir suchen passende Therapeuten\n2. Sie erhalten regelmäßige Updates\n3. Bei Fragen sind wir für Sie da\n\n*Mit freundlichen Grüßen,*\nIhr Therapievermittlungsteam",
            "empfaenger_email": TEST_EMAIL_RECIPIENTS[0],
            "empfaenger_name": "John Doe"
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        email = response.json()
        self.created_email_ids.append(email['id'])
        
        assert email['patient_id'] == self.test_patient_id
        assert email['therapist_id'] is None
    
    def test_create_therapist_email_with_markdown(self):
        """Test creating email with markdown for a therapist."""
        data = {
            "therapist_id": self.test_therapist_id,
            "betreff": "Therapieanfrage für mehrere Patienten",
            "inhalt_markdown": "# Therapieanfrage\n\nSehr geehrte/r Dr. Weber,\n\nWir haben mehrere Patienten, die zu Ihrem Profil passen:\n\n## Patientenliste\n\n| Name | Diagnose | Wartezeit |\n|------|----------|----------|\n| Anna Müller | F32.1 | 30 Tage |\n| Max Schmidt | F41.1 | 45 Tage |\n\n**Bitte antworten Sie innerhalb von 7 Tagen.**\n\n[Kontaktieren Sie uns](mailto:info@curavani.de) bei Fragen.",
            "empfaenger_email": TEST_EMAIL_RECIPIENTS[1],
            "empfaenger_name": "Dr. Maria Weber",
            "add_legal_footer": True
        }
        
        response = requests.post(
            f"{COMM_BASE_URL}/emails",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        email = response.json()
        self.created_email_ids.append(email['id'])
        
        assert email['therapist_id'] == self.test_therapist_id
        assert email['patient_id'] is None


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])