"""Integration tests for Patient Success Emails and PDF Attachments.

Tests the complete implementation of:
- Feature 3: Enhanced patient success email system with 4 templates
- Feature 4: PDF attachment functionality for therapist forms
"""
import pytest
import requests
import time
import os
import json
from datetime import date, datetime, timedelta
import uuid

# Base URLs for services
BASE_URL = os.environ["MATCHING_API_URL"]
PATIENT_BASE_URL = os.environ["PATIENT_API_URL"]
THERAPIST_BASE_URL = os.environ["THERAPIST_API_URL"]
COMMUNICATION_BASE_URL = os.environ["COMMUNICATION_API_URL"]

# Test email address
TEST_EMAIL = "mail@peterhaupt.de"

# Path to test PDFs
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fixtures', 'pdfs')
TEST_PDF_1 = os.path.join(FIXTURES_DIR, 'Einwilligung und Datenschutz Praxis Ellendt-Moonen 2025-1-1.pdf')
TEST_PDF_2 = os.path.join(FIXTURES_DIR, 'Therapieanfrage Praxis Müller-Eßer.pdf')


class TestPatientSuccessEmailsAndPDFs:
    """Test class for patient success emails with PDF attachments."""

    @classmethod
    def setup_class(cls):
        """Setup test class - wait for services to be ready."""
        # Check Matching Service
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/platzsuchen")
                if response.status_code == 200:
                    print("Matching service is ready")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Matching service did not start in time")
        
        # Check Patient Service
        for i in range(max_retries):
            try:
                response = requests.get(f"{PATIENT_BASE_URL}/patients")
                if response.status_code == 200:
                    print("Patient service is ready")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Patient service did not start in time")
        
        # Check Therapist Service
        for i in range(max_retries):
            try:
                response = requests.get(f"{THERAPIST_BASE_URL}/therapists")
                if response.status_code == 200:
                    print("Therapist service is ready")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Therapist service did not start in time")
        
        # Check Communication Service
        for i in range(max_retries):
            try:
                response = requests.get(f"{COMMUNICATION_BASE_URL}/emails")
                if response.status_code == 200:
                    print("Communication service is ready")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Communication service did not start in time")
        
        # Verify test PDFs exist
        if not os.path.exists(TEST_PDF_1):
            pytest.fail(f"Test PDF not found: {TEST_PDF_1}")
        if not os.path.exists(TEST_PDF_2):
            pytest.fail(f"Test PDF not found: {TEST_PDF_2}")
        
        print("All services ready and test PDFs found")

    def setup_method(self, method):
        """Setup for each test - initialize tracking lists."""
        self.cleanup_therapists = []
        self.cleanup_patients = []
        self.cleanup_platzsuchen = []
        self.cleanup_emails = []
        self.cleanup_pdfs = []  # Track (therapist_id, filename) tuples

    def teardown_method(self, method):
        """Cleanup after each test - remove all created resources."""
        # Clean up PDFs first (before deleting therapists)
        for therapist_id, filename in self.cleanup_pdfs:
            try:
                if filename:
                    # Delete specific PDF
                    response = requests.delete(
                        f"{THERAPIST_BASE_URL}/therapists/{therapist_id}/pdfs",
                        params={"filename": filename}
                    )
                else:
                    # Delete all PDFs for therapist
                    response = requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist_id}/pdfs")
                
                if response.status_code not in [200, 404]:
                    print(f"Warning: Failed to delete PDFs for therapist {therapist_id}: {response.status_code}")
            except Exception as e:
                print(f"Warning: Exception deleting PDFs: {e}")
        
        # Clean up emails
        for email_id in self.cleanup_emails:
            try:
                response = requests.delete(f"{COMMUNICATION_BASE_URL}/emails/{email_id}")
                if response.status_code not in [200, 404]:
                    print(f"Warning: Failed to delete email {email_id}: {response.status_code}")
            except Exception as e:
                print(f"Warning: Exception deleting email {email_id}: {e}")
        
        # Clean up platzsuchen
        for search_id in self.cleanup_platzsuchen:
            try:
                response = requests.delete(f"{BASE_URL}/platzsuchen/{search_id}")
                if response.status_code not in [200, 404]:
                    print(f"Warning: Failed to delete platzsuche {search_id}: {response.status_code}")
            except Exception as e:
                print(f"Warning: Exception deleting platzsuche {search_id}: {e}")
        
        # Clean up patients
        for patient_id in self.cleanup_patients:
            try:
                response = requests.delete(f"{PATIENT_BASE_URL}/patients/{patient_id}")
                if response.status_code not in [200, 404]:
                    print(f"Warning: Failed to delete patient {patient_id}: {response.status_code}")
            except Exception as e:
                print(f"Warning: Exception deleting patient {patient_id}: {e}")
        
        # Clean up therapists
        for therapist_id in self.cleanup_therapists:
            try:
                response = requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist_id}")
                if response.status_code not in [200, 404]:
                    print(f"Warning: Failed to delete therapist {therapist_id}: {response.status_code}")
            except Exception as e:
                print(f"Warning: Exception deleting therapist {therapist_id}: {e}")

    def generate_unique_email(self, prefix="test"):
        """Generate a unique email address for testing."""
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}.{unique_id}@example.com"

    def create_test_therapist(self, **kwargs):
        """Helper to create a test therapist."""
        default_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": f"Therapeut_{str(uuid.uuid4())[:8]}",
            "titel": "Dr.",
            "strasse": "Teststraße 123",
            "plz": "52062",
            "ort": "Aachen",
            "telefon": "+49 241 123456",
            "email": self.generate_unique_email("therapist"),
            "status": "aktiv",
            "potenziell_verfuegbar": True,
            "ueber_curavani_informiert": True,
            "psychotherapieverfahren": "Verhaltenstherapie",
            "bevorzugt_gruppentherapie": False,
            "telefonische_erreichbarkeit": {
                "Mo": ["9:00-12:00"],
                "Di": ["14:00-18:00"]
            }
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{THERAPIST_BASE_URL}/therapists", json=data)
        assert response.status_code == 201, f"Failed to create therapist: {response.status_code} - {response.text}"
        
        therapist = response.json()
        self.cleanup_therapists.append(therapist['id'])
        return therapist

    def create_test_patient(self, **kwargs):
        """Helper to create a test patient with all required fields."""
        default_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "vorname": "Test",
            "nachname": f"Patient_{str(uuid.uuid4())[:8]}",
            "plz": "52064",
            "ort": "Aachen",
            "email": TEST_EMAIL,  # Use real test email
            "telefon": "+49 123 456789",
            "strasse": "Patientenstraße 456",
            "geburtsdatum": "1990-01-01",
            "symptome": ["Depression / Niedergeschlagenheit", "Schlafstörungen"],
            "krankenkasse": "Test Krankenkasse",
            "erfahrung_mit_psychotherapie": False,
            "offen_fuer_gruppentherapie": False,
            "zeitliche_verfuegbarkeit": {
                "montag": ["09:00-17:00"],
                "mittwoch": ["14:00-18:00"],
                "freitag": ["10:00-15:00"]
            },
            "raeumliche_verfuegbarkeit": {"max_km": 25},
            "bevorzugtes_therapeutengeschlecht": "Egal",
            "bevorzugtes_therapieverfahren": "egal"
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{PATIENT_BASE_URL}/patients", json=data)
        assert response.status_code == 201, f"Failed to create patient: {response.status_code} - {response.text}"
        
        patient = response.json()
        self.cleanup_patients.append(patient['id'])
        return patient

    def create_platzsuche(self, patient_id):
        """Helper to create a platzsuche."""
        search_data = {
            "patient_id": patient_id,
            "notizen": "Test platzsuche for email and PDF testing"
        }
        
        response = requests.post(f"{BASE_URL}/platzsuchen", json=search_data)
        assert response.status_code == 201, f"Failed to create platzsuche: {response.status_code} - {response.text}"
        
        search = response.json()
        self.cleanup_platzsuchen.append(search['id'])
        return search

    def upload_pdf_for_therapist(self, therapist_id, pdf_path):
        """Helper to upload a PDF for a therapist."""
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            response = requests.post(
                f"{THERAPIST_BASE_URL}/therapists/{therapist_id}/pdfs",
                files=files
            )
        
        assert response.status_code == 201, f"Failed to upload PDF: {response.status_code} - {response.text}"
        
        result = response.json()
        filename = result.get('filename')
        self.cleanup_pdfs.append((therapist_id, filename))
        return result

    # ==================== PDF MANAGEMENT TESTS ====================

    def test_upload_single_pdf_for_therapist(self):
        """Test uploading a single PDF form for a therapist."""
        # Create therapist
        therapist = self.create_test_therapist()
        
        # Upload PDF
        result = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_1)
        
        assert 'filename' in result
        assert result['therapist_id'] == therapist['id']
        print(f"Successfully uploaded PDF: {result['filename']}")
        
        # Verify PDF appears in list
        response = requests.get(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}/pdfs")
        assert response.status_code == 200
        
        pdf_data = response.json()
        assert pdf_data['therapist_id'] == therapist['id']
        assert pdf_data['pdf_count'] == 1
        assert len(pdf_data['pdfs']) == 1
        
        # Check the uploaded file details
        pdf_info = pdf_data['pdfs'][0]
        assert 'filename' in pdf_info
        assert 'size' in pdf_info
        assert 'path' in pdf_info

    def test_upload_multiple_pdfs_with_german_names(self):
        """Test uploading multiple PDFs with German filenames containing special characters."""
        # Create therapist
        therapist = self.create_test_therapist()
        
        # Upload both test PDFs
        result1 = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_1)
        result2 = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_2)
        
        print(f"Uploaded PDF 1: {result1['filename']}")
        print(f"Uploaded PDF 2: {result2['filename']}")
        
        # Verify both PDFs appear in list
        response = requests.get(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}/pdfs")
        assert response.status_code == 200
        
        pdf_data = response.json()
        assert pdf_data['pdf_count'] == 2
        assert len(pdf_data['pdfs']) == 2
        
        # Check that German characters are preserved or properly sanitized
        filenames = [pdf['filename'] for pdf in pdf_data['pdfs']]
        print(f"Stored filenames: {filenames}")

    def test_delete_specific_pdf(self):
        """Test deleting a specific PDF file."""
        # Create therapist and upload two PDFs
        therapist = self.create_test_therapist()
        result1 = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_1)
        result2 = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_2)
        
        # Delete first PDF
        response = requests.delete(
            f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}/pdfs",
            params={"filename": result1['filename']}
        )
        assert response.status_code == 200
        
        # Verify only one PDF remains
        response = requests.get(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}/pdfs")
        assert response.status_code == 200
        
        pdf_data = response.json()
        assert pdf_data['pdf_count'] == 1
        assert pdf_data['pdfs'][0]['filename'] == result2['filename']
        
        # Remove from cleanup since we manually deleted it
        self.cleanup_pdfs.remove((therapist['id'], result1['filename']))

    def test_delete_all_pdfs_for_therapist(self):
        """Test deleting all PDFs for a therapist at once."""
        # Create therapist and upload PDFs
        therapist = self.create_test_therapist()
        self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_1)
        self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_2)
        
        # Delete all PDFs
        response = requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}/pdfs")
        assert response.status_code == 200
        
        delete_result = response.json()
        assert delete_result['files_deleted'] == 2
        
        # Verify no PDFs remain
        response = requests.get(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}/pdfs")
        assert response.status_code == 200
        
        pdf_data = response.json()
        assert pdf_data['pdf_count'] == 0
        assert len(pdf_data['pdfs']) == 0
        
        # Clear cleanup list since we deleted all
        self.cleanup_pdfs = [(tid, fn) for tid, fn in self.cleanup_pdfs if tid != therapist['id']]

    # ==================== EMAIL TEMPLATE SELECTION TESTS ====================

    def test_email_template_selection_email_contact(self):
        """Test that email_contact template is used by default."""
        # Create therapist and patient
        therapist = self.create_test_therapist()
        patient = self.create_test_patient()
        
        # Create platzsuche
        search = self.create_platzsuche(patient['id'])
        
        # Mark as successful with default template (email_contact)
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich"
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email to be created
        time.sleep(2)
        
        # Check that email was created with correct template
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        assert response.status_code == 200
        
        emails = response.json()['data']
        assert len(emails) > 0
        
        email = emails[0]
        self.cleanup_emails.append(email['id'])
        
        # Verify email content indicates email_contact template
        assert "E-Mail an" in email['inhalt_text'] or "schicken Sie folgende E-Mail" in email['inhalt_text']
        print("Email_contact template used successfully")

    def test_email_template_selection_phone_contact(self):
        """Test phone_contact template selection."""
        # Create therapist WITHOUT email (to trigger phone template)
        therapist = self.create_test_therapist(email=None)
        patient = self.create_test_patient()
        
        # Create platzsuche
        search = self.create_platzsuche(patient['id'])
        
        # Mark as successful with phone_contact template
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich",
            "email_template_type": "phone_contact"
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email to be created
        time.sleep(2)
        
        # Check that email was created
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        assert response.status_code == 200
        
        emails = response.json()['data']
        assert len(emails) > 0
        
        email = emails[0]
        self.cleanup_emails.append(email['id'])
        
        # Verify email content indicates phone_contact template
        assert "Rufen Sie" in email['inhalt_text'] or "telefonisch" in email['inhalt_text']
        print("Phone_contact template used successfully")

    def test_email_template_meeting_confirmation_email(self):
        """Test meeting_confirmation_email template with meeting details."""
        therapist = self.create_test_therapist()
        patient = self.create_test_patient()
        
        # Create platzsuche
        search = self.create_platzsuche(patient['id'])
        
        # Mark as successful with meeting_confirmation_email template
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich",
            "email_template_type": "meeting_confirmation_email",
            "meeting_details": {
                "date": "15. Februar 2025",
                "time": "14:00 Uhr"
            }
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email to be created
        time.sleep(2)
        
        # Check that email was created
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        assert response.status_code == 200
        
        emails = response.json()['data']
        assert len(emails) > 0
        
        email = emails[0]
        self.cleanup_emails.append(email['id'])
        
        # Verify email content contains meeting details
        assert "15. Februar 2025" in email['inhalt_text']
        assert "14:00 Uhr" in email['inhalt_text']
        assert "Terminbestätigung" in email['inhalt_text'] or "bestätigen Sie den Termin" in email['inhalt_text']
        print("Meeting_confirmation_email template used successfully with meeting details")

    def test_email_template_meeting_confirmation_phone(self):
        """Test meeting_confirmation_phone template."""
        therapist = self.create_test_therapist()
        patient = self.create_test_patient()
        
        # Create platzsuche
        search = self.create_platzsuche(patient['id'])
        
        # Mark as successful with meeting_confirmation_phone template
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich",
            "email_template_type": "meeting_confirmation_phone",
            "meeting_details": {
                "date": "20. Februar 2025",
                "time": "10:00 Uhr"
            }
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email to be created
        time.sleep(2)
        
        # Check that email was created
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        assert response.status_code == 200
        
        emails = response.json()['data']
        assert len(emails) > 0
        
        email = emails[0]
        self.cleanup_emails.append(email['id'])
        
        # Verify email content
        assert "20. Februar 2025" in email['inhalt_text']
        assert "10:00 Uhr" in email['inhalt_text']
        assert "telefonisch" in email['inhalt_text']
        print("Meeting_confirmation_phone template used successfully")

    # ==================== PDF ATTACHMENT TO EMAILS TESTS ====================

    def test_success_email_with_single_pdf_attachment(self):
        """Test that success email includes PDF attachment when therapist has PDFs."""
        # Create therapist and upload PDF
        therapist = self.create_test_therapist()
        pdf_result = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_1)
        
        # Create patient
        patient = self.create_test_patient()
        
        # Create platzsuche
        search = self.create_platzsuche(patient['id'])
        
        # Mark as successful
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich"
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email to be created and processed
        time.sleep(3)
        
        # Get the created email
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        assert response.status_code == 200
        
        emails = response.json()['data']
        assert len(emails) > 0
        
        # Get full email details
        email_id = emails[0]['id']
        self.cleanup_emails.append(email_id)
        
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails/{email_id}")
        assert response.status_code == 200
        
        email = response.json()
        
        # Check for attachments
        assert 'attachments' in email
        assert len(email['attachments']) == 1
        
        # Verify attachment path contains therapist ID
        attachment_path = email['attachments'][0]
        assert str(therapist['id']) in attachment_path
        print(f"Email created with PDF attachment: {attachment_path}")

    def test_success_email_with_multiple_pdf_attachments(self):
        """Test that success email includes all PDFs when therapist has multiple forms."""
        # Create therapist and upload multiple PDFs
        therapist = self.create_test_therapist()
        pdf1 = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_1)
        pdf2 = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_2)
        
        # Create patient
        patient = self.create_test_patient()
        
        # Create platzsuche
        search = self.create_platzsuche(patient['id'])
        
        # Mark as successful
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich"
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email processing
        time.sleep(3)
        
        # Get the created email
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        assert response.status_code == 200
        
        emails = response.json()['data']
        assert len(emails) > 0
        
        email_id = emails[0]['id']
        self.cleanup_emails.append(email_id)
        
        # Get full email details
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails/{email_id}")
        assert response.status_code == 200
        
        email = response.json()
        
        # Check for multiple attachments
        assert 'attachments' in email
        assert len(email['attachments']) == 2
        
        print(f"Email created with {len(email['attachments'])} PDF attachments")
        for attachment in email['attachments']:
            print(f"  - {attachment}")

    def test_success_email_without_pdfs_still_sends(self):
        """Test that success email is sent even when therapist has no PDFs."""
        # Create therapist WITHOUT uploading any PDFs
        therapist = self.create_test_therapist()
        patient = self.create_test_patient()
        
        # Create platzsuche
        search = self.create_platzsuche(patient['id'])
        
        # Mark as successful
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich"
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email
        time.sleep(3)
        
        # Verify email was created
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        assert response.status_code == 200
        
        emails = response.json()['data']
        assert len(emails) > 0
        
        email_id = emails[0]['id']
        self.cleanup_emails.append(email_id)
        
        # Get full email details
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails/{email_id}")
        assert response.status_code == 200
        
        email = response.json()
        
        # Check that email has no attachments but was still created
        assert 'attachments' in email
        assert len(email['attachments']) == 0
        print("Email sent successfully without attachments")

    def test_email_content_mentions_attached_forms(self):
        """Test that email content mentions the attached PDF forms."""
        # Create therapist with PDFs
        therapist = self.create_test_therapist()
        self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_1)
        self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_2)
        
        patient = self.create_test_patient()
        search = self.create_platzsuche(patient['id'])
        
        # Mark as successful
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich"
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email
        time.sleep(3)
        
        # Get email
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        emails = response.json()['data']
        email = emails[0]
        self.cleanup_emails.append(email['id'])
        
        # Check that email text mentions forms
        assert "Formular" in email['inhalt_text'] or "beigefügt" in email['inhalt_text'] or "Anhang" in email['inhalt_text']
        print("Email content correctly references attached forms")

    # ==================== END-TO-END INTEGRATION TESTS ====================

    def test_complete_workflow_with_pdfs_and_email_template(self):
        """Test complete workflow from therapist creation to success email with PDFs."""
        print("\n=== Starting Complete Workflow Test ===")
        
        # Step 1: Create therapist
        print("Step 1: Creating therapist...")
        therapist = self.create_test_therapist(
            vorname="Dr. Maria",
            nachname="Müller",
            titel="Dr. med.",
            geschlecht="weiblich",
            anrede="Frau"
        )
        print(f"  Created therapist ID: {therapist['id']}")
        
        # Step 2: Upload PDFs
        print("Step 2: Uploading PDFs...")
        pdf1 = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_1)
        pdf2 = self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_2)
        print(f"  Uploaded: {pdf1['filename']}")
        print(f"  Uploaded: {pdf2['filename']}")
        
        # Step 3: Create patient
        print("Step 3: Creating patient...")
        patient = self.create_test_patient(
            vorname="Hans",
            nachname="Schmidt",
            geschlecht="männlich",
            anrede="Herr"
        )
        print(f"  Created patient ID: {patient['id']}")
        
        # Step 4: Create platzsuche
        print("Step 4: Creating platzsuche...")
        search = self.create_platzsuche(patient['id'])
        print(f"  Created platzsuche ID: {search['id']}")
        
        # Step 5: Mark as successful with specific template
        print("Step 5: Marking as successful with meeting confirmation...")
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich",
            "email_template_type": "meeting_confirmation_email",
            "meeting_details": {
                "date": "25. Februar 2025",
                "time": "15:30 Uhr"
            }
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        print("  Platzsuche marked as successful")
        
        # Step 6: Wait and verify email
        print("Step 6: Verifying email creation...")
        time.sleep(5)  # Give more time for email processing
        
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        assert response.status_code == 200
        
        emails = response.json()['data']
        assert len(emails) > 0
        
        email_id = emails[0]['id']
        self.cleanup_emails.append(email_id)
        
        # Get full email details
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails/{email_id}")
        assert response.status_code == 200
        
        email = response.json()
        
        # Verify everything
        print("Step 7: Verifying results...")
        assert email['patient_id'] == patient['id']
        assert len(email['attachments']) == 2
        assert "25. Februar 2025" in email['inhalt_text']
        assert "15:30 Uhr" in email['inhalt_text']
        assert email['empfaenger_email'] == TEST_EMAIL
        
        print("✅ Complete workflow test successful!")
        print(f"  - Email ID: {email_id}")
        print(f"  - Recipient: {email['empfaenger_email']}")
        print(f"  - Attachments: {len(email['attachments'])} PDFs")
        print(f"  - Template: meeting_confirmation_email")
        print(f"  - Status: {email['status']}")

    def test_actual_email_sending_with_pdfs(self):
        """Test that emails with PDFs are actually queued and sent to test address."""
        print("\n=== Testing Actual Email Sending ===")
        
        # Create therapist with PDFs
        therapist = self.create_test_therapist()
        self.upload_pdf_for_therapist(therapist['id'], TEST_PDF_1)
        
        # Create patient with test email
        patient = self.create_test_patient(
            email=TEST_EMAIL,
            vorname="Test",
            nachname="EmailRecipient"
        )
        
        # Create and complete platzsuche
        search = self.create_platzsuche(patient['id'])
        
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich"
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email creation
        time.sleep(3)
        
        # Get email
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        emails = response.json()['data']
        email = emails[0]
        email_id = email['id']
        self.cleanup_emails.append(email_id)
        
        # Check initial status
        print(f"Email {email_id} initial status: {email['status']}")
        
        # The email should be queued (In_Warteschlange)
        assert email['status'] == 'In_Warteschlange'
        
        # Wait for email queue processor to send it (runs every 30 seconds)
        print("Waiting for email queue processor to send the email...")
        max_wait = 40  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{COMMUNICATION_BASE_URL}/emails/{email_id}")
            if response.status_code == 200:
                current_email = response.json()
                if current_email['status'] == 'Gesendet':
                    print(f"✅ Email sent successfully to {TEST_EMAIL}")
                    print(f"  Sent at: {current_email.get('gesendet_am', 'N/A')}")
                    break
                elif current_email['status'] == 'Fehlgeschlagen':
                    print(f"❌ Email sending failed: {current_email.get('fehlermeldung', 'Unknown error')}")
                    break
            time.sleep(5)
        else:
            print(f"⚠️ Email still in status {current_email['status']} after {max_wait} seconds")

    def test_invalid_template_type_falls_back_to_default(self):
        """Test that invalid template type falls back to default email_contact."""
        therapist = self.create_test_therapist()
        patient = self.create_test_patient()
        search = self.create_platzsuche(patient['id'])
        
        # Try with invalid template type
        update_data = {
            "vermittelter_therapeut_id": therapist['id'],
            "status": "erfolgreich",
            "email_template_type": "invalid_template_name"
        }
        
        response = requests.put(f"{BASE_URL}/platzsuchen/{search['id']}", json=update_data)
        assert response.status_code == 200
        
        # Wait for email
        time.sleep(3)
        
        # Verify email was still created (with default template)
        response = requests.get(f"{COMMUNICATION_BASE_URL}/emails", params={"patient_id": patient['id']})
        emails = response.json()['data']
        assert len(emails) > 0
        
        email = emails[0]
        self.cleanup_emails.append(email['id'])
        
        # Should have used default template (email_contact)
        assert "E-Mail an" in email['inhalt_text'] or "schicken Sie folgende E-Mail" in email['inhalt_text']
        print("Invalid template type correctly fell back to default")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
