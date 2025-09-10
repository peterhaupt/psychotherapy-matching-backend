Sehr geehrte{{ 'r Herr' if patient.geschlecht == 'männlich' else ' Frau' }} {{ patient.nachname }},

wir haben einen freien {% if is_group_therapy %}Psychotherapieplatz in einer Gruppe{% else %}Psychotherapieplatz{% endif %} für Sie gefunden und bereits einen Termin für das Erstgespräch zum Kennenlernen {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}des Therapeuten{% endif %} vereinbart.

#### Ihr Erstgespräch:

**Datum:** {{ meeting_date }}  
**Uhrzeit:** {{ meeting_time }}  
**Ort:** Praxis {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.nachname }}  
{{ therapist.strasse }}  
{{ therapist.plz }} {{ therapist.ort }}

**Bei:** {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.vorname }} {{ therapist.nachname }}

#### Wichtige nächste Schritte:

1. **Bitte bestätigen Sie den Termin per E-Mail** an {% if therapist.geschlecht == 'weiblich' %}die Therapeutin{% else %}den Therapeuten{% endif %}.
2. Setzen Sie uns mit der E-Mail info@curavani.com dabei in Kopie.
3. Teilen Sie uns nach dem Erstgespräch mit, ob Sie mit {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}dem Therapeuten{% endif %} einverstanden sind. Ohne eine Rückmeldung von Ihnen gehen wir davon aus, dass Sie mit {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}dem Therapeuten{% endif %} einverstanden sind.
4. {% if therapist.geschlecht == 'weiblich' %}Die Therapeutin{% else %}Der Therapeut{% endif %} gibt uns keine Informationen über den Therapieverlauf mit Ihnen. Wenn also irgendetwas nicht passt und Sie sich Unterstützung von uns wünschen, müssen Sie sich aktiv bei uns melden.

#### Kontaktdaten {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}des Therapeuten{% endif %}:

**{% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.vorname }} {{ therapist.nachname }}**  
{{ therapist.strasse }}  
{{ therapist.plz }} {{ therapist.ort }}  
{% if therapist.telefon %}Telefon: {{ therapist.telefon }}  
{% endif %}
E-Mail: {{ therapist.email }}

{% if has_pdf_forms %}
#### Wichtige Formulare:

Die folgenden Formulare sind dieser E-Mail beigefügt. Bitte füllen Sie diese aus und senden Sie sie mit Ihrer Bestätigungs-E-Mail an {% if therapist.geschlecht == 'weiblich' %}die Therapeutin{% else %}den Therapeuten{% endif %} zurück:
{% for form in pdf_forms %}
- {{ form }}
{% endfor %}
{% endif %}

---

#### Bitte schicken Sie folgende Bestätigungs-E-Mail:

**An:** {{ therapist.email }}  
**CC:** info@curavani.com  
**Betreff:** Terminbestätigung Erstgespräch am {{ meeting_date }}

Sehr geehrte{{ 'r Herr' if therapist.geschlecht == 'männlich' else ' Frau' }} {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.nachname }},

vielen Dank, dass Sie mir einen Termin für ein Erstgespräch anbieten können.

Hiermit bestätige ich den Termin:
- **Datum:** {{ meeting_date }}
- **Uhrzeit:** {{ meeting_time }}
- **Ort:** Ihre Praxis in {{ therapist.ort }}

Ich werde pünktlich erscheinen und mein Versicherungskärtchen mitbringen. {% if has_pdf_forms %}Die ausgefüllten Formulare sind im Anhang dieser E-Mail.{% endif %}

Ich freue mich darauf, Sie kennenzulernen.

Mit freundlichen Grüßen

{{ patient.vorname }} {{ patient.nachname }}  

{% if patient.telefon %}Telefon: {{ patient.telefon }}{% endif %}  
{% if patient.email %}E-Mail: {{ patient.email }}{% endif %}

---

#### Wichtige Hinweise:

- Das Erstgespräch dient dem gegenseitigen Kennenlernen. Sie können danach entscheiden, ob Sie die Therapie bei {% if therapist.geschlecht == 'weiblich' %}dieser Therapeutin{% else %}diesem Therapeuten{% endif %} beginnen möchten.
- Bringen Sie zum Erstgespräch unbedingt Ihr **Versicherungskärtchen** mit.

#### Ihre nächsten Schritte zusammengefasst:

1. **Sofort:** {% if has_pdf_forms %}Formulare ausfüllen und {% endif %}Bestätigungs-E-Mail an {% if therapist.geschlecht == 'weiblich' %}Therapeutin{% else %}Therapeuten{% endif %} senden (mit CC an uns)
2. **Termin:** In Ihren Kalender eintragen
3. **Am {{ meeting_date }} um {{ meeting_time }}:** Pünktlich mit Versicherungskärtchen erscheinen
4. **Nach dem Erstgespräch:** Rückmeldung an uns

Wenn Sie noch Fragen haben oder Unterstützung benötigen, melden Sie sich jederzeit gerne bei uns.

Wir wünschen Ihnen alles Gute für Ihre Therapie!

Mit freundlichen Grüßen

Ihr Curavani Team