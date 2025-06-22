"""Integration tests for Communication Service API with pagination support."""
import pytest
import requests
import time
from datetime import date, datetime, timedelta

# Base URL for the Communication Service
BASE_URL = "http://localhost:8004/api"

# Base URLs for other services (for cross-service testing)
PATIENT_BASE_URL = "http://localhost:8001/api"
THERAPIST_BASE_URL = "http://localhost:8002/api"


class TestCommunicationServiceAPI:
    """Test class for Communication Service API endpoints."""

    @classmethod
    def setup_class(cls):
        """Setup test class - wait for service to be ready."""
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/emails")
                if response.status_code == 200:
                    print("Communication service is ready")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Communication service did not start in time")

    def create_test_patient(self, **kwargs):
        """Helper to create a test patient in patient service."""
        default_data = {
            "vorname": "Test",
            "nachname": "Patient",
            "email": "test.patient@example.com",
            "telefon": "+49 123 456789",
            "plz": "12345",
            "ort": "Berlin",
            "diagnose": "F32.1"
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{PATIENT_BASE_URL}/patients", json=data)
        assert response.status_code == 201
        return response.json()

    def create_test_therapist(self, **kwargs):
        """Helper to create a test therapist in therapist service."""
        default_data = {
            "vorname": "Test",
            "nachname": "Therapeut",
            "email": "test.therapeut@example.com",
            "telefon": "+49 123 456789",
            "strasse": "Therapiestraße 1",
            "plz": "10115",
            "ort": "Berlin",
            "status": "aktiv"
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{THERAPIST_BASE_URL}/therapists", json=data)
        assert response.status_code == 201
        return response.json()

    def create_test_email(self, therapist_id=None, patient_id=None, **kwargs):
        """Helper method to create a test email."""
        # Ensure we have either a therapist or patient
        if not therapist_id and not patient_id:
            # Create a default therapist if none provided
            therapist = self.create_test_therapist()
            therapist_id = therapist['id']
            # Store for cleanup
            if not hasattr(self, '_temp_therapists'):
                self._temp_therapists = []
            self._temp_therapists.append(therapist_id)
        
        default_data = {
            "betreff": "Test Email",
            "inhalt_text": "This is a test email",
            "empfaenger_email": "test@example.com",
            "empfaenger_name": "Test Recipient"
        }
        
        if therapist_id:
            default_data["therapist_id"] = therapist_id
        if patient_id:
            default_data["patient_id"] = patient_id
            
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{BASE_URL}/emails", json=data)
        assert response.status_code == 201
        return response.json()

    def create_test_phone_call(self, therapist_id=None, patient_id=None, **kwargs):
        """Helper method to create a test phone call."""
        # Ensure we have either a therapist or patient
        if not therapist_id and not patient_id:
            # Create a default therapist if none provided
            therapist = self.create_test_therapist()
            therapist_id = therapist['id']
            # Store for cleanup
            if not hasattr(self, '_temp_therapists'):
                self._temp_therapists = []
            self._temp_therapists.append(therapist_id)
        
        default_data = {
            "notizen": "Test phone call"
        }
        
        if therapist_id:
            default_data["therapist_id"] = therapist_id
        if patient_id:
            default_data["patient_id"] = patient_id
            
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{BASE_URL}/phone-calls", json=data)
        assert response.status_code == 201
        return response.json()

    def teardown_method(self, method):
        """Clean up any temporary therapists/patients created by helpers."""
        if hasattr(self, '_temp_therapists'):
            for therapist_id in self._temp_therapists:
                requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist_id}")
            self._temp_therapists = []
        
        if hasattr(self, '_temp_patients'):
            for patient_id in self._temp_patients:
                requests.delete(f"{PATIENT_BASE_URL}/patients/{patient_id}")
            self._temp_patients = []

    # Email Tests

    def test_create_email_for_therapist(self):
        """Test creating an email for a therapist."""
        # Create a therapist first
        therapist = self.create_test_therapist(
            vorname="Max",
            nachname="Mustermann",
            email="therapist@example.com"
        )
        
        email_data = {
            "therapist_id": therapist['id'],
            "betreff": "Neue Therapieanfrage",
            "inhalt_markdown": "Sehr geehrte/r Therapeut/in,\n\nwir haben neue Anfragen für Sie.",
            "empfaenger_email": "therapist@example.com",
            "empfaenger_name": "Dr. Max Mustermann"
        }
        
        response = requests.post(f"{BASE_URL}/emails", json=email_data)
        assert response.status_code == 201
        
        created_email = response.json()
        assert created_email["therapist_id"] == therapist['id']
        assert created_email["betreff"] == "Neue Therapieanfrage"
        assert created_email["status"] == "Entwurf"
        assert "id" in created_email
        
        # Cleanup
        requests.delete(f"{BASE_URL}/emails/{created_email['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")

    def test_create_email_for_patient(self):
        """Test creating an email for a patient."""
        # Create a patient first
        patient = self.create_test_patient(
            vorname="Anna",
            nachname="Schmidt",
            email="patient@example.com"
        )
        
        email_data = {
            "patient_id": patient['id'],
            "betreff": "Therapieplatz Update",
            "inhalt_markdown": "Liebe/r Patient/in,\n\nwir haben Neuigkeiten zu Ihrer Therapieplatzsuche.",
            "empfaenger_email": "patient@example.com",
            "empfaenger_name": "Anna Schmidt"
        }
        
        response = requests.post(f"{BASE_URL}/emails", json=email_data)
        assert response.status_code == 201
        
        created_email = response.json()
        assert created_email["patient_id"] == patient['id']
        assert created_email["betreff"] == "Therapieplatz Update"
        assert created_email["status"] == "Entwurf"
        assert "id" in created_email
        
        # Cleanup
        requests.delete(f"{BASE_URL}/emails/{created_email['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    def test_get_emails_list_empty(self):
        """Test getting empty email list with pagination."""
        response = requests.get(f"{BASE_URL}/emails")
        assert response.status_code == 200
        
        # Now expecting paginated structure
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert data['page'] == 1
        assert data['limit'] == 20  # Default limit
        assert data['total'] >= 0  # Could be 0 or more

    def test_get_emails_list_with_data(self):
        """Test getting email list with data and pagination."""
        # Create a therapist for the emails
        therapist = self.create_test_therapist()
        
        # Create test emails
        email1 = self.create_test_email(therapist_id=therapist['id'], betreff="Email 1")
        email2 = self.create_test_email(therapist_id=therapist['id'], betreff="Email 2")
        
        response = requests.get(f"{BASE_URL}/emails")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        emails = data['data']
        assert len(emails) >= 2
        
        # Verify our emails are in the list
        email_ids = [e['id'] for e in emails]
        assert email1['id'] in email_ids
        assert email2['id'] in email_ids
        
        # Verify pagination metadata
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] >= 2
        
        # Cleanup
        requests.delete(f"{BASE_URL}/emails/{email1['id']}")
        requests.delete(f"{BASE_URL}/emails/{email2['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")

    def test_get_emails_with_pagination(self):
        """Test email pagination parameters."""
        # Create a therapist for all emails
        therapist = self.create_test_therapist()
        
        # Create multiple emails
        created_emails = []
        for i in range(5):
            email = self.create_test_email(
                therapist_id=therapist['id'],
                betreff=f"Test Email {i}",
                empfaenger_email=f"test{i}@example.com"
            )
            created_emails.append(email)
        
        # Test page 1 with limit 2
        response = requests.get(f"{BASE_URL}/emails?page=1&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        assert data['total'] >= 5
        
        # Test page 2 with limit 2
        response = requests.get(f"{BASE_URL}/emails?page=2&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 2
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        
        # Cleanup
        for email in created_emails:
            requests.delete(f"{BASE_URL}/emails/{email['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")

    def test_get_emails_filtered_by_therapist(self):
        """Test filtering emails by therapist_id with pagination."""
        # Create different therapists
        therapist1 = self.create_test_therapist(email="therapist1@example.com")
        therapist2 = self.create_test_therapist(email="therapist2@example.com")
        patient = self.create_test_patient()
        
        # Create emails for different recipients
        email1 = self.create_test_email(therapist_id=therapist1['id'], betreff="Therapist 1 Email")
        email2 = self.create_test_email(therapist_id=therapist2['id'], betreff="Therapist 2 Email")
        email3 = self.create_test_email(patient_id=patient['id'], betreff="Patient Email")
        
        # Filter by therapist_id
        response = requests.get(f"{BASE_URL}/emails?therapist_id={therapist1['id']}")
        assert response.status_code == 200
        
        data = response.json()
        emails = data['data']
        
        # Check that all returned emails are for the correct therapist
        for email in emails:
            assert email['therapist_id'] == therapist1['id']
        
        # Verify only email1 is in results
        email_ids = [e['id'] for e in emails]
        assert email1['id'] in email_ids
        assert email2['id'] not in email_ids
        assert email3['id'] not in email_ids
        
        # Cleanup
        requests.delete(f"{BASE_URL}/emails/{email1['id']}")
        requests.delete(f"{BASE_URL}/emails/{email2['id']}")
        requests.delete(f"{BASE_URL}/emails/{email3['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist1['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist2['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    def test_get_emails_filtered_by_status(self):
        """Test filtering emails by status with pagination."""
        # Create a therapist
        therapist = self.create_test_therapist()
        
        # Create email and update its status
        email = self.create_test_email(therapist_id=therapist['id'])
        
        # Update status to In_Warteschlange
        update_response = requests.put(
            f"{BASE_URL}/emails/{email['id']}",
            json={"status": "In_Warteschlange"}
        )
        assert update_response.status_code == 200
        
        # Filter by status
        response = requests.get(f"{BASE_URL}/emails?status=In_Warteschlange")
        assert response.status_code == 200
        
        data = response.json()
        emails = data['data']
        
        # Check that returned emails have the correct status
        email_ids = [e['id'] for e in emails if e['status'] == 'In_Warteschlange']
        assert email['id'] in email_ids
        
        # Cleanup
        requests.delete(f"{BASE_URL}/emails/{email['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")

    # Phone Call Tests

    def test_create_phone_call_for_therapist(self):
        """Test creating a phone call for a therapist."""
        # Create a therapist first
        therapist = self.create_test_therapist()
        
        call_data = {
            "therapist_id": therapist['id'],
            "notizen": "Follow-up für Anfrage A456",
            "dauer_minuten": 5
        }
        
        response = requests.post(f"{BASE_URL}/phone-calls", json=call_data)
        assert response.status_code == 201
        
        created_call = response.json()
        assert created_call["therapist_id"] == therapist['id']
        assert created_call["dauer_minuten"] == 5
        assert created_call["status"] == "geplant"
        assert "id" in created_call
        assert "geplantes_datum" in created_call
        assert "geplante_zeit" in created_call
        
        # Cleanup
        requests.delete(f"{BASE_URL}/phone-calls/{created_call['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")

    def test_create_phone_call_for_patient(self):
        """Test creating a phone call for a patient."""
        # Create a patient first
        patient = self.create_test_patient()
        
        call_data = {
            "patient_id": patient['id'],
            "notizen": "Erstgespräch mit Patient",
            "dauer_minuten": 10
        }
        
        response = requests.post(f"{BASE_URL}/phone-calls", json=call_data)
        assert response.status_code == 201
        
        created_call = response.json()
        assert created_call["patient_id"] == patient['id']
        assert created_call["dauer_minuten"] == 10
        assert created_call["status"] == "geplant"
        assert "id" in created_call
        
        # Cleanup
        requests.delete(f"{BASE_URL}/phone-calls/{created_call['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    def test_get_phone_calls_list_empty(self):
        """Test getting empty phone call list with pagination."""
        response = requests.get(f"{BASE_URL}/phone-calls")
        assert response.status_code == 200
        
        # Now expecting paginated structure
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert data['page'] == 1
        assert data['limit'] == 20  # Default limit
        assert data['total'] >= 0  # Could be 0 or more

    def test_get_phone_calls_list_with_data(self):
        """Test getting phone call list with data and pagination."""
        # Create a therapist for the calls
        therapist = self.create_test_therapist()
        
        # Create test phone calls
        call1 = self.create_test_phone_call(therapist_id=therapist['id'], notizen="Call 1")
        call2 = self.create_test_phone_call(therapist_id=therapist['id'], notizen="Call 2")
        
        response = requests.get(f"{BASE_URL}/phone-calls")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        calls = data['data']
        assert len(calls) >= 2
        
        # Verify our calls are in the list
        call_ids = [c['id'] for c in calls]
        assert call1['id'] in call_ids
        assert call2['id'] in call_ids
        
        # Verify pagination metadata
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] >= 2
        
        # Cleanup
        requests.delete(f"{BASE_URL}/phone-calls/{call1['id']}")
        requests.delete(f"{BASE_URL}/phone-calls/{call2['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")

    def test_get_phone_calls_with_pagination(self):
        """Test phone call pagination parameters."""
        # Create a therapist for all calls
        therapist = self.create_test_therapist()
        
        # Create multiple phone calls with explicit scheduling to avoid conflicts
        created_calls = []
        base_date = (date.today() + timedelta(days=1)).isoformat()
        
        for i in range(5):
            # Give each call a different time slot
            hour = 9 + i  # 9:00, 10:00, 11:00, 12:00, 13:00
            call = self.create_test_phone_call(
                therapist_id=therapist['id'],
                notizen=f"Test Call {i}",
                geplantes_datum=base_date,
                geplante_zeit=f"{hour:02d}:00"
            )
            created_calls.append(call)
        
        # Test page 1 with limit 2
        response = requests.get(f"{BASE_URL}/phone-calls?page=1&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        assert data['total'] >= 5
        
        # Test page 2 with limit 2
        response = requests.get(f"{BASE_URL}/phone-calls?page=2&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 2
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        
        # Cleanup
        for call in created_calls:
            requests.delete(f"{BASE_URL}/phone-calls/{call['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")

    def test_get_phone_calls_filtered_by_recipient_type(self):
        """Test filtering phone calls by recipient type with pagination."""
        # Create different recipients
        therapist = self.create_test_therapist()
        patient = self.create_test_patient()
        
        # Create calls for different recipients
        call1 = self.create_test_phone_call(therapist_id=therapist['id'], notizen="Therapist Call")
        call2 = self.create_test_phone_call(patient_id=patient['id'], notizen="Patient Call")
        
        # Filter by recipient_type=therapist
        response = requests.get(f"{BASE_URL}/phone-calls?recipient_type=therapist")
        assert response.status_code == 200
        
        data = response.json()
        calls = data['data']
        
        # Check that all returned calls are for therapists
        for call in calls:
            assert call['therapist_id'] is not None
            assert call['patient_id'] is None
        
        # Verify only call1 is in results
        call_ids = [c['id'] for c in calls]
        assert call1['id'] in call_ids
        assert call2['id'] not in call_ids
        
        # Filter by recipient_type=patient
        response = requests.get(f"{BASE_URL}/phone-calls?recipient_type=patient")
        assert response.status_code == 200
        
        data = response.json()
        calls = data['data']
        
        # Check that all returned calls are for patients
        for call in calls:
            assert call['patient_id'] is not None
            assert call['therapist_id'] is None
        
        # Cleanup
        requests.delete(f"{BASE_URL}/phone-calls/{call1['id']}")
        requests.delete(f"{BASE_URL}/phone-calls/{call2['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    def test_get_phone_calls_filtered_by_status(self):
        """Test filtering phone calls by status with pagination."""
        # Create a therapist
        therapist = self.create_test_therapist()
        
        # Create call and update its status
        call = self.create_test_phone_call(therapist_id=therapist['id'])
        
        # Update status to abgeschlossen
        update_response = requests.put(
            f"{BASE_URL}/phone-calls/{call['id']}",
            json={
                "status": "abgeschlossen",
                "tatsaechliches_datum": date.today().isoformat(),
                "tatsaechliche_zeit": "14:30"
            }
        )
        assert update_response.status_code == 200
        
        # Filter by status
        response = requests.get(f"{BASE_URL}/phone-calls?status=abgeschlossen")
        assert response.status_code == 200
        
        data = response.json()
        calls = data['data']
        
        # Check that returned calls have the correct status
        call_ids = [c['id'] for c in calls if c['status'] == 'abgeschlossen']
        assert call['id'] in call_ids
        
        # Cleanup
        requests.delete(f"{BASE_URL}/phone-calls/{call['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")

    def test_email_markdown_support(self):
        """Test that markdown is properly converted to HTML."""
        # Create a therapist
        therapist = self.create_test_therapist()
        
        email_data = {
            "therapist_id": therapist['id'],
            "betreff": "Markdown Test",
            "inhalt_markdown": "# Heading\n\n**Bold text** and *italic text*\n\n[Link](https://example.com)",
            "empfaenger_email": "test@example.com",
            "empfaenger_name": "Test User"
        }
        
        response = requests.post(f"{BASE_URL}/emails", json=email_data)
        assert response.status_code == 201
        
        created_email = response.json()
        assert "<h1>" in created_email["inhalt_html"]
        assert "<strong>" in created_email["inhalt_html"]
        assert "<em>" in created_email["inhalt_html"]
        assert '<a href="https://example.com">' in created_email["inhalt_html"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/emails/{created_email['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")

    def test_pagination_limits(self):
        """Test pagination limit constraints for both emails and phone calls."""
        # Test emails - max limit (should be capped at 100)
        response = requests.get(f"{BASE_URL}/emails?limit=200")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 100  # Should be capped at max limit
        
        # Test phone calls - zero limit (should be set to 1)
        response = requests.get(f"{BASE_URL}/phone-calls?limit=0")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 1  # Should be set to minimum
        
        # Test negative page (should be set to 1)
        response = requests.get(f"{BASE_URL}/emails?page=-1")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1  # Should be set to minimum

    def test_invalid_recipient_error(self):
        """Test that creating email/call without recipient fails."""
        # Email without recipient
        email_data = {
            "betreff": "No Recipient",
            "inhalt_text": "This should fail",
            "empfaenger_email": "test@example.com",
            "empfaenger_name": "Test"
        }
        
        response = requests.post(f"{BASE_URL}/emails", json=email_data)
        assert response.status_code == 400
        assert "Either therapist_id or patient_id is required" in response.json()["message"]
        
        # Phone call without recipient
        call_data = {
            "notizen": "No recipient call"
        }
        
        response = requests.post(f"{BASE_URL}/phone-calls", json=call_data)
        assert response.status_code == 400
        assert "Either therapist_id or patient_id is required" in response.json()["message"]

    def test_both_recipients_error(self):
        """Test that specifying both therapist and patient fails."""
        # Create both
        therapist = self.create_test_therapist()
        patient = self.create_test_patient()
        
        # Email with both recipients
        email_data = {
            "therapist_id": therapist['id'],
            "patient_id": patient['id'],
            "betreff": "Both Recipients",
            "inhalt_text": "This should fail",
            "empfaenger_email": "test@example.com",
            "empfaenger_name": "Test"
        }
        
        response = requests.post(f"{BASE_URL}/emails", json=email_data)
        assert response.status_code == 400
        assert "Cannot specify both therapist_id and patient_id" in response.json()["message"]
        
        # Cleanup
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])