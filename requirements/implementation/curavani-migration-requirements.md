# Curavani System Migration - Requirements & Implementation Plan
## UPDATED with Week 2 Day 1-2 COMPLETED - September 3, 2025

## Executive Summary

Migration of the Curavani patient registration system from multiple providers (domainfactory, GoDaddy, SendGrid, Google Cloud) to a single provider (Infomaniak) with enhanced security and simplified architecture using Object Storage with three environments for testing.

## 1. Core Migration Goals

1. **Get rid of SendGrid** - Move all email sending to communication-service with local SMTP relay ✅ **PHP SIDE COMPLETE**
2. **Get rid of Google Cloud Storage** - Replace with Infomaniak Object Storage (Swift) ✅ **INFRASTRUCTURE READY**
3. **Consolidate on Infomaniak** - Use their PHP hosting, MariaDB, and Object Storage ✅ **INFRASTRUCTURE COMPLETED**
4. **Maintain decoupled architecture** - Continue using JSON files as interface ✅ **READY TO IMPLEMENT**
5. **Increase security level** - Implement security enhancements inline with migration ✅ **IN PROGRESS**
6. **Support three test environments** - Dev, Test, and Production containers for backend testing ✅ **INFRASTRUCTURE CREATED**

## 2. Current Architecture

### 2.1 Email Flow
- **Verification emails**: PHP → SendGrid API (direct)
- **Confirmation emails**: Patient-service → Communication service → Local SMTP relay (already implemented)
- **Contact form**: PHP → Google Cloud Storage → (no email currently)

### 2.2 Data Storage
- **Registration data**: PHP → Google Cloud Storage → Patient-service import
- **Database**: MySQL/MariaDB at domainfactory
- **Files**: JSON format in GCS buckets

### 2.3 Providers
- **Web hosting**: domainfactory
- **Domain**: GoDaddy
- **Email**: SendGrid (for verification only)
- **Cloud storage**: Google Cloud Storage
- **Backend services**: Self-hosted (patient-service, communication-service, etc.)

## 3. Target Architecture (SIMPLIFIED)

### 3.1 Unified Email Flow
All emails go through communication-service:
```
User Request → PHP → JSON file in Object Storage → Communication-service → Local SMTP relay → Send
```

### 3.2 Infrastructure Overview ✅ **INFRASTRUCTURE SETUP COMPLETED**
- **ONE PHP hosting environment** at Infomaniak (production web hosting) ✅ **DEPLOYED**
- **ONE MariaDB** at Infomaniak (for tokens and rate limiting only) ✅ **CONFIGURED & WORKING**
- **THREE Object Storage containers** at Infomaniak (dev, test, prod) ✅ **CREATED**
- **THREE backend environments** running locally in Docker containers 🔄 **NOT CONFIGURED YET**

### 3.3 Data Storage Structure ✅ **INFRASTRUCTURE CREATED**
```
Object Storage (Infomaniak Swift): ✅ CONTAINERS CREATED
  Containers:
    dev/                    # Development container ✅ CREATED & TESTED
      verifications/        # Email verification requests ✅ ACTIVELY USED
      contacts/            # Contact form submissions ✅ FOLDER READY  
      registrations/       # Patient registrations ✅ FOLDER READY
    
    test/                   # Test container ✅ CREATED
      verifications/      ✅ FOLDER READY
      contacts/          ✅ FOLDER READY
      registrations/     ✅ FOLDER READY
    
    prod/                   # Production container ✅ CREATED
      verifications/      ✅ FOLDER READY
      contacts/          ✅ FOLDER READY
      registrations/     ✅ FOLDER READY
```

**Status**: Infrastructure ready, send_verification.php migrated, others pending.

### 3.4 Environment Configuration ✅ **FULLY CONFIGURED**
- **PHP Environment**: Single production hosting at Infomaniak ✅ **DEPLOYED**
- **Environment Selection**: Manual config file change (`config.php`) ✅ **CONFIGURED**
- **Backend Services**: Each Docker container reads only from its corresponding Object Storage container
  - Dev backend → `dev` container 🔄 **INFRASTRUCTURE READY**
  - Test backend → `test` container 🔄 **INFRASTRUCTURE READY**
  - Prod backend → `prod` container 🔄 **INFRASTRUCTURE READY**
