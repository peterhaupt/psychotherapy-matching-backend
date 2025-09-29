# Cookie Consent Implementation Plan - Curavani
Version 1.0 - January 2025

## Overview
Implementation of cookie consent for Curavani website to support:
- Matomo Analytics (with/without cookies)
- Google Ads tracking
- Meta (Facebook/Instagram) Pixel
- Full GDPR compliance

## Phase 1: Legal & Preparation (Offline Work)

### 1.1 Update datenschutz.html

#### [ ] Add new section for Cookie Usage

Add after the current "Datenschutzerklärung" heading:

```html
<h2>Cookie-Richtlinie</h2>

<h3>Was sind Cookies?</h3>
<p>Cookies sind kleine Textdateien, die auf Ihrem Gerät gespeichert werden, wenn Sie unsere Website besuchen. Sie helfen uns, die Website funktionsfähig zu machen, sicherer zu gestalten und Ihre Nutzererfahrung zu verbessern.</p>

<h3>Kategorien von Cookies, die wir verwenden</h3>

<h4>1. Notwendige Cookies</h4>
<p>Diese Cookies sind für den Betrieb unserer Website unerlässlich. Sie können diese Cookies nicht ablehnen, da sie für die Grundfunktionen erforderlich sind.</p>
<table>
  <tr>
    <th>Cookie-Name</th>
    <th>Anbieter</th>
    <th>Zweck</th>
    <th>Speicherdauer</th>
  </tr>
  <tr>
    <td>curavani_cookie_consent</td>
    <td>curavani.com</td>
    <td>Speichert Ihre Cookie-Einstellungen</td>
    <td>1 Jahr</td>
  </tr>
</table>

<h4>2. Analyse-Cookies</h4>
<p>Diese Cookies helfen uns zu verstehen, wie Besucher unsere Website nutzen. Alle Daten werden anonymisiert erhoben.</p>
<table>
  <tr>
    <th>Cookie-Name</th>
    <th>Anbieter</th>
    <th>Zweck</th>
    <th>Speicherdauer</th>
  </tr>
  <tr>
    <td>_pk_id.*</td>
    <td>Matomo</td>
    <td>Unterscheidung von Besuchern</td>
    <td>13 Monate</td>
  </tr>
  <tr>
    <td>_pk_ses.*</td>
    <td>Matomo</td>
    <td>Session-Tracking</td>
    <td>30 Minuten</td>
  </tr>
</table>

<h4>3. Marketing-Cookies</h4>
<p>Diese Cookies werden verwendet, um Werbung relevanter zu gestalten und die Effektivität unserer Werbekampagnen zu messen.</p>
<table>
  <tr>
    <th>Cookie-Name</th>
    <th>Anbieter</th>
    <th>Zweck</th>
    <th>Speicherdauer</th>
  </tr>
  <tr>
    <td>_gcl_*</td>
    <td>Google Ads</td>
    <td>Conversion-Tracking</td>
    <td>90 Tage</td>
  </tr>
  <tr>
    <td>_gac_*</td>
    <td>Google Ads</td>
    <td>Kampagnen-Tracking</td>
    <td>90 Tage</td>
  </tr>
  <tr>
    <td>_fbp</td>
    <td>Meta</td>
    <td>Facebook/Instagram Werbung</td>
    <td>90 Tage</td>
  </tr>
  <tr>
    <td>fr</td>
    <td>Facebook</td>
    <td>Werbe-Tracking</td>
    <td>90 Tage</td>
  </tr>
</table>

<h3>Ihre Cookie-Einstellungen verwalten</h3>
<p>Sie können Ihre Cookie-Einstellungen jederzeit ändern, indem Sie auf <a href="#" data-cc="c-settings">Cookie-Einstellungen</a> in der Fußzeile unserer Website klicken.</p>

<h3>Weitere Informationen</h3>
<p>Für weitere Informationen über die Verarbeitung Ihrer personenbezogenen Daten lesen Sie bitte unsere vollständige Datenschutzerklärung oben.</p>
```

#### [ ] Update existing Matomo section

Replace current Matomo text with:

