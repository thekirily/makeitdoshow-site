/* Head bootstrap: optional PostHog flag, fixed 250ms deadline, fail open to original content. */
(() => {
  'use strict';
  const cfg = JSON.parse(document.getElementById('site-config').textContent);
  const state = window.midExperiment = {assignment: null, settled: false, hold_ms: 0};
  const exp = cfg.experiment;
  let allowed = false, stored, choice;
  const signalBlocked = navigator.globalPrivacyControl === true || navigator.doNotTrack === '1' || window.doNotTrack === '1';
  try {
    choice = localStorage.getItem('mid_analytics_consent') || (localStorage.getItem('mid_analytics_off') === '1' ? 'no' : null);
    allowed = choice === 'yes' && !signalBlocked;
    if (allowed) stored = JSON.parse(sessionStorage.getItem('mid_visit') || 'null');
  } catch {}
  if (choice || signalBlocked) document.documentElement.classList.add('analytics-decided');
  if (!exp?.enabled || !cfg.posthog_project_key || !allowed || navigator.globalPrivacyControl === true || navigator.doNotTrack === '1' || window.doNotTrack === '1') return;
  // Only a consented returning visit is eligible; never hide the first visitor's content.
  if (!stored || Date.now() - stored.last_seen > 30 * 60 * 1000) return;
  const root = document.documentElement, start = performance.now(), controller = new AbortController();
  root.classList.add('ab-pending');
  function finish(assignment) {
    if (state.settled) return;
    state.settled = true; state.hold_ms = performance.now() - start;
    state.assignment = assignment;
    root.classList.remove('ab-pending');
    window.dispatchEvent(new CustomEvent('mid-experiment-ready'));
  }
  const deadline = setTimeout(() => { controller.abort(); finish(null); }, 250);
  function apply(variant, response) {
    if (state.settled || performance.now() - start >= 250) { finish(null); return; }
    const values = exp.variants[variant];
    // Predeclared local content only. No remote HTML or JavaScript is evaluated.
    for (const name of ['headline', 'price']) {
      const slot = document.querySelector(`[data-ab-slot="${name}"]`);
      if (slot && typeof values[name] === 'string') slot.textContent = values[name];
    }
    const hero = document.querySelector('[data-ab-slot="hero"]');
    if (hero && values.hero && /^[-a-zA-Z0-9_.]+\.(webp|png|jpg)$/.test(values.hero.src)) { hero.src = '/assets/img/' + values.hero.src; hero.alt = values.hero.alt; }
    clearTimeout(deadline);
    finish({key: exp.key, variant, request_id: response.requestId || null});
  }
  fetch(cfg.posthog_host + '/flags?v=2', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, credentials: 'omit', signal: controller.signal,
    body: JSON.stringify({api_key: cfg.posthog_project_key, distinct_id: stored.id, evaluation_contexts: ['web']})
  }).then(r => { if (!r.ok) throw new Error('Flag unavailable'); return r.json(); }).then(data => {
    const flag = data.flags?.[exp.key];
    const variant = flag?.enabled ? flag.variant || 'control' : data.featureFlags?.[exp.key];
    if (typeof variant !== 'string' || !Object.hasOwn(exp.variants, variant)) { clearTimeout(deadline); finish(null); return; }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => apply(variant, data), {once: true});
    else apply(variant, data);
  }).catch(() => { clearTimeout(deadline); finish(null); });
})();
