# API Pagination Consistency Implementation Guide

## Overview

### Problem
The microservices in the therapy platform have inconsistent API response formats:
- **Patient & Therapist Services**: Return plain lists `[{}, {}, ...]`
- **Communication Service**: Returns plain lists `[{}, {}, ...]`
- **Matching Service**: Returns paginated structure `{"data": [...], "page": ..., "limit": ..., "total": ...}`
- **Service Consumers**: Expect `{"data": [...]}` structure

This causes 500 errors when services try to call each other.

### Solution
Standardize all list endpoints to return the paginated structure:
```json
{
  "data": [...],
  "page": 1,
  "limit": 20,
  "total": 100
}
```

## Implementation Steps

### Step 1: Update Base Resource Class

**File**: `shared/api/base_resource.py`

Add a new helper method to the `PaginatedListResource` class:

```python
def create_paginated_response(self, query, marshal_func, resource_fields):
    """Create a standardized paginated response.
    
    Args:
        query: SQLAlchemy query object (before pagination)
        marshal_func: Flask-RESTful marshal function
        resource_fields: Field definition for marshalling
        
    Returns:
        dict: Paginated response with data, page, limit, and total
    """
    # Get pagination parameters
    page, limit = self.get_pagination_params()
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    paginated_query = self.paginate_query(query)
    
    # Get results
    items = paginated_query.all()
    
    # Marshal the results
    data = [marshal_func(item, resource_fields) for item in items]
    
    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total
    }
```

### Step 2: Update Patient Service

**File**: `patient_service/api/patients.py`

Update the `PatientListResource.get()` method:

```python
def get(self):
    """Get a list of patients with optional filtering and pagination."""
    # Parse query parameters for filtering
    status = request.args.get('status')
    
    db = SessionLocal()
    try:
        query = db.query(Patient)
        
        # Apply filters if provided
        if status:
            try:
                status_enum = validate_and_get_patient_status(status)
                query = query.filter(Patient.status == status_enum)
            except ValueError:
                # If status value not found, return empty result
                return {
                    "data": [],
                    "page": 1,
                    "limit": self.DEFAULT_LIMIT,
                    "total": 0
                }
        
        # Use the new helper method
        return self.create_paginated_response(query, marshal, patient_fields)
        
    except SQLAlchemyError as e:
        return {'message': f'Database error: {str(e)}'}, 500
    finally:
        db.close()
```

### Step 3: Update Therapist Service

**File**: `therapist_service/api/therapists.py`

Update the `TherapistListResource.get()` method:

```python
def get(self):
    """Get a list of therapists with optional filtering and pagination."""
    # Parse query parameters for filtering
    status = request.args.get('status')
    potenziell_verfuegbar = request.args.get('potenziell_verfuegbar', type=bool)
    
    db = SessionLocal()
    try:
        query = db.query(Therapist)
        
        # Apply filters if provided
        if status:
            try:
                status_enum = validate_and_get_therapist_status(status)
                query = query.filter(Therapist.status == status_enum)
            except ValueError:
                # If status value not found, return empty result
                return {
                    "data": [],
                    "page": 1,
                    "limit": self.DEFAULT_LIMIT,
                    "total": 0
                }
        
        if potenziell_verfuegbar is not None:
            query = query.filter(Therapist.potenziell_verfuegbar == potenziell_verfuegbar)
        
        # Use the new helper method
        return self.create_paginated_response(query, marshal, therapist_fields)
        
    except SQLAlchemyError as e:
        return {'message': f'Database error: {str(e)}'}, 500
    finally:
        db.close()
```

### Step 4: Update Communication Service

**File**: `communication_service/api/emails.py`

Update the `EmailListResource.get()` method to use the helper:

```python
def get(self):
    """Get a list of emails with optional filtering and pagination."""
    # ... existing filter parsing code ...
    
    db = SessionLocal()
    try:
        query = db.query(Email)
        
        # ... existing filter application code ...
        
        # Use the new helper method
        return self.create_paginated_response(query, marshal, email_fields)
        
    except SQLAlchemyError as e:
        return {'message': f'Database error: {str(e)}'}, 500
    finally:
        db.close()
```

**File**: `communication_service/api/phone_calls.py`

Update the `PhoneCallListResource.get()` method similarly:

```python
def get(self):
    """Get a list of phone calls with optional filtering and pagination."""
    # ... existing filter parsing code ...
    
    db = SessionLocal()
    try:
        query = db.query(PhoneCall)
        
        # ... existing filter application code ...
        
        # Use the new helper method
        return self.create_paginated_response(query, marshal, phone_call_fields)
        
    except SQLAlchemyError as e:
        return {'message': f'Database error: {str(e)}'}, 500
    finally:
        db.close()
```

### Step 5: Update Matching Service Consumers

**File**: `matching_service/services.py`

Update the service consumer methods:

1. **PatientService.get_all_patients()**:
```python
@staticmethod
def get_all_patients(status: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """Get all patients from the Patient Service."""
    try:
        url = f"{config.get_service_url('patient', internal=True)}/api/patients"
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            # Now expecting paginated structure
            return result.get("data", [])
        else:
            logger.error(f"Error fetching patients: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        logger.error(f"Failed to fetch patients: {str(e)}")
        return []
```

