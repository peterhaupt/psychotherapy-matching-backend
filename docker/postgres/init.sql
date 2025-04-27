-- Create schemas for each service
CREATE SCHEMA IF NOT EXISTS patient_service;
CREATE SCHEMA IF NOT EXISTS therapist_service;
CREATE SCHEMA IF NOT EXISTS matching_service;
CREATE SCHEMA IF NOT EXISTS communication_service;
CREATE SCHEMA IF NOT EXISTS geocoding_service;
CREATE SCHEMA IF NOT EXISTS scraping_service;

-- Set search path
SET search_path TO patient_service, public;