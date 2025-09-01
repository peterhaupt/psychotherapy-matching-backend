# Curavani System Migration - Requirements & Implementation Plan

## Executive Summary

Migration of the Curavani patient registration system from multiple providers (domainfactory, GoDaddy, SendGrid, Google Cloud) to a single provider (Infomaniak) with enhanced security and maintained decoupled architecture using Object Storage.

## 1. Core Migration Goals

1. **Get rid of SendGrid** - Move all email sending to communication-service with local SMTP relay
2. **Get rid of Google Cloud Storage** - Replace with Infomaniak Object Storage (Swift)
3. **Consolidate on Infomaniak** - Use their PHP hosting, MariaDB, and Object Storage
4. **Maintain decoupled architecture** - Continue using JSON files as interface
5. **Increase security level** - Address critical vulnerabilities
6. **Support three environments** - Dev, Test, and Production

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

## 3. Target Architecture

### 3.1 Unified Email Flow
All emails go through communication-service:
```
User Request → PHP → JSON file in Object Storage → Communication-service → Local SMTP relay → Send
```

### 3.2 Data Storage
- **All JSON files**: Infomaniak Object Storage (Swift)
- **Database**: MariaDB at Infomaniak
- **Object Storage Structure**:
  ```
  Buckets (Containers):
    dev/                    # Development environment bucket
      verifications/        # Email verification requests
      contacts/            # Contact form submissions  
      registrations/       # Patient registrations
    
    test/                   # Test environment bucket
      verifications/      
      contacts/          
      registrations/     
    
    prod/                   # Production environment bucket
      verifications/      
      contacts/          
      registrations/
  ```

### 3.3 Environment Configuration
- **PHP Scripts**: Single codebase for all environments
- **Environment Selection**: Via configuration file (`config.php`)
- **Backend Services**: Each connects only to its corresponding bucket
  - Dev backend → `dev` bucket
  - Test backend → `test` bucket
  - Prod backend → `prod` bucket

### 3.4 Single Provider
- **Everything at Infomaniak**: PHP hosting, MariaDB, Object Storage, Domain (after migration)
- **Local infrastructure**: Communication-service with local SMTP relay (already configured)

## 4. Technical Stack

### 4.1 Object Storage Details
- **Provider**: Infomaniak OpenStack Swift
- **Access Method**: Native Swift API (not S3-compatible)
- **PHP Library**: `php-opencloud/openstack`
- **Python Library**: `python-swiftclient` or `python-openstacksdk`
- **Authentication**: Application Credentials (ID + Secret)
- **Endpoint**: `https://api.pub1.infomaniak.cloud/identity/v3`
- **Region**: `dc4-a`

