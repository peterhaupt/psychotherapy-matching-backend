# Formelle Prozessbeschreibung: Therapeutenvermittlung mit manueller Bündelauswahl

## 1. Datenmodell-Anforderungen

### 1.1 Patient - Neue/Erweiterte Felder
- `bevorzugtes_therapieverfahren` (JSONB Array) - **NEU**
- Bestehende relevante Felder:
  - `bevorzugtes_therapeutengeschlecht` (Enum: Männlich/Weiblich/Egal)
  - `offen_fuer_gruppentherapie` (Boolean)
  - `raeumliche_verfuegbarkeit.max_km` (Integer in JSONB)

### 1.2 Therapeut - Neue/Erweiterte Felder
- `ueber_curavani_informiert` (Boolean) - **NEU**
- Bestehende relevante Felder:
  - `bevorzugte_diagnosen` (JSONB Array)
  - `alter_min`, `alter_max` (Integer)
  - `geschlechtspraeferenz` (String)
  - `bevorzugt_gruppentherapie` (Boolean)
  - `psychotherapieverfahren` (JSONB Array)

## 2. Prozess: Manuelle Bündelerstellung

### 2.1 Therapeutenauswahl
**Eingabe**: Zweistelliger PLZ-Code (z.B. "52")

**Therapeutenliste - Filterung**:
- Nur aktive Therapeuten (`status = 'aktiv'`)
- PLZ beginnt mit gewähltem Code (`plz LIKE '52%'`)
- Kontakt heute möglich (`naechster_kontakt_moeglich <= heute`)

**Therapeutenliste - Sortierung** (in dieser Reihenfolge):
1. `potenziell_verfuegbar = true` UND `ueber_curavani_informiert = true`
2. `potenziell_verfuegbar = true` UND `ueber_curavani_informiert = false`
3. `potenziell_verfuegbar = false` UND `ueber_curavani_informiert = true`
4. Alle anderen alphabetisch nach Nachname, Vorname

### 2.2 Automatische Patientenauswahl
**Nach Auswahl eines Therapeuten**:

**Platzsuchen-Liste - Filterung**:
- Nur aktive Platzsuchen (`status = 'aktiv'`)
- PLZ beginnt mit gleichem Code wie Therapeut (`plz LIKE '52%'`)

**Platzsuchen-Liste - Sortierung**:
- Nach Erstelldatum aufsteigend (älteste zuerst)

**Für jede Platzsuche - Prüfung** (alle Kriterien sind HART):

1. **Distanzprüfung**:
   - Berechne Distanz zwischen Patient und Therapeut
   - Prüfe: Distanz ≤ Patient.raeumliche_verfuegbarkeit.max_km

2. **Ausschlussprüfung**:
   - Therapeut NOT IN Patient.ausgeschlossene_therapeuten

3. **Präferenzprüfung** (ALLE müssen erfüllt sein oder NULL sein):
   - **Geschlecht**: 
     - WENN Patient.bevorzugtes_therapeutengeschlecht != 'Egal' 
     - DANN muss Therapeut.geschlecht matchen
   - **Therapieverfahren**:
     - WENN Patient.bevorzugtes_therapieverfahren != NULL
     - DANN mindestens ein Verfahren muss in Therapeut.psychotherapieverfahren sein
   - **Gruppentherapie**:
     - WENN Patient.offen_fuer_gruppentherapie = false
     - DANN darf Therapeut.bevorzugt_gruppentherapie != true
   
4. **Therapeutenpräferenzen** (ALLE müssen erfüllt sein oder NULL sein):
   - **Diagnose**:
     - WENN Therapeut.bevorzugte_diagnosen != NULL
     - DANN Patient.diagnose IN bevorzugte_diagnosen
   - **Patientenalter**:
     - WENN Therapeut.alter_min != NULL
     - DANN Patientenalter ≥ alter_min
     - WENN Therapeut.alter_max != NULL
     - DANN Patientenalter ≤ alter_max
   - **Geschlecht**:
     - WENN Therapeut.geschlechtspraeferenz != 'Egal'
     - DANN Patient.geschlecht muss matchen

**Bündelerstellung**:
- Nehme die ersten N passenden Platzsuchen (N = systemweit konfigurierbare Maximalgröße)
- Keine Mindestgröße - auch einzelne Patienten möglich
- Maximalgröße: Systemweit konfigurierbar (Standard: 6)

## 3. Antwortverarbeitung und Konfliktauflösung

### 3.1 Therapeutenantwort
- Therapeut antwortet auf Bündel mit individuellem Status pro Patient
- Mögliche Stati: `angenommen`, `abgelehnt_Kapazitaet`, `abgelehnt_nicht_geeignet`, etc.

### 3.2 Automatische Statusaktualisierung
**Bei Patientenannahme**:
- Platzsuche.status → `erfolgreich`
- Platzsuche.erfolgreiche_vermittlung_datum → heute

**Bei Ablehnung**:
- Therapeut → Patient.ausgeschlossene_therapeuten (nur bei bestimmten Ablehnungsgründen)
- Platzsuche bleibt `aktiv`

## 4. Automatische Bündelaktualisierung

### 4.1 Trigger
- Immer wenn eine Platzsuche den Status auf `erfolgreich` ändert

### 4.2 Prozess
- Finde alle Bündel, die diese Platzsuche enthalten
- Für jedes betroffene Bündel:
  - WENN Bündel noch nicht beantwortet:
    - Entferne den vermittelten Patienten
    - Aktualisiere Bündelgröße
    - Markiere Status als "reduziert"

### 4.3 Optionen bei reduziertem Bündel
- **Option A**: Bündel stornieren
- **Option B**: Neue Patienten hinzufügen (gleicher Auswahlprozess)
- **Option C**: Fortfahren mit reduzierter Größe

## 5. Übersichtsanforderungen

### 5.1 Bündel-Dashboard
Zeige für jedes offene Bündel:
- Ursprüngliche Patientenanzahl
- Aktuelle Patientenanzahl (nach automatischen Entfernungen)
- Status-Indikator wenn Patienten entfernt wurden
- Tage seit Versand
- Antwort-Status

### 5.2 API-Anforderungen
`GET /api/therapeutenanfragen/{id}` muss für jeden Patient zeigen:
- Bündel-interner Status
- Aktueller Platzsuche-Status
- Konfliktinformation (falls anderweitig vermittelt)

## 6. Prozessparameter

- **Mindest-Bündelgröße**: Keine (auch Einzelvermittlung möglich)
- **Maximal-Bündelgröße**: Systemweit konfigurierbar (Standard: 6)
- **Abkühlungsphase**: 4 Wochen nach Kontakt
- **Nachfass-Zeitraum**: 7 Tage für Telefonanruf
- **PLZ-Filter**: Hart (keine Übergreifung zwischen PLZ-Bereichen)
- **Präferenz-Matching**: Hart (alle Präferenzen müssen erfüllt sein)

## 7. Systemweite Konfiguration

Folgende Parameter müssen systemweit konfigurierbar sein:
- `MAX_BUNDLE_SIZE`: Maximale Anzahl Patienten pro Bündel (Standard: 6)
- `COOLING_PERIOD_WEEKS`: Wochen bis zum nächsten möglichen Kontakt (Standard: 4)
- `FOLLOW_UP_DAYS`: Tage bis zum Nachfass-Telefonat (Standard: 7)