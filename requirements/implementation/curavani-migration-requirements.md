# Curavani System Migration - Requirements & Implementation Plan

## Executive Summary

Migration of the Curavani patient registration system from multiple providers (domainfactory, GoDaddy, SendGrid, Google Cloud) to a single provider (Infomaniak) with enhanced security and maintained decoupled architecture.

## 1. Core Migration Goals

1. **Get rid of SendGrid** - Move all email sending to communication-service with local SMTP relay
2. **Get rid of Google Cloud Storage** - Replace with Infomaniak SFTP
3. **Consolidate on Infomaniak** - Use their PHP hosting, MariaDB, and SFTP
4. **Maintain decoupled architecture** - Continue using JSON files as interface
5. **Increase security level** - Address critical vulnerabilities

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
- **File structure**:
  ```
  /curavani/
    /pending/
      /verifications/      # Email verification requests
      /contacts/          # Contact form submissions  
      /registrations/     # Patient registrations
    /processing/          # Files currently being processed
    /completed/          # Successfully processed files (deleted immediately)
    /failed/            # Failed processing attempts (kept 24-48 hours max)
  ```

### 3.3 Single Provider
- **Everything at Infomaniak**: PHP hosting, MariaDB, SFTP, Domain (after migration)
- **Local infrastructure**: Communication-service with local SMTP relay

## 4. Specific Requirements

### 4.1 Email Verification Migration
- Move email sending from `send_verification.php` to communication-service
- PHP creates `verification_request.json` file
- Communication-service polls and sends verification email
- Keep token storage in MariaDB for rate limiting

### 4.2 Contact Form Enhancement
- Modify `patienten.html` contact form
- Create `contact_form.json` file via PHP
- Communication-service sends to predefined support email
- Support email address: **[TO BE DEFINED]**

### 4.3 Patient Registration
- Continue current flow but with SFTP instead of GCS
- PHP (`verify_token.php`) → JSON file → SFTP
- Patient-service imports from SFTP

### 4.4 Performance Requirements
- **Email delay**: 10-30 seconds acceptable
- **Polling frequency**: Every 10-30 seconds
- **Expected load**: 
  - < 100 registrations/hour
  - < 1,000 emails/hour
- **File cleanup**: Immediate deletion after successful processing, failed files kept 24-48 hours maximum

## 5. Security Improvements (Priority 1 - Do First)

### 5.1 HMAC Signatures for JSON Files

**Problem**: No authentication between PHP and services

**Solution**: Sign all JSON files with HMAC
```json
{
  "signature": "hmac_sha256_hash",
  "timestamp": "2024-01-15T10:00:00Z",
  "type": "email_verification",
  "data": { ... actual payload ... }
}
```

**Implementation**:
- Shared secret key between PHP and services
- Store in environment variables
- Include timestamp to prevent replay attacks
- Include type to prevent cross-purpose use

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

## 6. Migration Plan

### 6.1 Phase 1: Infomaniak Setup
1. Set up Infomaniak hosting environment
2. Install PHP application
3. Configure MariaDB
4. Set up SFTP structure
5. Configure local SMTP relay for communication-service

### 6.2 Phase 2: Code Changes
1. Add JSON file import functionality to communication-service
2. Implement HMAC signatures
3. Add prepared statements
4. Implement validation layer
5. Add rate limiting
6. Modify PHP to write to SFTP instead of GCS/SendGrid
7. Modify patient-service to poll SFTP instead of GCS

### 6.3 Phase 3: Testing
1. Test all workflows on Infomaniak
2. Security testing
3. Performance testing
4. Backup/recovery testing

### 6.4 Phase 4: Migration
1. DNS preparation
2. Data migration
3. Switch DNS to Infomaniak
4. Monitor for 48-72 hours
5. Keep domainfactory as backup
6. Decommission old infrastructure

## 7. Technical Decisions Made

1. **Email service**: Local SMTP relay via communication-service (not Infomaniak SMTP)
2. **Database**: MariaDB (already in use)
3. **Monitoring**: File age monitoring in SFTP folders
4. **Performance**: 10-30 second delays acceptable
5. **Migration strategy**: Full setup on Infomaniak, then DNS switch
6. **File retention**: Immediate deletion after successful processing

## 8. Open Questions

### 8.1 Configuration
- [ ] Support email address for contact forms?
- [ ] SMTP relay configuration details?
- [ ] Infomaniak SFTP credentials and limits?
- [ ] Specific rate limits for each operation?

### 8.2 Security
- [ ] How to manage/rotate HMAC secret keys?
- [ ] IP whitelist for SFTP access?
- [ ] Backup encryption for files at rest?

### 8.3 Monitoring
- [ ] Alerting thresholds for stuck files?
- [ ] Who receives security alerts?
- [ ] Log retention policy?

## 9. Risk Assessment

### Acceptable Risks
- **Single provider dependency**: Similar to current domainfactory situation
- **SFTP performance**: Adequate for expected load (< 1000 registrations/hour)
- **10-30 second delays**: Acceptable for email delivery

### Risks to Monitor
- **Migration errors**: Require thorough testing
- **SFTP credential security**: Use strong passwords, IP restrictions
- **File accumulation**: Implement automated cleanup (immediate deletion)
- **DNS propagation**: Keep old system for 48-72 hours

## 10. Success Criteria

- [ ] All emails sent through communication-service
- [ ] Zero dependency on SendGrid
- [ ] Zero dependency on Google Cloud
- [ ] All infrastructure on Infomaniak (except local services)
- [ ] No SQL injection vulnerabilities
- [ ] HMAC signatures on all JSON files
- [ ] Global rate limiting in place
- [ ] Successfully handling 100+ registrations/hour
- [ ] 99.9% uptime after migration
- [ ] Immediate file cleanup after processing implemented

## 11. Next Steps

1. **Confirm requirements** and open questions above
2. **Security implementation** (HMAC, prepared statements, validation, rate limiting)
3. **Add JSON file import to communication-service** for verification/contact emails
4. **Create detailed technical specifications** for each component
5. **Set up Infomaniak environment**
6. **Develop and test changes**
7. **Plan migration window**

---

*Document Version: 1.0*  
*Date: January 2025*  
*Status: Requirements Gathering Complete - Ready for Implementation Planning*