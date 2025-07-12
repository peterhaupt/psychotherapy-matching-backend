"""Patient Service - Psychotherapy Patient Management System.

This service handles patient registration, data management, and import processes
for the Curavani psychotherapy matching platform.

Key Components:
- Patient API endpoints for CRUD operations
- Automated GCS file import system
- Event-driven communication with other services
- Patient data validation and processing
"""

__version__ = "1.0.0"
__service_name__ = "patient-service"

# Optional: Import key components for easier access
# Uncomment if you want to allow: from patient_service import Patient
# from .models.patient import Patient
# from .imports.import_status import ImportStatus