- **MariaDB**: Single database for all environments (only stores transient data) ✅ **CONFIGURED & WORKING**

### 3.5 Testing Workflow 🔄 **INFRASTRUCTURE READY FOR TESTING**
1. Set PHP config to `environment: 'dev'` → Test with dev backend ✅ **TESTED WITH VERIFICATION**
2. Set PHP config to `environment: 'test'` → Validate with test backend 🔄 **READY WHEN TEST BACKEND CONFIGURED**
3. Set PHP config to `environment: 'prod'` → Go live with production backend 🔄 **READY WHEN PROD BACKEND CONFIGURED**

**Status**: Dev environment actively used for send_verification.php testing.

## 4. Technical Stack - VERIFIED ✅

### 4.1 Object Storage Details ✅ **FULLY TESTED SEPTEMBER 3, 2025**
- **Provider**: Infomaniak OpenStack Swift ✅ **WORKING**
- **Access Method**: Native Swift API (not S3-compatible) ✅ **UPLOAD/DOWNLOAD TESTED**
- **PHP Library**: `php-opencloud/openstack` v3.14.0 ✅ **INSTALLED & WORKING**
- **Python Library**: `python-swiftclient` with `keystoneauth1` 🔄 **NOT CONFIGURED YET**
- **Authentication**: Application Credentials (ID + Secret) ✅ **CONFIGURED & WORKING**
- **Auth Endpoint**: `https://api.pub1.infomaniak.cloud/identity/v3` ✅ **WORKING**
- **Storage Endpoint**: `***REMOVED***` ✅ **WORKING**
- **Region**: `dc4-a` ✅ **VERIFIED**
- **Performance**: Upload and download operations tested successfully ✅ **TESTED SEPTEMBER 3, 2025**
- **Metadata Fix**: Timestamp must be string, not integer ✅ **FIXED SEPTEMBER 3, 2025**

### 4.2 PHP Environment ✅ **FULLY OPERATIONAL**
- **PHP Version**: 8.1.33 ✅ **VERIFIED**
- **Memory Limit**: 640M ✅ **SUFFICIENT**
- **Max Execution Time**: 60 seconds ✅ **SUFFICIENT**
- **Required Extensions**: All present (mysqli, pdo, json, curl, mbstring, openssl, hash) ✅ **VERIFIED**
- **Composer**: v2.8.3 installed and working ✅ **OPERATIONAL**
- **ObjectStorageClient**: Enhanced with specific upload methods ✅ **FULLY WORKING**
- **SecureDatabase**: Database connection class with prepared statements ✅ **WORKING**

### 4.3 MariaDB ✅ **FULLY CONFIGURED & OPERATIONAL**
- **Version**: 10.11.13-MariaDB-deb11-log ✅ **VERIFIED SEPTEMBER 2, 2025**
- **Host Pattern**: `[database].myd.infomaniak.com` ✅ **CONNECTED**
- **Connection Methods**: MySQLi and PDO both supported ✅ **PDO WORKING**
- **Features**: Transactions, JSON columns, UTF8MB4, Prepared statements ✅ **ALL VERIFIED**
- **Purpose**: Token storage, rate limiting, duplicate prevention only ✅ **TABLES CREATED**
- **Tables Created**:
  - `verification_tokens` with `form_submitted` column ✅
  - `verification_requests` for rate limiting ✅
  - `system_logs` for monitoring ✅

