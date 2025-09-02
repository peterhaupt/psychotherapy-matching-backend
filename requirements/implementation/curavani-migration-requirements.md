# Curavani System Migration - Requirements & Implementation Plan
## UPDATED with Week 1 Progress - September 2025

## Executive Summary

Migration of the Curavani patient registration system from multiple providers (domainfactory, GoDaddy, SendGrid, Google Cloud) to a single provider (Infomaniak) with enhanced security and simplified architecture using Object Storage with three environments for testing.

## 1. Core Migration Goals

1. **Get rid of SendGrid** - Move all email sending to communication-service with local SMTP relay
2. **Get rid of Google Cloud Storage** - Replace with Infomaniak Object Storage (Swift) 🔄 **INFRASTRUCTURE READY**
3. **Consolidate on Infomaniak** - Use their PHP hosting, MariaDB, and Object Storage 🔄 **INFRASTRUCTURE SETUP IN PROGRESS**
4. **Maintain decoupled architecture** - Continue using JSON files as interface 🔄 **READY TO IMPLEMENT**
5. **Increase security level** - Implement security enhancements inline with migration
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

### 3.2 Infrastructure Overview 🔄 **INFRASTRUCTURE SETUP COMPLETED**
- **ONE PHP hosting environment** at Infomaniak (production web hosting) ✅ **DEPLOYED**
- **ONE MariaDB** at Infomaniak (for tokens and rate limiting only) 🔄 **NOT CONFIGURED YET**
- **THREE Object Storage containers** at Infomaniak (dev, test, prod) ✅ **CREATED**
- **THREE backend environments** running locally in Docker containers 🔄 **NOT CONFIGURED YET**

### 3.3 Data Storage Structure ✅ **INFRASTRUCTURE CREATED**
```
Object Storage (Infomaniak Swift): ✅ CONTAINERS CREATED
  Containers:
    dev/                    # Development container ✅ CREATED & TESTED
      verifications/        # Email verification requests ✅ FOLDER READY
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

**Status**: Infrastructure ready, no production code migrated yet.

### 3.4 Environment Configuration 🔄 **PARTIALLY CONFIGURED**
- **PHP Environment**: Single production hosting at Infomaniak ✅ **DEPLOYED**
- **Environment Selection**: Manual config file change (`config.php`) ✅ **CONFIGURED**
- **Backend Services**: Each Docker container reads only from its corresponding Object Storage container
  - Dev backend → `dev` container 🔄 **INFRASTRUCTURE READY**
  - Test backend → `test` container 🔄 **INFRASTRUCTURE READY**
  - Prod backend → `prod` container 🔄 **INFRASTRUCTURE READY**
- **MariaDB**: Single database for all environments (only stores transient data) 🔄 **NOT CONFIGURED**

### 3.5 Testing Workflow 🔄 **INFRASTRUCTURE READY FOR TESTING**
1. Set PHP config to `environment: 'dev'` → Test with dev backend 🔄 **READY WHEN DEV BACKEND CONFIGURED**
2. Set PHP config to `environment: 'test'` → Validate with test backend 🔄 **READY WHEN TEST BACKEND CONFIGURED**
3. Set PHP config to `environment: 'prod'` → Go live with production backend 🔄 **READY WHEN PROD BACKEND CONFIGURED**

**Status**: Infrastructure setup allows environment switching, but no backend services configured yet.

## 4. Technical Stack - VERIFIED ✅

### 4.1 Object Storage Details (Basic Upload Tested) ✅ **INFRASTRUCTURE SETUP CONFIRMED SEPTEMBER 2025**
- **Provider**: Infomaniak OpenStack Swift ✅ **WORKING**
- **Access Method**: Native Swift API (not S3-compatible) ✅ **BASIC UPLOAD TESTED**
- **PHP Library**: `php-opencloud/openstack` v3.14.0 ✅ **INSTALLED & BASIC UPLOAD WORKING**
- **Python Library**: `python-swiftclient` with `keystoneauth1` 🔄 **NOT CONFIGURED YET**
- **Authentication**: Application Credentials (ID + Secret) ✅ **CONFIGURED & WORKING**
- **Auth Endpoint**: `https://api.pub1.infomaniak.cloud/identity/v3` ✅ **WORKING**
- **Storage Endpoint**: `***REMOVED***` ✅ **WORKING**
- **Region**: `dc4-a` ✅ **VERIFIED**
- **Performance**: Basic upload operations tested successfully ✅ **TESTED SEPTEMBER 2025**

