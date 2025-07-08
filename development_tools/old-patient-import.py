#!/usr/bin/env python3
"""
Script to convert patient data from Excel to JSON files for import.
Reads from Patientenverwaltung.xlsx and outputs to old_patients/ directory.
"""

import os
import json
import hashlib
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_token(data_string):
    """Generate a short unique token from patient data."""
    hash_object = hashlib.md5(data_string.encode())
    return hash_object.hexdigest()[:8]


def convert_german_date(date_str):
    """Convert German date format (DD.MM.YYYY) to ISO format (YYYY-MM-DD)."""
    if pd.isna(date_str) or not date_str:
        return None
    
    try:
        # Handle if it's already a datetime object
        if isinstance(date_str, pd.Timestamp):
            return date_str.strftime('%Y-%m-%d')
        
        # Convert string format
        date_str = str(date_str).strip()
        # Try parsing DD.MM.YYYY format
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        logger.warning(f"Could not parse date: {date_str}")
        return None


def convert_boolean(value):
    """Convert German Ja/Nein to boolean."""
    if pd.isna(value) or not value:
        return False
    
    value_str = str(value).strip().lower()
    return value_str == 'ja'


def sanitize_filename(name):
    """Sanitize a string for use in filename."""
    # Remove special characters and replace spaces with underscores
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    return name.lower()


def process_patient_row(row, row_index):
    """Process a single patient row and return JSON data."""
    try:
        # Check required fields
        if pd.isna(row['Name']) or pd.isna(row['Vorname']) or pd.isna(row['Anrede']):
            logger.warning(f"Row {row_index}: Missing required fields (Name, Vorname, or Anrede)")
            return None
        
        # Validate Anrede
        anrede = str(row['Anrede']).strip()
        if anrede not in ['Herr', 'Frau']:
            logger.warning(f"Row {row_index}: Invalid Anrede '{anrede}' - must be 'Herr' or 'Frau'")
            return None
        
        # Derive geschlecht from Anrede
        geschlecht = 'männlich' if anrede == 'Herr' else 'weiblich'
        
        # Build patient_data structure
        patient_data = {
            'anrede': anrede,
            'geschlecht': geschlecht,
            'vorname': str(row['Vorname']).strip(),
            'nachname': str(row['Name']).strip(),
            'status': 'offen',  # Fixed value for imports
            'erfahrung_mit_psychotherapie': False,  # Default value
        }
        
        # Add optional fields if they exist and are not empty
        field_mappings = {
            'Hausarzt': 'hausarzt',
            'Straße': 'strasse',
            'PLZ': 'plz',
            'Ort': 'ort',
            'E-Mail': 'email',
            'Telefon': 'telefon',
            'Krankenkasse': 'krankenkasse',
            'Diagnose': 'diagnose'
        }
        
        for excel_field, json_field in field_mappings.items():
            if excel_field in row and not pd.isna(row[excel_field]) and str(row[excel_field]).strip():
                patient_data[json_field] = str(row[excel_field]).strip()
        
        # Handle date field
        if 'Geburtsdatum' in row:
            geburtsdatum = convert_german_date(row['Geburtsdatum'])
            if geburtsdatum:
                patient_data['geburtsdatum'] = geburtsdatum
        
        # Handle boolean fields
        if 'Verträge unterschrieben' in row:
            patient_data['vertraege_unterschrieben'] = convert_boolean(row['Verträge unterschrieben'])
        
        if 'psych. Sprechstunde' in row:
            patient_data['hat_ptv11'] = convert_boolean(row['psych. Sprechstunde'])
        
        if 'Gruppentherapie' in row:
            patient_data['offen_fuer_gruppentherapie'] = convert_boolean(row['Gruppentherapie'])
        
        # Create the full JSON structure
        json_data = {
            'patient_data': patient_data
        }
        
        return json_data
        
    except Exception as e:
        logger.error(f"Row {row_index}: Error processing row - {str(e)}")
        return None


def main():
    """Main function to process the Excel file and generate JSON files."""
    excel_file = 'Patientenverwaltung.xlsx'
    output_dir = 'old_patients'
    
    # Check if Excel file exists
    if not os.path.exists(excel_file):
        logger.error(f"Excel file '{excel_file}' not found!")
        return
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    logger.info(f"Reading Excel file: {excel_file}")
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_file)
        logger.info(f"Found {len(df)} rows in Excel file")
        
        # Process counters
        success_count = 0
        error_count = 0
        
        # Process each row
        for index, row in df.iterrows():
            row_number = index + 2  # Excel row number (accounting for header)
            
            # Process the row
            json_data = process_patient_row(row, row_number)
            
            if json_data:
                # Generate filename
                nachname = sanitize_filename(json_data['patient_data']['nachname'])
                vorname = sanitize_filename(json_data['patient_data']['vorname'])
                date_str = datetime.now().strftime('%Y%m%d')
                
                # Generate unique token
                token_data = f"{nachname}_{vorname}_{row_number}_{datetime.now().isoformat()}"
                token = generate_token(token_data)
                
                filename = f"{nachname}_{vorname}_{date_str}_{token}.json"
                filepath = os.path.join(output_dir, filename)
                
                # Write JSON file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Row {row_number}: Created {filename}")
                success_count += 1
            else:
                error_count += 1
        
        # Summary
        logger.info(f"\nProcessing complete!")
        logger.info(f"Successfully processed: {success_count} patients")
        logger.info(f"Errors/Skipped: {error_count} rows")
        logger.info(f"JSON files saved to: {output_dir}/")
        
    except Exception as e:
        logger.error(f"Error reading Excel file: {str(e)}")
        return


if __name__ == "__main__":
    main()
