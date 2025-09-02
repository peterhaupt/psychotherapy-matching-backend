# Curavani System Migration - Requirements & Implementation Plan

## Executive Summary

Migration of the Curavani patient registration system from multiple providers (domainfactory, GoDaddy, SendGrid, Google Cloud) to a single provider (Infomaniak) with enhanced security and simplified architecture using Object Storage with three environments for testing.

## 1. Core Migration Goals

1. **Get rid of SendGrid** - Move all email sending to communication-service with local SMTP relay
2. **Get rid of Google Cloud Storage** - Replace with Infomaniak Object Storage (Swift)
3. **Consolidate on Infomaniak** - Use their PHP hosting, MariaDB, and Object Storage
4. **Maintain decoupled architecture** - Continue using JSON files as interface
5. **Increase security level** - Implement security enhancements inline with migration
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
- **Security built-in**: HMAC signatures, prepared statements, rate limiting

### 5.2 Contact Form Enhancement
- Modify `patienten.html` contact form
- Create `contact_form.json` file via PHP in Object Storage
- Communication-service sends to support email
- **Support email address**: `patienten@curavani.com`
- **Security built-in**: Input validation, XSS prevention, HMAC signatures

### 5.3 Patient Registration
- Continue current flow but with Object Storage instead of GCS
- PHP (`verify_token.php`) → JSON file → Object Storage
- Patient-service imports from Object Storage
- **Security built-in**: Duplicate prevention, validation, HMAC signatures

### 5.4 File Processing
- Backend services poll their respective containers
- Download and process files immediately
- Delete files from Object Storage after processing (both success and failure)
- Files older than 30 minutes indicate backend processing problems
- Services handle their own error tracking
- **Security built-in**: HMAC verification on all files

### 5.5 Performance Requirements
- **Email delay**: 10-30 seconds acceptable
- **Polling frequency**: Every 10-30 seconds
- **Expected load**: 
  - < 100 registrations/hour
  - < 1,000 emails/hour
- **File monitoring**: Alert if files older than 30 minutes exist
- **Measured performance**: 62ms write, 42ms read (well within requirements) ✅

## 6. Security Implementation (INLINE WITH DEVELOPMENT)

### 6.1 Security Features by Component

#### PHP Files (Week 2 Implementation)
Each PHP file will be updated ONCE with all security features:

**send_verification.php**:
- Prepared statements for all database queries
- Rate limiting (enhance existing)
- HMAC signature on JSON output
- Input validation and sanitization

**verify_token.php**:
- Prepared statements for all queries
- Duplicate submission prevention (`form_submitted` column)
- HMAC signature on JSON output
- Comprehensive input validation
- XSS prevention

**process_contact.php** (new file):
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

### 6.2 HMAC Signature Structure
```json
{
  "signature": "hmac_sha256_hash",
  "timestamp": "2024-01-15T10:00:00Z",
  "type": "email_verification",
  "environment": "prod",
  "data": { ... actual payload ... }
}
```

### 6.3 Database Schema Updates
```sql
-- Add to verification_tokens table during Week 1 setup
ALTER TABLE verification_tokens 
ADD COLUMN form_submitted BOOLEAN DEFAULT FALSE,
ADD INDEX idx_email_hash (email_hash),
ADD INDEX idx_created_at (created_at);
```

## 7. Implementation Plan (REVISED)

### 7.1 Week 1: Infrastructure Setup
**Day 1-2: Object Storage Setup**
- Create three containers (`dev`, `test`, `prod`)
- Create folder structure in each container
- Generate and test Application Credentials

**Day 3: Database Setup**
- Set up single MariaDB database
- Create verification_tokens table WITH all columns including `form_submitted`
- Create verification_requests table for rate limiting
- Test database connection

**Day 4-5: PHP Hosting Setup**
- Deploy PHP application to Infomaniak
- Configure environment variables
- Create and test `config.php`
- Verify Swift connection works

### 7.2 Week 2: PHP Implementation WITH Security

**Day 1: ObjectStorageClient Implementation**
```php
class ObjectStorageClient {
    // Implement with:
    // - HMAC signature generation built-in
    // - Proper error handling
    // - Environment-based container selection
    // - Connection testing methods
}
```

**Day 2-3: send_verification.php Update**
- Replace SendGrid with Object Storage
- Implement all prepared statements
- Enhance rate limiting
- Add HMAC signatures
- Complete testing

**Day 4: verify_token.php Update**
- Replace GCS upload with Object Storage
- Add duplicate submission prevention
- Implement all prepared statements
- Add HMAC signatures
- Secure all validation functions
- Complete testing

**Day 5: process_contact.php Creation**
- Create new file for contact form handling
- Implement Object Storage upload
- Add comprehensive input validation
- Add HMAC signatures
- Complete testing

### 7.3 Week 3: Backend Updates WITH Security

**Day 1-2: Communication-service Update**
- Implement Swift client with storage URL override
- Add HMAC verification in polling logic
- Implement file age monitoring
- Add email verification processing
- Add contact form processing
- Environment-specific configuration
- Test in dev environment