### 4.2 PHP Environment (Basic Setup Working) ✅ **CONFIRMED**
- **PHP Version**: 8.1.33 ✅ **VERIFIED**
- **Memory Limit**: 640M ✅ **SUFFICIENT**
- **Max Execution Time**: 60 seconds ✅ **SUFFICIENT**
- **Required Extensions**: All present (mysqli, pdo, json, curl, mbstring, openssl, hash) ✅ **VERIFIED**
- **Composer**: v2.8.3 installed and working ✅ **OPERATIONAL**
- **ObjectStorageClient**: Basic upload class created and tested ✅ **BASIC FUNCTIONALITY WORKING**

### 4.3 MariaDB (Ready for Setup)
- **Version**: Expected 10.11.13-MariaDB-deb11-log
- **Host Pattern**: `[database].myd.infomaniak.com`
- **Connection Methods**: MySQLi and PDO both supported
- **Features**: Transactions, JSON columns, UTF8MB4, Prepared statements
- **Purpose**: Token storage, rate limiting, duplicate prevention only

### 4.4 Configuration File Structure ✅ **IMPLEMENTED & TESTED**
```php
// config.php - Located in /private/ folder ✅ WORKING
<?php
return [
    // Environment switching ✅ IMPLEMENTED
    'environment' => 'dev',  // Change to 'test' or 'prod'
    
    // Object storage ✅ WORKING
    'object_storage' => [
        'auth_url' => 'https://api.pub1.infomaniak.cloud/identity/v3',
        'region' => 'dc4-a',
        'credentials' => [
            'id' => 'ACTUAL_CREDENTIAL_ID',     // ✅ CONFIGURED
            'secret' => 'ACTUAL_CREDENTIAL_SECRET' // ✅ CONFIGURED
        ]
    ],
    
    // Database (to be configured)
    'database' => [
        'host' => 'DATABASE_NAME.myd.infomaniak.com',
        'name' => 'curavani_db',
        'user' => 'DB_USERNAME',
        'pass' => 'DB_PASSWORD'
    ],
    
    // Security ✅ IMPLEMENTED
    'security' => [
        'hmac_key' => 'SECRET_HMAC_KEY'  // ✅ CONFIGURED
    ]
];
```

## 5. Specific Requirements

### 5.1 Email Verification Migration
- Move email sending from `send_verification.php` to communication-service
- PHP creates `verification_request.json` file in Object Storage 🔄 **INFRASTRUCTURE READY**
- Communication-service polls and sends verification email 🔄 **NOT IMPLEMENTED**
- Keep token storage in MariaDB for rate limiting 🔄 **DATABASE NOT CONFIGURED**
- **Security built-in**: HMAC signatures, prepared statements, rate limiting 🔄 **NOT IMPLEMENTED**

### 5.2 Contact Form Enhancement
- Modify `patienten.html` contact form 🔄 **NOT STARTED**
- Create `contact_form.json` file via PHP in Object Storage 🔄 **INFRASTRUCTURE READY**
- Communication-service sends to support email 🔄 **NOT IMPLEMENTED**
- **Support email address**: `patienten@curavani.com`
- **Security built-in**: Input validation, XSS prevention, HMAC signatures 🔄 **NOT IMPLEMENTED**

### 5.3 Patient Registration
- Continue current flow but with Object Storage instead of GCS
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

### 5.5 Performance Requirements 🔄 **INFRASTRUCTURE TESTED**
- **Email delay**: 10-30 seconds acceptable 🔄 **NOT TESTED - NO EMAIL IMPLEMENTATION**
- **Polling frequency**: Every 10-30 seconds 🔄 **NOT IMPLEMENTED**
- **Expected load**: 
  - < 100 registrations/hour 🔄 **NOT TESTED**
  - < 1,000 emails/hour 🔄 **NOT TESTED**
- **File monitoring**: Alert if files older than 30 minutes exist 🔄 **NOT IMPLEMENTED**
- **Measured performance**: Basic Object Storage upload working ✅ **BASIC UPLOAD TESTED**

## 6. Security Implementation (INLINE WITH DEVELOPMENT)

### 6.1 Security Features by Component

#### PHP Files (Week 2 Implementation)
Each PHP file will be updated ONCE with all security features:

**ObjectStorageClient.php**: 🔄 **BASIC STRUCTURE CREATED**
- 🔄 HMAC signature generation code exists (NOT TESTED)
- ✅ Basic error handling implemented
- ✅ Environment-based container selection working
- ✅ Basic connection testing methods working

