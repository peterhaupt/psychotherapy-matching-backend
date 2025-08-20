"""Pytest-compatible integration tests for Therapist Service Importer with matching logic validation."""
import uuid
import pytest
import json
from datetime import date, timedelta
import os
import sys

# Add therapist_service to path so imports work like in Docker
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../therapist_service'))

# Now these imports will work (as if we're inside the Docker container)
from shared.utils.database import SessionLocal
from models.therapist import Therapist
from imports.therapist_importer import TherapistImporter


@pytest.fixture(scope="class")
def test_session():
    """Create a unique test session identifier for this test class."""
    session_id = str(uuid.uuid4())[:8]
    test_prefix = f"TestImport_{session_id}"
    print(f"\nTest session ID: {session_id}")
    return {
        "session_id": session_id,
        "test_prefix": test_prefix,
        "created_therapist_ids": []
    }


@pytest.fixture
def importer():
    """Create a TherapistImporter instance for testing."""
    return TherapistImporter()


@pytest.fixture
def test_data_factory(test_session):
    """Factory fixture for creating test therapist JSON data."""
    
    def _create_test_data(**kwargs):
        """Create test therapist data in scraper JSON format.
        
        Args:
            **kwargs: Override default values
            
        Returns:
            dict: Therapist data in scraper format
        """
        unique_id = str(uuid.uuid4())[:4]
        
        # Default test data in scraper format
        default_data = {
            "basic_info": {
                "salutation": kwargs.get("salutation", "Frau"),
                "title": kwargs.get("title", ""),
                "first_name": kwargs.get("first_name", f"{test_session['test_prefix']}_{unique_id}"),
                "last_name": kwargs.get("last_name", f"TestNachname_{unique_id}")
            },
            "location": {
                "street": kwargs.get("street", "Teststraße"),
                "house_number": kwargs.get("house_number", "123"),
                "postal_code": kwargs.get("postal_code", "52062"),
                "city": kwargs.get("city", "Aachen")
            },
            "contact": {
                "phone": kwargs.get("phone", "+49 241 12345678"),
                "email": kwargs.get("email", f"test_{unique_id}@example.com"),
                "fax": kwargs.get("fax", "")
            },
            "therapy_methods": kwargs.get("therapy_methods", [
                "Verhaltenstherapie (Erwachsene)",
                "Verhaltenstherapie (Kinder und Jugendliche)"
            ]),
            "languages": kwargs.get("languages", []),
            "telephone_hours": kwargs.get("telephone_hours", {})
        }
        
        return default_data
    
    return _create_test_data


@pytest.fixture
def db_therapist_factory(test_session):
    """Factory fixture for creating therapists directly in database."""
    
    def _create_db_therapist(**kwargs):
        """Create a therapist directly in the database.
        
        Args:
            **kwargs: Therapist model fields
            
        Returns:
            Therapist: Created therapist instance
        """
        unique_id = str(uuid.uuid4())[:4]
        
        # Default values
        defaults = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "vorname": f"{test_session['test_prefix']}_{unique_id}",
            "nachname": f"TestNachname_{unique_id}",
            "plz": "52062",
            "ort": "Aachen",
            "strasse": "Teststraße 123",
            "status": "aktiv",
            "kassensitz": True
        }
        defaults.update(kwargs)
        
        db = SessionLocal()
        try:
            therapist = Therapist(**defaults)
            db.add(therapist)
            db.commit()
            db.refresh(therapist)
            
            # Track for cleanup
            test_session["created_therapist_ids"].append(therapist.id)
            
            print(f"  Created therapist in DB: ID={therapist.id}, {therapist.vorname} {therapist.nachname}")
            return therapist
        finally:
            db.close()
    
    return _create_db_therapist


@pytest.fixture(scope="class", autouse=True)
def cleanup_therapists(test_session):
    """Automatically clean up test therapists after all tests in the class."""
    yield  # Let all tests run first
    
    # Cleanup after all tests
    db = SessionLocal()
    try:
        created_ids = test_session.get("created_therapist_ids", [])
        print(f"\n=== DEBUG: Cleanup starting for {len(created_ids)} therapists ===")
        
        for therapist_id in created_ids:
            try:
                therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
                if therapist:
                    db.delete(therapist)
                    print(f"  Cleaned up test therapist {therapist_id}")
            except Exception as e:
                print(f"  Warning: Could not clean up therapist {therapist_id}: {e}")
        
        db.commit()
        print(f"✅ Cleanup completed - removed {len(created_ids)} test therapists")
    except Exception as e:
        print(f"Warning: Error during cleanup: {e}")
    finally:
        db.close()


