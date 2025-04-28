"""Main application file for the Patient Service."""
import logging
from flask import Flask
from flask_restful import Api

from api.patients import PatientResource, PatientListResource
from events.producers import producer
# Commented out for now as we're not using consumers yet
# from events.consumers import start_consumers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://boona:boona_password@pgbouncer:6432/therapy_platform"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints
    api.add_resource(PatientListResource, '/api/patients')
    api.add_resource(PatientResource, '/api/patients/<int:patient_id>')

    # Initialize Kafka event consumers
    # Commented out for now until we need them
    # start_consumers()

    @app.teardown_appcontext
    def shutdown_kafka(exception=None):
        """Close Kafka connections when application shuts down."""
        producer.close()
        logger.info("Kafka producer closed")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8001, debug=True)
