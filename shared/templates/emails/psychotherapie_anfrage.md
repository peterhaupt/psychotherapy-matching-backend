{% if therapist.anrede == "Frau" -%}
Sehr geehrte Frau
{%- elif therapist.anrede == "Herr" -%}
Sehr geehrter Herr
{%- else -%}
Sehr geehrte Damen und Herren
{%- endif %} {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.nachname }},

wir sind auf der Suche nach Psychotherapieplätzen für {{ patient_count }} Patienten. Können Sie hierfür ein oder mehrere Erstgespräche innerhalb der nächsten drei Wochen anbieten? Außerdem ist uns wichtig, dass bei entsprechender Passung die Therapie innerhalb von weiteren sechs Wochen nach dem Erstgespräch beginnen kann.

Vielen Dank für eine kurze Rückmeldung.

Hier die wichtigsten Infos zu den Patienten, aus Datenschutzgründen hier ohne Namen. Wenn Sie einen Platz anbieten können, stellen wir Ihnen für diese Patienten selbstverständlich auch den vollen Namen zur Verfügung.

{% for patient in patients %}

**Patienten-ID:** {{ patient.id }}
**Alter:** {{ patient.age }} Jahre
**Geschlecht:** {{ patient.geschlecht }}  
**Symptome:** {{ patient.symptome|join(', ')|default("Nicht angegeben") }}  
**Krankenversicherung:** {{ patient.krankenkasse|default("Nicht angegeben") }}  
**Erfahrung mit Psychotherapie:** {% if patient.erfahrung_mit_psychotherapie %}Ja{% else %}Nein{% endif %}
{%- if patient.erfahrung_mit_psychotherapie and patient.letzte_sitzung_vorherige_psychotherapie %}  
**Letzte Sitzung vorherige Psychotherapie:** {{ patient.letzte_sitzung_vorherige_psychotherapie }}
{%- endif %}  
**Offen für Gruppentherapie:** {% if patient.offen_fuer_gruppentherapie %}Ja{% else %}Nein{% endif %}  
**Zeitliche Verfügbarkeit:**
{{ patient.zeitliche_verfuegbarkeit_formatted|default("Nicht angegeben") }}

{% endfor %}

Wenn Sie noch mehr Informationen benötigen, stellen wir Ihnen diese ebenfalls gerne zur Verfügung. Schreiben Sie uns einfach, was Sie benötigen.

Mit freundlichen Grüßen

**Peter Haupt**

Telefon: +49 151 46359691

{% if not therapist.ueber_curavani_informiert %}
**PS:** Curavani ist eine Vermittlungsplattform, die Patienten bei der Suche nach Psychotherapieplätzen unterstützt. Wir übernehmen für Patienten die Kontaktaufnahme mit Therapeuten und stellen sicher, dass nur qualifizierte Anfragen bei Ihnen ankommen. Diesen Service bieten wir in Kooperation mit zahlreichen Hausarztpraxen an.
{% endif %}