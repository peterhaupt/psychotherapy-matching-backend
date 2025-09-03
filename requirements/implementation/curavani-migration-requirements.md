# Curavani System Migration - Requirements & Implementation Plan
## UPDATED with Week 2 COMPLETED - September 3, 2025

## Executive Summary

Migration of the Curavani patient registration system from multiple providers (domainfactory, GoDaddy, SendGrid, Google Cloud) to a single provider (Infomaniak) with enhanced security and simplified architecture using Object Storage with three environments for testing.

## 1. Core Migration Goals

1. **Get rid of SendGrid** - Move all email sending to communication-service with local SMTP relay ✅ **PHP SIDE COMPLETE**
2. **Get rid of Google Cloud Storage** - Replace with Infomaniak Object Storage (Swift) ✅ **PHP SIDE COMPLETE**
3. **Consolidate on Infomaniak** - Use their PHP hosting, MariaDB, and Object Storage ✅ **INFRASTRUCTURE COMPLETED**
4. **Maintain decoupled architecture** - Continue using JSON files as interface ✅ **IMPLEMENTED**
5. **Increase security level** - Implement security enhancements inline with migration ✅ **IMPLEMENTED**
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
- **THREE backend environments** running locally in Docker containers 🔄 **PENDING CONFIGURATION**

### 3.3 Data Storage Structure ✅ **FULLY IMPLEMENTED**
```
Object Storage (Infomaniak Swift): ✅ CONTAINERS CREATED AND IN USE
  Containers:
    dev/                    # Development container ✅ ACTIVELY USED
      verifications/        # Email verification requests ✅ RECEIVING DATA
      contacts/            # Contact form submissions ✅ RECEIVING DATA  
      registrations/       # Patient registrations ✅ RECEIVING DATA
    
    test/                   # Test container ✅ CREATED
      verifications/      ✅ READY FOR TESTING
      contacts/          ✅ READY FOR TESTING
      registrations/     ✅ READY FOR TESTING
    
    prod/                   # Production container ✅ CREATED
      verifications/      ✅ READY FOR PRODUCTION
      contacts/          ✅ READY FOR PRODUCTION
      registrations/     ✅ READY FOR PRODUCTION
```

**Status**: All PHP files migrated and uploading to Object Storage. Backend services need to process files.

### 3.4 Environment Configuration ✅ **FULLY CONFIGURED**
- **PHP Environment**: Single production hosting at Infomaniak ✅ **DEPLOYED**
- **Environment Selection**: Manual config file change (`config.php`) ✅ **CONFIGURED**
- **Backend Services**: Each Docker container reads only from its corresponding Object Storage container
  - Dev backend → `dev` container ✅ **INFRASTRUCTURE READY**
  - Test backend → `test` container ✅ **INFRASTRUCTURE READY**
  - Prod backend → `prod` container ✅ **INFRASTRUCTURE READY**
- **MariaDB**: Single database for all environments (only stores transient data) ✅ **CONFIGURED & WORKING**

### 3.5 Testing Workflow ✅ **READY FOR BACKEND INTEGRATION**
1. Set PHP config to `environment: 'dev'` → Test with dev backend ✅ **PHP SIDE WORKING**
2. Set PHP config to `environment: 'test'` → Validate with test backend ✅ **PHP SIDE READY**
3. Set PHP config to `environment: 'prod'` → Go live with production backend ✅ **PHP SIDE READY**

**Status**: PHP side complete, awaiting backend service updates.

## 4. Technical Stack - VERIFIED ✅

### 4.1 Object Storage Details ✅ **FULLY OPERATIONAL**
- **Provider**: Infomaniak OpenStack Swift ✅ **WORKING**
- **Access Method**: Native Swift API (not S3-compatible) ✅ **IMPLEMENTED IN ALL PHP FILES**
- **PHP Library**: `php-opencloud/openstack` v3.14.0 ✅ **INSTALLED & WORKING**
- **Python Library**: `python-swiftclient` with `keystoneauth1` 🔄 **PENDING BACKEND IMPLEMENTATION**
- **Authentication**: Application Credentials (ID + Secret) ✅ **CONFIGURED & WORKING**
- **Auth Endpoint**: `https://api.pub1.infomaniak.cloud/identity/v3` ✅ **WORKING**
- **Storage Endpoint**: `***REMOVED***` ✅ **WORKING**
- **Region**: `dc4-a` ✅ **VERIFIED**
- **Performance**: Upload operations tested successfully across all PHP files ✅ **VERIFIED**

