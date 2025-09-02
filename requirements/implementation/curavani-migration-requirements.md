# Curavani System Migration - Requirements & Implementation Plan

## Executive Summary

Migration of the Curavani patient registration system from multiple providers (domainfactory, GoDaddy, SendGrid, Google Cloud) to a single provider (Infomaniak) with enhanced security and simplified architecture using Object Storage with three environments for testing.

## 1. Core Migration Goals

1. **Get rid of SendGrid** - Move all email sending to communication-service with local SMTP relay
2. **Get rid of Google Cloud Storage** - Replace with Infomaniak Object Storage (Swift)
3. **Consolidate on Infomaniak** - Use their PHP hosting, MariaDB, and Object Storage
4. **Maintain decoupled architecture** - Continue using JSON files as interface
5. **Increase security level** - Address critical vulnerabilities
6. **Support three test environments** - Dev, Test, and Production containers for backend testing

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

### 3.2 Infrastructure Overview
- **ONE PHP hosting environment** at Infomaniak (production web hosting)
- **ONE MariaDB** at Infomaniak (for tokens and rate limiting only)
- **THREE Object Storage containers** at Infomaniak (dev, test, prod)
- **THREE backend environments** running locally in Docker containers

### 3.3 Data Storage Structure
```
Object Storage (Infomaniak Swift):
  Containers:
    dev/                    # Development container
      verifications/        # Email verification requests
      contacts/            # Contact form submissions  
      registrations/       # Patient registrations
    
    test/                   # Test container
      verifications/      
      contacts/          
      registrations/     
    
    prod/                   # Production container
      verifications/      
      contacts/          
      registrations/
```

### 3.4 Environment Configuration
- **PHP Environment**: Single production hosting at Infomaniak
- **Environment Selection**: Manual config file change (`config.php`)
- **Backend Services**: Each Docker container reads only from its corresponding Object Storage container
  - Dev backend → `dev` container
  - Test backend → `test` container
  - Prod backend → `prod` container
- **MariaDB**: Single database for all environments (only stores transient data)

### 3.5 Testing Workflow
1. Set PHP config to `environment: 'dev'` → Test with dev backend
2. Set PHP config to `environment: 'test'` → Validate with test backend
3. Set PHP config to `environment: 'prod'` → Go live with production backend

## 4. Technical Stack - VERIFIED ✅

### 4.1 Object Storage Details (Tested & Working)
- **Provider**: Infomaniak OpenStack Swift
- **Access Method**: Native Swift API (not S3-compatible)
- **PHP Library**: `php-opencloud/openstack` ✅ Tested
- **Python Library**: `python-swiftclient` with `keystoneauth1` ✅ Tested
- **Authentication**: Application Credentials (ID + Secret)
- **Auth Endpoint**: `https://api.pub1.infomaniak.cloud/identity/v3`
- **Storage Endpoint**: `***REMOVED***`
- **Region**: `dc4-a`
- **Performance**: 62ms write, 42ms read average ✅

### 4.2 PHP Environment (Tested & Working)
- **PHP Version**: 8.1.33 ✅
- **Memory Limit**: 640M ✅
- **Max Execution Time**: 60 seconds ✅
- **Required Extensions**: All present (mysqli, pdo, json, curl, mbstring, openssl, hash) ✅
- **Performance**: Excellent (0.14ms INSERT, 0.08ms SELECT) ✅

### 4.3 MariaDB (Tested & Working)
- **Version**: 10.11.13-MariaDB-deb11-log ✅
- **Host Pattern**: `[database].myd.infomaniak.com` ✅
- **Connection Methods**: MySQLi and PDO both working ✅
- **Features Tested**: Transactions, JSON columns, UTF8MB4, Prepared statements ✅
- **Performance**: < 1ms for most operations ✅
- **Purpose**: Token storage, rate limiting, duplicate prevention only

### 4.4 Configuration File Structure (SIMPLIFIED)
```php
// config.php - Located on PHP hosting at Infomaniak
<?php
return [
    // CHANGE THIS to switch environments: 'dev', 'test', or 'prod'
    'environment' => 'dev',
    
    'object_storage' => [
        'authUrl' => 'https://api.pub1.infomaniak.cloud/identity/v3',
        'storageUrl' => '***REMOVED***',
        'region' => 'dc4-a',
        'credentials' => [
            'id' => getenv('SWIFT_APP_CREDENTIAL_ID'),
            'secret' => getenv('SWIFT_APP_CREDENTIAL_SECRET')
        ]
    ],
    
    'database' => [
        'host' => '[dbname].myd.infomaniak.com',
        'name' => 'curavani_db',
        'user' => getenv('DB_USER'),
        'pass' => getenv('DB_PASS')
    ],
    
    // Single HMAC key for all environments
    'hmac_key' => getenv('HMAC_KEY')
];
```