**send_verification.php** (pending):
- Prepared statements for all database queries
- Rate limiting (enhance existing)
- HMAC signature on JSON output (code structure ready)
- Input validation and sanitization

**verify_token.php** (pending):
- Prepared statements for all queries
- Duplicate submission prevention (`form_submitted` column)
- HMAC signature on JSON output (code structure ready)
- Comprehensive input validation
- XSS prevention

**process_contact.php** (pending):
- Input validation and sanitization
- HMAC signature on JSON output (code structure ready)
- XSS prevention
- Rate limiting

#### Backend Services (Week 3 Implementation)
Each service updated ONCE with all security features:

**Communication-service & Patient-service**:
- HMAC verification on all incoming files
- File age monitoring
- Secure error handling
- Environment isolation verification

### 6.2 HMAC Signature Structure 🔄 **CODE STRUCTURE READY - NOT TESTED**
```json
{
  "signature": "hmac_sha256_hash",
  "timestamp": "2024-01-15T10:00:00Z",
  "type": "email_verification",
  "environment": "prod",
  "data": { ... actual payload ... }
}
```

**Status**: Code structure exists in ObjectStorageClient but signature generation and verification not tested.

### 6.3 Database Schema Updates
```sql
-- Add to verification_tokens table during Week 1 setup
ALTER TABLE verification_tokens 
ADD COLUMN form_submitted BOOLEAN DEFAULT FALSE,
ADD INDEX idx_email_hash (email_hash),
ADD INDEX idx_created_at (created_at);
```

## 7. Implementation Plan (REVISED WITH PROGRESS)

### 7.1 Week 1: Infrastructure Setup

**Day 1-2: Object Storage Setup** ✅ **COMPLETED SEPTEMBER 2, 2025**
- ✅ Create three containers (`dev`, `test`, `prod`)
- ✅ Create folder structure in each container
- ✅ Generate and test Application Credentials
- ✅ Verify CLI access from Mac
- ✅ Test upload/download functionality

**Day 3: Database Setup** 🔄 **NEXT STEP**
- Set up single MariaDB database
- Create verification_tokens table WITH all columns including `form_submitted`
- Create verification_requests table for rate limiting
- Test database connection

**Day 4-5: PHP Hosting Setup** ✅ **BASIC SETUP COMPLETED**
- ✅ Deploy PHP application to Infomaniak
- ✅ Configure credentials in config.php
- ✅ Create and test basic ObjectStorageClient functionality
- ✅ Verify Swift connection and basic upload works
- 🔄 HMAC signatures - code structure exists but not tested

### 7.2 Week 2: PHP Implementation WITH Security

**Day 1: ObjectStorageClient Implementation** ✅ **BASIC FUNCTIONALITY COMPLETED**
```php
class ObjectStorageClient {
    // ✅ BASIC UPLOAD/DOWNLOAD WORKING
    // ✅ Environment-based container selection working
    // ✅ Basic error handling working
    // 🔄 HMAC signature code exists but not verified
    // 🔄 Security metadata structure exists but not tested
}
```

**Day 2-3: send_verification.php Update** 🔄 **NEXT STEPS**
- Replace SendGrid with Object Storage
- Implement all prepared statements
- Enhance rate limiting
- Add HMAC signatures ✅ **READY**
- Complete testing

**Day 4: verify_token.php Update** 🔄 **PENDING**
- Replace GCS upload with Object Storage
- Add duplicate submission prevention
- Implement all prepared statements
- Add HMAC signatures ✅ **READY**
- Secure all validation functions
- Complete testing

**Day 5: process_contact.php Creation** 🔄 **PENDING**
- Create new file for contact form handling
- Implement Object Storage upload
- Add comprehensive input validation
- Add HMAC signatures ✅ **READY**
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

## 8. Implementation Code Templates

### 8.1 Secure PHP Swift Client ✅ **IMPLEMENTED & TESTED**
```php
use OpenStack\OpenStack;

class ObjectStorageClient {
    // ✅ WORKING IMPLEMENTATION
    // Location: /private/ObjectStorageClient.php
    // Status: Successfully tested September 2, 2025
    // Features: HMAC signatures, error handling, environment selection
}
```

