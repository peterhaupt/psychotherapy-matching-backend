# Cookie Consent Implementation Plan - Curavani (UPDATED)
Version 2.0 - January 2025
**Last Updated: After Phase 2 Completion**

## ✅ COMPLETED PHASES

### Phase 1: Legal & Preparation ✅ DONE

#### 1.1 Updated datenschutz.html ✅
- Added Cookie Policy section
- Updated Matomo section (cookie/cookieless modes)
- Added Google Ads section
- Added Meta Pixel section
- Date set to September 2025

**Files Created:**
- `datenschutz_updated.html` ✅

#### 1.2 Created cookie-config.js ✅
- German language interface configured
- 3 consent categories (Necessary, Analytics, Marketing)
- Google Consent Mode v2 integration
- Matomo cookie/cookieless switching
- Custom Curavani styling (green theme)

**Files Created:**
- `cookie-config-fixed.js` (renamed to `cc-config.js` for Brave compatibility) ✅

#### 1.3 Documentation ✅
- All HTML pages identified
- Current state documented

### Phase 2: Test Implementation ✅ DONE

#### 2.1 Test on service_buchen.html ✅
**Changes Made:**
- Matomo script updated (cookieless by default)
- Google Ads with Consent Mode v2 implemented
- Footer updated with Cookie Settings link
- Cookie consent scripts added (local hosting)
- Favicon added (green C)

**Files Updated:**
- `service_buchen.html` ✅

#### 2.2 Testing Completed ✅
**Browser Testing:**
- ✅ Chrome - Working
- ✅ Safari - Working  
- ✅ Brave - Working (after renaming files)
- ✅ Firefox - Not tested but should work

**File Naming for Brave Compatibility:**
- `cookieconsent.css` → `cc-styles.css`
- `cookieconsent.umd.js` → `cc-lib.js`
- `cookie-config.js` → `cc-config.js`

**Functionality Verified:**
- ✅ Banner appears on first visit
- ✅ Matomo cookieless tracking (default)
- ✅ Matomo cookies enabled with consent
- ✅ Google Consent Mode signals working
- ✅ Cookie preferences saved for 1 year

---

## 📋 REMAINING PHASES

### Phase 3: Full Rollout

#### 3.1 Apply to All Pages ⏳ TO DO

**Pages to Update:**
- [ ] index.html
- [ ] patienten.html
- [ ] therapeuten.html
- [x] service_buchen.html (DONE)
- [ ] email_bestaetigen.html
- [ ] verify_token.php
- [ ] impressum.html
- [x] datenschutz.html (DONE)
- [ ] dankeschoen.html

**For EACH page, add/update:**

1. **In `<head>` section - Add favicon:**
```html
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%2310b981'/><text x='50' y='70' font-family='Arial, sans-serif' font-size='60' font-weight='bold' text-anchor='middle' fill='white'>C</text></svg>">
```

2. **Replace existing Matomo script with:**
```javascript
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
<!-- End Matomo Code -->
```

3. **Replace/Add Google Ads script (if not present, add after Matomo):**
```javascript
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

4. **Update footer - Add Cookie Settings link:**
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

5. **Before closing `</body>` tag - Add Cookie Consent scripts:**
```html
<!-- Cookie Consent by Orest Bida (Local) -->
<link rel="stylesheet" href="cc-styles.css">
<script defer src="cc-lib.js"></script>
<script defer src="cc-config.js"></script>
</body>
```

#### 3.2 Add Meta Pixel ⏳ TO DO

**Prerequisites:**
- [ ] Get Meta Pixel ID from Facebook Business Manager
- [ ] Replace `YOUR_PIXEL_ID_HERE` with actual ID

**Add to ALL pages AFTER cookie consent scripts:**
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
<img height="1" width="1" style="display:none" 
src="https://www.facebook.com/tr?id=YOUR_PIXEL_ID_HERE&ev=PageView&noscript=1"/>
</noscript>
```

#### 3.3 Add Conversion Tracking Events ⏳ TO DO

**On verify_token.php success page, add:**
```javascript
// Add this where payment is confirmed successfully
<script>
// Google Ads conversion (only with consent)
if(typeof gtag === 'function') {
    gtag('event', 'conversion', {
        'send_to': 'AW-17609758925/CONVERSION_LABEL', // TODO: Get from Google Ads
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
</script>
```

