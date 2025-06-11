# TERMINOLOGY

This document standardizes terminology used throughout the Psychotherapy Matching Platform, providing consistent English-German translations for key terms.

## Language Policy

### English (API Protocol Layer)
- **Response wrappers**: `data`, `message`, `error`, `status`
- **Pagination**: `page`, `limit`, `total`
- **System fields**: `id`, `created_at`, `updated_at`
- **HTTP/Technical concepts**: Status codes, technical errors
- **Foreign keys**: All fields ending in `_id`

### German (Business Domain Layer)
- **All entity fields**: Names, addresses, preferences, etc.
- **Enum values**: Status values, types, categories
- **Calculated fields**: Counts, summaries, derived data
- **Business logic fields**: All domain-specific data
- **Table names**: Entity tables use German names
- **Enum type names**: Use German names

### Priority Rule
When a field exists in the database, use that exact German name throughout the API.

## Core Entities

| English | German |
|---------|--------|
| Patient | Patient |
| Therapist | Therapeut |
| Placement Request | Platzanfrage |
| Match | Zuordnung |
| Therapy Place | Therapieplatz |
| Therapy Session | Therapiesitzung |
| Insurance Provider | Krankenkasse |
| Referral | Empfehlung |
| Patient Search | Platzsuche |
| Therapist Inquiry | Therapeutenanfrage |
| Bundle | Bündel |
| Contact Request | Kontaktanfrage |

## Database Tables

| Current Name | German Name |
|--------------|-------------|
| patients | patienten |
| therapists | therapeuten |
| phone_calls | telefonanrufe |
| emails | emails |
| platzsuche | platzsuche |
| therapeutenanfrage | therapeutenanfrage |
| therapeut_anfrage_patient | therapeut_anfrage_patient |
| geocache | geocache |
| distance_cache | distance_cache |

## Bundle-Based System Terms

| English | German |
|---------|--------|
| Patient Search | Platzsuche |
| Therapist Inquiry | Therapeutenanfrage |
| Bundle Composition | Bündelzusammensetzung |
| Contact Request | Kontaktanfrage |
| Cooling Period | Abkühlungsphase |
| Bundle Size | Bündelgröße |
| Parallel Search | Parallele Suche |
| Exclusion List | Ausschlussliste |
| Progressive Filtering | Progressive Filterung |
| Preference Matching | Präferenzabgleich |
| Bundle History | Buendel_verlauf |
| Response Summary | Antwort_zusammenfassung |
| Response Complete | Antwort_vollstaendig |

## Enum Types and Values

### patientenstatus (Patient Status)
| Enum Value | German Display |
|------------|----------------|
| `offen` | Offen |
| `auf_der_Suche` | Auf der Suche |
| `in_Therapie` | In Therapie |
| `Therapie_abgeschlossen` | Therapie abgeschlossen |
| `Suche_abgebrochen` | Suche abgebrochen |
| `Therapie_abgebrochen` | Therapie abgebrochen |

### therapeutstatus (Therapist Status)
| Enum Value | German Display |
|------------|----------------|
| `aktiv` | Aktiv |
| `gesperrt` | Gesperrt |
| `inaktiv` | Inaktiv |

### suchstatus (Search Status)
| Enum Value | German Display |
|------------|----------------|
| `aktiv` | Aktiv |
| `erfolgreich` | Erfolgreich |
| `pausiert` | Pausiert |
| `abgebrochen` | Abgebrochen |

### emailstatus (Email Status)
| Enum Value | German Display |
|------------|----------------|
| `Entwurf` | Entwurf |
| `In_Warteschlange` | In Warteschlange |
| `Wird_gesendet` | Wird gesendet |
| `Gesendet` | Gesendet |
| `Fehlgeschlagen` | Fehlgeschlagen |

### telefonanrufstatus (Phone Call Status)
| Enum Value | German Display |
|------------|----------------|
| `geplant` | Geplant |
| `abgeschlossen` | Abgeschlossen |
| `fehlgeschlagen` | Fehlgeschlagen |
| `abgebrochen` | Abgebrochen |

### therapeutgeschlechtspraeferenz (Therapist Gender Preference)
| Enum Value | German Display |
|------------|----------------|
| `Männlich` | Männlich |
| `Weiblich` | Weiblich |
| `Egal` | Egal |

### antworttyp (Response Type)
| Enum Value | German Display |
|------------|----------------|
| `vollstaendige_Annahme` | Vollständige Annahme |
| `teilweise_Annahme` | Teilweise Annahme |
| `vollstaendige_Ablehnung` | Vollständige Ablehnung |
| `keine_Antwort` | Keine Antwort |

