# Curavani System Migration - Requirements & Implementation Plan
## UPDATED September 5, 2025 - Patient Service Integration COMPLETED

## Executive Summary

Migration of the Curavani patient registration system from multiple providers (domainfactory, GoDaddy, SendGrid, Google Cloud) to a single provider (Infomaniak) with enhanced security and simplified architecture using Object Storage with three environments for testing.

**Current Status**: Week 2 FULLY COMPLETED, Week 3 PARTIALLY COMPLETED (Patient service done, Communication service pending)

## 1. Core Migration Goals

1. **Get rid of SendGrid** - Move all email sending to communication-service with local SMTP relay ✅ **PHP SIDE COMPLETE**
2. **Get rid of Google Cloud Storage** - Replace with Infomaniak Object Storage (Swift) ✅ **BOTH PHP AND PYTHON COMPLETE**
3. **Consolidate on Infomaniak** - Use their PHP hosting, MariaDB, and Object Storage ✅ **INFRASTRUCTURE COMPLETED**
4. **Maintain decoupled architecture** - Continue using JSON files as interface ✅ **IMPLEMENTED & TESTED**
5. **Increase security level** - Implement security enhancements inline with migration ✅ **IMPLEMENTED**
6. **Support three test environments** - Dev, Test, and Production containers for backend testing ✅ **INFRASTRUCTURE READY**

## 2. Current Architecture

### 2.1 Email Flow
- **Verification emails**: PHP → Object Storage → Communication service (pending backend)
- **Confirmation emails**: Patient-service → Communication service → Local SMTP relay ✅ **WORKING**
- **Contact form**: PHP → Object Storage → Communication service (pending backend)

### 2.2 Data Storage
- **Registration data**: PHP → Object Storage → Patient-service import ✅ **FULLY WORKING**
- **Database**: MariaDB at Infomaniak ✅ **MIGRATED**
- **Files**: JSON format in Object Storage ✅ **WORKING**

### 2.3 Providers
- **Web hosting**: Infomaniak ✅
- **Domain**: GoDaddy (to be migrated)
- **Email**: Local SMTP relay ✅
- **Cloud storage**: Infomaniak Object Storage ✅
- **Backend services**: Self-hosted Docker containers ✅

## 3. Target Architecture ✅ **ACHIEVED FOR PATIENT SERVICE**

### 3.1 Unified Email Flow
All emails go through communication-service:
```
User Request → PHP → JSON file in Object Storage → Backend Service → Communication-service → Local SMTP relay → Send
```
✅ **Working for patient registration emails**
🔄 **Pending for verification and contact emails**

### 3.2 Infrastructure Overview ✅ **FULLY DEPLOYED**
- **ONE PHP hosting environment** at Infomaniak ✅ **DEPLOYED**
- **ONE MariaDB** at Infomaniak ✅ **CONFIGURED & WORKING**
- **THREE Object Storage containers** at Infomaniak (dev, test, prod) ✅ **CREATED & IN USE**
- **Backend services** running locally in Docker containers ✅ **PATIENT SERVICE INTEGRATED**

### 3.3 Data Storage Structure ✅ **FULLY OPERATIONAL**
```
Object Storage (Infomaniak Swift):
  Containers:
    dev/                    # Development container ✅ ACTIVELY USED
      verifications/        # Email verification requests ✅ PHP UPLOADS WORKING
      contacts/            # Contact form submissions ✅ PHP UPLOADS WORKING  
      registrations/       # Patient registrations ✅ FULL PIPELINE WORKING
    
    test/                   # Test container ✅ READY
    prod/                   # Production container ✅ READY
```

### 3.4 Environment Configuration ✅ **FULLY OPERATIONAL**
- **PHP Environment**: Single production hosting at Infomaniak ✅
- **Environment Selection**: Manual config file change ✅
- **Backend Services**: 
  - Dev backend → `dev` container ✅ **PATIENT SERVICE CONNECTED**
  - Test backend → `test` container ✅ **READY**
  - Prod backend → `prod` container ✅ **READY**

## 4. Technical Stack - VERIFIED & UPDATED ✅

### 4.1 Object Storage Details ✅ **FULLY OPERATIONAL WITH FIXES**
- **Provider**: Infomaniak OpenStack Swift ✅
- **Access Method**: Native Swift API ✅
- **PHP Library**: `php-opencloud/openstack` v3.14.0 ✅
- **Python Library**: `python-swiftclient` with `keystoneauth1` ✅ **WORKING**
- **Authentication**: Application Credentials (ID + Secret) ✅
- **Auth Endpoint**: `https://api.pub1.infomaniak.cloud/identity/v3` ✅
- **Storage Endpoint**: `https://s3.pub2.infomaniak.cloud/object/v1/AUTH_REDACTED_PROJECT_ID` ✅ **MUST USE PUB2**
- **Region**: `dc4-a` ✅
- **HMAC Signature**: Signs entire JSON payload (not pipe-delimited) ✅ **FIXED SEPTEMBER 5**