### 4.2 Configuration File Structure
```php
// config.php
<?php
return [
    'environment' => 'dev',  // 'dev', 'test', or 'prod'
    
    'object_storage' => [
        'authUrl' => 'https://api.pub1.infomaniak.cloud/identity/v3',
        'region' => 'dc4-a',
        'credentials' => [
            'id' => getenv('SWIFT_APP_CREDENTIAL_ID'),
            'secret' => getenv('SWIFT_APP_CREDENTIAL_SECRET')
        ]
    ],
    
    'buckets' => [
        'dev' => 'dev',
        'test' => 'test',
        'prod' => 'prod'
    ],
    
    'database' => [
        'dev' => [
            'host' => 'dev.db.infomaniak.com',
            'name' => 'curavani_dev',
            'user' => getenv('DB_USER_DEV'),
            'pass' => getenv('DB_PASS_DEV')
        ],
        'test' => [
            'host' => 'test.db.infomaniak.com',
            'name' => 'curavani_test',
            'user' => getenv('DB_USER_TEST'),
            'pass' => getenv('DB_PASS_TEST')
        ],
        'prod' => [
            'host' => 'prod.db.infomaniak.com',
            'name' => 'curavani_prod',
            'user' => getenv('DB_USER_PROD'),
            'pass' => getenv('DB_PASS_PROD')
        ]
    ],
    
    'hmac_keys' => [
        'dev' => getenv('HMAC_KEY_DEV'),
        'test' => getenv('HMAC_KEY_TEST'),
        'prod' => getenv('HMAC_KEY_PROD')
    ]
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
- Backend services poll their respective buckets
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
- Shared secret key between PHP and services (per environment)
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

**Pattern to follow**:
- Never concatenate user input into SQL strings
- Use parameterized queries exclusively
- Validate data types before queries

### 6.4 Global Rate Limiting

**Problem**: Only per-email rate limiting exists

**Solution layers**:
1. **Per IP**: Limit requests from single IP
2. **Global**: System-wide limits (100 verifications/minute)
3. **Per action**: Different limits for different operations
4. **Progressive penalties**: Increasing block durations

**Implementation approach**:
- Database table with atomic counters
- Check before creating JSON files
- Monitor all endpoints

### 6.5 Duplicate Form Submission Prevention (Simple Solution)

**Problem**: Patients can submit registration form multiple times with same token

**Solution**: Add separate tracking for form submission
```sql
ALTER TABLE verification_tokens 
ADD COLUMN form_submitted BOOLEAN DEFAULT FALSE;
```

**Implementation**:
1. **Current `used` column**: Tracks email verification only
2. **New `form_submitted` column**: Tracks registration completion
3. **On POST request**: Check `form_submitted = FALSE` before processing
4. **After successful Object Storage upload**: Set `form_submitted = TRUE`

## 7. Migration Plan

### 7.1 Phase 0: Infomaniak Capability Testing ✅ COMPLETED
- ✅ PHP hosting capabilities verified
- ✅ MariaDB features tested
- ✅ Object Storage access validated
- ✅ Swift API authentication working
- ✅ Performance acceptable

### 7.2 Phase 1: Infomaniak Setup
1. Create three buckets/containers (`dev`, `test`, `prod`)
2. Set up folder structure within each bucket
3. Configure Application Credentials for each environment
4. Install PHP application at Infomaniak
5. Configure MariaDB instances for each environment
6. Set up environment-specific credentials

### 7.3 Phase 2: Code Changes

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
1. **Communication-service**:
   - Add Swift client for Object Storage polling
   - Poll `/verifications` folder for email verification requests
   - Poll `/contacts` folder for contact form submissions
   - Delete processed files

2. **Patient-service**:
   - Replace GCS client with Swift client
   - Poll `/registrations` folder
   - Delete processed files

3. **All services**:
   - Add HMAC signature verification
   - Add file age monitoring
   - Environment-specific configuration

### 7.4 Phase 3: Testing
1. **Dev Environment**:
   - Test all workflows
   - Verify HMAC signatures
   - Test rate limiting
   - Performance testing

2. **Test Environment**:
   - Full integration testing
   - Security testing
   - Load testing
   - Backup/recovery testing

3. **Pre-Production Validation**:
   - DNS preparation
   - Final security audit
   - Performance benchmarking

### 7.5 Phase 4: Production Migration
1. DNS preparation (reduce TTL 48 hours before)
2. Data migration from domainfactory to Infomaniak
3. Final sync of databases
4. Switch DNS to Infomaniak
5. Monitor for 48-72 hours
6. Keep domainfactory as backup for 1 week
7. Decommission old infrastructure

## 8. Object Storage Implementation Details

### 8.1 PHP Swift Client Usage
```php
use OpenStack\OpenStack;

class ObjectStorageClient {
    private $container;
    private $config;
    