## 5. Specific Requirements

### 5.1 Email Verification Migration
- Move email sending from `send_verification.php` to communication-service
- PHP creates `verification_request.json` file in Object Storage
- Communication-service polls and sends verification email
- Keep token storage in MariaDB for rate limiting

### 5.2 Contact Form Enhancement
- Modify `patienten.html` contact form
- Create `contact_form.json` file via PHP in Object Storage
- Communication-service sends to support email
- **Support email address**: `patienten@curavani.com`

### 5.3 Patient Registration
- Continue current flow but with Object Storage instead of GCS
- PHP (`verify_token.php`) → JSON file → Object Storage
- Patient-service imports from Object Storage

### 5.4 File Processing
- Backend services poll their respective containers
- Download and process files immediately
- Delete files from Object Storage after processing (both success and failure)
- Files older than 30 minutes indicate backend processing problems
- Services handle their own error tracking

### 5.5 Performance Requirements
- **Email delay**: 10-30 seconds acceptable
- **Polling frequency**: Every 10-30 seconds
- **Expected load**: 
  - < 100 registrations/hour
  - < 1,000 emails/hour
- **File monitoring**: Alert if files older than 30 minutes exist
- **Measured performance**: 62ms write, 42ms read (well within requirements) ✅

## 6. Security Improvements (Priority 1 - Do After Phase 0)

### 6.1 HMAC Signatures for JSON Files

**Problem**: No authentication between PHP and services

**Solution**: Sign all JSON files with HMAC
```json
{
  "signature": "hmac_sha256_hash",
  "timestamp": "2024-01-15T10:00:00Z",
  "type": "email_verification",
  "environment": "prod",
  "data": { ... actual payload ... }
}
```

**Implementation**:
- Single shared secret key between PHP and all backend services
- Store in environment variables
- Include timestamp to prevent replay attacks
- Include type to prevent cross-purpose use
- Include environment to prevent cross-environment attacks

### 6.2 Strict Input Validation

**Problem**: Inconsistent validation between layers

**Solution**: Validate at both layers with clear responsibilities
- **PHP**: Format validation, XSS prevention, file system safety
- **Services**: Business logic, database constraints

**Critical validations**:
- Symptom array (1-3 items from approved list)
- Email format and header injection prevention
- PLZ format (exactly 5 digits)
- Phone number format
- Date validations

### 6.3 Prepared Statements Everywhere

**Problem**: SQL injection vulnerabilities

**Required changes**:
- `send_verification.php`: Token queries, rate limit checks
- `verify_token.php`: Token validation, updates
- Services: Ensure all SQLAlchemy queries are parameterized

### 6.4 Global Rate Limiting

**Problem**: Only per-email rate limiting exists

**Solution layers**:
1. **Per IP**: Limit requests from single IP
2. **Global**: System-wide limits (100 verifications/minute)
3. **Per action**: Different limits for different operations
4. **Progressive penalties**: Increasing block durations

### 6.5 Duplicate Form Submission Prevention

**Problem**: Patients can submit registration form multiple times with same token

**Solution**: Add separate tracking for form submission
```sql
ALTER TABLE verification_tokens 
ADD COLUMN form_submitted BOOLEAN DEFAULT FALSE;
```

## 7. Migration Plan

### 7.1 Phase 0: Infrastructure Testing ✅ COMPLETED
- ✅ All infrastructure components tested and verified
- ✅ Ready for implementation

### 7.2 Phase 1: Infomaniak Setup
1. Create three containers (`dev`, `test`, `prod`)
2. Set up folder structure within each container
3. Configure Application Credentials
4. Set up single MariaDB database
5. Configure environment variables on PHP hosting
6. Deploy PHP application to Infomaniak

### 7.3 Phase 2: Code Implementation

#### PHP Updates
1. Create `config.php` for environment management
2. Implement Swift client wrapper class
3. Add HMAC signing to all JSON outputs
4. Modify `send_verification.php` to write to Object Storage
5. Modify `verify_token.php` to write to Object Storage
6. Create `process_contact.php` for contact form handling
7. Add prepared statements to all database queries
8. Implement rate limiting checks
9. Add duplicate submission prevention