**Day 3-4: Patient-service Update**
- Replace GCS with Swift client
- Add HMAC verification in import logic
- Implement file age monitoring
- Environment-specific configuration
- Test in dev environment

**Day 5: Integration Testing**
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

### 8.1 Secure PHP Swift Client
```php
use OpenStack\OpenStack;

class ObjectStorageClient {
    private $container;
    private $config;
    private $containerName;
    
    public function __construct() {
        $this->config = require 'config.php';
        $this->containerName = $this->config['environment'];
        
        try {
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
        } catch (Exception $e) {
            error_log("Failed to initialize Object Storage: " . $e->getMessage());
            throw new Exception("Storage initialization failed");
        }
    }
    
    public function uploadJson($folder, $filename, $data, $type = 'generic') {
        // Add metadata
        $payload = $this->addSecurityMetadata($data, $type);
        
        // Sign with HMAC
        $signedPayload = $this->addHmacSignature($payload);
        
        // Upload
        $jsonContent = json_encode($signedPayload);
        $objectName = $folder . '/' . $filename;
        
        try {
            $this->container->createObject([
                'name' => $objectName,
                'content' => $jsonContent
            ]);
            return true;
        } catch (Exception $e) {
            error_log("Failed to upload to Object Storage: " . $e->getMessage());
            return false;
        }
    }
    
    private function addSecurityMetadata($data, $type) {
        return [
            'type' => $type,
            'timestamp' => date('c'),
            'environment' => $this->config['environment'],
            'data' => $data
        ];
    }
    
    private function addHmacSignature($payload) {
        $key = $this->config['hmac_key'];
        $signature = hash_hmac('sha256', json_encode($payload), $key);
        $payload['signature'] = $signature;
        return $payload;
    }
}
```

### 8.2 Secure Database Connection
```php
class SecureDatabase {
    private static $instance = null;
    private $connection;
    
    private function __construct() {
        $config = require 'config.php';
        
        try {
            $dsn = "mysql:host={$config['database']['host']};dbname={$config['database']['name']};charset=utf8mb4";
            $this->connection = new PDO($dsn, 
                $config['database']['user'], 
                $config['database']['pass'],
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false
                ]
            );
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            throw new Exception("Database connection failed");
        }
    }
    
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    public function getConnection() {
        return $this->connection;
    }
}
```

### 8.3 Python Backend with Security
```python
import os
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from swiftclient import client
from keystoneauth1 import session
from keystoneauth1.identity import v3
import logging

logger = logging.getLogger(__name__)

class SecureObjectStorageClient:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'dev')
        self.container = self.environment
        self.hmac_key = os.getenv('HMAC_KEY')
        
        if not self.hmac_key:
            raise ValueError("HMAC_KEY environment variable is required")
        
        # Initialize Swift connection
        auth = v3.ApplicationCredential(
            auth_url='https://api.pub1.infomaniak.cloud/identity/v3',
            application_credential_id=os.getenv('SWIFT_APP_CREDENTIAL_ID'),
            application_credential_secret=os.getenv('SWIFT_APP_CREDENTIAL_SECRET')
        )
        
        sess = session.Session(auth=auth)
        token = sess.get_token()
        
        self.conn = client.Connection(
            preauthurl='***REMOVED***',
            preauthtoken=token
        )
        
        logger.info(f"Initialized storage client for environment: {self.environment}")
    
    def poll_and_process(self, folder, process_function, max_age_minutes=30):
        """Poll folder with security checks"""
        prefix = f"{folder}/"
        
        try:
            headers, objects = self.conn.get_container(
                self.container,
                prefix=prefix
            )
            
            for obj in objects:
                # Check file age
                last_modified = datetime.fromisoformat(
                    obj['last_modified'].replace('+00:00', 'Z').replace('Z', '+00:00')
                )
                age = datetime.now(timezone.utc) - last_modified
                
                if age > timedelta(minutes=max_age_minutes):
                    logger.warning(f"Old file detected: {obj['name']} ({age.total_seconds()/60:.1f} minutes)")
                
                # Download and process
                headers, content = self.conn.get_object(
                    self.container,
                    obj['name']
                )
                
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                
                data = json.loads(content)
                
                # Verify HMAC
                if not self.verify_hmac(data):
                    logger.error(f"HMAC verification failed for {obj['name']}")
                    self.conn.delete_object(self.container, obj['name'])
                    continue
                
                # Verify environment matches
                if data.get('environment') != self.environment:
                    logger.error(f"Environment mismatch in {obj['name']}")
                    self.conn.delete_object(self.container, obj['name'])
                    continue
                
                # Process the file
                try:
                    success = process_function(data['data'])
                    logger.info(f"Processed {obj['name']}: {'success' if success else 'failed'}")
                except Exception as e:
                    logger.error(f"Error processing {obj['name']}: {str(e)}")
                
                # Always delete after processing
                self.conn.delete_object(self.container, obj['name'])
                
        except Exception as e:
            logger.error(f"Error polling {folder}: {str(e)}")
    
    def verify_hmac(self, payload):
        """Verify HMAC signature with timing attack protection"""
        if 'signature' not in payload:
            return False
        
        provided_signature = payload.pop('signature')
        calculated_signature = hmac.new(
            self.hmac_key.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Use compare_digest to prevent timing attacks
        return hmac.compare_digest(provided_signature, calculated_signature)
```

