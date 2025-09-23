Sehr geehrte{% if patient.anrede == "Herr" %}r Herr{% elif patient.anrede == "Frau" %} Frau{% else %}r/geehrte{% endif %} {{ patient.nachname }},

Ihre Zahlung ist bei uns eingegangen - vielen Dank!

**Zahlungsreferenz:** {{ patient.zahlungsreferenz }}

{% if patient.offen_fuer_gruppentherapie -%}
Ab sofort suchen wir aktiv einen **Gruppentherapieplatz** für Sie.
{%- else -%}
Ab sofort suchen wir aktiv einen **Einzeltherapieplatz** für Sie.
{%- endif %}

Wir kontaktieren nun Therapeuten in Ihrer Nähe und melden uns bei Ihnen, sobald wir einen passenden Platz gefunden haben.

Bei Fragen erreichen Sie uns unter info@curavani.com

Mit freundlichen Grüßen
  
Ihr Curavani Team