Sehr geehrte{{ 'r Herr' if patient.geschlecht == 'männlich' else ' Frau' }} {{ patient.nachname }},

wir haben einen freien {% if is_group_therapy %}Psychotherapieplatz in einer Gruppe{% else %}Psychotherapieplatz{% endif %} für Sie gefunden bei {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.vorname }} {{ therapist.nachname }}.

Bitte führen Sie folgende Schritte durch:

1. Rufen Sie {% if therapist.geschlecht == 'weiblich' %}die Therapeutin{% else %}den Therapeuten{% endif %} an, um einen Termin für ein persönliches Erstgespräch zu vereinbaren.
2. Informieren Sie uns bitte nach dem Telefonat über das Ergebnis.
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

#### Telefonische Kontaktaufnahme:

Bitte rufen Sie {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.nachname }} unter der Nummer **{{ therapist.telefon }}** an.

##### Telefonische Erreichbarkeit:
{{ phone_availability_formatted }}

##### Was Sie am Telefon sagen sollten:
- Sich mit Namen vorstellen
- Erwähnen, dass Sie von Curavani vermittelt wurden
- Mitteilen, dass Sie gerne {% if is_group_therapy %}an der Gruppentherapie teilnehmen{% else %}einen Therapieplatz in Anspruch nehmen{% endif %} möchten
- Um einen Termin für ein Erstgespräch bitten
- Ihre zeitliche Verfügbarkeit nennen (siehe unten)

##### Ihre zeitliche Verfügbarkeit für das Erstgespräch:
{{ availability_formatted }}

#### Wichtige Hinweise:

- Bringen Sie zum Erstgespräch unbedingt Ihr **Versicherungskärtchen** mit.
{% if has_pdf_forms %}- Bringen Sie die ausgefüllten Formulare zum Erstgespräch mit.
{% endif %}- Das Erstgespräch dient dem gegenseitigen Kennenlernen. Sie können danach entscheiden, ob Sie die Therapie bei {% if therapist.geschlecht == 'weiblich' %}dieser Therapeutin{% else %}diesem Therapeuten{% endif %} beginnen möchten.
- Falls das Erstgespräch nicht zustande kommt, melden Sie sich bitte umgehend bei uns.

#### Ihre nächsten Schritte zusammengefasst:

1. **Während der nächsten telefonischen Erreichbarkeit:** {% if therapist.geschlecht == 'weiblich' %}Therapeutin{% else %}Therapeuten{% endif %} anrufen (siehe Zeiten oben)
2. **Nach dem Telefonat:** Curavani über das Ergebnis informieren
{% if has_pdf_forms %}3. **Vor dem Termin:** Formulare ausfüllen
4. **Nach Terminvereinbarung:** Termin in Ihren Kalender eintragen
5. **Am Tag des Erstgesprächs:** Versicherungskärtchen und ausgefüllte Formulare mitnehmen
6. **Nach dem Erstgespräch:** Rückmeldung an uns
{% else %}3. **Nach Terminvereinbarung:** Termin in Ihren Kalender eintragen
4. **Am Tag des Erstgesprächs:** Versicherungskärtchen mitnehmen
5. **Nach dem Erstgespräch:** Rückmeldung an uns
{% endif %}

Wenn Sie noch Fragen haben oder Unterstützung benötigen, melden Sie sich jederzeit gerne bei uns.

Wir wünschen Ihnen alles Gute für Ihre Therapie!

Mit freundlichen Grüßen

Ihr Curavani Team