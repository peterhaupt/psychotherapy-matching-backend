"""Main application file for the Matching Service."""
from flask import Flask
from flask_restful import Api


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
    # To be implemented

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8003, debug=True)