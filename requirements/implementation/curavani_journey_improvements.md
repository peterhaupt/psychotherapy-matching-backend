# Curavani User Journey Improvements - Complete Implementation Guide
**Version:** 2.0  
**Date:** January 2025  
**Purpose:** Comprehensive guide for implementing patient registration and therapy placement journey improvements

---

## Overview

### Current Problems Being Solved:
1. Confusing "Registrierung" terminology suggesting completion when it's just email verification
2. Unclear journey with no upfront explanation of process
3. Complex legal documents overwhelming patients
4. Form requirements too restrictive (3 symptoms max, 20 hours minimum)
5. No regular communication updates during therapy search
6. Missing support options during registration

### New User Journey:
1. **Click "Therapieplatz finden"** → Process Overview Page ("Service buchen")
2. **Process Overview** → Email Validation ("E-Mail bestätigen")  
3. **Email Confirmation** → Main Registration Form with service booking
4. **Form Submission** → Success page with payment instructions
5. **Payment Received** → Confirmation email with webinar invite
6. **Weekly** → Automated progress updates

---

## Phase 1: Create New Contract Files

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
- § 3(3) - 48-hour response requirement → Use simpler language: "Bitte antworten Sie innerhalb von 2 Tagen auf unsere Nachrichten"
- § 3(4) - Keep therapist exclusion list as is
- § 3(5) - Keep digital communication consent

**Final structure for new Teil A:**
```
# Vereinbarung zur Therapieplatzsuche

## § 1 Unser Service
[Keep current content]

## § 2 Was wir für Sie tun
[Keep current content, use bullet points]

## § 3 Ihre Mithilfe
- Antworten Sie bitte innerhalb von 2 Tagen
- Nehmen Sie an vermittelten Erstgesprächen teil
- Informieren Sie uns bei Urlaub oder Krankheit
- Sie können bis zu 10 Therapeuten ausschließen
- Kommunikation erfolgt digital (E-Mail/Telefon)

## § 4 Kosten und Garantie
- Gruppentherapie: 45€ (Garantie: 1 Monat)
- Einzeltherapie: 95€ (Garantie: 3 Monate)
- Bei Nichterfüllung: Vollständige Rückerstattung

## § 5 Datenschutz
Alle Daten werden vertraulich behandelt.

## § 6 Allgemeine Bestimmungen
- Gerichtsstand: Aachen
- Anwendbares Recht: Deutsches Recht
- Vertragsbestandteile: Diese Vereinbarung, Vollmacht, Datenschutzerklärung, Widerrufsbelehrung
```

### 1.3 Implementation Tasks

**Files to create/modify:**
- Create `/contracts/teil_a_vereinbarung_simplified.md`
- Update `verify_token_functions.php` to use new structure
- Update `getContractText()` function to handle simplified version
- Create PDF generator for new combined contract

**Open Questions:**
- [ ] Who reviews the simplified legal language?
- [ ] Do we archive old contract versions?
- [ ] How to handle patients who signed old contracts?
- [ ] Should PDF show version number and date?

---

## Phase 2: Configure Live Helper Chat

### 2.1 Service Setup

