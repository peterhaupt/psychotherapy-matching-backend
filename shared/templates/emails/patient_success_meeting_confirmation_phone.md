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

1. **Bitte bestätigen Sie den Termin telefonisch** bei {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}dem Therapeuten{% endif %}.
2. Informieren Sie uns bitte nach dem Telefonat über die Bestätigung.
3. Teilen Sie uns nach dem Erstgespräch mit, ob Sie mit {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}dem Therapeuten{% endif %} einverstanden sind. Ohne eine Rückmeldung von Ihnen gehen wir davon aus, dass Sie mit {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}dem Therapeuten{% endif %} einverstanden sind.
4. {% if therapist.geschlecht == 'weiblich' %}Die Therapeutin{% else %}Der Therapeut{% endif %} gibt uns keine Informationen über den Therapieverlauf mit Ihnen. Wenn also irgendetwas nicht passt und Sie sich Unterstützung von uns wünschen, müssen Sie sich aktiv bei uns melden.

#### Kontaktdaten {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}des Therapeuten{% endif %}:

**{% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.vorname }} {{ therapist.nachname }}**  
{{ therapist.strasse }}  
{{ therapist.plz }} {{ therapist.ort }}  
Telefon: {{ therapist.telefon }}  
{% if therapist.email %}E-Mail: {{ therapist.email }}{% endif %}

{% if has_pdf_forms %}
#### Wichtige Formulare:

Bitte füllen Sie die beigefügten Formulare aus und bringen Sie diese zum Erstgespräch mit:
{% for form in pdf_forms %}
- {{ form }}
{% endfor %}
{% endif %}

#### Telefonische Terminbestätigung:

Bitte rufen Sie {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.nachname }} unter der Nummer **{{ therapist.telefon }}** an, um den Termin zu bestätigen.

##### Telefonische Erreichbarkeit:
{{ phone_availability_formatted }}

##### Was Sie am Telefon sagen sollten:

- Sich mit Namen vorstellen: "{{ patient.vorname }} {{ patient.nachname }}"
- Erwähnen, dass Curavani einen Termin vereinbart hat
- Termin bestätigen: **{{ meeting_date }} um {{ meeting_time }} Uhr**
- Bestätigen, dass Sie pünktlich erscheinen werden
- Erwähnen, dass Sie Ihr Versicherungskärtchen mitbringen
{% if has_pdf_forms %}- Erwähnen, dass Sie die ausgefüllten Formulare mitbringen{% endif %}
- Sich für den Termin bedanken

#### Wichtige Hinweise:

- Das Erstgespräch dient dem gegenseitigen Kennenlernen. Sie können danach entscheiden, ob Sie die Therapie bei {% if therapist.geschlecht == 'weiblich' %}dieser Therapeutin{% else %}diesem Therapeuten{% endif %} beginnen möchten.
- Bringen Sie zum Erstgespräch unbedingt Ihr **Versicherungskärtchen** mit.
{% if has_pdf_forms %}- Bringen Sie die ausgefüllten Formulare zum Erstgespräch mit.
{% endif %}

#### Ihre nächsten Schritte zusammengefasst:

1. **Während der nächsten telefonischen Erreichbarkeit:** {% if therapist.geschlecht == 'weiblich' %}Therapeutin{% else %}Therapeuten{% endif %} anrufen und Termin bestätigen (siehe Zeiten oben)
2. **Nach dem Telefonat:** Curavani über die Bestätigung informieren
{% if has_pdf_forms %}3. **Vor dem Termin:** Formulare ausfüllen
4. **Termin:** In Ihren Kalender eintragen
5. **Am {{ meeting_date }} um {{ meeting_time }}:** Pünktlich mit Versicherungskärtchen und Formularen erscheinen
6. **Nach dem Erstgespräch:** Rückmeldung an uns
{% else %}3. **Termin:** In Ihren Kalender eintragen
4. **Am {{ meeting_date }} um {{ meeting_time }}:** Pünktlich mit Versicherungskärtchen erscheinen
5. **Nach dem Erstgespräch:** Rückmeldung an uns
{% endif %}

Wenn Sie noch Fragen haben oder Unterstützung benötigen, melden Sie sich jederzeit gerne bei uns.

Wir wünschen Ihnen alles Gute für Ihre Therapie!

Mit freundlichen Grüßen

Ihr Curavani Team