### 4.4 Configuration File Structure ✅ **IMPLEMENTED & TESTED**
```php
// config.php - Located in /private/ folder ✅ WORKING
<?php
// Path constants defined with guards
if (!defined('BASE_PATH')) {
    define('BASE_PATH', '/home/clients/f12cc10f4c32b1843b96c779a0928932');
    define('PRIVATE_PATH', BASE_PATH . '/private');
    define('PUBLIC_PATH', BASE_PATH . '/sites/curavani.de');
}

return [
    // Environment switching ✅ IMPLEMENTED
    'environment' => 'dev',  // Change to 'test' or 'prod'
    
    // Object storage ✅ WORKING
    'object_storage' => [
        'auth_url' => 'https://api.pub1.infomaniak.cloud/identity/v3',
        'region' => 'dc4-a',
        'credentials' => [
            'id' => 'CONFIGURED',     // ✅ CONFIGURED
            'secret' => 'CONFIGURED'  // ✅ CONFIGURED
        ]
    ],
    
    // Database ✅ CONFIGURED & WORKING
    'database' => [
        'host' => 'DATABASE_NAME.myd.infomaniak.com', // ✅ CONNECTED
        'name' => 'curavani_db',                      // ✅ WORKING
        'user' => 'DB_USERNAME',                      // ✅ AUTHENTICATED
        'pass' => 'DB_PASSWORD'                       // ✅ SECURE
    ],
    
    // Security ✅ IMPLEMENTED
    'security' => [
        'hmac_key' => 'CONFIGURED'  // ✅ CONFIGURED & WORKING
    ]
];
```
- **Helper Functions**: Moved to separate config_functions.php ✅ **IMPLEMENTED SEPTEMBER 3, 2025**

## 5. Specific Requirements

### 5.1 Email Verification Migration ✅ **COMPLETED SEPTEMBER 3, 2025**
- Move email sending from `send_verification.php` to communication-service ✅ **PHP SIDE DONE**
- PHP creates `verification_request.json` file in Object Storage ✅ **WORKING**
- Communication-service polls and sends verification email 🔄 **NOT IMPLEMENTED**
- Keep token storage in MariaDB for rate limiting ✅ **WORKING**
- **Security built-in**: HMAC signatures, prepared statements, rate limiting ✅ **IMPLEMENTED**

### 5.2 Contact Form Enhancement
- Modify `patienten.html` contact form 🔄 **NOT STARTED**
- Create `contact_form.json` file via PHP in Object Storage 🔄 **INFRASTRUCTURE READY**
- Communication-service sends to support email 🔄 **NOT IMPLEMENTED**
- **Support email address**: `patienten@curavani.com`
- **Security built-in**: Input validation, XSS prevention, HMAC signatures 🔄 **NOT IMPLEMENTED**

### 5.3 Patient Registration
- Continue current flow but with Object Storage instead of GCS 🔄 **NEXT PRIORITY**
- PHP (`verify_token.php`) → JSON file → Object Storage 🔄 **INFRASTRUCTURE READY**
- Patient-service imports from Object Storage 🔄 **NOT IMPLEMENTED**
- **Security built-in**: Duplicate prevention, validation, HMAC signatures 🔄 **NOT IMPLEMENTED**

### 5.4 File Processing 🔄 **INFRASTRUCTURE READY**
- Backend services poll their respective containers 🔄 **NOT IMPLEMENTED**
- Download and process files immediately 🔄 **NOT IMPLEMENTED**
- Delete files from Object Storage after processing (both success and failure) 🔄 **NOT IMPLEMENTED**
- Files older than 30 minutes indicate backend processing problems 🔄 **NOT IMPLEMENTED**
- Services handle their own error tracking 🔄 **NOT IMPLEMENTED**
- **Security built-in**: HMAC verification 🔄 **NOT IMPLEMENTED**

### 5.5 Performance Requirements 🔄 **PARTIALLY TESTED**
- **Email delay**: 10-30 seconds acceptable 🔄 **NOT TESTED - PENDING EMAIL IMPLEMENTATION**
- **Polling frequency**: Every 10-30 seconds 🔄 **NOT IMPLEMENTED**
- **Expected load**: 
  - < 100 registrations/hour 🔄 **NOT TESTED**
  - < 1,000 emails/hour 🔄 **NOT TESTED**
- **File monitoring**: Alert if files older than 30 minutes exist 🔄 **NOT IMPLEMENTED**
- **Measured performance**: Object Storage upload/download working ✅ **UPLOAD TESTED**

## 6. Security Implementation (INLINE WITH DEVELOPMENT)

### 6.1 Security Features by Component

#### PHP Files (Week 2 Implementation)
Each PHP file will be updated ONCE with all security features:

**ObjectStorageClient.php**: ✅ **COMPLETED SEPTEMBER 3, 2025**
- ✅ HMAC signature generation working
- ✅ Enhanced error handling implemented
- ✅ Environment-based container selection working
- ✅ Connection testing methods working
- ✅ Specific upload methods for different types

