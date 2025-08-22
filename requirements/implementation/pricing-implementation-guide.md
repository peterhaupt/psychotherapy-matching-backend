# Curavani Pricing Update - Implementation Guide

## Overview
Implementation of two-tier pricing model for Curavani psychotherapy placement service and update of the maximum distance field to a dropdown.

## Business Requirements

### Pricing Structure
- **Einzeltherapie (Individual Therapy)**: 95,00 EUR
- **Gruppentherapie (Group Therapy)**: 45,00 EUR
- Service type determined by `offen_fuer_gruppentherapie` field:
  - `true` = Gruppentherapie (45 EUR)
  - `false` = Einzeltherapie (95 EUR)
- Upgrade from group to individual therapy costs additional 50,00 EUR

### Maximum Distance Field
- Change from number input (1-100) to dropdown with options: 10, 20, 30
- Default value: 20
- Backend continues to accept any value 1-100 for API compatibility
- Existing patient data remains unchanged

## Technical Specifications

### Data Structure
- **NO database schema changes**
- **NO new fields added**
- Continue using existing `offen_fuer_gruppentherapie` boolean field
- Prices NOT stored in database (will be implemented with invoice system later)
- Payment reference (Verwendungszweck) remains unchanged (first 8 chars of token)

### Price Configuration Strategy
- Single source of truth: `prices.json` file
- Located at: `curavani_com/prices.json` (publicly accessible)
- Both PHP and Python services read from this file
- JSON structure:
```json
{
  "einzeltherapie": 95,
  "gruppentherapie": 45
}
```

## Implementation Tasks

### 1. Create Price Configuration File

**File**: `curavani_com/prices.json`
- Create new JSON file with pricing configuration
- Place in public web directory
- Ensure readable by both PHP and Python services

### 2. Update PHP Components

#### 2.1 Create Price Reading Function
**File**: `curavani_com/includes/verify_token_functions.php`
- Add function to read and parse `prices.json`
- Add function to determine price based on `offen_fuer_gruppentherapie`
- Cache prices in memory to avoid repeated file reads

#### 2.2 Update Main Verification Page
**File**: `curavani_com/verify_token.php`

**Changes needed:**
1. **Load prices at beginning of script**
   - Read from prices.json
   - Determine price based on form data

2. **Maximum Distance Dropdown** (Step 1 - Personal Information)
   - Replace number input with select dropdown
   - Options: 10, 20, 30
   - Default: 20
   - Keep same field name: `max_km`

3. **Therapiepräferenzen Section Text** (Step 1)
   - Update explanation text to include pricing information
   - Clarify upgrade cost from group to individual therapy
   - Text to be provided by client

4. **Verbraucherinformation Section** (Step 7)
   - Dynamic price display based on `offen_fuer_gruppentherapie`
   - Show correct service type and price

5. **Success/Confirmation Page**
   - Display correct price in payment instructions
   - Show service type purchased

### 3. Update Public Website

**File**: `patienten.html` (location to be confirmed)
- Update pricing information to show both tiers
- Text to be provided by client

### 4. Update Python Services

#### 4.1 Configuration Updates
**File**: `shared/config.py`
- Add environment variables for prices (with defaults from prices.json)
- Add method to fetch prices from public URL or file path
- Consider fallback values if prices.json unavailable

#### 4.2 Patient Service Updates
**File**: `patient_service/imports/patient_importer.py`
- Update `_send_patient_confirmation_email` method
- Fetch current prices from configuration
- Pass service type and price to email template

### 5. Update Email Template

**File**: `shared/templates/emails/patient_registration_confirmation.md`
- Add conditional logic based on service type
- Use Jinja2 templating:
  ```jinja
  {% if patient.offen_fuer_gruppentherapie %}
    Gruppentherapie-specific content (45,00 EUR)
  {% else %}
    Einzeltherapie-specific content (95,00 EUR)
  {% endif %}
  ```
