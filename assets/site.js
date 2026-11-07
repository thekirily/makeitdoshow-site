/* Make It Do: explicit visit events. No third-party SDK, replay, or form capture. */
(() => {
  'use strict';
  const cfg = JSON.parse(document.getElementById('site-config').textContent);
  const q = new URLSearchParams(location.search);
  const safeStorage = (name) => ({
    get(key) { try { return window[name].getItem(key); } catch { return null; } },
    set(key, value) { try { window[name].setItem(key, value); } catch {} },
    remove(key) { try { window[name].removeItem(key); } catch {} }
  });
  const session = safeStorage('sessionStorage');
  const local = safeStorage('localStorage');
  let memoryConsent = null;
  const signalBlocked = () => navigator.globalPrivacyControl === true || navigator.doNotTrack === '1' || window.doNotTrack === '1';
  const trackingBlocked = () => signalBlocked() || local.get('mid_analytics_off') === '1' || (memoryConsent || local.get('mid_analytics_consent')) !== 'yes' || !cfg.posthog_project_key;
  const uuid = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const mediumMap = {q: 'qr', d: 'description', p: 'pinned', e: 'endscreen'};
  const allowedDoors = new Set(['typed', 'qr', 'description', 'pinned', 'endscreen']);
  const doorPath = location.pathname.match(/^\/(\d{2})(?:\/(q|d))?\/?$/);
  const campaign = /^film\d{2}$/.test(q.get('utm_campaign') || '') ? q.get('utm_campaign') : null;
  const utmDoor = allowedDoors.has(q.get('utm_medium')) ? q.get('utm_medium') : null;
  let referringHost = '';
  try { referringHost = new URL(document.referrer).hostname; } catch {}
  const ownReferrer = referringHost === location.hostname;
  let source = 'direct';
  if (referringHost && !ownReferrer) {
    source = /(^|\.)(google|bing|duckduckgo|search\.yahoo)\./.test(referringHost) ? 'search'
      : /(^|\.)(chatgpt\.com|chat\.openai\.com|perplexity\.ai|claude\.ai|copilot\.microsoft\.com|gemini\.google\.com)$/.test(referringHost) ? 'ai_referral' : 'referral';
  }
  let previous;
  try { if (!trackingBlocked()) previous = JSON.parse(session.get('mid_visit') || 'null'); } catch {}
  const explicitDoor = Boolean(doorPath || (campaign && utmDoor));
  let visit = previous;
  const incomingFilm = doorPath ? `film${doorPath[1]}` : campaign && utmDoor ? campaign : 'none';
  const incomingDoor = doorPath ? mediumMap[doorPath[2] || q.get('s')] || 'typed' : campaign && utmDoor ? utmDoor : source;
  const changedDoor = explicitDoor && (visit?.film !== incomingFilm || visit?.door !== incomingDoor);
  if (!visit || Date.now() - visit.last_seen > 30 * 60 * 1000 || changedDoor) {
    const film = incomingFilm;
    const door = incomingDoor;
    visit = {id: uuid(), film, door, source: explicitDoor ? 'youtube' : source, referrer_host: ownReferrer ? '' : referringHost, attribution: explicitDoor ? 'explicit_film_door' : 'unattributed', is_new: true};
  } else visit.is_new = false;
  visit.last_seen = Date.now();
  const utm = Object.fromEntries(['utm_source','utm_medium','utm_campaign','utm_content'].filter(k => /^[A-Za-z0-9_.-]{1,80}$/.test(q.get(k) || '')).map(k => [k,q.get(k)]));
  visit.utm = {...(visit.utm || {}), ...utm};
  if (!trackingBlocked()) session.set('mid_visit', JSON.stringify(visit));
  const pageYear = location.pathname.match(/^\/(19\d{2})\/?$/)?.[1];
  function experimentProperties() {
    const assignment = window.midExperiment?.assignment || visit.experiment;
    return assignment ? {['$feature/' + assignment.key]: assignment.variant, experiment: assignment.key, variant: assignment.variant} : {};
  }
  let exposed = false;
  function expose() {
    const assignment = window.midExperiment?.assignment;
    if (!assignment || exposed || trackingBlocked()) return;
    exposed = true; visit.experiment = assignment;
    session.set('mid_visit', JSON.stringify(visit));
    capture('$feature_flag_called', {$feature_flag: assignment.key, $feature_flag_response: assignment.variant, $feature_flag_request_id: assignment.request_id});
    capture('experiment_exposed', {experiment: assignment.key, variant: assignment.variant});
  }
  window.addEventListener('mid-experiment-ready', expose);
  function capture(event, data = {}) {
    if (trackingBlocked()) return;
    const properties = {
      distinct_id: visit.id, $process_person_profile: false,
      $current_url: cfg.origin ? cfg.origin + location.pathname : 'https://makeitdoshow.com' + location.pathname,
      $pathname: location.pathname, film: visit.film, door: visit.door,
      source: visit.source, attribution: visit.attribution,
      referrer_host: visit.referrer_host, ...visit.utm, ...experimentProperties(), ...(pageYear ? {year: pageYear} : {}), ...data
    };
    // Local QA can inspect payloads without polluting the production project.
    if (!cfg.posthog_project_key || ['localhost', '127.0.0.1', '::1'].includes(location.hostname)) return;
    const body = JSON.stringify({api_key: cfg.posthog_project_key, event, properties, timestamp: new Date().toISOString()});
    const endpoint = cfg.posthog_host.replace(/\/$/, '') + '/i/v0/e/';
    try {
      const sent = navigator.sendBeacon?.(endpoint, new Blob([body], {type: 'text/plain'}));
      if (!sent) fetch(endpoint, {method: 'POST', body, headers: {'Content-Type': 'text/plain'}, keepalive: true, credentials: 'omit'}).catch(() => {});
    } catch {} // A blocked analytics request never blocks the visitor.
  }
  if (visit.is_new) capture('visit_started');
  capture('$pageview');
  expose();
  const parseYear = (value, upper = 1975) => {
    if (!/^\d{2}$|^\d{4}$/.test(value)) return null;
    const year = value.length === 2 ? 1900 + Number(value) : Number(value);
    return year >= 1930 && year <= upper ? year : null;
  };
  document.querySelectorAll('.year-form').forEach(form => {
    form.addEventListener('submit', event => {
      event.preventDefault();
      const input = form.querySelector('input[name="year"]');
      const year = parseYear(input.value.trim());
      const error = form.querySelector('.form-error');
      if (!year) {
        error.textContent = 'Please enter a year from 1930 to 1975, such as 1953.';
        error.hidden = false; input.setAttribute('aria-invalid', 'true'); input.focus(); return;
      }
      capture('year_selected', {year: String(year)});
      location.assign(`/${year}/`);
    });
  });
  // A GET form remains a useful, human-readable directory when scripting is off.
  if (location.pathname === '/year/' && q.has('year')) {
    const year = parseYear(q.get('year').trim());
    if (year) { capture('year_selected', {year: String(year)}); location.replace(`/${year}/`); }
  }
  // Preserve legacy chapter links with only an admitted local destination.
  if (doorPath && q.get('to') === 'kitchen') location.replace('/kitchen/');
  const bookYear = document.getElementById('book-year');
  if (bookYear) {
    const initial = parseYear(q.get('year') || '', 1970);
    if (initial) bookYear.value = String(initial);
    bookYear.addEventListener('change', () => capture('book_year_selected', {year: bookYear.value}));
  }
  document.querySelectorAll('a[data-checkout]').forEach(link => {
    const product = link.dataset.checkout;
    link.addEventListener('click', () => {
      const url = new URL(link.href);
      if (!trackingBlocked()) {
      for (const [key, value] of Object.entries(visit.utm || {})) url.searchParams.set(key, value);
      url.searchParams.set('mid_analytics', 'yes');
      if (visit.experiment) { url.searchParams.set('mid_experiment', visit.experiment.key); url.searchParams.set('mid_variant', visit.experiment.variant); }
      // Campaign tags and film-door attribution are separate facts. Keep both.
      url.searchParams.set('mid_film', visit.film);
      url.searchParams.set('mid_door', visit.door);
      for (const [key, fallback] of [['utm_source',visit.source],['utm_campaign',visit.film],['utm_medium',visit.door]]) {
        if (!url.searchParams.has(key)) url.searchParams.set(key, fallback);
      }
      url.searchParams.set('mid_visit', visit.id);
      url.searchParams.set('mid_attribution', visit.attribution);
      } else {
        for (const key of ['mid_visit','mid_film','mid_door','mid_experiment','mid_variant','utm_source','utm_medium','utm_campaign','utm_content','mid_attribution']) url.searchParams.delete(key);
        url.searchParams.set('mid_analytics', 'no');
      }
      const year = bookYear?.value || link.dataset.year;
      if (year) {
        url.searchParams.set('mid_year', year);
        url.searchParams.set('variant', year);
      }
      link.href = url.href;
      capture(product.startsWith('free') ? 'signup_started' : 'checkout_started', {product, year: year || ''});
    });
  });
  document.querySelectorAll('a[data-download]').forEach(link => link.addEventListener('click', () => capture('sheet_downloaded', {product: link.dataset.download, year: link.dataset.year || ''})));
  document.querySelectorAll('a[data-event]').forEach(link => link.addEventListener('click', () => capture(link.dataset.event)));
  document.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (!link || !link.closest('main') || (!link.matches('.button,.text-link,[data-checkout],[data-download],[data-event]'))) return;
    const destination = new URL(link.href);
    capture('cta_clicked', {destination: destination.origin === location.origin ? destination.pathname : destination.hostname, action: link.dataset.checkout || link.dataset.download || link.dataset.event || 'navigate'});
  });
  document.querySelectorAll('.email-signup').forEach(form => form.addEventListener('submit', () => {
    // Submission is an intent; only the provider's double confirmation proves subscription.
    capture('signup_started', {provider: 'brevo'});
  }));
  const choice = document.getElementById('analytics-choice');
  const toggle = document.getElementById('analytics-toggle');
  function refreshConsent() {
    if (choice) choice.hidden = !cfg.posthog_project_key || signalBlocked() || Boolean(memoryConsent || local.get('mid_analytics_consent')) || local.get('mid_analytics_off') === '1';
    if (toggle) {
      toggle.textContent = trackingBlocked() ? 'Allow visit analytics' : 'Turn off visit analytics';
      document.getElementById('analytics-status').textContent = signalBlocked() ? 'Visit analytics are off because your browser sends DNT or GPC.' : !cfg.posthog_project_key ? 'Analytics are not configured on this version of the site.' : trackingBlocked() ? 'Visit analytics are off in this browser.' : 'Visit analytics are on.';
    }
  }
  function choose(value) {
    const wasBlocked = trackingBlocked();
    memoryConsent = value;
    local.set('mid_analytics_consent', value); local.set('mid_analytics_off', value === 'yes' ? '0' : '1');
    if (value === 'no' || signalBlocked()) {
      session.remove('mid_visit'); delete visit.experiment;
      if (window.midExperiment) window.midExperiment.assignment = null;
    } else if (wasBlocked && !trackingBlocked()) {
      visit.is_new = true; visit.last_seen = Date.now(); session.set('mid_visit', JSON.stringify(visit));
      capture('visit_started'); capture('$pageview');
    }
    refreshConsent();
  }
  document.querySelectorAll('[data-consent]').forEach(button => button.addEventListener('click', () => choose(button.dataset.consent)));
  if (toggle) toggle.addEventListener('click', () => choose(trackingBlocked() ? 'yes' : 'no'));
  // Withdrawal signals also clear previously stored attribution on subsequent pages.
  if (signalBlocked() || local.get('mid_analytics_off') === '1' || local.get('mid_analytics_consent') === 'no') session.remove('mid_visit');
  refreshConsent();
})();
