# Curavani User Journey Improvements - Complete Implementation Guide
**Version:** 4.0  
**Date:** January 2025  
**Status:** Major Progress - Phase 4 Completed!
**Last Updated:** January 2025

---

## Implementation Status Overview

### ✅ COMPLETED ITEMS (January 2025)

#### Terminology Updates
- ✅ Changed "Jetzt Therapieplatz finden" → "Therapieplatz finden lassen" throughout
- ✅ Replaced "Service" → "Therapieplatzsuche" or "professionelle Unterstützung"
- ✅ Updated "Registrierung" → "Therapieplatzsuche starten"
- ✅ All links from `registrierung.html` → `service_buchen.html`

#### Pricing System Overhaul
- ✅ Implemented dynamic pricing from `prices.json`
- ✅ Removed all hardcoded prices
- ✅ Removed "Sonderaktion" (special offers) completely
- ✅ Added JavaScript fallback to "-" or "Preis auf Anfrage" on error
- ✅ Single source of truth for all pricing

#### Guarantee Time Differentiation
- ✅ Updated all guarantees to show: 1 Monat (Gruppentherapie) / 3 Monate (Einzeltherapie)
- ✅ Consistent messaging across all pages
- ✅ FAQ sections updated accordingly

#### Group Therapy Positioning
- ✅ Removed "upgrade" terminology
- ✅ Changed to "Wechsel zur Einzeltherapie möglich" (switch possible)
- ✅ Added benefits highlighting for group therapy
- ✅ Positioned as legitimate first choice, not budget option

#### Page Updates
- ✅ **patienten.html** - Fully updated with all changes
- ✅ **service_buchen.html** - Created with new approach and content

#### Email Confirmation System (Phase 4 - ✅ COMPLETED!)
- ✅ **email_bestaetigen.html** - Created with step indicators and improved UX
- ✅ **verification_email.md** - Updated template with new content and fixed variables
- ✅ **Email subject line** - Updated in ObjectStorageClient.php
- ✅ **Template fallback eliminated** - Templates now work correctly
- ✅ **Step-by-step process** - Clear 4-step journey with consistent terminology
- ✅ **User flow improvements** - Reduced warnings before submission, moved to post-submission

### ⏳ PENDING ITEMS

- ⏳ Phase 1: Contract simplification
- ⏳ Phase 2: Live Helper Chat integration
- ⏳ Phase 5: Main registration form updates
- ⏳ Phase 6: Backend email automation

---

## Current Problems Being Solved

### Already Addressed:
- ✅ Unclear pricing (now dynamic and centralized)
- ✅ Poor group therapy positioning (now presented as valuable option)
- ✅ Confusing terminology (standardized across site)
- ✅ Confusing "Registrierung" terminology in email verification (now "E-Mail bestätigen")
- ✅ Poor email template fallbacks (templates now work correctly)
- ✅ Inconsistent step messaging (now consistent 4-step process)

### Still To Address:
1. Complex legal documents overwhelming patients
2. Form requirements too restrictive (3 symptoms max, 20 hours minimum)
3. No regular communication updates during therapy search
4. Missing support options during registration

---

## New User Journey

### Current Implementation:
1. **Click "Therapieplatz finden lassen"** ✅ → Service Overview Page (`service_buchen.html`)
2. **Service Overview** ✅ → Email Validation (`email_bestaetigen.html`)
3. **Email Confirmation** ✅ → Professional email template with 4-step process
4. **Email Link Click** → Main Registration Form with service booking
5. **Form Submission** → Success page with payment instructions
6. **Payment Received** → Confirmation email (manual process currently)
7. **Weekly Updates** → Not yet implemented

---

## Pricing Management System (IMPLEMENTED)

### Current Setup
**Single Source of Truth:** `/prices.json`
```json
{
  "einzeltherapie": 95,
  "gruppentherapie": 45
}
```

### Implementation Details
- All pages load prices dynamically via JavaScript
- Consistent price loading script across pages
- Fallback handling for network/loading errors
- Price displays use span elements with IDs: `price-gruppe` and `price-einzel`

### Pages Using Dynamic Pricing:
- `patienten.html` ✅
- `service_buchen.html` ✅
- `email_bestaetigen.html` ✅
- `verify_token.php` (pending update)
- Email templates (pending update)

---

## Phase 1: Create New Contract Files (PENDING)

### 1.1 Contract Structure Changes

**New Structure (4 parts instead of 6):**
- **teil_a_vereinbarung_simplified.md** - Merged version of Teil A + Teil E
- **teil_b_vollmacht.md** - Keep as is (power of attorney)
- **teil_c_datenschutz.md** - Keep as is (data protection)
- **teil_d_widerruf.md** - Keep as is (withdrawal rights)
- **DELETE:** anlage_widerrufsformular.md - Not needed, email withdrawal sufficient