### 4.2 PHP Environment ✅ **FULLY OPERATIONAL**
- **PHP Version**: 8.1.33 ✅ **VERIFIED**
- **Memory Limit**: 640M ✅ **SUFFICIENT**
- **Max Execution Time**: 60 seconds ✅ **SUFFICIENT**
- **Required Extensions**: All present ✅ **VERIFIED**
- **Composer**: v2.8.3 installed and working ✅ **OPERATIONAL**
- **ObjectStorageClient**: Working in all PHP files ✅ **FULLY DEPLOYED**
- **SecureDatabase**: Implemented with prepared statements ✅ **WORKING**

### 4.3 MariaDB ✅ **FULLY CONFIGURED & OPERATIONAL**
- **Version**: 10.11.13-MariaDB ✅ **VERIFIED**
- **Host Pattern**: `[database].myd.infomaniak.com` ✅ **CONNECTED**
- **Connection Methods**: SecureDatabase class with PDO ✅ **IMPLEMENTED**
- **Features**: Transactions, Prepared statements, Rate limiting ✅ **ALL VERIFIED**
- **Purpose**: Token storage, rate limiting, duplicate prevention only ✅ **IN USE**
- **Tables Created and In Use**:
  - `verification_tokens` with `form_submitted` column ✅
  - `verification_requests` for rate limiting ✅
  - `system_logs` for monitoring ✅

### 4.4 Configuration File Structure ✅ **FINALIZED & DEPLOYED**
- **Location**: `/private/config.php` ✅
- **Environment switching**: Working ✅
- **Object Storage credentials**: Configured ✅
- **Database credentials**: Configured ✅
- **HMAC security key**: Configured ✅
- **Helper functions**: Separated to `config_functions.php` ✅

## 5. Specific Requirements

### 5.1 Email Verification Migration ✅ **COMPLETED SEPTEMBER 3, 2025**
- ✅ Moved email sending from `send_verification.php` to Object Storage
- ✅ PHP creates `verification_request.json` file in Object Storage
- 🔄 Communication-service polls and sends verification email **PENDING BACKEND**
- ✅ Token storage in MariaDB for rate limiting working
- ✅ **Security implemented**: HMAC signatures, prepared statements, rate limiting

### 5.2 Contact Form Enhancement ✅ **COMPLETED SEPTEMBER 3, 2025**
- ✅ Modified `process_contact.php` for patienten.html
- ✅ Creates `contact_form.json` file via PHP in Object Storage
- 🔄 Communication-service sends to support email **PENDING BACKEND**
- ✅ **Support email address**: `patienten@curavani.com` configured
- ✅ **Security implemented**: Input validation, XSS prevention, HMAC signatures

### 5.3 Patient Registration ✅ **COMPLETED SEPTEMBER 3, 2025**
- ✅ Migrated from GCS to Object Storage
- ✅ PHP (`verify_token.php`) → JSON file → Object Storage working
- 🔄 Patient-service imports from Object Storage **PENDING BACKEND**
- ✅ **Security implemented**: Duplicate prevention, validation, HMAC signatures

### 5.4 File Processing 🔄 **PENDING BACKEND IMPLEMENTATION**
- 🔄 Backend services poll their respective containers **NOT IMPLEMENTED**
- 🔄 Download and process files immediately **NOT IMPLEMENTED**
- 🔄 Delete files from Object Storage after processing **NOT IMPLEMENTED**
- 🔄 Files older than 30 minutes indicate problems **NOT IMPLEMENTED**
- 🔄 Services handle their own error tracking **NOT IMPLEMENTED**
- ✅ **Security ready**: HMAC signatures generated by PHP

### 5.5 Performance Requirements ✅ **PHP SIDE MEETS REQUIREMENTS**
- **Email delay**: 10-30 seconds acceptable (pending backend)
- **Polling frequency**: Every 10-30 seconds (backend configuration)
- **Expected load**: System capable of handling:
  - < 100 registrations/hour
  - < 1,000 emails/hour
- **File monitoring**: Pending backend implementation
- **Measured performance**: Object Storage upload < 100ms ✅

## 6. Security Implementation ✅ **COMPLETED FOR PHP**

### 6.1 Security Features by Component

#### PHP Files (Week 2 Implementation) ✅ **ALL COMPLETED**

**ObjectStorageClient.php**: ✅ **COMPLETED SEPTEMBER 3, 2025**
- ✅ HMAC signature generation working
- ✅ Enhanced error handling implemented
- ✅ Environment-based container selection working
- ✅ Connection testing methods working
- ✅ Specific upload methods for different types

**SecureDatabase.php**: ✅ **COMPLETED SEPTEMBER 2-3, 2025**
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