#### Backend Service Updates
1. **Communication-service** (each environment):
   - Add Swift client for Object Storage polling
   - Configure to read from specific container (dev/test/prod)
   - Poll `/verifications` folder for email verification requests
   - Poll `/contacts` folder for contact form submissions
   - Delete processed files
   - Use storage URL override for connection

2. **Patient-service** (each environment):
   - Replace GCS client with Swift client
   - Configure to read from specific container (dev/test/prod)
   - Poll `/registrations` folder
   - Delete processed files
   - Use storage URL override for connection

3. **All services**:
   - Add HMAC signature verification
   - Add file age monitoring
   - Environment-specific configuration

### 7.4 Phase 3: Testing
1. **Dev Environment Testing**:
   - Set PHP config to `environment: 'dev'`
   - Test all workflows with dev backend
   - Verify HMAC signatures
   - Test rate limiting
   - Performance testing

2. **Test Environment Validation**:
   - Set PHP config to `environment: 'test'`
   - Full integration testing
   - Security testing
   - Load testing
   - Backup/recovery testing

3. **Pre-Production Validation**:
   - Set PHP config to `environment: 'prod'`
   - Final security audit
   - Performance benchmarking
   - Rollback procedures

### 7.5 Phase 4: Production Migration
1. DNS preparation (reduce TTL 48 hours before)
2. Data migration from domainfactory to Infomaniak
3. Final database migration
4. Switch DNS to Infomaniak
5. Monitor for 48-72 hours
6. Keep domainfactory as backup for 1 week
7. Decommission old infrastructure

## 8. Implementation Code Examples

### 8.1 PHP Swift Client (Tested & Working)
```php
use OpenStack\OpenStack;

class ObjectStorageClient {
    private $container;
    private $config;
    private $containerName;
    
    public function __construct() {
        $this->config = require 'config.php';
        
        // Use the environment setting from config
        $this->containerName = $this->config['environment']; // 'dev', 'test', or 'prod'
        
        $openstack = new OpenStack([
            'authUrl' => $this->config['object_storage']['authUrl'],
            'region' => $this->config['object_storage']['region'],
            'application_credential' => [
                'id' => $this->config['object_storage']['credentials']['id'],
                'secret' => $this->config['object_storage']['credentials']['secret']
            ]
        ]);
        
        $objectStore = $openstack->objectStoreV1();
        $this->container = $objectStore->getContainer($this->containerName);
    }
    
    public function uploadJson($folder, $filename, $data) {
        $jsonContent = json_encode($this->addHmacSignature($data));
        $objectName = $folder . '/' . $filename;
        
        $this->container->createObject([
            'name' => $objectName,
            'content' => $jsonContent
        ]);
    }
    
    private function addHmacSignature($data) {
        $environment = $this->config['environment'];
        $key = $this->config['hmac_key'];
        
        $payload = [
            'timestamp' => date('c'),
            'environment' => $environment,
            'data' => $data
        ];
        
        $signature = hash_hmac('sha256', json_encode($payload), $key);
        $payload['signature'] = $signature;
        
        return $payload;
    }
}
```

### 8.2 Python Swift Client for Backend Services
```python
from swiftclient import client
from keystoneauth1 import session
from keystoneauth1.identity import v3
import json
import hmac
import hashlib
from datetime import datetime
import os

class ObjectStorageClient:
    def __init__(self):
        # Each backend knows its own environment
        self.environment = os.getenv('ENVIRONMENT', 'dev')  # 'dev', 'test', or 'prod'
        self.container = self.environment
        
        # Create auth
        auth = v3.ApplicationCredential(
            auth_url='https://api.pub1.infomaniak.cloud/identity/v3',
            application_credential_id=os.getenv('SWIFT_APP_CREDENTIAL_ID'),
            application_credential_secret=os.getenv('SWIFT_APP_CREDENTIAL_SECRET')
        )
        
        # Create session and get token
        sess = session.Session(auth=auth)
        token = sess.get_token()
        
        # Create connection with explicit storage URL
        self.conn = client.Connection(
            preauthurl='***REMOVED***',
            preauthtoken=token
        )
    
    def poll_and_process(self, folder, process_function):
        """Poll for new files in a folder and process them"""
        prefix = f"{folder}/"
        
        # List objects in folder
        headers, objects = self.conn.get_container(
            self.container,
            prefix=prefix
        )
        
        for obj in objects:
            # Download and process
            headers, content = self.conn.get_object(
                self.container,
                obj['name']
            )
            
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            data = json.loads(content)
            
            # Verify HMAC
            if self.verify_hmac(data):
                # Process the file
                success = process_function(data['data'])
                
                # Delete after processing (regardless of success)
                self.conn.delete_object(self.container, obj['name'])
            else:
                # Log security error and delete
                print(f"HMAC verification failed for {obj['name']}")
                self.conn.delete_object(self.container, obj['name'])
    
    def verify_hmac(self, payload):
        """Verify HMAC signature"""
        key = os.getenv('HMAC_KEY')
        
        signature = payload.pop('signature', None)
        calculated = hmac.new(
            key.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature == calculated
```