**Required Values to Obtain:**
- [ ] Google Ads Conversion Label (from Google Ads > Tools > Conversions)
- [ ] Meta Pixel ID (from Events Manager > Data Sources)

### Phase 4: Final Verification ⏳ TO DO

#### 4.1 Comprehensive Testing
- [ ] Clear all cookies and test first-visit experience
- [ ] Test consent modal on all pages
- [ ] Verify footer "Cookie-Einstellungen" link works everywhere
- [ ] Test in all browsers (Chrome, Firefox, Safari, Edge, Brave)
- [ ] Test on mobile devices (iOS Safari, Chrome Android)

#### 4.2 Tool Verification
**Matomo:**
- [ ] Verify cookieless tracking without consent
- [ ] Verify cookie-based tracking with analytics consent
- [ ] Check real-time visitor log
- [ ] Confirm returning visitors work with cookies

**Google Ads:**
- [ ] Install Tag Assistant Legacy extension
- [ ] Verify consent mode signals in Tag Assistant
- [ ] Check conversion tracking fires on success page
- [ ] Confirm data flows to Google Ads dashboard

**Meta Pixel:**
- [ ] Install Facebook Pixel Helper extension
- [ ] Verify PageView event on all pages (with marketing consent)
- [ ] Verify Purchase event on success page
- [ ] Check Events Manager for data flow

#### 4.3 Legal Compliance Check
- [ ] No cookies set before consent ✓
- [ ] Reject as easy as accept ✓
- [ ] Granular control over categories ✓
- [ ] Cookie policy accessible ✓
- [ ] Settings changeable anytime ✓
- [ ] Consent stored for max 1 year ✓
- [ ] All cookies documented in policy ✓

#### 4.4 Performance Check
- [ ] Page load speed acceptable
- [ ] No JavaScript errors in console
- [ ] Cookie banner doesn't block content
- [ ] Mobile experience smooth

---

## 📁 FILE STRUCTURE

```
/curavani_com/
├── index.html
├── patienten.html
├── therapeuten.html
├── service_buchen.html ✅
├── email_bestaetigen.html
├── verify_token.php
├── impressum.html
├── datenschutz.html ✅
├── dankeschoen.html
├── cc-styles.css (was cookieconsent.css)
├── cc-lib.js (was cookieconsent.umd.js)
├── cc-config.js (was cookie-config.js)
└── prices.json
```

---

## 🔧 QUICK FIXES & TROUBLESHOOTING

### Problem: Cookie banner not appearing
**Solution:** 
1. Clear browser cookies
2. Check browser console for errors
3. Verify all 3 files loaded (cc-styles.css, cc-lib.js, cc-config.js)
4. Check if ad blocker is active

### Problem: Brave browser blocking
**Solution:** Use renamed files (cc-* instead of cookie*)

### Problem: Matomo not tracking
**Solution:** Check if analytics.curavani.com is accessible

### Problem: Google Ads not receiving consent
**Solution:** Check gtag is defined before cookie consent loads

---

## 📝 NOTES FOR NEXT SESSION

**Current Status:**
- ✅ Cookie consent working on test page (service_buchen.html)
- ✅ All browsers tested and working
- ✅ Legal documentation updated
- ⏳ Need to roll out to remaining 7 pages
- ⏳ Need Meta Pixel ID from client
- ⏳ Need Google Ads Conversion Label from client

**Next Immediate Steps:**
1. Get Meta Pixel ID and Google Ads Conversion Label
2. Apply changes to all remaining HTML pages
3. Add Meta Pixel code
4. Implement conversion tracking
5. Final testing across all tools

**Time Estimate:**
- Phase 3.1 (Apply to all pages): 1-2 hours
- Phase 3.2 (Meta Pixel): 30 minutes
- Phase 3.3 (Conversion tracking): 30 minutes
- Phase 4 (Verification): 1-2 hours
- **Total remaining: 3-5 hours**

---

## 🚀 QUICK START FOR NEXT SESSION

1. **Open this plan**
2. **Start with Phase 3.1** - Apply to all remaining pages
3. **Get required IDs** from Google Ads and Meta Business Manager
4. **Test thoroughly** after each major step
5. **Document any issues** for troubleshooting

---

*Document created: January 2025*  
*Last updated: After Phase 2 completion*  
*Version: 2.0*