**verify_token.php** ✅ **COMPLETED SEPTEMBER 3, 2025**:
- ✅ Prepared statements for all queries
- ✅ Duplicate submission prevention (`form_submitted` column)
- ✅ HMAC signature on JSON output
- ✅ Comprehensive input validation
- ✅ XSS prevention
- ✅ Transaction management with rollback

**process_contact.php** ✅ **COMPLETED SEPTEMBER 3, 2025**:
- ✅ Input validation and sanitization
- ✅ HMAC signature on JSON output
- ✅ XSS prevention with htmlspecialchars
- ✅ Message length validation

#### Backend Services (Week 3 Implementation) 🔄 **PENDING**
Each service needs updating with:
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

**Status**: HMAC signatures successfully implemented in all PHP files.

### 6.3 Database Schema Updates ✅ **COMPLETED**
- ✅ `form_submitted` column added to verification_tokens
- ✅ Indexes created for performance
- ✅ Rate limiting tables operational

## 7. Implementation Plan (REVISED WITH PROGRESS)

### 7.1 Week 1: Infrastructure Setup ✅ **COMPLETED SEPTEMBER 2, 2025**
- ✅ Object Storage setup complete
- ✅ Database setup complete
- ✅ PHP hosting setup complete
- ✅ Basic functionality verified

### 7.2 Week 2: PHP Implementation WITH Security ✅ **COMPLETED SEPTEMBER 3, 2025**

**Day 1: ObjectStorageClient Implementation** ✅ **COMPLETED**
- ✅ Enhanced with specific upload methods
- ✅ Environment-based container selection
- ✅ HMAC signatures working
- ✅ Metadata issue fixed

**Day 2: send_verification.php Update** ✅ **COMPLETED**
- ✅ Replaced SendGrid with Object Storage
- ✅ Using SecureDatabase with prepared statements
- ✅ HMAC signatures on JSON files
- ✅ Rate limiting maintained

**Day 3-4: verify_token.php Update** ✅ **COMPLETED SEPTEMBER 3, 2025**
- ✅ Replaced GCS with Object Storage
- ✅ Added duplicate submission prevention
- ✅ Implemented all prepared statements
- ✅ Added HMAC signatures
- ✅ Secured all validation functions
- ✅ Complete testing in dev environment

**Day 5: process_contact.php Creation** ✅ **COMPLETED SEPTEMBER 3, 2025**
- ✅ Created new file for contact form handling
- ✅ Implemented Object Storage upload
- ✅ Added comprehensive input validation
- ✅ Added HMAC signatures
- ✅ XSS prevention implemented

### 7.3 Week 3: Backend Updates WITH Security 🔄 **NEXT PRIORITY**

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

### 7.4 Week 4: Testing & Validation 🔄 **UPCOMING**

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

### 7.5 Week 5: Production Migration 🔄 **UPCOMING**
1. DNS preparation (reduce TTL 48 hours before)
2. Data migration from domainfactory to Infomaniak
3. Final database migration
4. Switch DNS to Infomaniak
5. Monitor for 48-72 hours
6. Keep domainfactory as backup for 1 week
7. Decommission old infrastructure

## 8. Implementation Code Status

### 8.1 Secure PHP Swift Client ✅ **FULLY DEPLOYED**
- **Location**: `/private/ObjectStorageClient.php`
- **Status**: Working in production
- **Features**: HMAC signatures, error handling, environment selection
- **Methods**: uploadVerificationRequest, uploadRegistration, uploadContactForm

### 8.2 Secure Database Connection ✅ **FULLY DEPLOYED**
- **Location**: `/private/SecureDatabase.php`
- **Features**: Prepared statements, transactions, secure error handling
- **Status**: Used by all PHP files

### 8.3 Python Backend with Security 🔄 **TO BE IMPLEMENTED**
```python
# Week 3 implementation needed
class SecureObjectStorageClient:
    # HMAC verification
    # Swift API connection
    # File processing logic
```

## 9. Testing Strategy

### 9.1 Security Testing Checklist

**Week 1 - Infrastructure Testing** ✅ **COMPLETED**
- ✅ Object Storage connection verified
- ✅ Database connection verified
- ✅ Environment isolation confirmed
- ✅ Upload/download functionality verified
- ✅ Database tables created with security columns

**Week 2 - PHP Testing** ✅ **COMPLETED**
- ✅ HMAC signature generation tested
- ✅ HMAC signatures present in all uploads
- ✅ Rate limiting verification working
- ✅ SQL injection prevention (prepared statements)
- ✅ XSS prevention in contact form
- ✅ Duplicate submission prevention
- ✅ Invalid token handling
- ✅ Expired token handling