### 8.3 Backend Service Environment Configuration
```python
# Docker environment variables for each backend
# Dev backend:
ENVIRONMENT=dev
SWIFT_APP_CREDENTIAL_ID=xxxxx
SWIFT_APP_CREDENTIAL_SECRET=xxxxx
HMAC_KEY=shared-secret-key

# Test backend:
ENVIRONMENT=test
SWIFT_APP_CREDENTIAL_ID=xxxxx
SWIFT_APP_CREDENTIAL_SECRET=xxxxx
HMAC_KEY=shared-secret-key

# Prod backend:
ENVIRONMENT=prod
SWIFT_APP_CREDENTIAL_ID=xxxxx
SWIFT_APP_CREDENTIAL_SECRET=xxxxx
HMAC_KEY=shared-secret-key
```

## 9. Configuration Details

### 9.1 Confirmed Settings
- **Support email**: `patienten@curavani.com`
- **SMTP relay**: Already configured in communication-service
- **File age threshold**: 30 minutes for monitoring alerts
- **Environments**: Single PHP, Three containers, Three backends
- **Object Storage**: OpenStack Swift at Infomaniak ✅
- **Authentication**: Application Credentials ✅
- **PHP Environment**: 8.1.33, 640M memory ✅
- **MariaDB**: 10.11.13 (single database) ✅

### 9.2 Environment Variables Required

#### PHP Hosting (Infomaniak)
```bash
# Object Storage
SWIFT_APP_CREDENTIAL_ID=xxxxx
SWIFT_APP_CREDENTIAL_SECRET=xxxxx

# Database credentials (single database)
DB_USER=xxxxx
DB_PASS=xxxxx

# HMAC key (shared with all backends)
HMAC_KEY=xxxxx
```

#### Backend Services (Docker)
```bash
# Per environment
ENVIRONMENT=dev|test|prod
SWIFT_APP_CREDENTIAL_ID=xxxxx
SWIFT_APP_CREDENTIAL_SECRET=xxxxx
HMAC_KEY=xxxxx  # Same key as PHP
```

### 9.3 Important Notes for Implementation
1. **Python Swift Connection**: Must use explicit storage URL (`preauthurl`) due to endpoint discovery issue
2. **Container Names**: Case-sensitive (use exact names as created)
3. **Database Host Pattern**: `[dbname].myd.infomaniak.com`
4. **Performance**: Object Storage operations average 50ms (acceptable for use case)
5. **Environment Switching**: Manual config.php change on PHP hosting

## 10. Risk Assessment

### Acceptable Risks
- **Single provider dependency**: Simplified management worth the tradeoff
- **Manual environment switching**: Infrequent operation, reduces complexity
- **Single MariaDB**: Only transient data, no business data stored
- **10-30 second email delays**: Within acceptable range

### Risks to Monitor
- **Config file management**: Ensure proper version control and change documentation
- **Backend environment isolation**: Verify each backend only reads from its container
- **File accumulation**: Monitor for files > 30 minutes old
- **DNS propagation**: Keep old system for 48-72 hours during migration

## 11. Success Criteria

### Phase 0 Success ✅ FULLY COMPLETED
- ✅ All infrastructure components tested and verified

### Phase 1 Success (Infrastructure Setup)
- [ ] Three Object Storage containers created
- [ ] Single MariaDB database configured
- [ ] PHP hosting configured with environment variables
- [ ] Application Credentials working