**SecureDatabase.php**: ✅ **CREATED & WORKING**
- ✅ Prepared statements enforced
- ✅ Singleton pattern implemented
- ✅ Transaction support with nesting
- ✅ Secure error handling
- ✅ Automatic cleanup capability

**send_verification.php** ✅ **COMPLETED SEPTEMBER 3, 2025**:
- ✅ Prepared statements for all database queries
- ✅ Rate limiting (3 requests/hour)
- ✅ HMAC signature on JSON output
- ✅ Input validation and sanitization
- ✅ Using SecureDatabase class

**verify_token.php** (pending):
- Prepared statements for all queries
- Duplicate submission prevention (`form_submitted` column)
- HMAC signature on JSON output
- Comprehensive input validation
- XSS prevention

**process_contact.php** (pending):
- Input validation and sanitization
- HMAC signature on JSON output
- XSS prevention
- Rate limiting

#### Backend Services (Week 3 Implementation)
Each service updated ONCE with all security features:

**Communication-service & Patient-service**:
- HMAC verification on all incoming files
- File age monitoring
- Secure error handling
- Environment isolation verification

### 6.2 HMAC Signature Structure ✅ **IMPLEMENTED & VERIFIED**
```json
{
  "signature": "d14d8e5b3efb10a0b42bceb06afbaf5714f4b082433c04edf3317d880b42f231",
  "signature_version": "hmac-sha256-v1",
  "timestamp": "2025-09-03T11:53:44+02:00",
  "type": "email_verification",
  "environment": "dev",
  "data": { ... actual payload ... }
}
```

**Status**: HMAC signatures successfully implemented and verified in Object Storage uploads.

### 6.3 Database Schema Updates ✅ **COMPLETED**
```sql
-- Completed during Week 1 setup - September 2, 2025
ALTER TABLE verification_tokens 
ADD COLUMN form_submitted BOOLEAN DEFAULT FALSE,
ADD INDEX idx_email_hash (email_hash),
ADD INDEX idx_created_at (created_at);
```

## 7. Implementation Plan (REVISED WITH PROGRESS)

### 7.1 Week 1: Infrastructure Setup ✅ **COMPLETED SEPTEMBER 2, 2025**

**Day 1-2: Object Storage Setup** ✅ **COMPLETED SEPTEMBER 2, 2025**
- ✅ Create three containers (`dev`, `test`, `prod`)
- ✅ Create folder structure in each container
- ✅ Generate and test Application Credentials
- ✅ Verify CLI access from Mac
- ✅ Test upload/download functionality

**Day 3: Database Setup** ✅ **COMPLETED SEPTEMBER 2, 2025**
- ✅ Set up single MariaDB database at Infomaniak
- ✅ Create verification_tokens table WITH all columns including `form_submitted`
- ✅ Create verification_requests table for rate limiting
- ✅ Create system_logs table for monitoring (bonus)
- ✅ Test database connection with health check script
- ✅ Implement SecureDatabase class with prepared statements

**Day 4-5: PHP Hosting Setup** ✅ **COMPLETED SEPTEMBER 2, 2025**
- ✅ Deploy PHP application to Infomaniak
- ✅ Configure credentials in config.php
- ✅ Create and test basic ObjectStorageClient functionality
- ✅ Verify Swift connection and basic upload works
- ✅ Create SecureDatabase class for database operations

### 7.2 Week 2: PHP Implementation WITH Security

**Day 1: ObjectStorageClient Implementation** ✅ **COMPLETED SEPTEMBER 3, 2025**
- ✅ Enhanced with specific upload methods
- ✅ Environment-based container selection working
- ✅ HMAC signatures working and verified
- ✅ Metadata issue fixed (string conversion)
- ✅ Successfully tested with verification uploads

**Day 2: send_verification.php Update** ✅ **COMPLETED SEPTEMBER 3, 2025**
- ✅ Replaced SendGrid with Object Storage
- ✅ Using SecureDatabase with prepared statements
- ✅ HMAC signatures on JSON files
- ✅ Rate limiting maintained
- ✅ Successfully uploading to dev/verifications/
- ✅ JSON structure verified with correct HMAC
- ⏳ **PENDING**: Communication service integration for actual email sending

**Day 3-4: verify_token.php Update** 🔄 **NEXT PRIORITY**
- Replace GCS upload with Object Storage
- Add duplicate submission prevention
- Implement all prepared statements
- Add HMAC signatures
- Secure all validation functions
- Complete testing