### patientenergebnis (Patient Outcome)
| Enum Value | German Display |
|------------|----------------|
| `angenommen` | Angenommen |
| `abgelehnt_Kapazitaet` | Abgelehnt - Kapazität |
| `abgelehnt_nicht_geeignet` | Abgelehnt - Nicht geeignet |
| `abgelehnt_sonstiges` | Abgelehnt - Sonstiges |
| `nicht_erschienen` | Nicht erschienen |
| `in_Sitzungen` | In Sitzungen |

## Communication Terms

| English | German |
|---------|--------|
| Email | E-Mail |
| Phone Call | Telefonanruf |
| Batch | Stapel |
| Template | Vorlage |
| Recipient | Empfänger |
| Sender | Absender |
| Response | Antwort |
| Subject | Betreff |
| Content | Inhalt |
| Body HTML | Inhalt HTML |
| Body Text | Inhalt Text |
| Queued At | In Warteschlange am |
| Sent At | Gesendet am |
| Follow-up | Nachverfolgung |
| Reminder | Erinnerung |
| Bundle Email | Bündel-E-Mail |
| Individual Contact | Einzelkontakt |
| Response Type | Antworttyp |
| Response Outcome | Antwortergebnis |
| Response Status | Antwort_status |
| Sent Status | Versand_status |
| Needs Follow-up | Nachverfolgung_erforderlich |

## Process Terms

| English | German |
|---------|--------|
| Matching Algorithm | Zuordnungsalgorithmus |
| Distance Calculation | Entfernungsberechnung |
| Contact Frequency | Kontakthäufigkeit |
| Availability | Verfügbarkeit |
| Time Slot | Zeitfenster |
| Cooling Period | Abkühlungsphase |
| Prioritization | Priorisierung |
| Filtering | Filterung |
| Validation | Validierung |
| Processing | Verarbeitung |
| Batching | Stapelverarbeitung |
| Scheduling | Terminplanung |
| Bundle Creation | Bündelerstellung |
| Progressive Filtering | Progressive Filterung |
| Conflict Resolution | Konfliktlösung |
| Manual Assignment | Manuelle Zuweisung |
| Parallel Processing | Parallele Verarbeitung |
| Pre-qualification | Vorqualifizierung |
| Send Immediately | Sofort_senden |
| Dry Run | Testlauf |
| Created Date | Erstellt Datum |
| Sent Date | Gesendet Datum |
| Response Date | Antwort Datum |

## Count and Calculation Fields

| English | German |
|---------|--------|
| Days Since Sent | Tage_seit_versand |
| Wait Time Days | Wartezeit_tage |
| Excluded Therapists Count | Ausgeschlossene_therapeuten_anzahl |
| Active Bundles | Aktive_buendel |
| Total Bundles | Gesamt_buendel |
| Accepted Count | Angenommen_anzahl |
| Rejected Count | Abgelehnt_anzahl |
| No Response Count | Keine_antwort_anzahl |
| Bundles Created | Buendel_erstellt |
| Bundles Sent | Buendel_gesendet |

## Patient-Specific Terms

| English | German |
|---------|--------|
| Patient Name | Patienten_name |
| Diagnosis | Diagnose |
| Medical History | Krankengeschichte |
| Availability | Zeitliche Verfügbarkeit |
| Location Preferences | Räumliche Verfügbarkeit |
| Transportation Mode | Verkehrsmittel |
| Group Therapy | Gruppentherapie |
| Digital Health Application | Digitale Gesundheitsanwendung (DiGA) |
| Psychological Complaints | Psychische Beschwerden |
| Support Systems | Unterstützungssysteme |
| Therapy Goals | Therapieziele |
| Maximum Travel Distance | Maximale Reiseentfernung |
| Travel Mode | Verkehrsmittel |
| Availability Schedule | Verfügbarkeitsplan |
| Waiting Time | Wartezeit |
| Exclusion List | Ausschlussliste |
| Initial Sessions | Erstgespräche |
| Insurance Eligibility | Versicherungsberechtigung |
| Two-Year Rule | Zwei-Jahres-Regel |
| Accepted Patients | Angenommene_patienten |

## Therapist-Specific Terms

