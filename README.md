# Psychotherapy Matching Platform

A comprehensive microservice-based system for matching patients with therapists in Germany.

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
   git clone https://github.com/your-organization/therapy-platform.git
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

## License

[Specify the license here]

## Acknowledgments

[Any acknowledgments or credits for libraries, tools, or resources used]