### 1.2 Content for Simplified Teil A

**Remove these sections completely:**
- § 3(1) - Patient's obligation to report psychological changes
- § 3(2) - PTV-11 form submission requirement  
- § 4 - Entire liability section (Haftung)
- § 5(2) - Payment processor details
- § 6 - Data protection paragraphs 2-3 (keep only first sentence)
- From Teil E: Salvatorische Klausel (§2), Schriftformerfordernis (§3)

**Simplify but keep:**
- § 3(3) - 48-hour response requirement → Use simpler language
- § 3(4) - Keep therapist exclusion list as is
- § 3(5) - Keep digital communication consent

**Note:** Prices in contracts must be loaded dynamically or reference external pricing

### 1.3 Implementation Tasks

**Files to create/modify:**
- Create `/contracts/teil_a_vereinbarung_simplified.md`
- Update `verify_token_functions.php` to use new structure
- Update `getContractText()` function to handle simplified version
- Ensure contract PDFs show dynamic pricing

**Open Questions:**
- [ ] Legal review of simplified language needed
- [ ] Archive strategy for old contract versions
- [ ] Handling of patients who signed old contracts
- [ ] PDF generation with dynamic prices

---

## Phase 2: Configure Live Helper Chat (PENDING)

### 2.1 Service Setup