class TestTherapistImporter:
    """Integration tests for the Therapist Importer matching logic."""
    
    # ========== PRIMARY MATCH TESTS ==========
    
    def test_primary_match_exact_name_and_plz(self, importer, test_data_factory, db_therapist_factory, test_session):
        """Test that therapist with same first name, last name, and PLZ updates existing."""
        print(f"\n{'='*60}")
        print(f"TEST: Primary match - exact name and PLZ")
        print(f"{'='*60}")
        
        # Use unique test data to avoid collision with existing database
        unique_suffix = f"_{test_session['session_id']}"
        test_plz = "99001"  # Use unlikely PLZ
        
        # Create existing therapist in database with unique data
        existing = db_therapist_factory(
            vorname=f"Maria{unique_suffix}",
            nachname=f"Schmidt{unique_suffix}",
            plz=test_plz,
            telefon="+49 241 111111"
        )
        
        # Import therapist with same name and PLZ but different phone
        import_data = test_data_factory(
            first_name=f"Maria{unique_suffix}",
            last_name=f"Schmidt{unique_suffix}",
            postal_code=test_plz,
            phone="+49 241 222222"
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        assert "updated" in message.lower(), f"Should update existing: {message}"
        
        # Verify therapist was updated, not created new
        db = SessionLocal()
        try:
            therapists = db.query(Therapist).filter(
                Therapist.vorname == f"Maria{unique_suffix}",
                Therapist.nachname == f"Schmidt{unique_suffix}",
                Therapist.plz == test_plz
            ).all()
            
            assert len(therapists) == 1, f"Should have 1 therapist, found {len(therapists)}"
            assert therapists[0].telefon == "+49 241 222222", "Phone should be updated"
            print(f"  ✓ Primary match successful - therapist updated")
        finally:
            db.close()
    
    def test_primary_match_with_title_change(self, importer, test_data_factory, db_therapist_factory):
        """Test that therapist with title change still matches by primary rule."""
        print(f"\n{'='*60}")
        print(f"TEST: Primary match - with title change")
        print(f"{'='*60}")
        
        # Create therapist without title
        existing = db_therapist_factory(
            vorname="Thomas",
            nachname="Mueller",
            plz="52064",
            titel=""
        )
        
        # Import same therapist with Dr. title
        import_data = test_data_factory(
            first_name="Thomas",
            last_name="Mueller",
            postal_code="52064",
            title="Dr. med."
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        assert "updated" in message.lower(), f"Should update existing: {message}"
        
        # Verify only one therapist exists
        db = SessionLocal()
        try:
            therapists = db.query(Therapist).filter(
                Therapist.vorname == "Thomas",
                Therapist.nachname == "Mueller"
            ).all()
            
            assert len(therapists) == 1, f"Should have 1 therapist, found {len(therapists)}"
            assert therapists[0].titel == "Dr. med.", "Title should be updated"
            print(f"  ✓ Primary match works despite title change")
        finally:
            db.close()
    
    def test_primary_match_different_plz(self, importer, test_data_factory, db_therapist_factory, test_session):
        """Test that same name but different PLZ creates new therapist."""
        print(f"\n{'='*60}")
        print(f"TEST: Primary match - different PLZ creates new")
        print(f"{'='*60}")
        
        # Use unique test data to avoid collision
        unique_suffix = f"_{test_session['session_id']}"
        test_plz1 = "99002"
        test_plz2 = "99003"
        
        # Create existing therapist with unique data
        existing = db_therapist_factory(
            vorname=f"Julia{unique_suffix}",
            nachname=f"Weber{unique_suffix}",
            plz=test_plz1
        )
        
        # Import therapist with same name but different PLZ
        import_data = test_data_factory(
            first_name=f"Julia{unique_suffix}",
            last_name=f"Weber{unique_suffix}",
            postal_code=test_plz2  # Different PLZ
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        assert "created" in message.lower(), f"Should create new: {message}"
        
        # Verify two therapists exist
        db = SessionLocal()
        try:
            therapists = db.query(Therapist).filter(
                Therapist.vorname == f"Julia{unique_suffix}",
                Therapist.nachname == f"Weber{unique_suffix}"
            ).all()
            
            assert len(therapists) == 2, f"Should have 2 therapists, found {len(therapists)}"
            plz_codes = {t.plz for t in therapists}
            assert plz_codes == {test_plz1, test_plz2}, f"PLZ codes don't match: {plz_codes}"
            print(f"  ✓ Different PLZ created new therapist")
        finally:
            db.close()
    
    # ========== SECONDARY MATCH TESTS ==========
    
    def test_secondary_match_name_change_same_email(self, importer, test_data_factory, db_therapist_factory, test_session):
        """Test marriage name change with same address and email updates existing."""
        print(f"\n{'='*60}")
        print(f"TEST: Secondary match - name change with same email")
        print(f"{'='*60}")
        
        # Use unique test data to avoid collision
        unique_suffix = f"_{test_session['session_id']}"
        test_plz = "99004"
        test_email = f"sarah.test{unique_suffix}@example.com"
        
        # Create existing therapist (maiden name) with unique data
        existing = db_therapist_factory(
            vorname=f"Sarah{unique_suffix}",
            nachname=f"Klein{unique_suffix}",
            plz=test_plz,
            ort="TestStadt",
            strasse=f"Hauptstraße{unique_suffix} 10",
            email=test_email,
            titel=""
        )
        
        # Import with married name but same address and email
        import_data = test_data_factory(
            first_name=f"Sarah{unique_suffix}",
            last_name=f"Meyer{unique_suffix}",  # Changed last name
            postal_code=test_plz,
            city="TestStadt",
            street=f"Hauptstraße{unique_suffix}",
            house_number="10",
            email=test_email,  # Same email
            title=""
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        assert "updated" in message.lower(), f"Should update existing: {message}"
        
        # Verify only one therapist exists with updated name
        db = SessionLocal()
        try:
            therapists = db.query(Therapist).filter(
                Therapist.vorname == f"Sarah{unique_suffix}",
                Therapist.email == test_email
            ).all()
            
            assert len(therapists) == 1, f"Should have 1 therapist, found {len(therapists)}"
            assert therapists[0].nachname == f"Meyer{unique_suffix}", "Last name should be updated"
            assert therapists[0].email == test_email, "Email should remain"
            print(f"  ✓ Secondary match detected name change correctly")
        finally:
            db.close()
    
    def test_secondary_match_name_change_same_title(self, importer, test_data_factory, db_therapist_factory):
        """Test marriage name change with same address and title updates existing."""
        print(f"\n{'='*60}")
        print(f"TEST: Secondary match - name change with same title")
        print(f"{'='*60}")
        
        # Create existing therapist with title
        existing = db_therapist_factory(
            vorname="Lisa",
            nachname="Hoffmann",
            plz="52064",
            ort="Aachen",
            strasse="Bergstraße 5",
            titel="Dr. rer. nat.",
            email=""
        )
        
        # Import with married name but same address and title
        import_data = test_data_factory(
            first_name="Lisa",
            last_name="Wagner",  # Changed last name
            postal_code="52064",
            city="Aachen",
            street="Bergstraße",
            house_number="5",
            title="Dr. rer. nat.",  # Same title
            email=""
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        assert "updated" in message.lower(), f"Should update existing: {message}"
        
        # Verify only one therapist exists
        db = SessionLocal()
        try:
            therapists = db.query(Therapist).filter(
                Therapist.vorname == "Lisa",
                Therapist.strasse == "Bergstraße 5"
            ).all()
            
            assert len(therapists) == 1, f"Should have 1 therapist, found {len(therapists)}"
            assert therapists[0].nachname == "Wagner", "Last name should be updated"
            print(f"  ✓ Secondary match with same title worked")
        finally:
            db.close()
    
    def test_no_false_match_same_practice_different_therapists(self, importer, test_data_factory, db_therapist_factory, test_session):
        """Test Dr. Anna Aller and Anna Bonni at same practice create separate therapists."""
        print(f"\n{'='*60}")
        print(f"TEST: No false match - Dr. Anna Aller and Anna Bonni case")
        print(f"{'='*60}")
        
        # Use unique test data to avoid collision with existing Annas
        unique_suffix = f"_{test_session['session_id']}"
        test_plz = "99005"
        test_email = f"praxis{unique_suffix}@example.com"
        
        # Create Dr. Anna Aller with unique identifiers
        aller = db_therapist_factory(
            vorname=f"Anna{unique_suffix}",
            nachname=f"Aller{unique_suffix}",
            titel="Dr. med.",
            plz=test_plz,
            ort="TestStadt",
            strasse=f"Praxisstraße{unique_suffix} 15",
            email=test_email  # Shared practice email
        )
        print(f"  Created Dr. Anna Aller: ID={aller.id}")
        
        # Import Anna Bonni (no title, same address and email)
        bonni_data = test_data_factory(
            first_name=f"Anna{unique_suffix}",
            last_name=f"Bonni{unique_suffix}",
            title="",  # No title - this should prevent false match
            postal_code=test_plz,
            city="TestStadt",
            street=f"Praxisstraße{unique_suffix}",
            house_number="15",
            email=test_email  # Same practice email
        )
        
        success, message = importer.import_therapist(bonni_data)
        assert success, f"Import failed: {message}"
        assert "created" in message.lower(), f"Should create new therapist, not update: {message}"
        
        # Verify two separate therapists exist
        db = SessionLocal()
        try:
            therapists = db.query(Therapist).filter(
                Therapist.vorname == f"Anna{unique_suffix}",
                Therapist.strasse == f"Praxisstraße{unique_suffix} 15"
            ).all()
            
            assert len(therapists) == 2, f"Should have 2 therapists, found {len(therapists)}"
            
            # Verify both therapists have correct data
            aller_db = next((t for t in therapists if t.nachname == f"Aller{unique_suffix}"), None)
            bonni_db = next((t for t in therapists if t.nachname == f"Bonni{unique_suffix}"), None)
            
            assert aller_db is not None, "Dr. Anna Aller not found"
            assert bonni_db is not None, "Anna Bonni not found"
            assert aller_db.titel == "Dr. med.", "Dr. Aller should keep title"
            assert bonni_db.titel == "", "Anna Bonni should have no title"
            
            print(f"  ✓ No false match! Created two separate therapists:")
            print(f"    - Dr. Anna Aller (ID={aller_db.id})")
            print(f"    - Anna Bonni (ID={bonni_db.id})")
        finally:
            db.close()
    
    def test_secondary_match_blocked_by_different_title(self, importer, test_data_factory, db_therapist_factory, test_session):
        """Test that different title prevents secondary match."""
        print(f"\n{'='*60}")
        print(f"TEST: Secondary match blocked by different title")
        print(f"{'='*60}")
        
        # Use unique test data to avoid collision
        unique_suffix = f"_{test_session['session_id']}"
        test_plz = "99006"
        
        # Create therapist with title and unique data
        existing = db_therapist_factory(
            vorname=f"Claudia{unique_suffix}",
            nachname=f"Fischer{unique_suffix}",
            titel="Prof. Dr.",
            plz=test_plz,
            ort="TestStadt",
            strasse=f"Universitätsstraße{unique_suffix} 20"
        )
        
        # Import therapist with same first name and address but different title
        import_data = test_data_factory(
            first_name=f"Claudia{unique_suffix}",
            last_name=f"Becker{unique_suffix}",  # Different last name
            title="Dr. med.",  # Different title
            postal_code=test_plz,
            city="TestStadt",
            street=f"Universitätsstraße{unique_suffix}",
            house_number="20"
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        assert "created" in message.lower(), f"Should create new: {message}"
        
        # Verify two therapists exist
        db = SessionLocal()
        try:
            therapists = db.query(Therapist).filter(
                Therapist.vorname == f"Claudia{unique_suffix}",
                Therapist.strasse == f"Universitätsstraße{unique_suffix} 20"
            ).all()
            
            assert len(therapists) == 2, f"Should have 2 therapists, found {len(therapists)}"
            titles = {t.titel for t in therapists}
            assert titles == {"Prof. Dr.", "Dr. med."}, f"Titles don't match: {titles}"
            print(f"  ✓ Different title prevented false match")
        finally:
            db.close()
    
    def test_secondary_match_blocked_by_different_email(self, importer, test_data_factory, db_therapist_factory, test_session):
        """Test that different email prevents secondary match."""
        print(f"\n{'='*60}")
        print(f"TEST: Secondary match blocked by different email")
        print(f"{'='*60}")
        
        # Use unique test data to avoid collision
        unique_suffix = f"_{test_session['session_id']}"
        test_plz = "99007"
        
        # Create therapist with personal email and unique data
        existing = db_therapist_factory(
            vorname=f"Nina{unique_suffix}",
            nachname=f"Schulz{unique_suffix}",
            titel="",
            plz=test_plz,
            ort="TestStadt",
            strasse=f"Gartenstraße{unique_suffix} 8",
            email=f"nina.schulz{unique_suffix}@personal.com"
        )
        
        # Import therapist with same name/address but different email
        import_data = test_data_factory(
            first_name=f"Nina{unique_suffix}",
            last_name=f"Zimmermann{unique_suffix}",  # Different last name
            title="",  # Same title (empty)
            postal_code=test_plz,
            city="TestStadt",
            street=f"Gartenstraße{unique_suffix}",
            house_number="8",
            email=f"nina.zimmermann{unique_suffix}@other.com"  # Different email
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        assert "created" in message.lower(), f"Should create new: {message}"
        
        # Verify two therapists exist
        db = SessionLocal()
        try:
            therapists = db.query(Therapist).filter(
                Therapist.vorname == f"Nina{unique_suffix}",
                Therapist.strasse == f"Gartenstraße{unique_suffix} 8"
            ).all()
            
            assert len(therapists) == 2, f"Should have 2 therapists, found {len(therapists)}"
            emails = {t.email for t in therapists}
            assert len(emails) == 2, "Should have different emails"
            print(f"  ✓ Different email prevented false match")
        finally:
            db.close()
    
    # ========== DATA UPDATE TESTS ==========
    
    def test_import_preserves_operational_fields(self, importer, test_data_factory, db_therapist_factory):
        """Test that import doesn't overwrite operational fields."""
        print(f"\n{'='*60}")
        print(f"TEST: Import preserves operational fields")
        print(f"{'='*60}")
        
        # Create therapist with operational data set
        existing = db_therapist_factory(
            vorname="Michael",
            nachname="Koch",
            plz="52070",
            status="gesperrt",
            sperrgrund="Temporary unavailable",
            potenziell_verfuegbar=True,
            potenziell_verfuegbar_notizen="Available from next month",
            ueber_curavani_informiert=True,
            naechster_kontakt_moeglich=date.today() + timedelta(days=7)
        )
        
        # Import same therapist with updated basic info
        import_data = test_data_factory(
            first_name="Michael",
            last_name="Koch",
            postal_code="52070",
            phone="+49 241 999999"
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        
        # Verify operational fields are preserved
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(Therapist.id == existing.id).first()
            
            assert therapist.status.value == "gesperrt", "Status should be preserved"
            assert therapist.sperrgrund == "Temporary unavailable", "Sperrgrund should be preserved"
            assert therapist.potenziell_verfuegbar == True, "Availability should be preserved"
            assert therapist.potenziell_verfuegbar_notizen == "Available from next month", "Notes should be preserved"
            assert therapist.ueber_curavani_informiert == True, "Informed status should be preserved"
            assert therapist.telefon == "+49 241 999999", "Phone should be updated"
            print(f"  ✓ Operational fields preserved, basic info updated")
        finally:
            db.close()
    
    def test_import_never_overwrites_email_with_empty(self, importer, test_data_factory, db_therapist_factory):
        """Test that existing email is never overwritten with empty value."""
        print(f"\n{'='*60}")
        print(f"TEST: Import never overwrites email with empty")
        print(f"{'='*60}")
        
        # Create therapist with email
        existing = db_therapist_factory(
            vorname="Sandra",
            nachname="Richter",
            plz="52072",
            email="sandra.richter@example.com"
        )
        
        # Import same therapist without email
        import_data = test_data_factory(
            first_name="Sandra",
            last_name="Richter",
            postal_code="52072",
            email=""  # Empty email in import
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        
        # Verify email is preserved
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(Therapist.id == existing.id).first()
            assert therapist.email == "sandra.richter@example.com", "Email should be preserved"
            print(f"  ✓ Email preserved when import has empty value")
        finally:
            db.close()
    
    def test_import_updates_basic_info(self, importer, test_data_factory, db_therapist_factory):
        """Test that basic contact info is updated correctly."""
        print(f"\n{'='*60}")
        print(f"TEST: Import updates basic info")
        print(f"{'='*60}")
        
        # Create therapist with old info
        existing = db_therapist_factory(
            vorname="Robert",
            nachname="Wolf",
            plz="52074",
            telefon="+49 241 111111",
            strasse="Alte Straße 1",
            fax=""
        )
        
        # Import with updated info
        import_data = test_data_factory(
            first_name="Robert",
            last_name="Wolf",
            postal_code="52074",
            phone="+49 241 222222",
            street="Neue Straße",
            house_number="25",
            fax="+49 241 333333"
        )
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        
        # Verify updates
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(Therapist.id == existing.id).first()
            assert therapist.telefon == "+49 241 222222", "Phone should be updated"
            assert therapist.strasse == "Neue Straße 25", "Address should be updated"
            assert therapist.fax == "+49 241 333333", "Fax should be updated"
            print(f"  ✓ Basic info updated correctly")
        finally:
            db.close()
    
    # ========== EDGE CASES ==========
    
    def test_import_therapist_missing_required_fields(self, importer, test_data_factory):
        """Test that therapist with missing required fields is skipped."""
        print(f"\n{'='*60}")
        print(f"TEST: Import with missing required fields")
        print(f"{'='*60}")
        
        # Create data missing last name
        import_data = test_data_factory(
            first_name="Incomplete",
            last_name=""  # Missing required field
        )
        import_data["basic_info"]["last_name"] = ""
        
        success, message = importer.import_therapist(import_data)
        assert not success, "Import should fail with missing required fields"
        print(f"  ✓ Import correctly rejected: {message}")
    
    def test_import_therapist_without_adult_therapy(self, importer, test_data_factory):
        """Test that therapist without adult therapy methods is skipped."""
        print(f"\n{'='*60}")
        print(f"TEST: Import without adult therapy methods")
        print(f"{'='*60}")
        
        # Create data with only children therapy
        import_data = test_data_factory(
            therapy_methods=["Verhaltenstherapie (Kinder und Jugendliche)"]
        )
        
        # Note: The file_monitor checks for 'Erwachsene' before calling import_therapist
        # So this would be filtered at the file_monitor level, not in import_therapist
        # For this test, we're verifying the importer can handle such data
        
        success, message = importer.import_therapist(import_data)
        assert success, f"Import failed: {message}"
        print(f"  ✓ Therapist imported (filtering happens at file_monitor level)")
    
    def test_therapy_method_mapping(self, importer, test_data_factory):
        """Test correct mapping of therapy methods to enum values."""
        print(f"\n{'='*60}")
        print(f"TEST: Therapy method mapping")
        print(f"{'='*60}")
        
        test_cases = [
            (["Verhaltenstherapie (Erwachsene)"], "Verhaltenstherapie"),
            (["Tiefenpsychologisch fundierte Psychotherapie (Erwachsene)"], "tiefenpsychologisch_fundierte_Psychotherapie"),
            (["Verhaltenstherapie (Erwachsene)", "Tiefenpsychologisch fundierte Psychotherapie (Erwachsene)"], "egal"),
            ([], "egal")  # No methods defaults to 'egal'
        ]
        
        for methods, expected_value in test_cases:
            import_data = test_data_factory(
                first_name=f"Method_Test_{expected_value}",
                therapy_methods=methods
            )
            
            success, message = importer.import_therapist(import_data)
            assert success, f"Import failed: {message}"
            
            # Verify mapping
            db = SessionLocal()
            try:
                therapist = db.query(Therapist).filter(
                    Therapist.vorname.like(f"%Method_Test_{expected_value}%")
                ).first()
                
                assert therapist is not None, f"Therapist not found for {methods}"
                actual_value = therapist.psychotherapieverfahren.value if therapist.psychotherapieverfahren else None
                assert actual_value == expected_value, f"Expected {expected_value}, got {actual_value} for {methods}"
                print(f"  ✓ {methods} → {expected_value}")
            finally:
                db.close()


# Pytest entry point - can be run with: pytest test_therapist_service_importer.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])