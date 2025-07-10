{% if therapist.anrede == "Frau" -%}
Sehr geehrte Frau
{%- elif therapist.anrede == "Herr" -%}
Sehr geehrter Herr
{%- else -%}
Sehr geehrte Damen und Herren
{%- endif %} {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.nachname }},

ich bin auf der Suche nach Psychotherapieplätzen für {{ patient_count }} Patienten. Können Sie hier kurzfristig einen oder mehrere Plätze anbieten? Vielen Dank für eine kurze Info.

Hier die wichtigsten Infos zu den Patienten, aus Datenschutzgründen hier ohne Namen. Wenn Sie einen Platz anbieten können, stelle ich Ihnen für diese Patienten selbstverständlich auch den vollen Namen zur Verfügung.

{% for patient in patients %}

**Patienten-ID:** {{ patient.id }}  
**Geschlecht:** {{ patient.geschlecht }}  
**Diagnose:** {{ patient.diagnose|default("Nicht angegeben") }}  
**Symptome:** {{ patient.symptome|default("Nicht angegeben") }}  
**Krankenversicherung:** {{ patient.krankenkasse|default("Nicht angegeben") }}  
**Alter:** {{ patient.age }} Jahre  
**Erfahrung mit Psychotherapie:** {% if patient.erfahrung_mit_psychotherapie %}Ja{% else %}Nein{% endif %}
{%- if patient.erfahrung_mit_psychotherapie and patient.letzte_sitzung_vorherige_psychotherapie %}  
**Letzte Sitzung vorherige Psychotherapie:** {{ patient.letzte_sitzung_vorherige_psychotherapie }}
{%- endif %}  
**Offen für Gruppentherapie:** {% if patient.offen_fuer_gruppentherapie %}Ja{% else %}Nein{% endif %}  
**Zeitliche Verfügbarkeit:**
{{ patient.zeitliche_verfuegbarkeit_formatted|default("Nicht angegeben") }}

{% endfor %}

Wenn Sie noch mehr Informationen benötigen, stelle ich diese ebenfalls gerne zur Verfügung. Schreiben Sie mir einfach, was Sie benötigen.

Mit freundlichen Grüßen

**Peter Haupt**

Telefon: +49 151 46359691

{% if not therapist.ueber_curavani_informiert %}
**PS:** Curavani ist eine Vermittlungsplattform, die Patienten bei der Suche nach Psychotherapieplätzen unterstützt. Wir übernehmen für die Patienten die Kontaktaufnahme mit Therapeuten und stellen sicher, dass nur qualifizierte Anfragen bei Ihnen ankommen. Diesen Service bieten wir in Kooperation mit zahlreichen Hausarztpraxen an.
{% endif %}