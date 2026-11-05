/* Make It Do: explicit, anonymous events. No third-party SDK, replay, or form capture. */
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
  try { previous = JSON.parse(session.get('mid_visit') || 'null'); } catch {}
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
  session.set('mid_visit', JSON.stringify(visit));
  const pageYear = location.pathname.match(/^\/(19\d{2})\/?$/)?.[1];
  const trackingBlocked = () => local.get('mid_analytics_off') === '1' || navigator.globalPrivacyControl === true || navigator.doNotTrack === '1' || window.doNotTrack === '1';
  function capture(event, data = {}) {
    if (trackingBlocked()) return;
    const properties = {
      distinct_id: visit.id, $process_person_profile: false,
      $current_url: cfg.origin ? cfg.origin + location.pathname : 'https://makeitdoshow.com' + location.pathname,
      $pathname: location.pathname, film: visit.film, door: visit.door,
      source: visit.source, attribution: visit.attribution,
      referrer_host: visit.referrer_host, ...(pageYear ? {year: pageYear} : {}), ...data
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
      url.searchParams.set('utm_source', visit.source);
      url.searchParams.set('utm_campaign', visit.film);
      url.searchParams.set('utm_medium', visit.door);
      url.searchParams.set('mid_visit', visit.id);
      url.searchParams.set('mid_attribution', visit.attribution);
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
  const toggle = document.getElementById('analytics-toggle');
  if (toggle) {
    const status = document.getElementById('analytics-status');
    const refresh = () => {
      toggle.textContent = local.get('mid_analytics_off') === '1' ? 'Allow visit analytics' : 'Turn off visit analytics';
      status.textContent = trackingBlocked() ? 'Visit analytics are off in this browser.' : !cfg.posthog_project_key ? 'Analytics are not configured on this version of the site.' : 'Anonymous visit analytics are on.';
    };
    toggle.addEventListener('click', () => { local.set('mid_analytics_off', local.get('mid_analytics_off') === '1' ? '0' : '1'); refresh(); });
    refresh();
  }
})();
