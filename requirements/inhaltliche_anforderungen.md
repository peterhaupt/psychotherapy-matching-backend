# Anforderungsspezifikation: Psychotherapie-Vermittlungsplattform

## 1. Projektübersicht

Die Psychotherapie-Vermittlungsplattform ist ein Softwaresystem zur effizienten Vermittlung von Psychotherapieplätzen für Patienten in Deutschland. Die Plattform vereinfacht und beschleunigt den Vermittlungsprozess durch automatisierte Kommunikation mit Therapeuten und strukturierte Patientendatenverwaltung.

Die minimale lokale Version soll als Grundlage für ein erweiterbares System dienen, das später zu einer vollwertigen, in der Cloud gehosteten Plattform ausgebaut werden kann.

## 2. Datenmodell

### 2.1 Therapeuten

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| Anrede | Text | z.B. Herr, Frau |
| Titel | Text | z.B. Dr., Prof. |
| Vorname | Text | |
| Nachname | Text | |
| Straße | Text | |
| PLZ | Text | |
| Ort | Text | |
| Telefon | Text | |
| Fax | Text | |
| E-Mail | Text | |
| Webseite | Text | |
| Kassensitz | Boolean | |
| Geschlecht | Text | Abgeleitet aus Anrede |
| Telefonische Erreichbarkeit | Struktur | Zeiten, wann der Therapeut telefonisch erreichbar ist |
| Fremdsprachen | Liste | |
| Psychotherapieverfahren | Liste | z.B. Verhaltenstherapie, systemische Therapie, tiefenpsychologisch fundierte Therapie |
| Zusatzqualifikationen | Text | |
| Besondere Leistungsangebote | Text | |
| Letzter Kontakt per E-Mail | Datum | |
| Letzter Kontakt per Telefon | Datum | |
| Letztes persönliches Gespräch | Datum | |
| Freie Einzeltherapieplätze ab Datum | Datum | |
| Freie Gruppentherapieplätze ab Datum | Datum | |
| Gesperrt | Boolean | Ob der Therapeut aktuell für neue Anfragen gesperrt ist |
| Sperrgrund | Text | Grund für die Sperrung |
| Sperrdatum | Datum | Zeitpunkt der Sperrung |

### 2.2 Patienten

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| Anrede | Text | |
| Vorname | Text | |
| Nachname | Text | |
| Straße | Text | |
| PLZ | Text | |
| Ort | Text | |
| E-Mail | Text | |
| Telefon | Text | |
| Hausarzt | Text | |
| Krankenkasse | Text | |
| Krankenversicherungsnummer | Text | |
| Geburtsdatum | Datum | |
| Diagnose | Text | ICD-10 Diagnose |
| Verträge unterschrieben | Boolean | |
| Psychotherapeutische Sprechstunde | Boolean | |
| Startdatum | Datum | Beginn der Platzsuche |
| Erster Therapieplatz am | Datum | |
| Funktionierender Therapieplatz am | Datum | |
| Status | Enum | offen, auf der Suche, in Therapie, Therapie abgeschlossen, Suche abgebrochen, Therapie abgebrochen |
| Empfehler der Unterstützung | Text | Wer hat den Patienten auf die Unterstützung hingewiesen |
| Zeitliche Verfügbarkeit | Struktur | Wochentage und Uhrzeiten, strukturiert erfasst |
| Räumliche Verfügbarkeit | Struktur | Maximale Entfernung/Fahrzeit |
| Verkehrsmittel | Text | Auto oder ÖPNV für Entfernungsberechnung |
| Offen für Gruppentherapie | Boolean | |
| Offen für DIGA | Boolean | Digitale Gesundheitsanwendungen |
| Letzter Kontakt | Datum | |
| Psychotherapieerfahrung | Boolean | |
| Stationäre Behandlung | Boolean | Für psychische Erkrankung |
| Berufliche Situation | Text | |
| Familienstand | Text | |
| Aktuelle psychische Beschwerden | Text | |
| Beschwerden seit | Datum | |
| Bisherige Behandlungen | Text | Psychotherapeutisch oder psychiatrisch |
| Relevante körperliche Erkrankungen | Text | |
| Aktuelle Medikation | Text | |
| Aktuelle Belastungsfaktoren | Text | |
| Unterstützungssysteme | Text | |
| Anlass für die Therapiesuche | Text | |
| Erwartungen an die Therapie | Text | |
| Therapieziele | Text | |
| Frühere Therapieerfahrungen | Text | |
| Ausgeschlossene Therapeuten | Liste | Therapeuten, die bei der Platzsuche nicht berücksichtigt werden sollen |
| Bevorzugtes Therapeutengeschlecht | Enum | Männlich, Weiblich, Egal |