```html
<h3>5. Webanalyse mit Matomo</h3>
<p>Wir nutzen Matomo, eine Open-Source-Webanalyse-Software, die auf unseren eigenen Servern gehostet wird. Standardmäßig wird Matomo ohne Cookies betrieben. Mit Ihrer Zustimmung zu Analyse-Cookies können wir detailliertere Statistiken erheben, um unsere Website zu verbessern.</p>

<p><strong>Ohne Cookies (Standard):</strong></p>
<ul>
  <li>Anonymisierte IP-Adressen</li>
  <li>Keine personenbezogenen Daten</li>
  <li>Keine geräteübergreifende Verfolgung</li>
</ul>

<p><strong>Mit Cookies (nur mit Ihrer Zustimmung):</strong></p>
<ul>
  <li>Wiederkehrende Besucher erkennen</li>
  <li>Genauere Besuchsstatistiken</li>
  <li>Verbesserte Analyse der Nutzerreisen</li>
</ul>

<p>Rechtsgrundlage: Bei der Cookie-losen Variante ist unser berechtigtes Interesse gem. Art. 6 Abs. 1 lit. f DSGVO die Rechtsgrundlage. Bei der Variante mit Cookies ist Ihre Einwilligung gem. Art. 6 Abs. 1 lit. a DSGVO die Rechtsgrundlage.</p>
```

#### [ ] Add Google Ads section

```html
<h3>6. Google Ads</h3>
<p>Mit Ihrer Zustimmung zu Marketing-Cookies nutzen wir Google Ads für:</p>
<ul>
  <li>Conversion-Tracking: Messung der Effektivität unserer Anzeigen</li>
  <li>Remarketing: Anzeige relevanter Werbung auf anderen Websites</li>
  <li>Zielgruppenerstellung: Erreichen ähnlicher Nutzer</li>
</ul>
<p>Anbieter: Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland</p>
<p>Rechtsgrundlage: Ihre Einwilligung gem. Art. 6 Abs. 1 lit. a DSGVO</p>
<p>Weitere Informationen: <a href="https://policies.google.com/privacy" target="_blank">Google Datenschutzerklärung</a></p>
```

#### [ ] Add Meta Pixel section

```html
<h3>7. Meta Pixel (Facebook/Instagram)</h3>
<p>Mit Ihrer Zustimmung zu Marketing-Cookies nutzen wir den Meta Pixel für:</p>
<ul>
  <li>Messung der Werbekampagnen-Effektivität</li>
  <li>Remarketing auf Facebook und Instagram</li>
  <li>Erstellung von Lookalike Audiences</li>
</ul>
<p>Anbieter: Meta Platforms Ireland Limited, 4 Grand Canal Square, Grand Canal Harbour, Dublin 2, Irland</p>
<p>Rechtsgrundlage: Ihre Einwilligung gem. Art. 6 Abs. 1 lit. a DSGVO</p>
<p>Weitere Informationen: <a href="https://www.facebook.com/privacy/policy" target="_blank">Meta Datenschutzerklärung</a></p>
```

### 1.2 Prepare cookie-config.js file

#### [ ] Create cookie-config.js in root directory

