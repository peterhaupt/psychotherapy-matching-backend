# Psychotherapy Matching Platform

A comprehensive microservice-based system for matching patients with therapists in Germany.

---

## IMPORTANT DISCLAIMERS AND WARNINGS

### Medical and Mental Health Disclaimer

**THIS SOFTWARE IS NOT INTENDED FOR MEDICAL OR MENTAL HEALTH TREATMENT**

- This platform is a demonstration project and portfolio piece showing technical capabilities
- **DO NOT USE** this software to diagnose, treat, cure, or prevent any disease or medical condition
- **DO NOT USE** this software as a substitute for professional medical advice, diagnosis, or treatment
- This software is not designed to provide emergency services or crisis intervention
- Always seek the advice of qualified health providers with any questions regarding medical or mental health conditions
- If you are experiencing a mental health emergency, contact emergency services immediately

### Legal and Regulatory Compliance

**USERS ARE SOLELY RESPONSIBLE FOR LEGAL COMPLIANCE**

- Healthcare regulations vary significantly by country, region, and jurisdiction
- Users of this software must ensure full compliance with all applicable laws and regulations, including but not limited to:
  - Medical device regulations (e.g., EU MDR, FDA regulations)
  - Health data protection laws (e.g., GDPR, HIPAA, national data protection laws)
  - Healthcare provider licensing requirements
  - Patient consent and privacy requirements
  - Professional liability and insurance requirements
- This software is provided as a technical demonstration only
- The authors and contributors make no representations regarding regulatory compliance
- It is your responsibility to obtain all necessary legal approvals, certifications, and licenses before deploying this system

### Data Protection and Privacy

- This system processes sensitive personal health information
- You must implement appropriate security measures and data protection safeguards
- You are responsible for conducting privacy impact assessments and data protection compliance reviews
- Never deploy this system with real patient data without proper legal authorization and security measures

### No Warranty

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. See the LICENSE file for full details.

---

## Project Overview

The Psychotherapy Matching Platform facilitates the efficient assignment of psychotherapy places to patients in need. The system manages patient data, therapist information, and automates the matching and communication process.

## Core Components

- **Patient Service**: Patient profile management and tracking
- **Therapist Service**: Therapist data and availability management
- **Matching Service**: Implementation of matching algorithm
- **Communication Service**: Email and phone call management
- **Geocoding Service**: Location-based calculations and distance management
- **Scraping Service**: Therapist data acquisition from 116117.de ([Separate Repository](https://github.com/peterhaupt/curavani_scraping))

## Architecture

The system follows a microservice architecture with:

- Python/Flask backend services
- Kafka for event-driven communication
- PostgreSQL database with PgBouncer for connection pooling
- Docker containers for all components
- RESTful APIs for inter-service communication

## Development Status

- ✅ Environment Setup
- ✅ Database Configuration
- ✅ Patient Service
- ✅ Therapist Service
- ✅ Matching Service
- ✅ Communication Service
- ✅ Geocoding Service
- ✅ Scraping Service (Developed in [separate repository](https://github.com/peterhaupt/curavani_scraping))
- 🔄 Web Interface (Planned)
- 🔄 Testing Enhancements (In progress)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git
- Make (optional)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/peterhaupt/psychotherapy-matching-backend.git
   ```

2. Start the services:
   ```
   docker-compose up -d
   ```

3. Initialize the database:
   ```
   cd migrations
   alembic upgrade head
   ```

4. Access the service APIs:
   - Patient Service: http://localhost:8001
   - Therapist Service: http://localhost:8002
   - Matching Service: http://localhost:8003
   - Communication Service: http://localhost:8004
   - Geocoding Service: http://localhost:8005

## Web Scraper Integration

The web scraper component is developed in a separate repository: [curavani_scraping](https://github.com/peterhaupt/curavani_scraping). It integrates with the main system through a cloud storage bucket interface. See [SCRAPER_INTEGRATION.md](SCRAPER_INTEGRATION.md) for details.

## Documentation

Detailed documentation for each component is available in the `/documentation` directory.

## Related Projects

**Frontend Repository**: [psychotherapy-matching-frontend](https://github.com/peterhaupt/psychotherapy-matching-frontend)

The frontend web interface for this matching platform is maintained in a separate repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Important**: The MIT License provides this software "AS IS" without warranty. Users assume all responsibility for compliance with applicable laws and regulations.