**Day 5: process_contact.php Creation** 🔄 **PENDING**
- Create new file for contact form handling
- Implement Object Storage upload
- Add comprehensive input validation
- Add HMAC signatures
- Complete testing

### 7.3 Week 3: Backend Updates WITH Security

**Day 1-2: Communication-service Update** 🔄 **PENDING**
- Implement Swift client with storage URL override
- Add HMAC verification in polling logic
- Implement file age monitoring
- Add email verification processing
- Add contact form processing
- Environment-specific configuration
- Test in dev environment

**Day 3-4: Patient-service Update** 🔄 **PENDING**
- Replace GCS with Swift client
- Add HMAC verification in import logic
- Implement file age monitoring
- Environment-specific configuration
- Test in dev environment

**Day 5: Integration Testing** 🔄 **PENDING**
- Complete end-to-end test in dev environment
- Verify environment isolation
- Test all workflows

### 7.4 Week 4: Testing & Validation

**Day 1-2: Development Environment**
- Complete functional testing
- Security validation
- Performance testing
- Fix any issues

**Day 3: Test Environment**
- Switch config to 'test'
- Complete functional testing
- Load testing
- Security audit

**Day 4: Production Environment**
- Switch config to 'prod'
- Final validation
- Performance benchmarks
- Rollback procedure testing

**Day 5: Documentation & Monitoring**
- Complete documentation
- Set up monitoring
- Create operational runbooks
- Final security review

### 7.5 Week 5: Production Migration
1. DNS preparation (reduce TTL 48 hours before)
2. Data migration from domainfactory to Infomaniak
3. Final database migration
4. Switch DNS to Infomaniak
5. Monitor for 48-72 hours
6. Keep domainfactory as backup for 1 week
7. Decommission old infrastructure

## 8. Implementation Code Status

### 8.1 Secure PHP Swift Client ✅ **IMPLEMENTED & TESTED**
```php
use OpenStack\OpenStack;

class ObjectStorageClient {
    // ✅ FULLY WORKING IMPLEMENTATION
    // Location: /private/ObjectStorageClient.php
    // Status: Successfully tested September 3, 2025
    // Features: HMAC signatures, error handling, environment selection
    // Specific methods for verification, registration, contact uploads
}
```

### 8.2 Secure Database Connection ✅ **IMPLEMENTED**
```php
class SecureDatabase {
    // ✅ IMPLEMENTED SEPTEMBER 2-3, 2025
    // Location: /private/SecureDatabase.php
    // Features: Prepared statements, transactions, secure error handling
    // Fixed config loading issue with require vs require_once
}
```

### 8.3 Python Backend with Security
```python
# To be implemented in Week 3
class SecureObjectStorageClient:
    pass
```

## 9. Testing Strategy

### 9.1 Security Testing Checklist
**Week 1 - Infrastructure Testing** ✅ **COMPLETED**
- ✅ Object Storage connection verified
- ✅ Database connection verified
- ✅ Environment isolation confirmed (container selection works)
- ✅ Upload/download functionality verified
- ✅ Basic error handling tested
- ✅ Database tables created with security columns
- ✅ Prepared statements enforced in SecureDatabase

**Week 2 Day 1-2 - PHP Testing** ✅ **PARTIALLY COMPLETED**
- ✅ HMAC signature generation tested
- ✅ HMAC signatures present in uploads
- ✅ Rate limiting verification (3 requests/hour) working
- ✅ Config file security (no function redeclaration)
- [ ] SQL injection attempts on all forms
- [ ] XSS attempts in all input fields
- [ ] Duplicate submission prevention
- [ ] Invalid token handling
- [ ] Expired token handling

**Week 3 - Backend Testing**
- [ ] HMAC signature verification
- [ ] Environment isolation (no cross-reads)
- [ ] File age monitoring alerts
- [ ] Invalid JSON handling
- [ ] Missing signature handling
- [ ] Environment mismatch handling

### 9.2 Functional Testing per Environment
**Dev Environment** ✅ **PARTIALLY TESTED**
- ✅ Object Storage upload/download
- ✅ Database connectivity
- ✅ Environment selection working
- ✅ HMAC signature generation
- ✅ Email verification flow (PHP side)
- [ ] Patient registration flow
- [ ] Contact form submission
- [ ] File processing verification
- [ ] Error handling

