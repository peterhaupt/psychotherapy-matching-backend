**Betreff:** [Kontaktformular] Anfrage von {{ vorname }} {{ nachname }}

**Neue Nachricht über das Kontaktformular**

---

## Kontaktdaten

**Name:** {{ vorname }} {{ nachname }}  
**E-Mail:** {{ email }}  
**Telefon:** {{ telefon }}  

## Nachricht

{% if nachricht %}
{{ nachricht }}
{% else %}
*(Keine Nachricht eingegeben)*
{% endif %}

---

## Metadaten

**Zeitpunkt:** {{ timestamp }}  
**Quelle:** {{ source|default('curavani.com/patienten.html') }}  
**IP-Adresse:** {{ ip_address }}  
**Request-ID:** {{ request_id }}  
**Umgebung:** {{ environment }}  

---

*Diese Nachricht wurde automatisch vom Kontaktformular-System weitergeleitet.*  
*Der Absender erwartet eine Antwort an die angegebene E-Mail-Adresse: {{ email }}*