**Week 3 - Backend Testing** 🔄 **UPCOMING**
- [ ] HMAC signature verification
- [ ] Environment isolation (no cross-reads)
- [ ] File age monitoring alerts
- [ ] Invalid JSON handling
- [ ] Missing signature handling
- [ ] Environment mismatch handling

### 9.2 Functional Testing per Environment

**Dev Environment** ✅ **PHP SIDE COMPLETE**
- ✅ Object Storage upload/download
- ✅ Database connectivity
- ✅ Environment selection working
- ✅ HMAC signature generation
- ✅ Email verification flow (PHP side)
- ✅ Patient registration flow (PHP side)
- ✅ Contact form submission (PHP side)
- [ ] File processing verification (backend)
- [ ] End-to-end email sending

**Test Environment** 🔄 **READY FOR TESTING**
- Infrastructure ready
- PHP code deployable
- Awaiting backend updates

**Production Environment** 🔄 **READY FOR DEPLOYMENT**
- Infrastructure ready
- PHP code ready
- Awaiting full system testing

### 9.3 Performance Benchmarks ✅ **PHP SIDE VERIFIED**
- ✅ Object Storage write: < 100ms
- ✅ Object Storage read: < 100ms  
- ✅ Database queries: < 10ms
- Email processing: < 30 seconds (pending backend)
- Registration processing: < 60 seconds (pending backend)

## 10. Progress Summary - September 3, 2025

### ✅ WEEK 1 COMPLETED - Infrastructure Setup
- All infrastructure components deployed and configured
- Object Storage containers created
- Database configured with all tables
- PHP environment operational

### ✅ WEEK 2 COMPLETED - PHP Migration
1. **send_verification.php** - Fully migrated from SendGrid to Object Storage
2. **verify_token.php** - Fully migrated from GCS to Object Storage
3. **process_contact.php** - Created and integrated with Object Storage
4. **Security Features** - All implemented (HMAC, prepared statements, validation)
5. **Testing** - All PHP components tested in dev environment

### 🔄 IN PROGRESS - Week 3 Backend Services
1. **Communication Service** - Needs Swift client and polling logic
2. **Patient Service** - Needs Swift client and import logic

### ❌ NOT STARTED
1. Week 4: Full system testing
2. Week 5: Production migration

## 11. Next Steps - Immediate Priority

### Communication Service Integration (Week 3 Day 1-2)
1. **Implement Swift client** in Python
2. **Add polling logic** for all three folders:
   - `verifications/` - Send verification emails
   - `contacts/` - Forward to support email
   - `registrations/` - Send confirmation emails
3. **HMAC verification** for all files
4. **Delete processed files** from Object Storage
5. **Monitor file age** (alert if > 30 minutes)

### Patient Service Integration (Week 3 Day 3-4)
1. **Replace GCS client** with Swift
2. **Poll registrations/** folder
3. **HMAC verification** before processing
4. **Import patient data** to database
5. **Delete processed files**

### Testing Requirements
1. **Dev Environment First** - Complete end-to-end testing
2. **Performance Monitoring** - Ensure < 30 second email delivery
3. **Error Handling** - Test failure scenarios
4. **Security Validation** - Verify HMAC rejection of invalid signatures

## 12. Week 2 Completion Summary

### Files Successfully Migrated
| File | Status | Features | Testing |
|------|--------|----------|---------|
| send_verification.php | ✅ Deployed | HMAC, Rate limiting, Object Storage | ✅ Tested |
| verify_token.php | ✅ Deployed | HMAC, Duplicate prevention, Transactions | ✅ Tested |
| process_contact.php | ✅ Deployed | HMAC, XSS prevention, Validation | ✅ Tested |

### Security Features Implemented
- **HMAC Signatures**: All JSON files signed
- **Prepared Statements**: All database queries secured
- **Rate Limiting**: 3 requests/hour for verification
- **Duplicate Prevention**: form_submitted flag
- **Input Validation**: All forms validated
- **XSS Prevention**: htmlspecialchars on all inputs

### What's Working
- ✅ All PHP files uploading to Object Storage
- ✅ Environment switching (dev/test/prod)
- ✅ Database operations with SecureDatabase
- ✅ HMAC signatures on all uploads
- ✅ Rate limiting for verification emails

### What's Pending
- 🔄 Backend services processing files
- 🔄 Actual email sending
- 🔄 File deletion after processing
- 🔄 Monitoring and alerting
- 🔄 Full end-to-end testing

---

*Document Version: 10.0*  
*Date: September 3, 2025*  
*Status: Week 2 COMPLETED - All PHP files migrated to Object Storage*  
*Last Updated: September 3, 2025 - 15:30 CET*  
*Next Task: Update Communication and Patient services for Object Storage (Week 3)*