**Test Environment** ✅ **INFRASTRUCTURE READY**
- [ ] Complete end-to-end flow
- [ ] Load testing (100 registrations)
- [ ] Concurrent user testing
- [ ] Database transaction handling

**Production Environment** ✅ **INFRASTRUCTURE READY**
- [ ] Smoke tests only
- [ ] Monitoring verification
- [ ] Rollback procedure test

### 9.3 Performance Benchmarks ✅ **PARTIALLY VERIFIED**
- ✅ Object Storage write: Working (< 100ms tested)
- ✅ Object Storage read: Working (< 100ms tested)
- ✅ Database queries: < 10ms (verified with health check)
- Email processing: < 30 seconds (to be tested)
- Registration processing: < 60 seconds (to be tested)

## 10. Progress Summary - September 3, 2025

### ✅ WEEK 1 COMPLETED - Infrastructure Setup
1. **Object Storage Infrastructure**
   - 3 containers created at Infomaniak (dev, test, prod)
   - Folder structure created and verified
   - Application credentials configured and working
   - CLI access from Mac for container management
   - Basic PHP upload functionality tested and working

2. **PHP Environment**
   - Hosting account deployed at Infomaniak
   - Composer installed with `php-opencloud/openstack` library
   - Basic ObjectStorageClient.php created and tested for uploads
   - Config.php created with environment switching capability
   - Basic connectivity to Object Storage verified

3. **Database Infrastructure**
   - MariaDB 10.11.13 configured at Infomaniak
   - All tables created with security columns
   - SecureDatabase class implemented with prepared statements
   - Health check monitoring working
   - Rate limiting tables ready

### ✅ WEEK 2 DAY 1-2 COMPLETED - send_verification.php Migration
1. **ObjectStorageClient.php**
   - Enhanced with specific upload methods (uploadVerificationRequest, uploadRegistration, uploadContactForm)
   - HMAC signatures working and verified in production
   - Fixed metadata timestamp issue (must be string)
   - Environment-based container selection working

2. **Configuration Improvements**
   - Added BASE_PATH, PRIVATE_PATH, PUBLIC_PATH constants
   - Separated helper functions to config_functions.php
   - Fixed multiple inclusion issues with require vs require_once
   - Resolved function redeclaration errors

3. **send_verification.php**
   - Successfully migrated from SendGrid to Object Storage
   - Verification requests uploading to dev/verifications/
   - HMAC signatures validated and present in JSON files
   - Rate limiting maintained (3 requests/hour)
   - Using SecureDatabase with prepared statements

### 🔄 IN PROGRESS - Week 2 Remaining Tasks
1. **verify_token.php** - Next priority (Day 3-4)
2. **process_contact.php** - To be created (Day 5)
3. **Communication service** - Needs to poll verifications folder and send emails

### ❌ NOT STARTED
1. Backend service updates (Week 3)
2. Testing in test environment (Week 4)
3. Production migration (Week 5)

## 11. Next Steps - Immediate Priority

### verify_token.php Migration (Week 2 Day 3-4)
1. Replace Google Cloud Storage with Object Storage
2. Use ObjectStorageClient->uploadRegistration() method
3. Implement duplicate submission prevention using `form_submitted` flag
4. Switch to SecureDatabase class for all queries
5. Add HMAC signatures to patient registration JSON

### Communication Service Integration
1. Implement polling of dev/verifications/ folder
2. Process email verification JSON files
3. Send emails via local SMTP relay
4. Delete processed files from Object Storage
5. Monitor for files older than 30 minutes

### Actual Achievements vs Plan
- **Week 1**: 100% complete as planned
- **Week 2 Day 1-2**: send_verification.php fully migrated
- **Behind schedule**: Backend services not yet configured
- **Ahead on**: Security implementation (HMAC working earlier than expected)

---

*Document Version: 9.0*  
*Date: September 3, 2025*  
*Status: Week 2 Day 1-2 COMPLETED - send_verification.php migrated to Object Storage*  
*Last Updated: September 3, 2025 - 12:00 CET*  
*Next Task: Update verify_token.php to use Object Storage*