```javascript
window.addEventListener('load', function(){
    // Initialize Cookie Consent
    const cc = initCookieConsent();

    cc.run({
        current_lang: 'de',
        autoclear_cookies: true,
        page_scripts: true,
        cookie_name: 'curavani_cookie_consent',
        cookie_expiration: 365,
        
        // Google Consent Mode v2 integration
        onFirstAction: function(user_preferences, cookie){
            handleGoogleConsent(user_preferences.accepted_categories);
        },

        onChange: function(cookie, changed_preferences){
            handleGoogleConsent(cookie.categories);
            handleMatomoConsent(cookie.categories);
        },

        gui_options: {
            consent_modal: {
                layout: 'cloud',
                position: 'bottom center',
                transition: 'slide',
                swap_buttons: false
            },
            settings_modal: {
                layout: 'box',
                transition: 'slide'
            }
        },

        languages: {
            'de': {
                consent_modal: {
                    title: 'Wir verwenden Cookies! 🍪',
                    description: 'Wir nutzen Cookies und ähnliche Technologien, um Ihre Erfahrung zu verbessern und unsere Therapieplatz-Vermittlung zu optimieren. Mit Ihrer Zustimmung können wir auch Ihre Nutzung analysieren und zielgerichtete Werbung schalten. <button type="button" data-cc="c-settings" class="cc-link">Einstellungen anpassen</button>',
                    primary_btn: {
                        text: 'Alle akzeptieren',
                        role: 'accept_all'
                    },
                    secondary_btn: {
                        text: 'Nur notwendige',
                        role: 'accept_necessary'
                    }
                },
                settings_modal: {
                    title: 'Cookie Einstellungen',
                    save_settings_btn: 'Einstellungen speichern',
                    accept_all_btn: 'Alle akzeptieren',
                    reject_all_btn: 'Alle ablehnen',
                    close_btn_label: 'Schließen',
                    cookie_table_headers: [
                        {col1: 'Name'},
                        {col2: 'Domain'},
                        {col3: 'Ablauf'},
                        {col4: 'Beschreibung'}
                    ],
                    blocks: [
                        {
                            title: 'Cookie-Verwendung 📢',
                            description: 'Wir verwenden Cookies, um die grundlegenden Funktionen der Website zu gewährleisten und Ihre Online-Erfahrung zu verbessern. Für jede Kategorie können Sie sich jederzeit entscheiden, ob Sie diese zulassen möchten. Weitere Details finden Sie in unserer <a href="/datenschutz.html" class="cc-link">Datenschutzerklärung</a>.'
                        }, 
                        {
                            title: 'Notwendige Cookies',
                            description: 'Diese Cookies sind für die Grundfunktionen der Website unerlässlich.',
                            toggle: {
                                value: 'necessary',
                                enabled: true,
                                readonly: true
                            },
                            cookie_table: [
                                {
                                    col1: 'curavani_cookie_consent',
                                    col2: 'curavani.com',
                                    col3: '1 Jahr',
                                    col4: 'Speichert Ihre Cookie-Einstellungen'
                                }
                            ]
                        }, 
                        {
                            title: 'Analyse-Cookies',
                            description: 'Diese Cookies helfen uns zu verstehen, wie Besucher mit unserer Website interagieren.',
                            toggle: {
                                value: 'analytics',
                                enabled: false,
                                readonly: false
                            },
                            cookie_table: [
                                {
                                    col1: '_pk_id.*',
                                    col2: 'curavani.com',
                                    col3: '13 Monate',
                                    col4: 'Matomo - Unterscheidung von Besuchern'
                                },
                                {
                                    col1: '_pk_ses.*',
                                    col2: 'curavani.com',
                                    col3: '30 Minuten',
                                    col4: 'Matomo - Session-Tracking'
                                }
                            ]
                        }, 
                        {
                            title: 'Marketing-Cookies',
                            description: 'Diese Cookies werden für zielgerichtete Werbung und Kampagnen-Messung verwendet.',
                            toggle: {
                                value: 'marketing',
                                enabled: false,
                                readonly: false
                            },
                            cookie_table: [
                                {
                                    col1: '_gcl_*',
                                    col2: 'curavani.com',
                                    col3: '90 Tage',
                                    col4: 'Google Ads - Conversion-Tracking'
                                },
                                {
                                    col1: '_fbp',
                                    col2: 'curavani.com',
                                    col3: '90 Tage',
                                    col4: 'Meta - Facebook/Instagram Werbung'
                                }
                            ]
                        }
                    ]
                }
            }
        }
    });
});

// Helper functions
function handleGoogleConsent(categories) {
    if(typeof gtag === 'function') {
        gtag('consent', 'update', {
            'analytics_storage': categories.includes('analytics') ? 'granted' : 'denied',
            'ad_storage': categories.includes('marketing') ? 'granted' : 'denied',
            'ad_user_data': categories.includes('marketing') ? 'granted' : 'denied',
            'ad_personalization': categories.includes('marketing') ? 'granted' : 'denied'
        });
    }
}

function handleMatomoConsent(categories) {
    if(typeof _paq !== 'undefined') {
        if(categories.includes('analytics')) {
            _paq.push(['rememberCookieConsentGiven']);
            _paq.push(['setCookieConsentGiven']);
        } else {
            _paq.push(['forgetCookieConsentGiven']);
            _paq.push(['deleteCookies']);
        }
    }
}
```

