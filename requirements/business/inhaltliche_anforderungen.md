# Anforderungsspezifikation: Psychotherapie-Vermittlungsplattform

## 1. Projektübersicht

Curavani ist eine Vermittlungsplattform für Psychotherapieplätze im deutschen Gesundheitssystem mit dem Ziel, Patienten innerhalb von **Wochen** (nicht Monaten) einen Therapieplatz zu vermitteln.

**Kernwertversprechen:**
- **Patienten**: Therapieplatz in Wochen durch parallele Suche
- **Therapeuten**: Vorqualifizierte Patienten in effizienten Anfragen
- **Curavani**: Bevorzugter Kanal für Therapeuten werden

## 2. Geschäftskontext

### Therapeuten-Probleme
1. Ungeklärte Patientenverfügbarkeit (<20h/Woche)
2. Fehlende Versicherungsinformationen
3. Keine ICD-10 Diagnose
4. Verletzung der 2-Jahres-Regel
5. Unzuverlässige Patienten (Absagen, No-Shows)
6. Langatmige, unfokussierte Problembeschreibungen
7. Unklares Patientenalter für Spezialisierung

### Aktuelles Therapeutenverhalten
- "First come, first served" bei Öffnungen
- Keine Wartelisten (zu viel Aufwand für 6-12 Monate)
- Patienteninteresse erlischt nach 6 Monaten

### Curavani-Lösung: Patientenvorqualifizierung
1. Private Zahlung = Motivationsfilter
2. Aktuelle Diagnose verifiziert
3. Mindestens 20h/Woche Verfügbarkeit
4. 2-Jahres-Regel geprüft
5. Detaillierter Verfügbarkeitsplan

## 3. Kernprozesse

### 3.1 Platzsuche (Patient Search)
- **Definition**: Fortlaufender Prozess zur Therapieplatzvermittlung
- **Ziel**: Vermittlung in Wochen durch parallele Suche
- **Erfolg**: Patient nimmt 1-2 Probesitzungen wahr UND stimmt Fortsetzung zu
- **Bei Ablehnung**: Therapeut auf Ausschlussliste, Suche fortsetzen

### 3.2 Therapeutenanfrage (Therapist Inquiry)
- **Definition**: Anfrage mit 1-6 Patienten an einen Therapeuten
- **Antworttypen**:
  - Vollständige Annahme (selten)
  - Teilannahme (1-2 Patienten, häufig)
  - Vollständige Ablehnung
  - Keine Antwort → Telefonanruf nach 7 Tagen

## 4. Aktueller Prozess: Manuelle Therapeutenauswahl

### 4.1 Therapeutenauswahl mit PLZ-Filter
**Eingabe**: Zweistelliger PLZ-Code (z.B. "52")

**Filterung**:
- Nur aktive Therapeuten (`status = 'aktiv'`)
- PLZ beginnt mit gewähltem Code
- Kontakt heute möglich (nicht in Abkühlungsphase)

**Sortierung** (in dieser Reihenfolge):
1. Verfügbar UND über Curavani informiert
2. Verfügbar UND NICHT über Curavani informiert  
3. Nicht verfügbar UND über Curavani informiert
4. Alle anderen (alphabetisch)

### 4.2 Automatische Patientenauswahl
Nach Therapeutenauswahl werden passende Patienten automatisch ermittelt:

**Patientenfilterung**:
- Nur aktive Platzsuchen
- Gleicher PLZ-Bereich wie Therapeut
- Sortierung nach Erstelldatum (älteste zuerst)

**Harte Kriterien** (ALLE müssen erfüllt sein):

1. **Distanzprüfung**: Therapeut innerhalb maximaler Reisedistanz des Patienten
2. **Ausschlussprüfung**: Therapeut nicht auf Patientenausschlussliste
3. **Patientenpräferenzen** (alle müssen erfüllt oder NULL sein):
   - Geschlecht des Therapeuten
   - Therapieverfahren (mindestens eine Übereinstimmung)
   - Gruppentherapie-Kompatibilität
4. **Therapeutenpräferenzen** (alle müssen erfüllt oder NULL sein):
   - Diagnose des Patienten
   - Patientenalter (min/max)
   - Patientengeschlecht

**Anfragebildung**:
- 1-6 passende Patienten pro Anfrage
- Keine Mindestgröße (auch Einzelanfragen möglich)
- Maximalgröße systemweit konfigurierbar (Standard: 6)

### 4.3 Abkühlungsphase
- **Auslöser**: JEDE Therapeutenantwort (E-Mail oder erfolgreicher Telefonkontakt)
- **Dauer**: 4 Wochen (konfigurierbar)
- **Umfang**: Systemweit für alle Patienten
- **Speicherung**: `naechster_kontakt_moeglich` im Therapeutendatensatz

### 4.4 Parallele Verarbeitung & Konfliktlösung
- **Anforderung**: Patienten MÜSSEN in mehreren Anfragen gleichzeitig sein
- **Konflikt**: Bei Mehrfachannahmen → Erster Therapeut erhält Patient
- **Nachbearbeitung**: 
  - Andere Therapeuten sofort kontaktieren
  - Alternative Patienten aus deren Anfrage anbieten
  - Positive Beziehung aufrechterhalten

## 5. Datenmodell-Anforderungen

### 5.1 Patient - Erweiterte Felder
- `symptome` (Text) - Symptombeschreibung
- `erfahrung_mit_psychotherapie` (Text) - Vorerfahrung
- `bevorzugtes_therapieverfahren` (Array) - Präferierte Verfahren:
  - "egal"
  - "Verhaltenstherapie" 
  - "tiefenpsychologisch_fundierte_Psychotherapie"