### 4.2 PHP Environment ✅ **FULLY OPERATIONAL**
- **PHP Version**: 8.1.33 ✅
- **ObjectStorageClient**: Working with HMAC signatures ✅
- **All PHP files**: Migrated and tested ✅

### 4.3 MariaDB ✅ **FULLY OPERATIONAL**
- **Version**: 10.11.13-MariaDB ✅
- **Tables**: All created and in use ✅
- **Purpose**: Token storage, rate limiting only ✅

### 4.4 Python Backend ✅ **PATIENT SERVICE FIXED**
- **ObjectStorageClient**: Fixed indentation bug, using pub2 URL ✅
- **HMAC Verification**: Updated to match PHP's method ✅
- **Data Structure**: Handling nested JSON correctly ✅
- **Import Pipeline**: Fully functional ✅

## 5. Specific Requirements

### 5.1 Email Verification Migration ✅ **PHP COMPLETE, BACKEND PENDING**
- ✅ PHP creates `verification_request.json` in Object Storage
- 🔄 Communication-service needs to poll and send **PENDING**

### 5.2 Contact Form Enhancement ✅ **PHP COMPLETE, BACKEND PENDING**
- ✅ PHP creates `contact_form.json` in Object Storage
- 🔄 Communication-service needs to process **PENDING**

### 5.3 Patient Registration ✅ **FULLY COMPLETED SEPTEMBER 5, 2025**
- ✅ PHP uploads to Object Storage with HMAC
- ✅ Patient-service downloads and verifies HMAC
- ✅ Imports patient to database
- ✅ Sends confirmation email via communication-service
- ✅ Deletes file after processing
- ✅ **Full end-to-end pipeline tested and working**

### 5.4 File Processing ✅ **COMPLETED FOR PATIENT SERVICE**
- ✅ Patient service polls its container successfully
- ✅ Downloads and verifies HMAC signatures
- ✅ Processes files and deletes after completion
- ✅ Error handling and notifications working
- 🔄 Communication service implementation **PENDING**

### 5.5 Performance Requirements ✅ **MEETS REQUIREMENTS**
- **Email delay**: < 30 seconds (patient registration emails working)
- **Processing time**: < 1 second for file processing
- **Object Storage operations**: < 500ms typical

## 6. Security Implementation ✅ **FULLY IMPLEMENTED**

### 6.1 Security Features by Component

#### PHP Files ✅ **ALL COMPLETED**
- ✅ HMAC signatures on all uploads
- ✅ Prepared statements in database
- ✅ Rate limiting active
- ✅ Input validation comprehensive

#### Python Backend (Patient Service) ✅ **COMPLETED SEPTEMBER 5**
- ✅ HMAC verification working (fixed to match PHP format)
- ✅ Secure error handling
- ✅ Environment isolation verified
- ✅ File age monitoring active

### 6.2 HMAC Signature Implementation ✅ **WORKING**
PHP signs the entire JSON payload:
```php
$payloadString = json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
$signature = hash_hmac('sha256', $payloadString, $hmacKey);
```

Python verifies the same way:
```python
payload_string = json.dumps(payload_to_verify, separators=(',', ':'), ensure_ascii=False)
expected_signature = hmac.new(hmac_key.encode('utf-8'), payload_string.encode('utf-8'), hashlib.sha256).hexdigest()
```

## 7. Implementation Plan (UPDATED WITH ACTUAL PROGRESS)

### 7.1 Week 1: Infrastructure Setup ✅ **COMPLETED SEPTEMBER 2, 2025**
- ✅ Object Storage setup complete
- ✅ Database setup complete
- ✅ PHP hosting setup complete
- ✅ Basic functionality verified

### 7.2 Week 2: PHP Implementation WITH Security ✅ **COMPLETED SEPTEMBER 5, 2025**

**Day 1-4: PHP Migration** ✅ **COMPLETED SEPTEMBER 3**
- ✅ ObjectStorageClient implementation
- ✅ send_verification.php migration
- ✅ verify_token.php migration  
- ✅ process_contact.php creation
- ✅ All HMAC signatures working

**Day 5: Python Backend Fixes** ✅ **COMPLETED SEPTEMBER 5**
- ✅ Fixed ObjectStorageClient indentation bug
- ✅ Added explicit pub2 URL requirement
- ✅ Updated HMAC verification to match PHP
- ✅ Fixed nested JSON data structure handling
- ✅ Full end-to-end testing successful

### 7.3 Week 3: Backend Updates 🔄 **IN PROGRESS**

**Day 1-2: Communication-service Update** 🔄 **PENDING - NEXT PRIORITY**
- Implement Swift client with pub2 URL
- Add HMAC verification matching PHP format
- Implement polling for verifications/ and contacts/
- Add email sending for both types
- Test in dev environment

**Day 3-4: Patient-service Update** ✅ **COMPLETED SEPTEMBER 5**
- ✅ Replaced GCS with Swift client
- ✅ Fixed authentication with pub2 URL
- ✅ HMAC verification working
- ✅ File processing and deletion working
- ✅ Email notifications working
- ✅ Full integration tested

**Day 5: Integration Testing** 🔄 **PARTIALLY COMPLETE**
- ✅ Patient registration end-to-end tested
- 🔄 Verification emails pending
- 🔄 Contact forms pending