### 2.3 Platzanfrage

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| Patient | Referenz | Verweis auf den Patienten |
| Therapeut | Referenz | Verweis auf den Therapeuten |
| Status | Enum | Offen, In Bearbeitung, Abgelehnt, Angenommen |
| Erstellungsdatum | Datum | |
| Kontaktdatum E-Mail | Datum | Wann wurde der Therapeut per E-Mail kontaktiert |
| Kontaktdatum Telefon | Datum | Wann wurde der Therapeut telefonisch kontaktiert |
| Antwort | Text | Inhalt der Antwort des Therapeuten |
| Antwortdatum | Datum | |
| Nächster Kontakt frühestens | Datum | Bei Ablehnung - wann darf der Therapeut für diesen Patienten wieder kontaktiert werden |

### 2.4 E-Mail

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| Therapeut | Referenz | Verweis auf den Therapeuten |
| Betreff | Text | |
| Inhalt | Text | |
| Platzanfragen | Liste | Referenzen auf die enthaltenen Platzanfragen |
| Sendedatum | Datum | |

### 2.5 Telefonat

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| Therapeut | Referenz | Verweis auf den Therapeuten |
| Geplantes Datum | Datum | |
| Tatsächliches Datum | Datum | |
| Platzanfragen | Liste | Referenzen auf die besprochenen Platzanfragen |
| Notizen | Text | Ergebnis und Notizen zum Telefonat |

## 3. Kernprozesse

### 3.1 Vermittlungsprozess / Platzsuche-Management

1. **Patientenanlage**
   - Erfassung aller relevanten Patientendaten
   - Prüfung der Vollständigkeit

2. **Voraussetzungsprüfung**
   - Verträge müssen unterschrieben sein (wird außerhalb des Systems erledigt, muss aber dokumentiert werden)
   - Diagnose muss vorhanden sein (ICD-10)
   - Falls keine Diagnose: Patient muss erst eine psychotherapeutische Sprechstunde wahrnehmen

3. **Therapeutensuche**
   - Automatische Filterung nach folgenden Kriterien:
     - Entfernung vom Wohnort des Patienten (berechnet mit OpenStreetMap)
     - Verfügbarkeit des Therapeuten (nicht gesperrt)
     - Übereinstimmung der zeitlichen Verfügbarkeit
     - Geschlecht des Therapeuten (falls vom Patienten gewünscht)
     - Ausschluss von durch den Patienten abgelehnten Therapeuten
   - Manuelle Freigabe der Kontaktliste

4. **Therapeuten-Kontaktierung**
   - E-Mail-Versand (wenn E-Mail-Adresse vorhanden)
   - Planung von Telefonaten (wenn keine E-Mail oder keine Antwort innerhalb einer Woche)
   - Dokumentation aller Kontaktversuche

5. **Nachverfolgung**
   - Aktualisierung des Patientenstatus bei erfolgreicher Vermittlung
   - Bei Absagen: Dokumentation und neue Kontaktversuche zu anderen Therapeuten
   - Bei ausbleibender Antwort: Nachfassen nach 1 Woche telefonisch

### 3.2 Therapeuten-Kontaktmanagement

#### 3.2.1 E-Mail-Management
- **Frequenzbegrenzung**: Maximal eine E-Mail pro Therapeut pro Woche
- **Sammel-E-Mails**: Bei mehreren Anfragen für einen Therapeuten werden diese in einer E-Mail zusammengefasst
- **Verzögerte Anfragen**: Wenn ein Therapeut bereits in dieser Woche kontaktiert wurde, werden neue Anfragen auf die nächste Woche verschoben
- **Dokumentation**: Alle versendeten E-Mails werden im System dokumentiert
- **Antwortverarbeitung**: E-Mail-Antworten werden manuell im System erfasst

