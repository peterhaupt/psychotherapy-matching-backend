"""Geocoding cache database models."""
from datetime import datetime

from sqlalchemy import (
    Column, Float, Integer, String, DateTime, Index
)

from shared.utils.database import Base


class GeoCache(Base):
    """Database model for geocoding cache.
    
    This model stores geocoding results to minimize external API calls
    and improve response times for repeated requests.
    """

    __tablename__ = "geocache"
    __table_args__ = {"schema": "geocoding_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Input parameters
    query = Column(String(255), nullable=False)
    query_type = Column(String(50), nullable=False)  # 'address', 'coordinates', 'route'
    
    # Result data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    display_name = Column(String(255), nullable=True)
    result_data = Column(String, nullable=True)  # JSON string of full result
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    hit_count = Column(Integer, default=1, nullable=False)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_geocache_query", "query"),
        Index("ix_geocache_query_type", "query_type"),
        Index("ix_geocache_created_at", "created_at"),
        {"schema": "geocoding_service"}
    )
    
    def __repr__(self):
        """Provide a string representation of the GeoCache instance."""
        return (
            f"<GeoCache id={self.id} query='{self.query}' "
            f"type='{self.query_type}' hits={self.hit_count}>"
        )


class DistanceCache(Base):
    """Database model for distance calculation cache.
    
    This model stores distance calculation results between two points
    to avoid recalculating distances for the same locations.
    """

    __tablename__ = "distance_cache"
    __table_args__ = {"schema": "geocoding_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Input parameters
    origin_latitude = Column(Float, nullable=False)
    origin_longitude = Column(Float, nullable=False)
    destination_latitude = Column(Float, nullable=False)
    destination_longitude = Column(Float, nullable=False)
    travel_mode = Column(String(50), nullable=False)  # 'car', 'transit'
    
    # Result data
    distance_km = Column(Float, nullable=False)
    travel_time_minutes = Column(Float, nullable=True)
    route_data = Column(String, nullable=True)  # JSON string of route details
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    hit_count = Column(Integer, default=1, nullable=False)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index(
            "ix_distance_cache_points", 
            "origin_latitude", "origin_longitude", 
            "destination_latitude", "destination_longitude",
            "travel_mode"
        ),
        {"schema": "geocoding_service"}
    )
    
    def __repr__(self):
        """Provide a string representation of the DistanceCache instance."""
        return (
            f"<DistanceCache id={self.id} "
            f"origin=({self.origin_latitude},{self.origin_longitude}) "
            f"dest=({self.destination_latitude},{self.destination_longitude}) "
            f"mode='{self.travel_mode}' distance={self.distance_km}km>"
        )