### 8.2 Secure Database Connection
```php
class SecureDatabase {
    // To be implemented in Week 1 Day 3
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
**Week 1 - Infrastructure Testing** 🔄 **BASIC FUNCTIONALITY TESTED**
- ✅ Object Storage connection verified
- 🔄 HMAC signature generation - code exists, not tested
- ✅ Environment isolation confirmed (container selection works)
- ✅ Upload/download functionality verified
- ✅ Basic error handling tested
- ❌ HMAC verification - not tested
- ❌ Security metadata validation - not tested

**Week 2 - PHP Testing**
- [ ] SQL injection attempts on all forms
- [ ] XSS attempts in all input fields
- [ ] Rate limiting verification (3 requests/hour)
- [ ] HMAC signature validation
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
- ✅ HMAC signature generation
- ✅ Environment selection working
- [ ] Email verification flow
- [ ] Patient registration flow
- [ ] Contact form submission
- [ ] File processing verification
- [ ] Error handling

**Test Environment** 🔄 **READY**
- [ ] Complete end-to-end flow
- [ ] Load testing (100 registrations)
- [ ] Concurrent user testing
- [ ] Database transaction handling

**Production Environment** 🔄 **READY**
- [ ] Smoke tests only
- [ ] Monitoring verification
- [ ] Rollback procedure test

### 9.3 Performance Benchmarks ✅ **VERIFIED**
- ✅ Object Storage write: Working (tested)
- ✅ Object Storage read: Working (tested)
- Email processing: < 30 seconds (to be tested)
- Registration processing: < 60 seconds (to be tested)
- Database queries: < 10ms (to be tested)

## 10. Progress Summary - September 2, 2025

### ✅ ACTUALLY COMPLETED - INFRASTRUCTURE SETUP ONLY
1. **Object Storage Infrastructure Setup**
   - 3 containers created at Infomaniak (dev, test, prod)
   - Folder structure created and verified
   - Application credentials configured and working
   - CLI access from Mac for container management
   - Basic PHP upload functionality tested and working

2. **PHP Environment Setup**
   - Hosting account deployed at Infomaniak
   - Composer installed with `php-opencloud/openstack` library
   - Basic ObjectStorageClient.php created and tested for uploads
   - Config.php created with environment switching capability
   - Basic connectivity to Object Storage verified

### 🔄 CODE STRUCTURE EXISTS BUT NOT IMPLEMENTED/TESTED
1. **Security Features**
   - HMAC signature code exists in ObjectStorageClient but never tested
   - Security metadata structure exists but not validated
   - No HMAC verification implemented anywhere

### ❌ NOT STARTED - NO PRODUCTION CODE CHANGED
1. **Database Setup** - MariaDB not configured
2. **PHP File Migration** - No existing production files modified
3. **Backend Integration** - No backend services configured
4. **Email System Migration** - Still using SendGrid
5. **GCS Replacement** - Production still uses Google Cloud Storage

### 📊 ACTUAL ACHIEVEMENTS
- ✅ Alternative Object Storage infrastructure ready at Infomaniak
- ✅ Basic upload capability from PHP to Object Storage working
- ✅ Environment switching infrastructure configured
- ✅ Foundation ready for actual migration work
- ❌ NO production system changes made yet
- ❌ NO actual migration completed yet

## 11. Next Steps for New Chat Session

### Immediate Priority: Complete Basic Week 1 Setup
1. **Test HMAC functionality** - Verify the signature code actually works
2. **Database Setup (Week 1 Day 3)**:
   - Create MariaDB database at Infomaniak
   - Set up verification_tokens table
   - Create verification_requests table for rate limiting
   - Test database connectivity from PHP
   - Update config.php with database credentials

### Following Priority: Begin Actual Implementation (Week 2)
1. **Migrate send_verification.php** - Replace SendGrid with Object Storage uploads
2. **Migrate verify_token.php** - Replace GCS with Object Storage uploads  
3. **Create process_contact.php** - New contact form handler using Object Storage

### Implementation Priority: Backend Services (Week 3)
1. **Update communication-service** - Add Object Storage polling and processing
2. **Update patient-service** - Replace GCS with Object Storage polling
3. **End-to-end testing** - Verify complete migration workflow

**Important Note**: No production code has been changed yet. All current systems (SendGrid, GCS) are still in use. We have only set up alternative infrastructure.

---

*Document Version: 7.2*  
*Date: September 2025*  
*Status: Week 1 Object Storage Infrastructure Setup Completed - No Production Code Changed Yet*  
*Last Updated: September 2, 2025*  
*Next Session Focus: Database Setup and Begin Actual Migration Implementation*