### 7.4 Week 4: Testing & Validation 🔄 **UPCOMING**
- Development environment testing
- Test environment validation
- Production environment preparation

### 7.5 Week 5: Production Migration 🔄 **UPCOMING**
- DNS preparation
- Final migration
- Monitoring and validation

## 8. Implementation Code Status

### 8.1 PHP Swift Client ✅ **FULLY DEPLOYED**
- **Location**: `/private/ObjectStorageClient.php`
- **Status**: Production ready, all features working
- **HMAC**: Signing full JSON payload

### 8.2 Python Object Storage Client ✅ **FIXED & DEPLOYED**
- **Location**: `shared/utils/object_storage.py`
- **Fixes Applied September 5**:
  - Indentation bug in environment selection
  - Explicit pub2 URL requirement
  - HMAC verification matching PHP format
- **Status**: Fully functional in patient service

### 8.3 Patient Import Pipeline ✅ **FULLY FUNCTIONAL**
- **Status**: Complete end-to-end working
- **Performance**: < 1 second per file
- **Features**: HMAC verification, email sending, error handling

### 8.4 Communication Service 🔄 **TO BE IMPLEMENTED**
```python
# Needs Swift client with:
# - pub2 URL configuration
# - HMAC verification (full JSON payload)
# - Polling for verifications/ and contacts/
```

## 9. Testing Strategy

### 9.1 Security Testing Checklist

**Week 1-2 - PHP & Infrastructure** ✅ **COMPLETED**
- ✅ Object Storage connection verified
- ✅ HMAC signatures working
- ✅ Rate limiting active
- ✅ SQL injection prevention verified
- ✅ XSS prevention tested

**Week 3 - Backend Testing** 
- ✅ Patient Service: HMAC verification working
- ✅ Patient Service: Environment isolation verified
- ✅ Patient Service: File processing complete
- 🔄 Communication Service: Pending implementation

### 9.2 Functional Testing

**Dev Environment** 
- ✅ Object Storage upload/download working
- ✅ HMAC signatures verified
- ✅ Patient registration complete pipeline
- ✅ Confirmation emails sent
- 🔄 Verification emails pending
- 🔄 Contact form emails pending

### 9.3 Performance Benchmarks ✅ **VERIFIED**
- ✅ Object Storage write: < 100ms
- ✅ Object Storage read: < 100ms  
- ✅ File processing: < 1000ms
- ✅ Email queueing: < 500ms

## 10. Progress Summary - September 5, 2025

### ✅ WEEK 1 COMPLETED - Infrastructure Setup
- All infrastructure components deployed

### ✅ WEEK 2 COMPLETED - PHP Migration & Python Fixes
1. **PHP Side** - All files migrated to Object Storage
2. **Security** - HMAC signatures implemented
3. **Python Fixes** - ObjectStorageClient fixed and working
4. **Testing** - Patient registration fully tested end-to-end

### 🔄 WEEK 3 IN PROGRESS - Backend Services
1. **Patient Service** ✅ COMPLETED September 5
2. **Communication Service** 🔄 PENDING - Next priority

### ❌ NOT STARTED
1. Week 4: Full system testing
2. Week 5: Production migration

## 11. Next Steps - Immediate Priority

### Communication Service Integration (URGENT)
1. **Implement Swift client** with pub2 URL requirement
2. **Add HMAC verification** using full JSON payload method
3. **Poll for files**:
   - `verifications/` - Send verification emails
   - `contacts/` - Forward to support email
4. **Process and delete** files after sending
5. **Monitor file age** and alert if > 30 minutes

### Testing Requirements
1. **Verification emails** - Test with actual registration flow
2. **Contact forms** - Test submission and forwarding
3. **Error scenarios** - Invalid HMAC, missing data, etc.

## 12. Critical Implementation Notes

### Object Storage Connection
- **MUST use pub2 URL**: `https://s3.pub2.infomaniak.cloud/...`
- **NOT pub1**: This will result in 404 errors
- **Explicit URL required**: Don't rely on auto-discovery

### HMAC Signatures
- **PHP signs**: Entire JSON payload
- **Python verifies**: Same method (not pipe-delimited)
- **Remove signature fields**: Before verification

### Data Structure
- **PHP creates**: Nested structure with `data.data.patient_data`
- **Python expects**: Same nested structure
- **Handle carefully**: Double nesting from HMAC wrapper

## 13. Success Metrics Achieved

### Patient Registration Pipeline ✅
- **File upload**: Working with HMAC
- **Download & verify**: Successful
- **Import to database**: Creating patients
- **Email sending**: Confirmations sent
- **File cleanup**: Automatic deletion
- **Error handling**: Notifications working

### Remaining Goals
- Verification email automation
- Contact form email automation
- Full production deployment

---

*Document Version: 11.0*  
*Date: September 5, 2025*  
*Status: Week 2 COMPLETED, Patient Service INTEGRATED*  
*Last Updated: September 5, 2025 - 15:00 CET*  
*Next Task: Communication Service Swift Integration*