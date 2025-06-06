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
5. Unzuverlässige Patienten

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
- **Inhalt**: Suchhistorie, Ausschlüsse, Kontaktverfolgung

### 3.2 Therapeutenanfrage (Therapist Inquiry)
- **Definition**: Gebündelte Anfrage mit 3-6 Patienten
- **Zweck**: Therapeutenwahl bei minimalem Aufwand
- **Antwortzeit**: 7 Tage
- **Typisches Ergebnis**: 1-2 Annahmen pro Bündel

### 3.3 Bündelerstellung

**Progressive Filterung:**
1. **Harte Kriterien** (müssen erfüllt sein):
   - Innerhalb Patientenentfernung
   - Nicht auf Ausschlussliste
   - Geschlechterpräferenz erfüllt

2. **Weiche Kriterien** (Priorisierung):
   - Verfügbarkeitsüberschneidung
   - Diagnosepräferenz
   - Alterspräferenz
   - Gruppentherapiepräferenz

3. **Sortierung**:
   - Nach Patientenwartezeit
   - Nach geografischer Nähe

### 3.4 Abkühlungsphase
- **Auslöser**: Jede Therapeutenantwort
- **Dauer**: 4 Wochen
- **Umfang**: Systemweit für alle Patienten

### 3.5 Parallele Verarbeitung
- **Anforderung**: Patienten in mehreren Bündeln gleichzeitig
- **Konfliktlösung**: Bei Mehrfachannahmen → erster Therapeut erhält Patient

## 4. Datenmodell (Zusammenfassung)

### Erweiterte Entitäten
- **Patient**: +max_travel_distance_km, travel_mode, availability_schedule
- **Therapeut**: +next_contactable_date, preferred_diagnoses, age_min/max

### Neue Entitäten
- **Platzsuche**: patient_id, status, excluded_therapists
- **PlatzucheContactRequest**: requested_count, requested_date
- **Therapeutenanfrage**: therapist_id, bundle_size, response_type
- **TherapeutAnfragePatient**: Verknüpfung Anfrage↔Patient

## 5. Funktionale Anforderungen

### 5.1 Kontaktmanagement
- **E-Mail**: Max. 1/Woche pro Therapeut, Bündelung mehrerer Patienten
- **Telefon**: Nach 7 Tagen ohne E-Mail-Antwort, 5-Minuten-Slots
- **Priorisierung**: "Potenziell verfügbare" Therapeuten zuerst

### 5.2 Manuelle Eingriffe
- Direkte Zuweisung bei spontanen Öffnungen
- Ausnahmen von Abkühlungsphase (dokumentiert)
- Dynamische Ausschlusslisten-Verwaltung

### 5.3 Webscraping
- **Quelle**: arztsuche.116117.de
- **Frequenz**: Täglich
- **Integration**: Datei-basiert über Cloud Storage

## 6. Geschäftsmetriken

### Erfolgsmetriken
- **Vermittlungsgeschwindigkeit**: Tage bis Erfolg (Ziel: <30)
- **Annahmerate**: % angenommene Patienten/Bündel
- **Konfliktrate**: % Mehrfachannahmen (positiv)

### Operative Metriken
- **Bündeleffizienz**: Ø Annahmen/Bündel
- **Antwortrate**: % Antworten in 7 Tagen
- **Abkühlungseinhaltung**: % korrekte Kontaktpausen