- Include correct payment amount in bank transfer details
- Clarify service type purchased

### 6. JavaScript Updates

**File**: `curavani_com/verify_token.php` (inline JavaScript)
- Update validation for max_km dropdown (if any)
- No changes needed for price display (handled server-side)

## Text Updates Required from Client

The following German text updates are needed:

1. **patienten.html**
   - Pricing section showing both service tiers

2. **verify_token.php - Therapiepräferenzen section**
   - Updated explanation including pricing
   - Clarification about upgrade costs

3. **verify_token.php - Verbraucherinformation**
   - Conditional text for each service type

4. **Email template**
   - Conditional sections for each service type
   - Payment instructions with correct amounts

## Validation & Testing Checklist

### Functional Testing
- [ ] Dropdown shows 10, 20, 30 for max distance
- [ ] Default value is 20
- [ ] Form submission works with dropdown value
- [ ] Price displays correctly for group therapy (45 EUR)
- [ ] Price displays correctly for individual therapy (95 EUR)
- [ ] Confirmation page shows correct price
- [ ] Email contains correct price and service type
- [ ] Payment reference remains unchanged

### Integration Testing
- [ ] PHP correctly reads prices.json
- [ ] Python service correctly reads prices
- [ ] Email generation works for both service types
- [ ] Mock token mode handles both prices correctly

### Backward Compatibility
- [ ] API still accepts max_km values 1-100
- [ ] Existing patients with other max_km values unaffected
- [ ] No database migration needed
- [ ] Import process continues to work

## Risk Considerations

1. **Price Synchronization**
   - Risk: Prices could get out of sync if file not accessible
   - Mitigation: Implement fallback default values
   - Monitoring: Log when prices.json cannot be read

2. **Existing Data**
   - Risk: Existing patients with max_km not in [10,20,30]
   - Mitigation: Backend accepts all values, only UI constrained
   - No data migration needed

3. **Service Type Changes**
   - Risk: If offen_fuer_gruppentherapie changed after booking
   - Current decision: Accept this limitation, will be addressed with invoice system
   - Document that this field should not be changed after payment

## Deployment Steps

1. Create and deploy prices.json file
2. Deploy PHP updates (verify_token.php and functions)
3. Deploy Python service updates
4. Update public website
5. Test full flow for both service types
6. Monitor for any price reading errors

## Future Enhancements (Not in Current Scope)

- Store paid price in database
- Invoice generation system
- Payment tracking system
- Price history tracking
- Automated payment reconciliation

## Environment Variables to Add

For Python services (in deployment configuration):
```bash
# Optional - can fall back to reading from prices.json
PRICE_EINZELTHERAPIE=95
PRICE_GRUPPENTHERAPIE=45
PRICES_JSON_URL=https://curavani.com/prices.json
```

## Files to Modify - Summary

1. **CREATE**: `curavani_com/prices.json`
2. **UPDATE**: `curavani_com/verify_token.php`
3. **UPDATE**: `curavani_com/includes/verify_token_functions.php`
4. **UPDATE**: `patienten.html` (public website)
5. **UPDATE**: `shared/config.py`
6. **UPDATE**: `patient_service/imports/patient_importer.py`
7. **UPDATE**: `shared/templates/emails/patient_registration_confirmation.md`

## Notes for Implementation

- All price displays should use German format: "45,00 EUR" or "95,00 EUR"
- The decision logic is simple: `offen_fuer_gruppentherapie ? 45 : 95`
- No need to track which service was purchased beyond the boolean field
- Payment reference stays the same regardless of service type
- Email should clearly state which service was purchased to avoid confusion

## Success Criteria

- Patients can select group therapy and pay 45 EUR
- Patients can select individual therapy and pay 95 EUR
- Clear communication about upgrade costs
- All price displays are consistent and dynamic
- Maximum distance selection simplified to dropdown
- No changes to data structure or database schema
- Existing patient data remains valid