- Bestehende relevante Felder:
  - `bevorzugtes_therapeutengeschlecht` (Männlich/Weiblich/Egal)
  - `offen_fuer_gruppentherapie` (Boolean)
  - `raeumliche_verfuegbarkeit.max_km` (Maximale Reisedistanz)

### 5.2 Therapeut - Erweiterte Felder
- `ueber_curavani_informiert` (Boolean) - Kennt Curavani bereits
- Bestehende relevante Felder:
  - `bevorzugte_diagnosen` (Array) - Gewünschte Diagnosen
  - `alter_min`, `alter_max` (Integer) - Patientenalter
  - `geschlechtspraeferenz` (String) - Patientengeschlecht
  - `bevorzugt_gruppentherapie` (Boolean)
  - `psychotherapieverfahren` (Array) - Angebotene Verfahren

### 5.3 Neue Entitäten
- **Platzsuche**: `patient_id`, `status`, `ausgeschlossene_therapeuten`, `gesamt_angeforderte_kontakte`
- **Therapeutenanfrage**: `therapist_id`, `anfragegroesse`, `antworttyp`, `angenommen_anzahl`
- **TherapeutAnfragePatient**: Verknüpfung Anfrage↔Patient mit individuellem Status

## 6. Antwortverarbeitung und Automatisierung

### 6.1 Therapeutenantwort
- Therapeut antwortet mit individuellem Status pro Patient:
  - `angenommen`
  - `abgelehnt_Kapazitaet`
  - `abgelehnt_nicht_geeignet`
  - `abgelehnt_sonstiges`
  - `nicht_erschienen`
  - `in_Sitzungen`

### 6.2 Automatische Statusaktualisierung
**Bei Patientenannahme**:
- Platzsuche.status → `erfolgreich`
- Erfolgreiche Vermittlung dokumentiert

**Bei Ablehnung**:
- Therapeut → Patientenausschlussliste (je nach Ablehnungsgrund)
- Platzsuche bleibt `aktiv`

**Automatische Anfrageaktualisierung**:
- Bei erfolgreicher Vermittlung: Entfernung aus anderen laufenden Anfragen
- Aktualisierung der Anfragegrößen
- Benachrichtigung betroffener Therapeuten

## 7. Funktionale Anforderungen

### 7.1 Kontaktmanagement
- **E-Mail**: Professionelle Anfragen mit Patientenliste
- **Telefon**: Nach 7 Tagen ohne E-Mail-Antwort, 5-Minuten-Slots
- **Priorisierung**: "Verfügbare und informierte" Therapeuten zuerst
- **Kontaktanfragen**: Additiv (z.B. "25 weitere Kontakte")

### 7.2 Manuelle Eingriffe
- **Therapeutenauswahl**: PLZ-basierte manuelle Auswahl
- **Ausnahmen**: Abkühlungsphase kann überschrieben werden (dokumentiert)
- **Dynamische Ausschlüsse**: Nach schlechten Erfahrungen
- **"Meinungsänderung"**: Therapeut ruft nach Ablehnung mit Öffnung an

### 7.3 Operative Parameter (konfigurierbar)
- **Anfragegröße**: 1-6 Patienten (Standard: max 6)
- **Antwortwartezeit**: 7 Tage vor Telefonanruf
- **Abkühlungsphase**: 4 Wochen
- **PLZ-Filter**: 2-stellig (hart)
- **Präferenz-Matching**: Hart (alle müssen erfüllt sein)

## 8. Geschäftsmetriken

### Erfolgsmetriken
- **Vermittlungsgeschwindigkeit**: Tage bis Erfolg (Ziel: <30)
- **Annahmerate**: % angenommene Patienten/Anfrage
- **Konfliktrate**: % Mehrfachannahmen (positiv!)
- **Show-Rate**: % Erscheinen bei Probesitzungen

### Operative Metriken
- **Anfrageeffizienz**: Ø Annahmen/Anfrage
- **Antwortrate**: % Antworten in 7 Tagen
- **Abkühlungseinhaltung**: % korrekte Kontaktpausen
- **Parallele Suche**: Ø gleichzeitige Anfragen/Patient

## 9. Wettbewerbsvorteil

**Für Therapeuten**: 
- Null Aufwand bei Patientenakquise
- Vorqualifizierte Patienten
- Präferenzbasierte Anfragen
- Vorhersehbare Kontaktfrequenz
- Respektvolle Abkühlungsphasen

**Für Patienten**: 
- Vermittlung in Wochen durch parallele Suche
- Professionelle Interessenvertretung
- Zugang zu nicht-werbenden Therapeuten
- Kontinuierliche Betreuung während Suche

**Systemeffekt**: 
Therapeuten bevorzugen Curavani → mehr verfügbare Plätze → schnellere Vermittlung → rechtfertigt Privatzahlung → positiver Kreislauf

## 10. Qualitätssicherung

### Vorqualifizierung
- Private Zahlung als Motivationsfilter
- Aktuelle ICD-10 Diagnose erforderlich
- Mindestens 20h/Woche Verfügbarkeit
- 2-Jahres-Regel verifiziert
- Detaillierte Verfügbarkeitspläne

### Erfolgsmessung
- Erfolg erst nach 2 Probesitzungen und Zustimmung zur Fortsetzung
- Bei Ablehnung: Ausschluss und Weitersuche
- Kontinuierliches Monitoring der Vermittlungsqualität