# Curavani System Migration - Requirements & Implementation Plan

## Executive Summary

Migration of the Curavani patient registration system from multiple providers (domainfactory, GoDaddy, SendGrid, Google Cloud) to a single provider (Infomaniak) with enhanced security and maintained decoupled architecture.

## 1. Core Migration Goals

1. **Get rid of SendGrid** - Move all email sending to communication-service with local SMTP relay
2. **Get rid of Google Cloud Storage** - Replace with Infomaniak SFTP
3. **Consolidate on Infomaniak** - Use their PHP hosting, MariaDB, and SFTP
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
User Request → PHP → JSON file on SFTP → Communication-service → Local SMTP relay → Send
```

### 3.2 Data Storage
- **All JSON files**: Infomaniak SFTP
- **Database**: MariaDB at Infomaniak
- **File structure** (simplified):
  ```
  /curavani/
    /dev/
      /verifications/      # Email verification requests
      /contacts/          # Contact form submissions  
      /registrations/     # Patient registrations
    /test/
      /verifications/      
      /contacts/          
      /registrations/     
    /prod/
      /verifications/      
      /contacts/          
      /registrations/
  ```

### 3.3 Single Provider
- **Everything at Infomaniak**: PHP hosting, MariaDB, SFTP, Domain (after migration)
- **Local infrastructure**: Communication-service with local SMTP relay (already configured)

## 4. Specific Requirements

### 4.1 Email Verification Migration
- Move email sending from `send_verification.php` to communication-service
- PHP creates `verification_request.json` file in SFTP
- Communication-service polls and sends verification email
- Keep token storage in MariaDB for rate limiting

### 4.2 Contact Form Enhancement
- Modify `patienten.html` contact form
- Create `contact_form.json` file via PHP
- Communication-service sends to support email
- **Support email address**: `patienten@curavani.com`

### 4.3 Patient Registration
- Continue current flow but with SFTP instead of GCS
- PHP (`verify_token.php`) → JSON file → SFTP
- Patient-service imports from SFTP

### 4.4 File Processing
- Backend services poll their respective folders
- Download and process files immediately
- Delete files from SFTP after processing (both success and failure)
- Files older than 30 minutes indicate backend processing problems
- No complex folder structure needed - services handle their own error tracking

### 4.5 Performance Requirements
- **Email delay**: 10-30 seconds acceptable
- **Polling frequency**: Every 10-30 seconds
- **Expected load**: 
  - < 100 registrations/hour
  - < 1,000 emails/hour
- **File monitoring**: Alert if files older than 30 minutes exist

## 5. Security Improvements (Priority 1 - Do After Phase 0)

### 5.1 HMAC Signatures for JSON Files

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

### 5.2 Strict Input Validation

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

### 5.3 Prepared Statements Everywhere

**Problem**: SQL injection vulnerabilities

**Required changes**:
- `send_verification.php`: Token queries, rate limit checks
- `verify_token.php`: Token validation, updates
- Services: Ensure all SQLAlchemy queries are parameterized

**Pattern to follow**:
- Never concatenate user input into SQL strings
- Use parameterized queries exclusively
- Validate data types before queries

### 5.4 Global Rate Limiting

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

### 5.5 Duplicate Form Submission Prevention (Simple Solution)

**Problem**: Patients can submit registration form multiple times with same token

**Root Cause**: 
- Token is only validated when showing form (GET request)
- Token is NOT re-validated when submitting form (POST request)
- Same URL can be bookmarked and form resubmitted days later

**Solution**: Add separate tracking for form submission
```sql
ALTER TABLE verification_tokens 
ADD COLUMN form_submitted BOOLEAN DEFAULT FALSE;
```

**Implementation**:
1. **Current `used` column**: Tracks email verification only
2. **New `form_submitted` column**: Tracks registration completion
3. **On POST request**: Check `form_submitted = FALSE` before processing
4. **After successful GCS/SFTP upload**: Set `form_submitted = TRUE`

**Benefits**:
- Prevents duplicate registrations with same token
- Allows retries if upload fails
- Clean separation of email verification vs. form submission
- Minimal code changes required

## 6. Migration Plan

### 6.1 Phase 0: Infomaniak Capability Testing (NEW - Do First)
1. **Verify PHP hosting capabilities**
   - PHP version compatibility (8.0+)
   - Required extensions available
   - Memory and execution time limits adequate
2. **Test MariaDB features**
   - Version compatibility
   - Connection pooling support
   - Backup/restore procedures
3. **Validate SFTP access**
   - Multi-user access with different permissions
   - API access from backend services
   - File size and count limits
   - Performance with expected load
4. **Check monitoring capabilities**
   - Log access
   - Alert configuration options
   - Performance metrics availability
5. **Document any limitations or required workarounds**

### 6.2 Phase 1: Infomaniak Setup
1. Set up three environments (dev/test/prod)
2. Install PHP application in each environment
3. Configure MariaDB instances
4. Set up SFTP structure for all environments
5. Configure environment-specific credentials

### 6.3 Phase 2: Code Changes
1. Add JSON file import functionality to communication-service
2. Implement HMAC signatures with environment awareness
3. Add prepared statements everywhere
4. Implement validation layer
5. Add rate limiting
6. Modify PHP to write to SFTP instead of GCS/SendGrid
7. Modify patient-service to poll SFTP instead of GCS
8. Add monitoring for files older than 30 minutes

### 6.4 Phase 3: Testing
1. Test all workflows in dev environment
2. Security testing
3. Performance testing
4. Test environment validation
5. Backup/recovery testing

### 6.5 Phase 4: Production Migration
1. DNS preparation
2. Data migration
3. Switch DNS to Infomaniak
4. Monitor for 48-72 hours
5. Keep domainfactory as backup
6. Decommission old infrastructure

## 7. Technical Decisions Made

1. **Email service**: Local SMTP relay via communication-service (already configured)
2. **Database**: MariaDB (already in use)
3. **File structure**: Simplified three-folder structure per environment
4. **Monitoring**: File age monitoring (> 30 minutes = problem)
5. **Performance**: 10-30 second delays acceptable
6. **Migration strategy**: Full setup on Infomaniak, then DNS switch
7. **File handling**: Backend services delete files after processing

## 8. Configuration Details

### 8.1 Confirmed Settings
- **Support email**: `patienten@curavani.com`
- **SMTP relay**: Already configured in communication-service
- **File age threshold**: 30 minutes for monitoring alerts
- **Environments**: dev, test, prod

### 8.2 Open Questions
- [ ] Infomaniak SFTP credentials and limits per environment?
- [ ] Specific rate limits for each operation?
- [ ] How to manage/rotate HMAC secret keys?
- [ ] IP whitelist for SFTP access?
- [ ] Alerting thresholds and recipients?
- [ ] Log retention policy?

## 9. Risk Assessment

### Acceptable Risks
- **Single provider dependency**: Similar to current domainfactory situation
- **SFTP performance**: Adequate for expected load (< 1000 registrations/hour)
- **10-30 second delays**: Acceptable for email delivery
- **Simple file structure**: Backend services handle their own error tracking

### Risks to Monitor
- **Migration errors**: Require thorough testing in all environments
- **SFTP credential security**: Use strong passwords, IP restrictions
- **File accumulation**: Monitor for files > 30 minutes old
- **DNS propagation**: Keep old system for 48-72 hours

## 10. Success Criteria

### Phase 0 Success
- [ ] All required PHP features available at Infomaniak
- [ ] MariaDB meets all requirements
- [ ] SFTP performance acceptable for expected load
- [ ] Monitoring capabilities sufficient

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

## 11. Implementation Checklist

### Phase 0 - Capability Testing
- [ ] Create Infomaniak test account
- [ ] Test PHP hosting features
- [ ] Test MariaDB capabilities
- [ ] Test SFTP access and performance
- [ ] Document findings and limitations
- [ ] Go/No-Go decision

### Security Implementation
- [ ] Implement HMAC signatures
- [ ] Add prepared statements to all PHP files
- [ ] Implement comprehensive validation
- [ ] Add global rate limiting
- [ ] Add form_submitted column to verification_tokens table
- [ ] Implement duplicate submission check in verify_token.php
- [ ] Security testing and verification

### Service Updates
- [ ] Update communication-service to poll SFTP for verifications
- [ ] Update communication-service to poll SFTP for contacts
- [ ] Update patient-service to poll SFTP instead of GCS
- [ ] Add file age monitoring to all services
- [ ] Environment-specific configuration

### PHP Updates
- [ ] Modify send_verification.php to write to SFTP
- [ ] Modify verify_token.php to write to SFTP
- [ ] Modify process_contact.php to write to SFTP
- [ ] Add HMAC signing to all JSON outputs
- [ ] Environment detection and routing

### Testing & Migration
- [ ] Complete dev environment testing
- [ ] Complete test environment validation
- [ ] Production migration planning
- [ ] DNS migration
- [ ] Post-migration monitoring

## 12. Next Steps

1. **Phase 0 execution** - Test all Infomaniak capabilities
2. **Review Phase 0 results** and make go/no-go decision
3. **Security implementation** (HMAC, prepared statements, validation, rate limiting)
4. **Add JSON file import to communication-service** for verification/contact emails
5. **Set up three-environment structure** at Infomaniak
6. **Develop and test changes** in dev environment
7. **Validate in test environment**
8. **Plan production migration window**

---

*Document Version: 2.0*  
*Date: January 2025*  
*Status: Ready for Phase 0 - Infomaniak Capability Testing*