### Phase 2 Success (Code Implementation)
- [ ] PHP writes to correct container based on config
- [ ] All emails sent through communication-service
- [ ] HMAC signatures on all JSON files
- [ ] Backend services read from correct containers

### Phase 3 Success (Testing)
- [ ] All three environments tested independently
- [ ] No cross-environment data leakage
- [ ] Performance within requirements
- [ ] Security measures validated

### Overall Migration Success
- [ ] Zero dependency on SendGrid
- [ ] Zero dependency on Google Cloud
- [ ] All infrastructure on Infomaniak (except local Docker backends)
- [ ] No SQL injection vulnerabilities
- [ ] Successfully handling 100+ registrations/hour
- [ ] 99.9% uptime after migration

## 12. Implementation Checklist

### Phase 1 - Infrastructure Setup (READY TO START)
- [ ] Create three containers at Infomaniak (dev, test, prod)
- [ ] Set up folder structure in each container
- [ ] Configure Application Credentials
- [ ] Set up single MariaDB database
- [ ] Configure PHP hosting environment variables
- [ ] Deploy PHP application to Infomaniak

### Phase 2 - PHP Updates
- [ ] Create config.php with environment switching
- [ ] Implement ObjectStorageClient class
- [ ] Modify send_verification.php to use Object Storage
- [ ] Modify verify_token.php to use Object Storage
- [ ] Create process_contact.php for contact forms
- [ ] Add HMAC signing to all JSON outputs
- [ ] Add prepared statements everywhere
- [ ] Implement rate limiting
- [ ] Add duplicate submission prevention

### Phase 2 - Backend Service Updates
- [ ] Update communication-service for each environment
- [ ] Update patient-service for each environment
- [ ] Add HMAC verification to all services
- [ ] Configure environment-specific containers
- [ ] Add file age monitoring
- [ ] Test storage URL override

### Phase 3 - Testing
- [ ] Test dev environment completely
- [ ] Test test environment completely
- [ ] Validate production environment
- [ ] Security audit
- [ ] Performance testing
- [ ] Create rollback procedures

### Phase 4 - Migration
- [ ] DNS preparation
- [ ] Data migration
- [ ] Go live
- [ ] Monitor
- [ ] Decommission old infrastructure

## 13. Monitoring & Alerting

### 13.1 Key Metrics
- **File Age**: Alert if any file > 30 minutes old
- **Processing Rate**: Files processed per minute per environment
- **Error Rate**: Failed processing attempts
- **Storage Usage**: Total files and size per container
- **Environment Isolation**: Verify no cross-reads

### 13.2 Monitoring Implementation
```python
# monitoring.py - Run separately for each environment
import os
from datetime import datetime, timezone

def check_environment_isolation():
    """Ensure backend only reads from its designated container"""
    environment = os.getenv('ENVIRONMENT')
    storage_client = ObjectStorageClient()
    
    assert storage_client.container == environment, \
        f"Environment mismatch: {storage_client.container} != {environment}"
    
    print(f"✓ Backend {environment} correctly reading from {storage_client.container}")

def monitor_file_age(storage_client, max_age_minutes=30):
    """Check for old files in current environment"""
    # Implementation as before, but only checks current container
    pass
```

## 14. Next Steps (IMMEDIATE ACTIONS)

1. **Create three containers** at Infomaniak (`dev`, `test`, `prod`)
2. **Generate Application Credentials** (single set for all)
3. **Set up single MariaDB** database
4. **Create config.php** on PHP hosting
5. **Start with dev environment** - Set config to 'dev' and test
6. **Implement ObjectStorageClient** in PHP
7. **Update one backend service** for dev environment testing
8. **Validate environment isolation**

## 15. Testing Methodology

### 15.1 Environment Isolation Test
1. Set PHP config to `environment: 'dev'`
2. Submit test registration
3. Verify file appears ONLY in `dev` container
4. Verify ONLY dev backend processes the file
5. Repeat for test and prod

### 15.2 End-to-End Test per Environment
1. **Dev**: Complete registration flow with dev backend
2. **Test**: Complete registration flow with test backend
3. **Prod**: Complete registration flow with prod backend

### 15.3 Security Validation
- Verify HMAC signatures
- Test rate limiting
- Attempt SQL injection
- Verify prepared statements

---

*Document Version: 5.0*  
*Date: September 2025*  
*Status: Simplified Architecture - Ready for Implementation*  
*Major Updates: Single PHP environment, single MariaDB, three Object Storage containers for backend testing*