| English | German |
|---------|--------|
| Therapist Name | Therapeuten_name |
| Title | Titel |
| Phone Availability | Telefonische Erreichbarkeit |
| Foreign Languages | Fremdsprachen |
| Therapy Methods | Psychotherapieverfahren |
| Additional Qualifications | Zusatzqualifikationen |
| Special Services | Besondere Leistungsangebote |
| Insurance Coverage | Kassensitz |
| Single Therapy Places | Einzeltherapieplätze |
| Group Therapy Places | Gruppentherapieplätze |
| Potentially Available | Potenziell Verfügbar |
| Next Contactable Date | Nächster Kontakt Möglich |
| Last Contact Date | Letztes Kontaktdatum |
| Preferred Diagnoses | Bevorzugte Diagnosen |
| Age Preferences | Altersbereiche |
| Gender Preferences | Geschlechterpräferenzen |
| Working Hours | Arbeitszeiten |
| Response Pattern | Antwortmuster |
| Acceptance Rate | Annahmerate |

## Bundle-Specific Terms

| English | German |
|---------|--------|
| Bundle | Bündel |
| Bundle Size | Bündelgröße |
| Bundle Composition | Bündelzusammensetzung |
| Bundle Priority | Bündelpriorität |
| Accepted Count | Angenommene Anzahl |
| Position in Bundle | Position im Bündel |
| Bundle Efficiency | Bündeleffizienz |
| Optimal Bundle | Optimales Bündel |
| Bundle Preview | Bündelvorschau |
| Bundle Response | Bündelantwort |
| Full Acceptance | Vollständige Annahme |
| Partial Acceptance | Teilweise Annahme |
| Full Rejection | Vollständige Ablehnung |
| Bundle IDs | Buendel_ids |

## List/Collection Terms

| English | German |
|---------|--------|
| Therapist IDs | Therapeut_ids |
| Patient IDs | Patient_ids |
| Bundle IDs | Buendel_ids |
| Accepted Patients | Angenommene_patienten |

## Technical Terms

| English | German |
|---------|--------|
| Microservice | Mikroservice |
| Event | Ereignis |
| Message Queue | Nachrichtenwarteschlange |
| Producer | Erzeuger |
| Consumer | Verbraucher |
| Database | Datenbank |
| API | API |
| Web Scraping | Webdatenextraktion |
| Geocoding | Geokodierung |
| Schema | Schema |
| Migration | Migration |
| Container | Container |
| Service | Dienst |
| Cache | Zwischenspeicher |
| Queue | Warteschlange |
| Feature Flag | Feature-Flag |
| Rollback | Rückgängigmachung |
| Deployment | Bereitstellung |

## Business Metrics Terms

| English | German |
|---------|--------|
| Placement Speed | Vermittlungsgeschwindigkeit |
| Success Rate | Erfolgsquote |
| Response Rate | Antwortquote |
| Show Rate | Erscheinungsquote |
| Conflict Rate | Konfliktrate |
| Bundle Efficiency | Bündeleffizienz |
| Cooling Compliance | Einhaltung der Abkühlungsphase |
| Parallel Search Effectiveness | Effektivität der parallelen Suche |
| Acceptance Rate | Annahmerate |
| Rejection Rate | Ablehnungsquote |

## Database Field Naming Convention

**Important:** All database fields use German names to maintain consistency:

| English Concept | German Database Field |
|----------------|----------------------|
| Next Contactable Date | naechster_kontakt_moeglich |
| Preferred Diagnoses | bevorzugte_diagnosen |
| Age Min/Max | alter_min / alter_max |
| Gender Preference | geschlechtspraeferenz |
| Working Hours | arbeitszeiten |
| Phone Availability | telefonische_erreichbarkeit |
| Spatial Availability | raeumliche_verfuegbarkeit |
| Time Availability | zeitliche_verfuegbarkeit |
| Excluded Therapists | ausgeschlossene_therapeuten |
| Preferred Therapist Gender | bevorzugtes_therapeutengeschlecht |
| Body HTML | inhalt_html |
| Body Text | inhalt_text |
| Queued At | in_warteschlange_am |
| Sent At | gesendet_am |
| Created Date | erstellt_datum |
| Sent Date | gesendet_datum |
| Response Date | antwort_datum |

## API Response Field Naming Convention

When translating API response fields, use underscores for compound German words:
- `bundle_history` → `buendel_verlauf`
- `response_summary` → `antwort_zusammenfassung`
- `days_since_sent` → `tage_seit_versand`
- `excluded_therapists_count` → `ausgeschlossene_therapeuten_anzahl`

## Enum Naming Conventions

All enum types and values follow these rules:
1. **Enum type names**: Use German compound words without underscores (e.g., `patientenstatus`, `therapeutstatus`)
2. **Enum values**: Use underscores for multi-word values (e.g., `auf_der_Suche`, `in_Therapie`)
3. **Capitalization**: Follow German noun capitalization within enum values
4. **Special characters**: No umlauts in database names (use `ae`, `oe`, `ue`)

*Last updated: December 2024*