### 1.3 Document current state

#### [ ] List all HTML pages that need updates:
- [ ] index.html
- [ ] patienten.html
- [ ] therapeuten.html
- [ ] service_buchen.html
- [ ] email_bestaetigen.html
- [ ] verify_token.php
- [ ] impressum.html
- [ ] datenschutz.html
- [ ] dankeschoen.html

## Phase 2: Test Implementation

### 2.1 Test on service_buchen.html first

#### [ ] Add Cookie Consent library before </body>

```html
<!-- Cookie Consent by Orest Bida -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orestbida/cookieconsent@3.0.1/dist/cookieconsent.css">
<script defer src="https://cdn.jsdelivr.net/gh/orestbida/cookieconsent@3.0.1/dist/cookieconsent.umd.js"></script>
<script defer src="cookie-config.js"></script>
```

#### [ ] Modify existing Matomo code

Replace current Matomo script with:

```html
<!-- Matomo with Cookie Consent Support -->
<script>
var _paq = window._paq = window._paq || [];
// Start without cookies by default
_paq.push(['disableCookies']);
_paq.push(['trackPageView']);
_paq.push(['enableLinkTracking']);
(function() {
    var u="//analytics.curavani.com/";
    _paq.push(['setTrackerUrl', u+'matomo.php']);
    _paq.push(['setSiteId', '1']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
})();
</script>
```

#### [ ] Modify existing Google Ads code

Replace current Google script with:

```html
<!-- Google Ads with Consent Mode v2 -->
<script>
// Setup dataLayer and gtag
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}

// Default consent state (before user interaction)
gtag('consent', 'default', {
    'analytics_storage': 'denied',
    'ad_storage': 'denied',
    'ad_user_data': 'denied',
    'ad_personalization': 'denied',
    'wait_for_update': 500
});

// Initialize gtag
gtag('js', new Date());
gtag('config', 'AW-17609758925');
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-17609758925"></script>
```

#### [ ] Add footer link for cookie settings

```html
<footer>
    <div>
        <p>&copy; 2025 Curavani | Die Plattform zur Vermittlung von Psychotherapieplätzen</p>
        <div class="footer-links">
            <a href="impressum.html">Impressum</a>
            <a href="datenschutz.html">Datenschutz</a>
            <a href="#" data-cc="c-settings">Cookie-Einstellungen</a>
        </div>
    </div>
</footer>
```

### 2.2 Testing Checklist

#### [ ] Test consent modal appearance
- Opens on first visit
- Text is correct and in German
- Both buttons work

#### [ ] Test cookie categories
- Necessary cookies always enabled
- Analytics can be toggled
- Marketing can be toggled

#### [ ] Test Matomo behavior
- Without consent: No Matomo cookies set
- With analytics consent: _pk_id and _pk_ses cookies present

#### [ ] Test Google Ads behavior
- Check Network tab for consent mode signals
- Verify ad_storage status in dataLayer

## Phase 3: Full Rollout

### 3.1 Apply to all pages

#### [ ] For each HTML page, add:

1. Cookie Consent CSS and JS (before </body>)
2. Modified Matomo script
3. Modified Google Ads script
4. Cookie settings link in footer

### 3.2 Add Meta Pixel

#### [ ] Get Meta Pixel ID from Facebook Business Manager

#### [ ] Add Meta Pixel code to all pages

Add AFTER the cookie consent script:

```html
<!-- Meta Pixel Code (only loads with marketing consent) -->
<script type="text/plain" data-cookiecategory="marketing">
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'YOUR_PIXEL_ID_HERE'); // TODO: Replace with actual Pixel ID
fbq('track', 'PageView');
</script>
<noscript>
<img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id=YOUR_PIXEL_ID_HERE&ev=PageView&noscript=1"/>
</noscript>
```