#### 3.2.2 Telefonmanagement
- **Planung**: Telefonate werden gemäß der telefonischen Erreichbarkeit der Therapeuten geplant
- **Frequenzbegrenzung**: Maximal ein Telefonat pro Therapeut pro Woche
- **Sammeltelefonate**: Bei mehreren Anfragen für einen Therapeuten werden diese in einem Telefonat zusammengefasst
- **Dokumentation**: Alle Telefonate werden im System dokumentiert

### 3.3 Webscraping-Prozess

- **Quelle**: https://arztsuche.116117.de/
- **Frequenz**: Tägliches Scraping
- **Datenverarbeitung**:
  - Neue Therapeuten werden dem System hinzugefügt
  - Bestehende Therapeutendaten werden aktualisiert (E-Mail, telefonische Erreichbarkeit etc.)
- **Manuelle Validierung**:
  - Änderungen an bestehenden Therapeutendaten müssen manuell geprüft werden
  - Neue Therapeuten müssen manuell validiert werden

## 4. Funktionale Anforderungen

### 4.1 E-Mail-Management

- **Vorlagen**: Das System stellt standardisierte E-Mail-Vorlagen für verschiedene Szenarien bereit
- **Versand**: E-Mails werden direkt aus dem System über einen lokalen SMTP-Server versendet
- **Dokumentation**: Alle versendeten E-Mails werden mit Datum, Empfänger und Inhalt gespeichert
- **Antworterfassung**: Manuelle Erfassung von E-Mail-Antworten im System
- **Sammel-E-Mails**: Automatische Zusammenfassung mehrerer Anfragen in einer E-Mail

### 4.2 Telefonmanagement

- **Planung**: Telefonate werden basierend auf den Erreichbarkeitszeiträumen der Therapeuten geplant
- **Priorisierung**: Therapeuten ohne E-Mail oder ohne E-Mail-Antwort werden bevorzugt angerufen
- **Dokumentation**: Telefonate werden vor- und nachbereitet (Planung, Durchführung, Ergebnis)
- **Sammeltelefonate**: Automatische Planung von Sammeltelefonaten für mehrere Patienten

### 4.3 Therapeutensperrung

- **Sperrfunktion**: Therapeuten können temporär für neue Anfragen gesperrt werden
- **Sperrgrund**: Bei Sperrung muss ein Grund angegeben werden
- **Transparenz**: Sperrungen werden mit Grund und Datum dokumentiert
- **Automatische Sperrung**: Bei Absagen kann ein Therapeut automatisch für 4 Wochen für denselben Patienten gesperrt werden

### 4.4 Entfernungsberechnung

- **Methode**: OpenStreetMap API
- **Kriterien**: 
  - Für Patienten mit Auto: Fahrzeit mit dem Auto
  - Für Patienten ohne Auto: Fahrzeit mit ÖPNV
- **Filterung**: Automatischer Ausschluss von Therapeuten außerhalb des definierten Radius

## 5. Besondere Regeln und Einschränkungen

- **Kontaktfrequenz**: Ein Therapeut darf maximal einmal pro Woche kontaktiert werden (E-Mail oder Telefon)
- **Datenschutz**: Sensible Patientendaten müssen besonders geschützt werden
- **Erweiterbarkeit**: Das System muss modular und erweiterbar gestaltet sein
- **Lokaler Betrieb**: Die erste Version läuft nur lokal, muss aber für Cloud-Deployment vorbereitet sein
- **Manuelle Prozesse**: In der ersten Version werden viele Prozesse noch manuell durchgeführt (Eingabe von E-Mail-Antworten, Durchführung von Telefonaten)
- **Therapeutenfilterung**: Patienten können Therapeuten von ihrer Suche ausschließen
- **Geschlechterpräferenz**: Patienten können das Geschlecht ihrer Therapeuten auswählen