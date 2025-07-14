"""Integration tests for Therapeutenanfragen hard constraints in Matching Service API."""
import pytest
import requests
import time
from datetime import date, datetime
import os

# Base URL for the Matching Service
BASE_URL = os.environ["MATCHING_API_URL"]

# Base URLs for other services (for setup)
PATIENT_BASE_URL = os.environ["PATIENT_API_URL"]
THERAPIST_BASE_URL = os.environ["THERAPIST_API_URL"]


class TestTherapeutenanfragenConstraints:
    """Test class for Therapeutenanfragen hard constraints."""

    @classmethod
    def setup_class(cls):
        """Setup test class - wait for service to be ready and clean existing data."""
        # Wait for service to be ready
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
        
        # Clean up existing data
        cls._cleanup_existing_data()
    
    @classmethod
    def _cleanup_existing_data(cls):
        """Delete all existing platzsuchen and therapeutenanfragen before tests."""
        print("\nCleaning up existing data...")
        
        # Delete all existing platzsuchen
        try:
            # Get all platzsuchen (might need to paginate)
            page = 1
            while True:
                response = requests.get(f"{BASE_URL}/platzsuchen?page={page}&limit=100")
                if response.status_code == 200:
                    data = response.json()
                    platzsuchen = data.get('data', [])
                    
                    if not platzsuchen:
                        break
                    
                    for platzsuche in platzsuchen:
                        delete_response = requests.delete(f"{BASE_URL}/platzsuchen/{platzsuche['id']}")
                        if delete_response.status_code not in [200, 404]:
                            print(f"Warning: Failed to delete platzsuche {platzsuche['id']}: {delete_response.status_code}")
                    
                    # Check if there are more pages
                    if len(platzsuchen) < 100:
                        break
                    page += 1
                else:
                    print(f"Warning: Failed to fetch platzsuchen: {response.status_code}")
                    break
        except Exception as e:
            print(f"Warning: Exception during platzsuchen cleanup: {e}")
        
        # Delete all existing therapeutenanfragen
        try:
            # Get all therapeutenanfragen (might need to paginate)
            page = 1
            while True:
                response = requests.get(f"{BASE_URL}/therapeutenanfragen?page={page}&limit=100")
                if response.status_code == 200:
                    data = response.json()
                    anfragen = data.get('data', [])
                    
                    if not anfragen:
                        break
                    
                    for anfrage in anfragen:
                        delete_response = requests.delete(f"{BASE_URL}/therapeutenanfragen/{anfrage['id']}")
                        if delete_response.status_code not in [200, 404]:
                            print(f"Warning: Failed to delete therapeutenanfrage {anfrage['id']}: {delete_response.status_code}")
                    
                    # Check if there are more pages
                    if len(anfragen) < 100:
                        break
                    page += 1
                else:
                    print(f"Warning: Failed to fetch therapeutenanfragen: {response.status_code}")
                    break
        except Exception as e:
            print(f"Warning: Exception during therapeutenanfragen cleanup: {e}")
        
        print("Cleanup completed.\n")

    def create_test_patient(self, **kwargs):
        """Helper to create a test patient with ALL REQUIRED FIELDS for platzsuche validation."""
        default_data = {
            # Required enum fields
            "anrede": "Herr",
            "geschlecht": "männlich",
            
            # Basic info
            "vorname": "Test",
            "nachname": "Patient",
            "plz": "52064",  # Aachen PLZ for testing
            "ort": "Aachen",
            "email": "test.patient@example.com",
            "telefon": "+49 123 456789",
            "strasse": "Teststraße 123",
            
            # REQUIRED STRING FIELDS for platzsuche validation
            "geburtsdatum": "1990-01-01",
            "diagnose": "F32.1",
            "symptome": "Niedergeschlagenheit, Schlafstörungen, Antriebslosigkeit",
            "krankenkasse": "Test Krankenkasse",
            
            # REQUIRED BOOLEAN FIELDS for platzsuche validation  
            "erfahrung_mit_psychotherapie": False,
            "offen_fuer_gruppentherapie": False,
            
            # REQUIRED COMPLEX FIELD for platzsuche validation
            "zeitliche_verfuegbarkeit": {
                "montag": ["09:00-17:00"],
                "mittwoch": ["14:00-18:00"]
            },
            
            # Optional but useful fields
            "raeumliche_verfuegbarkeit": {"max_km": 25},
            "bevorzugtes_therapeutengeschlecht": "Egal",
            "bevorzugtes_therapieverfahren": "egal"
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{PATIENT_BASE_URL}/patients", json=data)
        assert response.status_code == 201, f"Failed to create patient: {response.status_code} - {response.text}"
        return response.json()

    def create_test_therapist(self, **kwargs):
        """Helper to create a test therapist in therapist service."""
        default_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": "Therapeut",
            "plz": "52062",
            "ort": "Aachen",
            "email": "test.therapeut@example.com",
            "telefon": "+49 241 123456",
            "status": "aktiv",
            "potenziell_verfuegbar": True,
            "ueber_curavani_informiert": True,
            "psychotherapieverfahren": "Verhaltenstherapie",
            "bevorzugt_gruppentherapie": False
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{THERAPIST_BASE_URL}/therapists", json=data)
        assert response.status_code == 201, f"Failed to create therapist: {response.status_code} - {response.text}"
        return response.json()

    def safe_delete_platzsuche(self, search_id):
        """Safely delete a platzsuche, ignoring errors."""
        try:
            response = requests.delete(f"{BASE_URL}/platzsuchen/{search_id}")
            if response.status_code not in [200, 404]:
                print(f"Warning: Failed to delete platzsuche {search_id}: {response.status_code}")
        except Exception as e:
            print(f"Warning: Exception deleting platzsuche {search_id}: {e}")

    def safe_delete_patient(self, patient_id):
        """Safely delete a patient, ignoring errors."""
        try:
            response = requests.delete(f"{PATIENT_BASE_URL}/patients/{patient_id}")
            if response.status_code not in [200, 404]:
                print(f"Warning: Failed to delete patient {patient_id}: {response.status_code}")
        except Exception as e:
            print(f"Warning: Exception deleting patient {patient_id}: {e}")

    def safe_delete_therapist(self, therapist_id):
        """Safely delete a therapist, ignoring errors."""
        try:
            response = requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist_id}")
            if response.status_code not in [200, 404]:
                print(f"Warning: Failed to delete therapist {therapist_id}: {response.status_code}")
        except Exception as e:
            print(f"Warning: Exception deleting therapist {therapist_id}: {e}")

    def create_platzsuche_for_patient(self, patient_id):
        """Helper to create a platzsuche for a patient."""
        response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient_id}
        )
        assert response.status_code == 201, f"Failed to create platzsuche: {response.status_code} - {response.text}"
        return response.json()

    def create_anfrage_for_therapist(self, therapist_id, plz_prefix="52"):
        """Helper to create an anfrage for a therapist."""
        response = requests.post(
            f"{BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist_id,
                "plz_prefix": plz_prefix,
                "sofort_senden": False
            }
        )
        return response

    # ==================== SINGLE CONSTRAINT TESTS ====================

    # --- Therapy Procedure Tests ---
    
    def test_therapy_procedure_matching_verhaltenstherapie_positive(self):
        """Patient preferring Verhaltenstherapie should be included for Verhaltenstherapie therapist."""
        # Create therapist offering Verhaltenstherapie
        therapist = self.create_test_therapist(
            psychotherapieverfahren="Verhaltenstherapie",
            email="vt.therapist@example.com"
        )
        
        # Create patient preferring Verhaltenstherapie
        patient = self.create_test_patient(
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            email="vt.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        assert anfrage['therapist_id'] == therapist['id']
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_therapy_procedure_matching_tiefenpsychologisch_positive(self):
        """Patient preferring tiefenpsychologisch should be included for tiefenpsychologisch therapist."""
        # Create therapist offering tiefenpsychologisch
        therapist = self.create_test_therapist(
            psychotherapieverfahren="tiefenpsychologisch_fundierte_Psychotherapie",
            email="tp.therapist@example.com"
        )
        
        # Create patient preferring tiefenpsychologisch
        patient = self.create_test_patient(
            bevorzugtes_therapieverfahren="tiefenpsychologisch_fundierte_Psychotherapie",
            email="tp.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_therapy_procedure_matching_egal_positive(self):
        """Patient with 'egal' preference should be included for any therapist."""
        # Create therapist with any procedure
        therapist = self.create_test_therapist(
            psychotherapieverfahren="Verhaltenstherapie",
            email="any.therapist@example.com"
        )
        
        # Create patient with 'egal' preference
        patient = self.create_test_patient(
            bevorzugtes_therapieverfahren="egal",
            email="egal.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_therapy_procedure_matching_mismatch_negative(self):
        """Patient preferring Verhaltenstherapie should NOT be included for tiefenpsychologisch therapist."""
        # Create therapist offering tiefenpsychologisch
        therapist = self.create_test_therapist(
            psychotherapieverfahren="tiefenpsychologisch_fundierte_Psychotherapie",
            email="tp.therapist@example.com"
        )
        
        # Create patient preferring Verhaltenstherapie
        patient = self.create_test_patient(
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            email="vt.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_therapy_procedure_matching_reverse_mismatch_negative(self):
        """Patient preferring tiefenpsychologisch should NOT be included for Verhaltenstherapie therapist."""
        # Create therapist offering Verhaltenstherapie
        therapist = self.create_test_therapist(
            psychotherapieverfahren="Verhaltenstherapie",
            email="vt.therapist@example.com"
        )
        
        # Create patient preferring tiefenpsychologisch
        patient = self.create_test_patient(
            bevorzugtes_therapieverfahren="tiefenpsychologisch_fundierte_Psychotherapie",
            email="tp.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    # --- Gender Preference Tests ---
    
    def test_gender_preference_female_positive(self):
        """Patient preferring female therapist should be included for female therapist."""
        # Create female therapist
        therapist = self.create_test_therapist(
            geschlecht="weiblich",
            anrede="Frau",
            email="female.therapist@example.com"
        )
        
        # Create patient preferring female
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            email="prefer.female.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_gender_preference_male_positive(self):
        """Patient preferring male therapist should be included for male therapist."""
        # Create male therapist
        therapist = self.create_test_therapist(
            geschlecht="männlich",
            anrede="Herr",
            email="male.therapist@example.com"
        )
        
        # Create patient preferring male
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Männlich",
            email="prefer.male.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_gender_preference_egal_positive(self):
        """Patient with 'Egal' gender preference should be included for any therapist."""
        # Create therapist with any gender
        therapist = self.create_test_therapist(
            geschlecht="divers",
            anrede="Herr",
            email="diverse.therapist@example.com"
        )
        
        # Create patient with 'Egal' preference
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Egal",
            email="egal.gender.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_gender_preference_female_to_male_negative(self):
        """Patient preferring female should NOT be included for male therapist."""
        # Create male therapist
        therapist = self.create_test_therapist(
            geschlecht="männlich",
            anrede="Herr",
            email="male.therapist@example.com"
        )
        
        # Create patient preferring female
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            email="prefer.female.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_gender_preference_male_to_female_negative(self):
        """Patient preferring male should NOT be included for female therapist."""
        # Create female therapist
        therapist = self.create_test_therapist(
            geschlecht="weiblich",
            anrede="Frau",
            email="female.therapist@example.com"
        )
        
        # Create patient preferring male
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Männlich",
            email="prefer.male.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_gender_preference_female_to_diverse_negative(self):
        """Patient preferring female should NOT be included for diverse therapist."""
        # Create diverse therapist
        therapist = self.create_test_therapist(
            geschlecht="divers",
            anrede="Herr",
            email="diverse.therapist@example.com"
        )
        
        # Create patient preferring female
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            email="prefer.female.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    # --- Group Therapy Tests ---
    
    def test_group_therapy_open_to_prefers_positive(self):
        """Patient open to group therapy should be included for therapist preferring group."""
        # Create therapist preferring group therapy
        therapist = self.create_test_therapist(
            bevorzugt_gruppentherapie=True,
            email="group.therapist@example.com"
        )
        
        # Create patient open to group therapy
        patient = self.create_test_patient(
            offen_fuer_gruppentherapie=True,
            email="open.group.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_group_therapy_open_to_no_preference_positive(self):
        """Patient open to group therapy should be included for therapist not preferring group."""
        # Create therapist not preferring group therapy
        therapist = self.create_test_therapist(
            bevorzugt_gruppentherapie=False,
            email="no.group.therapist@example.com"
        )
        
        # Create patient open to group therapy
        patient = self.create_test_patient(
            offen_fuer_gruppentherapie=True,
            email="open.group.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_group_therapy_not_open_to_no_preference_positive(self):
        """Patient not open to group therapy should be included for therapist not preferring group."""
        # Create therapist not preferring group therapy
        therapist = self.create_test_therapist(
            bevorzugt_gruppentherapie=False,
            email="no.group.therapist@example.com"
        )
        
        # Create patient not open to group therapy
        patient = self.create_test_patient(
            offen_fuer_gruppentherapie=False,
            email="no.group.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_group_therapy_not_open_to_prefers_negative(self):
        """Patient not open to group therapy should NOT be included for therapist preferring group."""
        # Create therapist preferring group therapy
        therapist = self.create_test_therapist(
            bevorzugt_gruppentherapie=True,
            email="group.therapist@example.com"
        )
        
        # Create patient not open to group therapy
        patient = self.create_test_patient(
            offen_fuer_gruppentherapie=False,
            email="no.group.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    # ==================== COMBINATION CONSTRAINT TESTS ====================

    # --- Gender + Therapy Procedure Tests ---
    
    def test_gender_and_therapy_procedure_both_match_positive(self):
        """Patient with gender AND therapy procedure preferences matching should be included."""
        # Create female therapist offering Verhaltenstherapie
        therapist = self.create_test_therapist(
            geschlecht="weiblich",
            anrede="Frau",
            psychotherapieverfahren="Verhaltenstherapie",
            email="female.vt.therapist@example.com"
        )
        
        # Create patient preferring female AND Verhaltenstherapie
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            email="female.vt.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_gender_mismatch_therapy_match_negative(self):
        """Patient should NOT be included if gender doesn't match even if therapy procedure matches."""
        # Create male therapist offering Verhaltenstherapie
        therapist = self.create_test_therapist(
            geschlecht="männlich",
            anrede="Herr",
            psychotherapieverfahren="Verhaltenstherapie",
            email="male.vt.therapist@example.com"
        )
        
        # Create patient preferring female AND Verhaltenstherapie
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            email="female.vt.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_gender_match_therapy_mismatch_negative(self):
        """Patient should NOT be included if therapy procedure doesn't match even if gender matches."""
        # Create female therapist offering tiefenpsychologisch
        therapist = self.create_test_therapist(
            geschlecht="weiblich",
            anrede="Frau",
            psychotherapieverfahren="tiefenpsychologisch_fundierte_Psychotherapie",
            email="female.tp.therapist@example.com"
        )
        
        # Create patient preferring female AND Verhaltenstherapie
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            email="female.vt.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    # --- Gender + Group Therapy Tests ---
    
    def test_gender_and_group_both_match_positive(self):
        """Patient with gender preference AND open to group should be included for matching therapist."""
        # Create female therapist preferring group therapy
        therapist = self.create_test_therapist(
            geschlecht="weiblich",
            anrede="Frau",
            bevorzugt_gruppentherapie=True,
            email="female.group.therapist@example.com"
        )
        
        # Create patient preferring female AND open to group
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            offen_fuer_gruppentherapie=True,
            email="female.group.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_gender_match_not_open_to_group_negative(self):
        """Patient NOT open to group should NOT be included even if gender matches."""
        # Create female therapist preferring group therapy
        therapist = self.create_test_therapist(
            geschlecht="weiblich",
            anrede="Frau",
            bevorzugt_gruppentherapie=True,
            email="female.group.therapist@example.com"
        )
        
        # Create patient preferring female but NOT open to group
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            offen_fuer_gruppentherapie=False,
            email="female.nogroup.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_gender_mismatch_open_to_group_negative(self):
        """Patient open to group should NOT be included if gender doesn't match."""
        # Create male therapist not preferring group
        therapist = self.create_test_therapist(
            geschlecht="männlich",
            anrede="Herr",
            bevorzugt_gruppentherapie=False,
            email="male.nogroup.therapist@example.com"
        )
        
        # Create patient preferring female AND open to group
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            offen_fuer_gruppentherapie=True,
            email="female.group.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    # --- Therapy Procedure + Group Therapy Tests ---
    
    def test_therapy_and_group_both_match_positive(self):
        """Patient with therapy preference AND open to group should be included for matching therapist."""
        # Create therapist offering Verhaltenstherapie and preferring group
        therapist = self.create_test_therapist(
            psychotherapieverfahren="Verhaltenstherapie",
            bevorzugt_gruppentherapie=True,
            email="vt.group.therapist@example.com"
        )
        
        # Create patient preferring Verhaltenstherapie AND open to group
        patient = self.create_test_patient(
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            offen_fuer_gruppentherapie=True,
            email="vt.group.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_therapy_match_not_open_to_group_negative(self):
        """Patient NOT open to group should NOT be included even if therapy matches."""
        # Create therapist offering Verhaltenstherapie and preferring group
        therapist = self.create_test_therapist(
            psychotherapieverfahren="Verhaltenstherapie",
            bevorzugt_gruppentherapie=True,
            email="vt.group.therapist@example.com"
        )
        
        # Create patient preferring Verhaltenstherapie but NOT open to group
        patient = self.create_test_patient(
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            offen_fuer_gruppentherapie=False,
            email="vt.nogroup.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_therapy_mismatch_open_to_group_negative(self):
        """Patient open to group should NOT be included if therapy doesn't match."""
        # Create therapist offering tiefenpsychologisch not preferring group
        therapist = self.create_test_therapist(
            psychotherapieverfahren="tiefenpsychologisch_fundierte_Psychotherapie",
            bevorzugt_gruppentherapie=False,
            email="tp.nogroup.therapist@example.com"
        )
        
        # Create patient preferring Verhaltenstherapie AND open to group
        patient = self.create_test_patient(
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            offen_fuer_gruppentherapie=True,
            email="vt.group.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    # --- All Three Constraints Tests ---
    
    def test_all_three_constraints_match_positive(self):
        """Patient matching ALL three constraints should be included."""
        # Create female therapist offering Verhaltenstherapie and preferring group
        therapist = self.create_test_therapist(
            geschlecht="weiblich",
            anrede="Frau",
            psychotherapieverfahren="Verhaltenstherapie",
            bevorzugt_gruppentherapie=True,
            email="female.vt.group.therapist@example.com"
        )
        
        # Create patient preferring female, Verhaltenstherapie, AND open to group
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            offen_fuer_gruppentherapie=True,
            email="female.vt.group.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created successfully
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] >= 1
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_all_three_constraints_group_mismatch_negative(self):
        """Patient NOT open to group should NOT be included even if other constraints match."""
        # Create female therapist offering Verhaltenstherapie and preferring group
        therapist = self.create_test_therapist(
            geschlecht="weiblich",
            anrede="Frau",
            psychotherapieverfahren="Verhaltenstherapie",
            bevorzugt_gruppentherapie=True,
            email="female.vt.group.therapist@example.com"
        )
        
        # Create patient preferring female, Verhaltenstherapie, but NOT open to group
        patient = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            offen_fuer_gruppentherapie=False,
            email="female.vt.nogroup.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should return 200 with "no eligible patients" message
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no eligible patients" in data['message'].lower()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    # ==================== MULTIPLE PATIENTS TESTS ====================

    def test_multiple_patients_mixed_constraints(self):
        """Test anfrage creation with multiple patients having different constraint matches."""
        # Create therapist: female, Verhaltenstherapie, preferring group
        therapist = self.create_test_therapist(
            geschlecht="weiblich",
            anrede="Frau",
            psychotherapieverfahren="Verhaltenstherapie",
            bevorzugt_gruppentherapie=True,
            email="female.vt.group.therapist@example.com"
        )
        
        # Patient 1: Perfect match - all constraints satisfied
        patient1 = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            offen_fuer_gruppentherapie=True,
            email="perfect.match.patient@example.com"
        )
        
        # Patient 2: Gender mismatch - should NOT be included
        patient2 = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Männlich",
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            offen_fuer_gruppentherapie=True,
            email="gender.mismatch.patient@example.com"
        )
        
        # Patient 3: Not open to group - should NOT be included
        patient3 = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            offen_fuer_gruppentherapie=False,
            email="no.group.patient@example.com"
        )
        
        # Patient 4: Therapy mismatch - should NOT be included
        patient4 = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Weiblich",
            bevorzugtes_therapieverfahren="tiefenpsychologisch_fundierte_Psychotherapie",
            offen_fuer_gruppentherapie=True,
            email="therapy.mismatch.patient@example.com"
        )
        
        # Patient 5: All preferences "egal" - should be included
        patient5 = self.create_test_patient(
            bevorzugtes_therapeutengeschlecht="Egal",
            bevorzugtes_therapieverfahren="egal",
            offen_fuer_gruppentherapie=True,
            email="all.egal.patient@example.com"
        )
        
        # Create platzsuchen for all patients
        searches = []
        for patient in [patient1, patient2, patient3, patient4, patient5]:
            search = self.create_platzsuche_for_patient(patient['id'])
            searches.append(search)
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should be created with only matching patients (patient1 and patient5)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        anfrage = response.json()
        assert anfrage['anfragegroesse'] == 2, f"Expected 2 patients, got {anfrage['anfragegroesse']}"
        
        # Cleanup
        for search in searches:
            self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        for patient in [patient1, patient2, patient3, patient4, patient5]:
            self.safe_delete_patient(patient['id'])

    def test_edge_case_therapist_no_therapy_procedure(self):
        """Test handling when therapist has no therapy procedure specified."""
        # Create therapist without psychotherapieverfahren
        therapist = self.create_test_therapist(
            psychotherapieverfahren=None,
            email="no.procedure.therapist@example.com"
        )
        
        # Create patient with specific therapy preference
        patient = self.create_test_patient(
            bevorzugtes_therapieverfahren="Verhaltenstherapie",
            email="vt.patient@example.com"
        )
        
        # Create platzsuche
        search = self.create_platzsuche_for_patient(patient['id'])
        
        # Create anfrage
        response = self.create_anfrage_for_therapist(therapist['id'])
        
        # Should handle gracefully - likely no match due to missing therapist data
        assert response.status_code in [200, 201], f"Unexpected status code: {response.status_code}: {response.text}"
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])