## 9. Testing Strategy

### 9.1 Security Testing Checklist
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
**Dev Environment**
- [ ] Email verification flow
- [ ] Patient registration flow
- [ ] Contact form submission
- [ ] File processing verification
- [ ] Error handling

**Test Environment**
- [ ] Complete end-to-end flow
- [ ] Load testing (100 registrations)
- [ ] Concurrent user testing
- [ ] Database transaction handling

**Production Environment**
- [ ] Smoke tests only
- [ ] Monitoring verification
- [ ] Rollback procedure test

### 9.3 Performance Benchmarks
- Object Storage write: < 100ms
- Object Storage read: < 100ms
- Email processing: < 30 seconds
- Registration processing: < 60 seconds
- Database queries: < 10ms

## 10. Monitoring & Alerting

### 10.1 Key Metrics
- **File Age**: Alert if any file > 30 minutes old
- **Processing Rate**: Files processed per minute per environment
- **Error Rate**: Failed processing attempts
- **Storage Usage**: Total files and size per container
- **Security Events**: Failed HMAC verifications, rate limit hits

### 10.2 Monitoring Implementation
```python
# monitoring.py - Separate instance per environment
import os
from datetime import datetime, timezone, timedelta

class EnvironmentMonitor:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT')
        self.storage_client = SecureObjectStorageClient()
        
    def check_isolation(self):
        """Verify environment isolation"""
        assert self.storage_client.container == self.environment
        return True
    
    def check_old_files(self, max_age_minutes=30):
        """Check for stuck files"""
        old_files = []
        for folder in ['verifications', 'contacts', 'registrations']:
            # Implementation
            pass
        return old_files
    
    def check_security_events(self):
        """Monitor security-related events"""
        # Check logs for HMAC failures
        # Check rate limiting hits
        # Check SQL injection attempts
        pass
```

## 11. Rollback Plan

### 11.1 Rollback Triggers
- Critical security breach detected
- Data loss or corruption
- Performance degradation > 50%
- Error rate > 10%

### 11.2 Rollback Procedure
1. **Immediate**: Switch config.php back to previous working environment
2. **Within 5 minutes**: Restore DNS if changed
3. **Within 15 minutes**: Restore database from backup
4. **Within 30 minutes**: Full service restoration

### 11.3 Rollback Testing
- Test rollback procedure in dev environment
- Document exact steps and timings
- Verify data integrity after rollback

## 12. Success Criteria

### Week 1 Success (Infrastructure)
- [ ] Three Object Storage containers accessible
- [ ] MariaDB database operational
- [ ] PHP hosting configured
- [ ] Swift connection tested

### Week 2 Success (PHP)
- [ ] All PHP files updated with security
- [ ] Object Storage uploads working
- [ ] HMAC signatures validated
- [ ] Rate limiting functional
- [ ] No SQL injection vulnerabilities

### Week 3 Success (Backend)
- [ ] Backend services updated
- [ ] HMAC verification working
- [ ] Environment isolation confirmed
- [ ] File processing functional

### Week 4 Success (Testing)
- [ ] All environments tested
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Documentation complete

### Overall Migration Success
- [ ] Zero dependency on SendGrid
- [ ] Zero dependency on Google Cloud
- [ ] All infrastructure on Infomaniak
- [ ] All security measures implemented
- [ ] 99.9% uptime maintained

## 13. Documentation Requirements

### 13.1 Technical Documentation
- API documentation for all endpoints
- Database schema documentation
- Environment configuration guide
- Security measures documentation

### 13.2 Operational Documentation
- Deployment procedures
- Environment switching guide
- Monitoring setup
- Incident response procedures

### 13.3 User Documentation
- Migration announcement
- Service status page
- Support contact information

## 14. Risk Mitigation

### 14.1 High-Risk Areas
**Data Loss**
- Mitigation: Backup before processing, soft delete initially
- Recovery: Restore from Object Storage archive

**Security Breach**
- Mitigation: HMAC signatures, environment isolation
- Recovery: Rotate keys, audit logs

**Performance Issues**
- Mitigation: Load testing, gradual rollout
- Recovery: Scale resources, optimize code

### 14.2 Communication Plan
- Weekly status updates during migration
- Immediate notification for issues
- Post-migration report

## 15. Next Steps (IMMEDIATE ACTIONS)

### This Week
1. **Create three containers** at Infomaniak
2. **Generate Application Credentials**
3. **Set up MariaDB** with complete schema
4. **Prepare development environment**

### Next Week
1. **Start PHP implementation** with security
2. **Test each component** thoroughly
3. **Document findings**

### Following Weeks
1. **Complete backend updates**
2. **Full testing cycle**
3. **Production migration**

---

*Document Version: 6.0*  
*Date: September 2025*  
*Status: Ready for Implementation with Inline Security*  
*Major Updates: Security implementation integrated into development phases, not separate*