2. **TherapistService.get_all_therapists()**:
```python
@staticmethod
def get_all_therapists(status: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """Get all therapists from the Therapist Service."""
    try:
        url = f"{config.get_service_url('therapist', internal=True)}/api/therapists"
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            # Now expecting paginated structure
            return result.get("data", [])
        else:
            logger.error(f"Error fetching therapists: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        logger.error(f"Failed to fetch therapists: {str(e)}")
        return []
```

3. **TherapistService.get_contactable_therapists()**:
```python
@staticmethod
def get_contactable_therapists() -> List[Dict[str, Any]]:
    """Get all therapists who can be contacted (not in cooling period)."""
    try:
        url = f"{config.get_service_url('therapist', internal=True)}/api/therapists"
        params = {
            'status': 'aktiv',
            'limit': 1000
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            therapists = result.get("data", [])
            
            # Filter out therapists in cooling period
            today = datetime.utcnow().date()
            contactable = []
            
            for therapist in therapists:
                next_contact = therapist.get('naechster_kontakt_moeglich')
                if not next_contact or datetime.fromisoformat(next_contact).date() <= today:
                    contactable.append(therapist)
            
            logger.info(f"Found {len(contactable)} contactable therapists out of {len(therapists)} active")
            return contactable
        else:
            logger.error(f"Error fetching therapists: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        logger.error(f"Failed to fetch therapists: {str(e)}")
        return []
```

### Step 6: Update Integration Tests

**File**: `tests/integration/test_patient_service_api.py`

Update assertions for list endpoints:

```python
def test_get_patients_list_empty(self):
    """Test getting empty patient list."""
    response = requests.get(f"{BASE_URL}/patients")
    assert response.status_code == 200
    
    # Now expecting paginated structure
    data = response.json()
    assert isinstance(data, dict)
    assert 'data' in data
    assert isinstance(data['data'], list)
    assert data['page'] == 1
    assert data['limit'] == 20  # Default limit
    assert data['total'] == 0

def test_get_patients_list_with_data(self):
    """Test getting patient list with data."""
    # Create test patients
    patient1 = self.create_test_patient(vorname="Anna", nachname="Müller")
    patient2 = self.create_test_patient(vorname="Max", nachname="Schmidt")
    
    response = requests.get(f"{BASE_URL}/patients")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert 'data' in data
    patients = data['data']
    assert len(patients) >= 2
    
    # Verify our patients are in the list
    patient_ids = [p['id'] for p in patients]
    assert patient1['id'] in patient_ids
    assert patient2['id'] in patient_ids
    
    # Verify pagination metadata
    assert data['total'] >= 2
```

**File**: `tests/integration/test_therapist_service_api.py`

Similar updates for therapist tests:

```python
def test_get_therapists_list_empty(self):
    """Test getting empty therapist list."""
    response = requests.get(f"{BASE_URL}/therapists")
    assert response.status_code == 200
    
    # Now expecting paginated structure
    data = response.json()
    assert isinstance(data, dict)
    assert 'data' in data
    assert isinstance(data['data'], list)
    assert data['page'] == 1
    assert data['limit'] == 20
    assert data['total'] == 0
```

**File**: `tests/integration/test_communication_service_api.py`

Update email and phone call list tests:

```python
def test_get_emails_list_empty(self):
    """Test getting empty email list."""
    response = requests.get(f"{COMM_BASE_URL}/emails")
    assert response.status_code == 200
    
    # Now expecting paginated structure
    data = response.json()
    assert isinstance(data, dict)
    assert 'data' in data
    assert isinstance(data['data'], list)
    assert data['page'] == 1
    assert data['limit'] == 20
    assert data['total'] == 0
```

## Verification Steps

1. **Run the updated integration tests**:
   ```bash
   pytest tests/integration/test_patient_service_api.py -v
   pytest tests/integration/test_therapist_service_api.py -v
   pytest tests/integration/test_communication_service_api.py -v
   pytest tests/integration/test_matching_service_api.py -v
   ```

2. **Test the API manually**:
   ```bash
   # Test patient service
   curl http://localhost:8001/api/patients
   
   # Test with pagination
   curl "http://localhost:8001/api/patients?page=2&limit=5"
   
   # Test therapist service
   curl http://localhost:8002/api/therapists
   
   # Test communication service
   curl http://localhost:8004/api/emails
   ```

3. **Verify inter-service communication**:
   - The matching service should now work without 500 errors when calling other services

## Expected Response Format

All list endpoints should now return:

```json
{
  "data": [
    {
      "id": 1,
      "vorname": "Test",
      "nachname": "Patient",
      // ... other fields
    },
    {
      "id": 2,
      "vorname": "Another",
      "nachname": "Patient",
      // ... other fields
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 42
}
```

## Notes

- Empty results still return the structure with `"data": []` and `"total": 0`
- The `page` parameter is 1-based (first page is 1, not 0)
- The `limit` parameter is capped at 100 by the base class
- When filters result in no matches, return the empty structure, not an empty list
- All services now have consistent pagination behavior