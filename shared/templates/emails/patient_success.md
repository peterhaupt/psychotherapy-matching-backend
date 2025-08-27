Sehr geehrte{{ 'r Herr' if patient.geschlecht == 'männlich' else ' Frau' }} {{ patient.nachname }},

wir haben einen freien {% if is_group_therapy %}Psychotherapieplatz in einer Gruppe{% else %}Psychotherapieplatz{% endif %} für Sie gefunden bei {{ therapist.titel }} {{ therapist.vorname }} {{ therapist.nachname }}.

Bitte führen Sie folgende Schritte durch:

1. {% if has_email %}Schicken Sie die unten von uns bereits vorformulierte E-Mail an {% if therapist.geschlecht == 'weiblich' %}die Therapeutin{% else %}den Therapeuten{% endif %}{% else %}Rufen Sie {% if therapist.geschlecht == 'weiblich' %}die Therapeutin{% else %}den Therapeuten{% endif %} an{% endif %}, um einen Termin für ein persönliches Erstgespräch zu vereinbaren.
2. {% if has_email %}Setzen Sie uns mit der E-Mail info@curavani.com dabei in Kopie.{% else %}Informieren Sie uns bitte nach dem Telefonat über das Ergebnis.{% endif %}
3. Teilen Sie uns nach dem Erstgespräch mit, ob Sie mit {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}dem Therapeuten{% endif %} einverstanden sind. Ohne eine Rückmeldung von Ihnen gehen wir davon aus, dass Sie mit {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}dem Therapeuten{% endif %} einverstanden sind.
4. {% if therapist.geschlecht == 'weiblich' %}Die Therapeutin{% else %}Der Therapeut{% endif %} gibt uns keine Informationen über den Therapieverlauf mit Ihnen. Wenn also irgendetwas nicht passt und Sie sich Unterstützung von uns wünschen, müssen Sie sich aktiv bei uns melden.

#### Kontaktdaten {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}des Therapeuten{% endif %}:

**{{ therapist.titel }} {{ therapist.vorname }} {{ therapist.nachname }}**  
{{ therapist.strasse }}  
{{ therapist.plz }} {{ therapist.ort }}  
{% if has_phone %}Telefon: {{ therapist.telefon }}  
{% endif %}
{% if has_email %}E-Mail: {{ therapist.email }}{% endif %}

{% if has_email %}
---

#### Bitte schicken Sie folgende E-Mail:

**An:** {{ therapist.email }}  
**CC:** info@curavani.com  
**Betreff:** {% if is_group_therapy %}Gruppentherapieplatz{% else %}Therapieplatz{% endif %} gemäß Absprache mit Curavani

Sehr geehrte{{ 'r Herr' if therapist.geschlecht == 'männlich' else ' Frau' }} {{ therapist.titel }} {{ therapist.nachname }},

wie mit Curavani besprochen, möchte ich gerne {% if is_group_therapy %}an der Gruppentherapie bei Ihnen teilnehmen{% else %}einen Therapieplatz bei Ihnen in Anspruch nehmen{% endif %}. 

Für ein Erstgespräch bin ich wie folgt verfügbar:

{{ availability_formatted }}

Schlagen Sie gerne in dieser Zeit einen Termin für ein Erstgespräch vor. Ich werde zum Termin mein Versicherungskärtchen mitbringen. Wenn Sie vorab noch weitere Informationen benötigen, lassen Sie mich dies gerne wissen. 

Ich freue mich darauf, Sie kennenzulernen.

Mit freundlichen Grüßen

{{ patient.vorname }} {{ patient.nachname }}  

{% if patient.telefon %}Telefon: {{ patient.telefon }}{% endif %}  
{% if patient.email %}E-Mail: {{ patient.email }}{% endif %}

---
{% else %}
#### Telefonische Kontaktaufnahme:

Bitte rufen Sie {{ therapist.titel }} {{ therapist.nachname }} unter der Nummer **{{ therapist.telefon }}** an.

##### Telefonische Erreichbarkeit:
{{ phone_availability_formatted }}

##### Was Sie am Telefon sagen sollten:
- Dass Sie von Curavani vermittelt wurden
- Dass Sie gerne {% if is_group_therapy %}an der Gruppentherapie teilnehmen{% else %}einen Therapieplatz in Anspruch nehmen{% endif %} möchten
- Dass Sie einen Termin für ein Erstgespräch vereinbaren möchten
- Ihre zeitliche Verfügbarkeit für das Erstgespräch

{% endif %}

#### Wichtige Hinweise:

- Bringen Sie zum Erstgespräch unbedingt Ihr **Versicherungskärtchen** mit.
- Das Erstgespräch dient dem gegenseitigen Kennenlernen. Sie können danach entscheiden, ob Sie die Therapie bei {% if therapist.geschlecht == 'weiblich' %}dieser Therapeutin{% else %}diesem Therapeuten{% endif %} beginnen möchten.
- Falls Sie mit {% if therapist.geschlecht == 'weiblich' %}der Therapeutin{% else %}dem Therapeuten{% endif %} nicht zurechtkommen oder das Erstgespräch nicht zustande kommt, melden Sie sich bitte umgehend bei uns.

#### Ihre nächsten Schritte zusammengefasst:

1. **Sofort:** {% if has_email %}E-Mail an {% if therapist.geschlecht == 'weiblich' %}Therapeutin{% else %}Therapeuten{% endif %} senden (mit CC an uns){% else %}{% if therapist.geschlecht == 'weiblich' %}Therapeutin{% else %}Therapeuten{% endif %} anrufen{% endif %}
2. **Nach Terminvereinbarung:** Termin in Ihren Kalender eintragen
3. **Am Tag des Erstgesprächs:** Versicherungskärtchen mitnehmen
4. **Nach dem Erstgespräch:** Rückmeldung an uns

Wenn Sie noch Fragen haben oder Unterstützung benötigen, melden Sie sich jederzeit gerne bei uns.

Wir wünschen Ihnen alles Gute für Ihre Therapie!

Mit freundlichen Grüßen

Ihr Curavani Team