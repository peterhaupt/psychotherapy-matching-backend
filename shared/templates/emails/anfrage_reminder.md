{% if therapist.anrede == "Frau" -%}
Sehr geehrte Frau
{%- elif therapist.anrede == "Herr" -%}
Sehr geehrter Herr
{%- else -%}
Sehr geehrte Damen und Herren
{%- endif %} {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.nachname }},

wir haben Ihnen vor {{ days_since_sent }} Tagen eine E-Mail geschickt, weil wir für {{ patient_count }} Patienten auf der Suche nach Psychotherapieplätzen sind.

{% if not therapist.ueber_curavani_informiert %}
Curavani ist eine Vermittlungsplattform, die Patienten bei der Suche nach Psychotherapieplätzen unterstützt. Für Sie bedeutet dies:
1. Sie erhalten nur vorqualifizierte Anfragen.
2. Sie erhalten gebündelte Anfragen für mehrere Patienten.
3. Wenn Sie möchten, übernehmen wir die Organisation der Erstgespräche.
4. Sie können uns Ihre Schwerpunkte mitteilen. Dann berücksichtigen wir dies bei zukünftigen Anfragen.

Mehr Informationen finden Sie unter [www.curavani.com/therapeuten.html](https://www.curavani.com/therapeuten.html).
{% endif %}

Können Sie für einen oder mehrere dieser Patienten innerhalb der nächsten drei Wochen ein Erstgespräch anbieten? Außerdem ist uns wichtig, dass bei entsprechender Passung die Therapie innerhalb von weiteren sechs Wochen nach dem Erstgespräch beginnen kann.

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