### 3.3 Add conversion tracking events

#### [ ] On verify_token.php success page

```javascript
// Google Ads conversion (only with consent)
if(typeof gtag === 'function') {
    gtag('event', 'conversion', {
        'send_to': 'AW-17609758925/CONVERSION_LABEL', // TODO: Add conversion label
        'value': <?php echo $selected_price; ?>,
        'currency': 'EUR'
    });
}

// Meta conversion (only if fbq exists)
if(typeof fbq === 'function') {
    fbq('track', 'Purchase', {
        value: <?php echo $selected_price; ?>,
        currency: 'EUR',
        content_type: 'product',
        content_ids: ['therapy_service']
    });
}
```

## Phase 4: Verification

### 4.1 Browser Testing

#### [ ] Test in different browsers:
- Chrome
- Firefox
- Safari
- Edge

#### [ ] Test scenarios:
- First-time visitor (banner appears)
- Accept all cookies
- Reject all cookies
- Custom selection
- Change settings later

### 4.2 Tool Verification

#### [ ] Matomo:
- Check real-time visitor log
- Verify cookie vs cookieless tracking
- Check if returning visitors work with cookies

#### [ ] Google Ads:
- Check Tag Assistant
- Verify conversions are tracked
- Check consent mode in Tag Manager preview

#### [ ] Meta Pixel:
- Use Facebook Pixel Helper extension
- Check Events Manager
- Verify PageView and Purchase events

### 4.3 Legal Compliance Check

#### [ ] GDPR Requirements:
- No cookies before consent ✓
- Easy to reject as to accept ✓
- Granular control over categories ✓
- Cookie policy accessible ✓
- Settings can be changed anytime ✓

## Additional Notes

### Custom Styling
If you want to customize the appearance, create a file `cookie-consent-custom.css`:

```css
/* Custom colors for Curavani brand */
.cc-window.cc-banner {
    background: #065f46;  /* Curavani green */
}

.cc-btn.cc-btn-primary {
    background: #10b981;
    border-color: #10b981;
}

.cc-btn.cc-btn-primary:hover {
    background: #059669;
    border-color: #059669;
}
```

### Debugging Tips

1. Clear cookies and localStorage to test first-visit experience
2. Use browser DevTools Network tab to verify script loading
3. Check Console for any JavaScript errors
4. Use browser extensions:
   - EditThisCookie (Chrome)
   - Facebook Pixel Helper
   - Tag Assistant Legacy (by Google)

### Conversion Tracking Labels

Remember to add these from your ad platforms:
- Google Ads Conversion Label: Get from Google Ads > Tools > Conversions
- Meta Pixel ID: Get from Events Manager > Data Sources > Your Pixel

### Performance Considerations

The cookie consent adds approximately:
- 15KB JavaScript (minified)
- 8KB CSS (minified)
- Loads asynchronously, doesn't block page rendering

### Support Resources

- CookieConsent Documentation: https://github.com/orestbida/cookieconsent
- Google Consent Mode: https://developers.google.com/tag-platform/security/guides/consent
- Meta Pixel Setup: https://developers.facebook.com/docs/meta-pixel

## Checklist Summary

### Pre-Launch
- [ ] datenschutz.html updated
- [ ] cookie-config.js created
- [ ] All pages identified

### Implementation
- [ ] Test page working
- [ ] Matomo configured
- [ ] Google Ads configured
- [ ] Meta Pixel added
- [ ] All pages updated

### Verification
- [ ] Cross-browser tested
- [ ] All tools tracking correctly
- [ ] GDPR compliant
- [ ] Documentation complete

## Estimated Timeline

- Phase 1: 2-3 hours (legal text, configuration)
- Phase 2: 1-2 hours (test implementation)
- Phase 3: 2-3 hours (full rollout)
- Phase 4: 1-2 hours (testing & verification)

**Total: 6-10 hours**

---

*Document created: January 2025*  
*Last updated: January 2025*  
*Version: 1.0*