    public function __construct($environment) {
        $this->config = require 'config.php';
        
        $openstack = new OpenStack([
            'authUrl' => $this->config['object_storage']['authUrl'],
            'region' => $this->config['object_storage']['region'],
            'application_credential' => [
                'id' => $this->config['object_storage']['credentials']['id'],
                'secret' => $this->config['object_storage']['credentials']['secret']
            ]
        ]);
        
        $bucketName = $this->config['buckets'][$environment];
        $this->container = $openstack->objectStoreV1()->getContainer($bucketName);
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
        $key = $this->config['hmac_keys'][$environment];
        
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

### 8.2 Python Swift Client Usage
```python
from swiftclient import client
import json
import hmac
import hashlib
from datetime import datetime
import os

class ObjectStorageClient:
    def __init__(self, environment):
        self.environment = environment
        self.container = environment  # 'dev', 'test', or 'prod'
        
        self.conn = client.Connection(
            authurl='https://api.pub1.infomaniak.cloud/identity/v3',
            auth_version='3',
            os_options={
                'application_credential_id': os.getenv('SWIFT_APP_CREDENTIAL_ID'),
                'application_credential_secret': os.getenv('SWIFT_APP_CREDENTIAL_SECRET'),
                'region_name': 'dc4-a'
            }
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
        key = os.getenv(f'HMAC_KEY_{self.environment.upper()}')
        
        signature = payload.pop('signature', None)
        calculated = hmac.new(
            key.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature == calculated
```

## 9. Configuration Details

### 9.1 Confirmed Settings
- **Support email**: `patienten@curavani.com`
- **SMTP relay**: Already configured in communication-service
- **File age threshold**: 30 minutes for monitoring alerts
- **Environments**: dev, test, prod
- **Object Storage**: OpenStack Swift at Infomaniak
- **Authentication**: Application Credentials

### 9.2 Environment Variables Required
```bash
# Object Storage
SWIFT_APP_CREDENTIAL_ID=xxxxx
SWIFT_APP_CREDENTIAL_SECRET=xxxxx

# Database credentials per environment
DB_USER_DEV=xxxxx
DB_PASS_DEV=xxxxx
DB_USER_TEST=xxxxx
DB_PASS_TEST=xxxxx
DB_USER_PROD=xxxxx
DB_PASS_PROD=xxxxx

# HMAC keys per environment
HMAC_KEY_DEV=xxxxx
HMAC_KEY_TEST=xxxxx
HMAC_KEY_PROD=xxxxx
```

## 10. Risk Assessment

### Acceptable Risks
- **Single provider dependency**: Similar to current domainfactory situation
- **Object Storage performance**: Adequate for expected load (< 1000 files/hour)
- **10-30 second delays**: Acceptable for email delivery
- **Simple folder structure**: Backend services handle their own error tracking

### Risks to Monitor
- **Migration errors**: Require thorough testing in all environments
- **Application Credential security**: Rotate regularly, use environment variables
- **File accumulation**: Monitor for files > 30 minutes old
- **DNS propagation**: Keep old system for 48-72 hours

## 11. Success Criteria

### Phase 0 Success ✅ COMPLETED
- ✅ All required PHP features available at Infomaniak
- ✅ MariaDB meets all requirements
- ✅ Object Storage performance acceptable for expected load
- ✅ Swift API authentication working

### Overall Migration Success
- [ ] All emails sent through communication-service
- [ ] Zero dependency on SendGrid
- [ ] Zero dependency on Google Cloud
- [ ] All infrastructure on Infomaniak (except local services)
- [ ] No SQL injection vulnerabilities
- [ ] HMAC signatures on all JSON files
- [ ] Global rate limiting in place
- [ ] No duplicate form submissions with same token
- [ ] Successfully handling 100+ registrations/hour
- [ ] 99.9% uptime after migration
- [ ] File monitoring alerts for > 30 minute old files
- [ ] All three environments operational

## 12. Implementation Checklist

### Phase 0 - Capability Testing ✅ COMPLETED
- ✅ Create Infomaniak test account
- ✅ Test PHP hosting features
- ✅ Test MariaDB capabilities
- ✅ Test Object Storage access and performance
- ✅ Document findings and limitations
- ✅ Go/No-Go decision: **GO**

### Phase 1 - Infrastructure Setup
- [ ] Create three buckets/containers (dev, test, prod)
- [ ] Set up folder structure in each bucket
- [ ] Configure Application Credentials
- [ ] Set up MariaDB instances (dev, test, prod)
- [ ] Configure PHP hosting at Infomaniak
- [ ] Set up environment variables

### Security Implementation
- [ ] Implement HMAC signatures
- [ ] Add prepared statements to all PHP files
- [ ] Implement comprehensive validation
- [ ] Add global rate limiting
- [ ] Add form_submitted column to verification_tokens table
- [ ] Implement duplicate submission check in verify_token.php
- [ ] Security testing and verification

### PHP Updates
- [ ] Create config.php for environment management
- [ ] Implement ObjectStorageClient class
- [ ] Modify send_verification.php to use Object Storage
- [ ] Modify verify_token.php to use Object Storage
- [ ] Create process_contact.php for contact forms
- [ ] Add HMAC signing to all JSON outputs
- [ ] Add prepared statements everywhere
- [ ] Implement rate limiting

### Service Updates
- [ ] Update communication-service to poll Object Storage
- [ ] Update patient-service to use Object Storage instead of GCS
- [ ] Add HMAC verification to all services
- [ ] Add file age monitoring to all services
- [ ] Environment-specific configuration for each service

### Testing & Migration
- [ ] Complete dev environment testing
- [ ] Complete test environment validation
- [ ] Security audit
- [ ] Performance testing
- [ ] Production migration planning
- [ ] DNS migration
- [ ] Post-migration monitoring

## 13. Code Examples

### 13.1 Email Verification Request (PHP)
```php
// send_verification.php
require_once 'config.php';
require_once 'ObjectStorageClient.php';

$config = require 'config.php';
$environment = $config['environment'];

// After generating verification token
$verificationData = [
    'type' => 'email_verification',
    'email' => $email,
    'token' => $token,
    'verification_url' => "https://curavani.de/verify?token=$token",
    'created_at' => date('c')
];

$storage = new ObjectStorageClient($environment);
$filename = 'verification_' . time() . '_' . uniqid() . '.json';
$storage->uploadJson('verifications', $filename, $verificationData);
```

### 13.2 Communication Service Polling (Python)
```python
# communication_service.py
import time
from object_storage_client import ObjectStorageClient

def process_verification(data):
    """Send verification email"""
    send_email(
        to=data['email'],
        subject='Email Verification',
        template='verification',
        context={
            'verification_url': data['verification_url']
        }
    )
    return True

def main():
    environment = os.getenv('ENVIRONMENT', 'dev')
    storage = ObjectStorageClient(environment)
    
    while True:
        # Poll for verification requests
        storage.poll_and_process('verifications', process_verification)
        
        # Poll for contact form submissions
        storage.poll_and_process('contacts', process_contact)
        
        time.sleep(10)  # Poll every 10 seconds
```

## 14. Monitoring & Alerting

### 14.1 Key Metrics
- **File Age**: Alert if any file > 30 minutes old
- **Processing Rate**: Files processed per minute
- **Error Rate**: Failed processing attempts
- **Storage Usage**: Total files and size per bucket
- **API Response Times**: Swift API latency

### 14.2 Monitoring Implementation
```python
# monitoring.py
def check_old_files(storage_client, max_age_minutes=30):
    """Check for files older than threshold"""
    old_files = []
    
    for folder in ['verifications', 'contacts', 'registrations']:
        headers, objects = storage_client.conn.get_container(
            storage_client.container,
            prefix=f"{folder}/"
        )
        
        for obj in objects:
            age = datetime.now() - datetime.fromisoformat(obj['last_modified'])
            if age.total_seconds() > max_age_minutes * 60:
                old_files.append({
                    'name': obj['name'],
                    'age_minutes': age.total_seconds() / 60
                })
    
    if old_files:
        send_alert(f"Found {len(old_files)} files older than {max_age_minutes} minutes")
    
    return old_files
```

## 15. Next Steps

1. **Set up Object Storage buckets** at Infomaniak (dev, test, prod)
2. **Create Application Credentials** for each environment
3. **Implement ObjectStorageClient** classes in PHP and Python
4. **Security implementation** (HMAC, prepared statements, validation, rate limiting)
5. **Update communication-service** to poll Object Storage
6. **Set up monitoring** for file age and processing
7. **Test in dev environment** thoroughly
8. **Plan production migration window**

## 16. Cost Analysis

### 16.1 Object Storage Costs
- **Storage**: 0.000013 € / GB / hour
- **Expected usage**: ~2.4 GB/day = ~72 GB/month
- **Monthly cost**: ~0.68 € (negligible)
- **Outgoing traffic**: Free (first 10TB/month)

### 16.2 Total Infrastructure at Infomaniak
- PHP hosting
- MariaDB (3 instances)
- Object Storage
- Domain hosting
- **Estimated total**: Significantly less than current multi-provider setup

---

*Document Version: 3.0*  
*Date: January 2025*  
*Status: Ready for Phase 1 - Infrastructure Setup*  
*Major Change: Migrated from SFTP to Object Storage (Swift)*