# Anforderungsspezifikation: Psychotherapie-Vermittlungsplattform

[English: Business requirements for the bundle-based therapy matching platform. German terminology preserved for domain accuracy. See TERMINOLOGY.md for translations.]

## 1. Projektübersicht

Curavani ist eine Vermittlungsplattform für Psychotherapieplätze im deutschen Gesundheitssystem mit dem Ziel, Patienten innerhalb von **Wochen** (nicht Monaten) einen Therapieplatz zu vermitteln.

**Kernwertversprechen:**
- **Patienten**: Therapieplatz in Wochen durch parallele Suche
- **Therapeuten**: Vorqualifizierte Patienten in effizienten Bündeln
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
- **Ziel**: Vermittlung in Wochen
- **Erfolg**: Patient nimmt 1-2 Probesitzungen wahr UND stimmt Fortsetzung zu
- **Bei Ablehnung**: Therapeut auf Ausschlussliste, Suche fortsetzen

### 3.2 Therapeutenanfrage (Therapist Inquiry)
- **Definition**: Gebündelte Anfrage mit 3-6 Patienten
- **Antworttypen**:
  - Vollständige Annahme (selten)
  - Teilannahme (1-2 Patienten, häufig)
  - Vollständige Ablehnung
  - Keine Antwort → Telefonanruf nach 7 Tagen

### 3.3 Bündelerstellung - Detaillierter Algorithmus

**Schritt 1: Ausgangsmenge**
- Alle aktiven Therapeuten
- Ausschluss: In Abkühlungsphase (`next_contactable_date > heute`)
- Ausschluss: Inaktive/gesperrte Therapeuten

**Schritt 2: Harte Kriterien** (MÜSSEN erfüllt sein)
Für jeden Therapeuten nur Patienten einbeziehen, die:
- Innerhalb der maximalen Reisedistanz des Patienten liegen
- NICHT auf der Ausschlussliste des Patienten stehen
- Geschlechterpräferenz des Patienten erfüllen (falls angegeben)

**Schritt 3: Progressive Filterung nach Priorität**
Filter anwenden bis Ziel-Therapeutenanzahl erreicht:

1. **Verfügbarkeitskompatibilität**
   - Bei bekanntem Therapeutenplan: Nur bei Überschneidung
   - Bei unbekannt: Alle (Therapeut prüft selbst)

2. **Therapeutenpräferenzen**
   - Diagnosepräferenz
   - Alterspräferenz
   - Geschlechterpräferenz
   - Gruppentherapiepräferenz

3. **Patientenwartezeit**
   - Sortierung nach längster Wartezeit

4. **Geografische Nähe**
   - Sortierung nach durchschnittlicher Entfernung

**Schritt 4: Bündelgröße**
- 3-6 Patienten pro Therapeut auswählen
- Priorisierung nach Wartezeit

### 3.4 Abkühlungsphase
- **Auslöser**: JEDE Therapeutenantwort (E-Mail oder erfolgreicher Telefonkontakt)
- **Dauer**: 4 Wochen
- **Umfang**: Systemweit für alle Patienten
- **Speicherung**: `next_contactable_date` im Therapeutendatensatz

### 3.5 Parallele Verarbeitung & Konfliktlösung
- **Anforderung**: Patienten MÜSSEN in mehreren Bündeln gleichzeitig sein
- **Konflikt**: Bei Mehrfachannahmen → Erster Therapeut erhält Patient
- **Nachbearbeitung**: 
  - Andere Therapeuten sofort kontaktieren
  - Alternative Patienten aus deren Bündel anbieten
  - Positive Beziehung aufrechterhalten

### 3.6 Manuelle Eingriffe
- **"Meinungsänderung"**: Therapeut ruft nach Ablehnung mit Öffnung an
  - Manuelle Patientenauswahl durch Personal
  - Zuweisung außerhalb Bündelprozess
- **Ausnahmen**: Abkühlungsphase kann überschrieben werden (dokumentiert)
- **Dynamische Ausschlüsse**: Nach schlechten Erfahrungen in Probesitzungen

## 4. Datenmodell

### Erweiterte Entitäten
- **Patient**: 
  - `max_travel_distance_km`, `travel_mode` (Auto/ÖPNV)
  - `availability_schedule` (stundengenau pro Tag)
  - `therapist_gender_preference` (HARTE Bedingung)
  - `group_therapy_preference` (WEICHE Bedingung)
  
- **Therapeut**: 
  - `next_contactable_date` (Abkühlungsphase)
  - `preferred_diagnoses`, `age_min/max`
  - `gender_preference`, `group_therapy_preference`
  - `working_hours` (wenn bekannt)

### Neue Entitäten
- **Platzsuche**: `patient_id`, `status`, `excluded_therapists`, `total_requested_contacts`
- **PlatzucheContactRequest**: `requested_count`, `requested_date`
- **Therapeutenanfrage**: `therapist_id`, `bundle_size`, `response_type`, `accepted_count`
- **TherapeutAnfragePatient**: Verknüpfung Anfrage↔Patient mit Status

## 5. Funktionale Anforderungen

### 5.1 Kontaktmanagement
- **E-Mail**: Max. 1/Woche pro Therapeut, Bündelung mehrerer Patienten
- **Telefon**: Nach 7 Tagen ohne E-Mail-Antwort, 5-Minuten-Slots
- **Priorisierung**: "Potenziell verfügbare" Therapeuten zuerst
- **Kontaktanfragen**: Additiv (z.B. "25 weitere Kontakte"), keine Erfüllungspflicht

### 5.2 Service-Architektur
- **Matching Service**: 
  - Erstellt Bündel mit Algorithmus
  - Verwaltet Therapeutenanfragen
  - Enforced Abkühlungsphasen
- **Communication Service**: 
  - Sendet einzelne E-Mails (KEINE Bündellogik)
  - Plant Telefonate
  - Meldet Antworten zurück

### 5.3 Operative Parameter
- **Bündelgröße**: 3-6 Patienten (konfigurierbar)
- **Antwortwartezeit**: 7 Tage vor Telefonanruf
- **Abkühlungsphase**: 4 Wochen (konfigurierbar)
- **Mindestverfügbarkeit Patient**: 20h/Woche
- **Erfolgsmessung**: Nach 2 Probesitzungen

## 6. Geschäftsmetriken

### Erfolgsmetriken
- **Vermittlungsgeschwindigkeit**: Tage bis Erfolg (Ziel: <30)
- **Annahmerate**: % angenommene Patienten/Bündel
- **Konfliktrate**: % Mehrfachannahmen (positiv!)
- **Show-Rate**: % Erscheinen bei Probesitzungen

### Operative Metriken
- **Bündeleffizienz**: Ø Annahmen/Bündel
- **Antwortrate**: % Antworten in 7 Tagen
- **Abkühlungseinhaltung**: % korrekte Kontaktpausen
- **Parallele Suche**: Ø gleichzeitige Bündel/Patient

## 7. Wettbewerbsvorteil

**Für Therapeuten**: Null Aufwand bei Patientenakquise, vorqualifizierte Patienten, präferenzbasierte Bündel, vorhersehbare Kontaktfrequenz

**Für Patienten**: Vermittlung in Wochen durch parallele Suche, professionelle Interessenvertretung, Zugang zu nicht-werbenden Therapeuten

Dies schafft einen positiven Kreislauf: Therapeuten bevorzugen Curavani → mehr Plätze → schnellere Vermittlung → rechtfertigt Privatzahlung.