**Provider:** LiveHelperChat (https://livehelperchat.com)
- Open source option available
- Self-hosted or cloud version
- GDPR compliant

### 2.2 Configuration Requirements

**Trigger Settings:**
- **Proactive invitation after:** 30 seconds on page
- **Pages to monitor:** `service_buchen.html`, `email_bestaetigen.html`, `verify_token.php`
- **Show widget on:** All pages

### 2.3 Chat Messages

**Initial greeting:**
```
"Hallo! 👋 Haben Sie Fragen zur Therapieplatzsuche? Ich helfe Ihnen gerne!"
```

### 2.4 Implementation Tasks

- Install LiveHelperChat
- Add JavaScript snippet to all HTML pages
- Configure operators and hours
- Create canned responses

**Decision Needed:**
- [ ] Self-hosted vs cloud version
- [ ] Operating hours
- [ ] Number of operators

---

## Phase 3: Process Overview Page (✅ COMPLETED)

### 3.1 Status: IMPLEMENTED

**URL:** `/service_buchen.html` ✅
**Title:** "Therapieplatz finden lassen - Ihre persönliche Therapieplatzsuche | Curavani" ✅

### 3.2 Implementation Summary

**What was implemented:**
- Clear 4-step booking process visualization
- Dynamic pricing from `prices.json`
- Improved group therapy information and positioning
- Support section with contact options
- Mobile-responsive design
- Eliminated "Sonderaktion" pricing confusion
- Enhanced therapy option comparison

**Still pending:**
- LiveHelperChat widget integration
- A/B testing setup

---

## Phase 4: Email Confirmation Logic (✅ COMPLETED!)

### 4.1 What Was Completed

✅ **Page Created:** `email_bestaetigen.html` with improved UX
✅ **Step Indicator:** "Therapieplatzsuche - Schritt 1 von 4: E-Mail-Adresse bestätigen"
✅ **Reduced friction:** Warnings moved to post-submission
✅ **Next steps preview:** Consistent terminology for steps 2-4
✅ **Template fixed:** `verification_email.md` with corrected variables
✅ **Subject updated:** "Curavani: Bestätigen Sie Ihre E-Mail für die Therapieplatzsuche"
✅ **Content improved:** Browser copy instructions, guarantee info, contact details

### 4.2 Technical Improvements

- Fixed template variable structure: `{{ data.verification_link }}` → `{{ verification_link }}`
- Eliminated fallback text usage (templates now work correctly)
- Added leerzeilen around links for email client compatibility
- Integrated 4-step process messaging consistently

### 4.3 User Experience Enhancements

- Clear progress indication throughout journey
- Reduced cognitive load before email submission
- Professional email content with branding consistency
- Support contact information readily available
- Motivational guarantee messaging

---

## Phase 5: Update Main Registration Form (PENDING)

### 5.1 Form Field Changes

**Location:** `verify_token.php`

### 5.2 Required Updates

#### Symptoms Selection
- **Current:** Max 3 symptoms
- **Target:** Max 6 symptoms
- Update validation in PHP and JavaScript

#### Previous Therapy Field
- **Current:** Date picker
- **Target:** Dropdown with 3 options
- Add validation for <2 years restriction

#### Availability Requirements  
- **Current:** Minimum 20 hours
- **Target:** Minimum 10 hours
- Update all validation logic

#### Contract Display
- **Current:** Full text in form
- **Target:** Summary + modal approach
- Create PDF download endpoints

#### Pricing Display
- Must load from `prices.json` (not hardcoded)
- Show both therapy options with benefits

### 5.3 Implementation Tasks

- Update form validations
- Create modal system for contracts
- Integrate dynamic pricing
- Test multi-step form flow

---

## Phase 6: Backend Email Automation (PENDING)

### 6.1 Payment Confirmation Email

**Trigger:** Payment marked as received
**Content:** Welcome message + webinar invitation

### 6.2 Weekly Progress Updates

**Trigger:** Every Monday at 9:00 AM
**Content:** Number of therapists contacted + encouragement

### 6.3 Implementation Requirements

**Database changes:**
- Add payment_confirmed_at timestamp
- Add email_log table
- Add weekly_update_last_sent field

**Services to create:**
- Payment confirmation service
- Weekly update cron job
- Email template system

---

## File Change Summary

### ✅ Files COMPLETED:
1. `/service_buchen.html` - Created with new content and approach
2. `/patienten.html` - Updated with all terminology and pricing changes
3. `/prices.json` - Now single source of truth for pricing
4. `/email_bestaetigen.html` - NEW! Professional email confirmation page
5. `/shared/templates/emails/verification_email.md` - NEW! Fixed template with updated content
6. `ObjectStorageClient.php` - Updated email subject line

### ⏳ Files to CREATE:
1. `/contracts/teil_a_vereinbarung_simplified.md` - Simplified contract
2. `/services/weekly_update_service.py` - Email automation
3. `/services/payment_confirmation_service.py` - Payment emails

### ⏳ Files to UPDATE:
1. `/verify_token.php` - Form changes, dynamic pricing
2. `/verify_token_functions.php` - Validation changes
3. `/curavani-simple.css` - Styles for modals
4. All pages - Add LiveHelperChat widget

### ⏳ Files to DELETE:
1. `/contracts/anlage_widerrufsformular.md`

---

## Testing Checklist

### ✅ Completed Testing:
- [x] "Therapieplatz finden lassen" buttons work correctly
- [x] Dynamic price loading from JSON
- [x] Fallback handling for price loading errors
- [x] Mobile responsiveness of service_buchen.html
- [x] Correct guarantee times displayed
- [x] Email confirmation page flow and UX
- [x] Template variable rendering
- [x] Step indicator consistency

### ⏳ Pending Testing:
- [ ] End-to-end email verification flow
- [ ] Template rendering in production environment
- [ ] Contract modal functionality
- [ ] PDF downloads
- [ ] Payment confirmation emails
- [ ] Weekly update triggers
- [ ] Live chat widget
- [ ] Form validation changes

---

## Success Metrics

### Currently Tracking:
- Page load times with dynamic pricing
- JavaScript error rates
- User engagement with new service_buchen.html page
- Email confirmation completion rates
- Template rendering success rates

### New Metrics (Phase 4):
- Email open rates for verification emails
- Click-through rates on verification links
- Time from email request to confirmation
- User drop-off at email confirmation step

### To Implement:
- Registration completion rate
- Drop-off at each step
- Support ticket reduction
- Live chat engagement
- Weekly update effectiveness

---

## Outstanding Decisions

### Immediate Priorities:
1. **Contract Simplification:** Need legal review timeline
2. **Live Chat:** Choose between self-hosted vs cloud
3. **Form Validation Updates:** Plan rollout strategy

### Before Full Launch:
1. A/B testing strategy for form changes
2. Email service provider optimization
3. Webinar platform decision
4. Support staffing for live chat

---

## Next Steps Priority Order

1. **HIGH:** Implement simplified contracts (reduce drop-off)
2. **HIGH:** Update form validations (reduce restrictions)
3. **MEDIUM:** Set up live chat (improve support)
4. **LOW:** Implement email automation (nice to have)

---

## Recent Achievements (Phase 4 Completion)

### What We Fixed:
- **Template Fallback Problem:** Templates now work correctly, no more bad fallback text
- **User Confusion:** Clear step indicators and consistent messaging
- **Email Client Compatibility:** Added proper spacing and copy instructions
- **Professional Communication:** Branded, motivational email content

### Impact:
- Better user experience in email confirmation step
- More professional brand presentation
- Reduced technical debt (eliminated fallbacks)
- Foundation for remaining phases

---

## Version History

- **v4.0** (January 2025): Phase 4 completed - Email confirmation system fully implemented
- **v3.0** (January 2025): Updated with completed implementations, dynamic pricing system
- **v2.0** (January 2025): Initial comprehensive plan
- **v1.0** (December 2024): Original requirements

**Document Status:** Living document, updated as implementation progresses
**Next Review:** After Phase 5 implementation
**Owner:** Development Team