**Provider:** LiveHelperChat (https://livehelperchat.com)
- Open source option available
- Self-hosted or cloud version
- GDPR compliant

### 2.2 Configuration Requirements

**Trigger Settings:**
- **Proactive invitation after:** 30 seconds on page (to be tested)
- **Pages to monitor:** service-buchen.html, email-bestaetigen.html, verify_token.php
- **Show widget on:** All pages

**Widget Settings:**
- **Language:** German
- **Position:** Bottom right
- **Mobile:** Floating button
- **Offline message:** Form to email info@curavani.com

### 2.3 Chat Messages

**Initial greeting:**
```
"Hallo! 👋 Haben Sie Fragen zur Therapieplatzsuche? Ich helfe Ihnen gerne!"
```

**Proactive message (after 30 seconds):**
```
"Ich sehe, Sie schauen sich unseren Service an. Kann ich Ihnen bei Fragen helfen?"
```

**Offline message:**
```
"Aktuell sind wir nicht online, aber hinterlassen Sie uns eine Nachricht. Wir melden uns schnellstmöglich!"
```

### 2.4 Implementation Tasks

**Technical setup:**
- Install LiveHelperChat on server OR use cloud version
- Add JavaScript snippet to all HTML pages
- Configure department: "Patientenberatung"
- Set up operator accounts
- Create canned responses for common questions

**Open Questions:**
- [ ] Self-hosted or cloud version?
- [ ] Operating hours? (Mon-Fri 9-17? Include weekends?)
- [ ] How many operators needed?
- [ ] Should chat history be saved to patient records?
- [ ] Integration with backend systems needed?
- [ ] Fallback to WhatsApp/Telegram?

---

## Phase 3: Create Process Overview Page

### 3.1 New Page: service-buchen.html

**URL:** `/service-buchen.html`
**Title:** "Service buchen - Ihr Weg zum Therapieplatz | Curavani"

### 3.2 Page Sections Content

**Hero Section:**
- Headline: "Ihr Weg zum Therapieplatz in 4 einfachen Schritten"
- Subheadline: "Keine Verpflichtung bis zum letzten Schritt - Sie entscheiden"

**Timeline Section (4 steps):**
1. **E-Mail bestätigen** - 2 Minuten - "Bestätigen Sie Ihre E-Mail-Adresse für sichere Kommunikation"
2. **Informationen angeben** - 10 Minuten - "Teilen Sie uns Ihre Bedürfnisse und Verfügbarkeiten mit"
3. **Service auswählen** - 2 Minuten - "Wählen Sie zwischen Einzel- oder Gruppentherapie"
4. **Wir suchen für Sie** - 1-4 Wochen - "Lehnen Sie sich zurück - wir finden Ihren Therapieplatz"

**Information Requirements Section:**
```
Was wir von Ihnen benötigen:

Persönliche Angaben:
• Name und Geburtsdatum
• Kontaktdaten (E-Mail, Telefon)  
• Wohnort (für die Umkreissuche)
• Krankenkasse und Hausarzt

Für die Therapiesuche:
• Ihre Beschwerden (max. 6 auswählbar)
• Zeitliche Verfügbarkeit (min. 10 Std./Woche)
• Gewünschte Entfernung zum Therapeuten
• Präferenzen (optional)

Info-Box: "Die Verfügbarkeit benötigen wir nur für die ersten Gespräche. 
Danach vereinbaren Sie feste Termine direkt mit Ihrem Therapeuten."
```

**Pricing Section:**
```
Gruppentherapie - 45€
✓ 1 Monat Garantie
✓ 4-8 Personen in der Gruppe
✓ Oft kürzere Wartezeiten
✓ Upgrade auf Einzeltherapie möglich

Einzeltherapie - 95€  
✓ 3 Monate Garantie
✓ Individuell auf Sie abgestimmt
✓ Intensivere Betreuung
✓ Flexiblere Termingestaltung

100% Geld-zurück-Garantie: Finden wir keinen Therapieplatz innerhalb 
der Garantiezeit, erhalten Sie Ihr Geld vollständig zurück.
```

**Guarantees Section:**
```
Unsere Versprechen an Sie:
✓ Erfolgsgarantie - Therapieplatz oder Geld zurück
🔒 Datenschutz - Ihre Daten sind sicher und vertraulich
💬 Persönliche Betreuung - Wir sind immer für Sie erreichbar
```

**Support Section:**
```
Haben Sie Fragen? Wir helfen Ihnen gerne!
📞 0151 46359691 - Anrufen
✉️ info@curavani.com - E-Mail schreiben
💬 Live Chat - Sofort Hilfe bekommen
```

**CTA Button:**
- Text: "Jetzt starten - E-Mail bestätigen"
- Target: `/email-bestaetigen.html`
- Subtext: "Keine Zahlung oder Verpflichtung in diesem Schritt"

### 3.3 Implementation Tasks

- Create new file `/service-buchen.html`
- Add CSS for timeline visualization
- Add CSS for pricing cards
- Ensure mobile responsive design
- Add LiveHelperChat widget

**Open Questions:**
- [ ] Should prices show crossed-out regular prices?
- [ ] Add testimonials on this page?
- [ ] Include FAQ section?
- [ ] Show number of successful placements?
- [ ] Add trust badges/certifications?

---

## Phase 4: Update Email Confirmation Logic

### 4.1 Page Rename and Updates

**Rename:** `registrierung.html` → `email-bestaetigen.html`

### 4.2 Page Content Updates

**New Title:** "E-Mail bestätigen | Curavani"

**New Heading:** "Schritt 1: E-Mail-Adresse bestätigen"

**New Subheading:** "Bestätigen Sie Ihre E-Mail-Adresse, um mit der Buchung fortzufahren"

**Warning Box (prominent):**
```
⚠️ Wichtiger Hinweis
Dies ist NUR die E-Mail-Bestätigung!

Nach Klick auf den Link in der E-Mail können Sie:
• Ihre Informationen eingeben
• Zwischen Gruppen- oder Einzeltherapie wählen
• Den Service verbindlich buchen
```

**Info Box:**
```
Nach dem Klick auf "E-Mail-Adresse bestätigen" erhalten Sie eine E-Mail 
mit einem Bestätigungslink. Dieser Link ist 30 Minuten gültig. 
Mit dem Klick auf den Link können Sie die Buchung fortführen.
```

**Button Text:** "E-Mail-Adresse bestätigen" (not "Registrierung starten")

### 4.3 Email Template Updates

**File:** `send_verification.php`

**Email Subject:** "E-Mail bestätigen - Service noch nicht gebucht"

**Email Body:**
```
Guten Tag,

vielen Dank für Ihr Interesse an unserem Service!

⚠️ WICHTIG: Dies ist NUR die Bestätigung Ihrer E-Mail-Adresse.

Sie haben unseren Service noch NICHT gebucht.

Nach der E-Mail-Bestätigung:
• Geben Sie Ihre Informationen ein
• Wählen Sie Ihren Service (Einzel- oder Gruppentherapie)
• Schließen Sie die Buchung ab


➡️ Bitte klicken Sie auf den folgenden Link, um fortzufahren:

[VERIFICATION_LINK]


Der Link ist 30 Minuten gültig.

Bei Fragen sind wir gerne für Sie da:
📞 0151 46359691
✉️ info@curavani.com

Mit freundlichen Grüßen
Ihr Curavani Team
```

### 4.4 Implementation Tasks

- Rename file and update all links pointing to it
- Update page content with new warnings
- Modify `send_verification.php` email template
- Test email rendering in different clients
- Update success/error messages

**Open Questions:**
- [ ] Should link be a button-style HTML element?
- [ ] Add resend link functionality?
- [ ] Track email open rates?
- [ ] Should we show remaining time for token?

---

## Phase 5: Update Service Booking (Main Registration Form)

### 5.1 Form Field Changes

**Location:** `verify_token.php`

### 5.2 Symptoms Selection Update

**Current:** Max 3 symptoms
**New:** Max 6 symptoms

**Update validation:**
- PHP: `validateSymptomArray()` function - change limit from 3 to 6
- JavaScript: Change validation from 3 to 6
- UI: Update counter display "0 von 6 Symptomen ausgewählt"

**New instruction text:**
```
"Bitte wählen Sie bis zu 6 Symptome aus, die Ihre Beschwerden am besten beschreiben. 
Je genauer Ihre Angaben, desto besser können wir einen passenden Therapeuten finden."
```

### 5.3 Previous Therapy Field

**Current:** Date picker for last therapy session
**New:** Dropdown with three options

**Dropdown options:**
```html
<select id="therapy_experience" name="therapy_experience" required>
    <option value="">Bitte wählen</option>
    <option value="never">Nein, noch nie</option>
    <option value="more_2_years">Ja, vor mehr als 2 Jahren</option>
    <option value="less_2_years">Ja, vor weniger als 2 Jahren</option>
</select>
```

**Warning for "less_2_years":**
```
"Leider können wir unseren Service nicht anbieten, wenn Ihre letzte 
Therapie vor weniger als 2 Jahren beendet wurde."
```

### 5.4 Availability Requirements

**Current:** Minimum 20 hours per week
**New:** Minimum 10 hours per week

**Update validation:** Change from 20 to 10 in `validateAvailability()`

**New explanation text:**
```
"Damit wir zeitnah einen Therapieplatz finden, benötigen wir Ihre 
Verfügbarkeit für die ersten Gespräche. Mindestens 10 Stunden pro 
Woche zwischen 8:00 und 18:00 Uhr.

Wichtig: Diese Zeiten gelten NUR für die ersten Termine zum Kennenlernen. 
Sobald die Therapie beginnt, vereinbaren Sie feste wöchentliche Termine 
direkt mit Ihrem Therapeuten."
```

### 5.5 Contract Display Changes

**Current:** Full contract text displayed in form
**New:** Summary + Modal/Download approach

**For each contract part:**
```
Summary Box:
- 3-4 bullet points of key information
- "Vollständige [Document name] lesen" button → Opens modal
- "Als PDF herunterladen" button → Download contract part
- Checkbox: "Ich habe die [Document name] gelesen und akzeptiere sie"
```

**Contract summaries:**

**Teil A (Vereinbarung):**
- Wir suchen aktiv nach einem passenden Therapeuten
- Garantie: Therapieplatz innerhalb der vereinbarten Zeit oder Geld zurück
- Sie können Therapeuten nach dem Erstgespräch ablehnen
- Kosten: 45€ (Gruppe) oder 95€ (Einzel)

**Teil B (Vollmacht):**
- Wir kontaktieren Therapeuten in Ihrem Namen
- Wir vereinbaren Termine für Sie
- Sie können die Vollmacht jederzeit widerrufen

**Teil C (Datenschutz):**
- Ihre Daten werden vertraulich behandelt
- Weitergabe nur an potenzielle Therapeuten
- Löschung nach Vertragsende möglich
- DSGVO-konforme Verarbeitung

**Teil D (Widerruf):**
- 14 Tage Widerrufsrecht ab Vertragsschluss
- Widerruf per E-Mail möglich
- Vollständige Rückerstattung bei Widerruf

### 5.6 Group vs Individual Therapy

**Add comparison info near selection:**
```
Gruppentherapie:
✓ Schnellere Vermittlung (1 Monat Garantie)
✓ Günstiger Preis (45€)
✓ Upgrade jederzeit möglich

Einzeltherapie:
✓ Klassische 1-zu-1 Betreuung
✓ 3 Monate Garantie
✓ Intensivere Behandlung
```

### 5.7 Implementation Tasks

- Update all form validations (PHP and JavaScript)
- Create modal system for contracts
- Add PDF download endpoints
- Update form field HTML
- Test multi-step form flow
- Ensure all error messages updated

**Open Questions:**
- [ ] Keep multi-step form or make single page after contract simplification?
- [ ] Should contract modals have "Accept" button or just "Close"?
- [ ] Track which contracts were actually opened/read?
- [ ] A/B test form changes?
- [ ] Add progress save functionality?

---

## Phase 6: Backend Email Automation

### 6.1 Payment Confirmation Email

**Trigger:** Payment marked as received in admin panel

**Email content:**
```
Betreff: Zahlung erhalten - Ihre Therapieplatzsuche beginnt

Guten Tag [Vorname] [Nachname],

wir haben Ihre Zahlung erhalten. Vielen Dank!

✅ Ihre Therapieplatzsuche ist nun aktiv

Was passiert als Nächstes:
• Wir beginnen sofort mit der Kontaktaufnahme zu passenden Therapeuten
• Sie erhalten wöchentliche Updates über den Fortschritt
• Sobald ein Therapeut einen Platz anbietet, informieren wir Sie umgehend

📅 Kostenloses Webinar
Wir laden Sie zu unserem wöchentlichen Webinar ein:
Datum: Jeden Mittwoch
Zeit: 18:00 Uhr  
Thema: "Erfolgreich zum Therapieplatz - Tipps und Informationen"

Anmeldung: https://curavani.com/webinar

Bei Fragen sind wir jederzeit für Sie da:
📞 0151 46359691
✉️ info@curavani.com

Mit freundlichen Grüßen
Ihr Curavani Team
```

### 6.2 Weekly Progress Updates

**Trigger:** Every Monday at 9:00 AM for active patients

**Query for statistics:**
```sql
-- Therapists contacted this week
SELECT COUNT(DISTINCT therapist_id) 
FROM therapeutenanfrage ta
JOIN therapeut_anfrage_patient tap ON ta.id = tap.therapeutenanfrage_id
WHERE tap.patient_id = [PATIENT_ID]
AND ta.created_at > NOW() - INTERVAL '7 days'
```

**Email content:**
```
Betreff: Ihr wöchentliches Update zur Therapieplatzsuche

Guten Tag [Vorname] [Nachname],

hier ist Ihr wöchentliches Update zur Therapieplatzsuche:

📊 Diese Woche kontaktiert: [X] Therapeuten

Wir setzen die Suche für Sie fort und melden uns, sobald wir eine 
positive Rückmeldung erhalten.

Haben Sie Fragen oder benötigen Sie Unterstützung?
📞 0151 46359691
✉️ info@curavani.com

Mit freundlichen Grüßen
Ihr Curavani Team
```

### 6.3 Implementation Tasks

**Database changes needed:**
- Add payment_confirmed_at timestamp to patients/platzsuche
- Add email_log table for tracking sent emails
- Add weekly_update_last_sent timestamp

**Create services:**
- Payment confirmation email service
- Weekly update cron job
- Email template system
- Webinar registration system (manual for now)

**Open Questions:**
- [ ] How is payment currently tracked?
- [ ] Should weekly updates stop after X weeks of no progress?
- [ ] Include unsubscribe link in emails?
- [ ] What if no therapists contacted in a week?
- [ ] Should updates be personalized based on progress?
- [ ] Webinar platform to use?

---

## File Change Summary

### Files to CREATE:
1. `/service-buchen.html` - New process overview page
2. `/contracts/teil_a_vereinbarung_simplified.md` - Merged contract
3. `/services/weekly_update_service.py` - Weekly email automation
4. `/services/payment_confirmation_service.py` - Payment emails

### Files to RENAME:
1. `/registrierung.html` → `/email-bestaetigen.html`

### Files to UPDATE:
1. `/patienten.html` - Change all "Therapieplatz finden" links
2. `/email-bestaetigen.html` - New warnings and text
3. `/send_verification.php` - New email template
4. `/verify_token.php` - Form changes, contract modals
5. `/verify_token_functions.php` - Validation changes
6. `/curavani-simple.css` - New styles for timeline, modals
7. All pages - Add LiveHelperChat widget

### Files to DELETE:
1. `/contracts/anlage_widerrufsformular.md`

---

## Testing Checklist

### User Journey:
- [ ] "Therapieplatz finden" → lands on service-buchen.html
- [ ] Process overview displays correctly on mobile
- [ ] Email validation page shows clear warnings
- [ ] Email contains "not yet booked" message
- [ ] Link has spacing and is clickable in all email clients
- [ ] Form accepts 6 symptoms
- [ ] Previous therapy dropdown shows warning
- [ ] 10 hours validation works
- [ ] Contracts show as modals
- [ ] PDF downloads work
- [ ] Payment confirmation email sends
- [ ] Weekly updates trigger correctly
- [ ] Live chat appears after 30 seconds

### Cross-browser Testing:
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile browsers

### Email Client Testing:
- [ ] Gmail
- [ ] Outlook (Windows/Mac)
- [ ] Apple Mail
- [ ] Mobile email apps

---

## Rollback Plan

### If issues occur:
1. **Phase 1 (Contracts):** Keep old contracts available as fallback
2. **Phase 2 (Chat):** Can disable widget instantly
3. **Phase 3 (Overview):** Redirect back to old flow
4. **Phase 4 (Email):** Revert template, rename page back
5. **Phase 5 (Form):** Feature flags for each change
6. **Phase 6 (Backend):** Disable cron jobs, manual emails

---

## Success Metrics

### Track from Day 1:
- Registration start → completion rate
- Drop-off at each step
- Time to complete registration
- Support tickets about confusion
- Live chat engagement rate
- Email open rates
- Weekly update unsubscribe rate

### Compare before/after:
- Overall conversion rate
- Average registration time
- Support ticket volume
- User satisfaction scores
- Payment completion rate

---

## Outstanding Decisions Needed

Before starting each phase, decide:

### Phase 1 (Contracts):
- Legal review process and timeline
- Version control strategy for contracts
- Handling of existing patients

### Phase 2 (Live Chat):
- Exact operating hours
- Staffing requirements
- Integration depth with backend

### Phase 3 (Process Overview):
- Final copy approval
- Visual design elements
- A/B testing approach

### Phase 4 (Email):
- Email service provider limits
- Tracking and analytics setup
- Resend functionality

### Phase 5 (Form):
- Single vs multi-step decision
- Testing strategy with users
- Rollout approach (gradual or all at once)

### Phase 6 (Backend):
- Payment tracking integration
- Email frequency limits
- Webinar platform selection

---

**Document Version:** 2.0
**Last Updated:** January 2025
**Next Review:** After Phase 1 implementation