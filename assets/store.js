// The store: live cover preview in the cover's own type, her year's true line, the second booklet, the leaf-through loop,
// and the thank-you status. No third-party script; the server checks everything again.
(function () {
  var form = document.getElementById('order');
  if (form) {
    var facts = JSON.parse(form.getAttribute('data-facts'));
    var img = form.querySelector('.shop-cover-img');
    var cap = document.getElementById('covername');
    var fact = document.getElementById('fact');
    var big = document.getElementById('bigfact');
    var total = document.getElementById('total');
    var second = document.getElementById('second');
    var y1 = document.getElementById('book-year'), n1 = document.getElementById('name1');
    var y2 = document.getElementById('year2'), n2 = document.getElementById('name2');
    var ok = /^[A-Za-zÀ-ÖØ-öø-ſ]+(?:[ '’.\-][A-Za-zÀ-ÖØ-öø-ſ]*)*\.?$/;
    function tidy(s) { return s.replace(/\s+/g, ' ').trim().replace(/'/g, '’'); }
    function line(y) {
      var f = facts[y]; if (!f) return '';
      return f.then ? 'In ' + y + ' a dozen eggs cost ' + f.eggs + ': ' + f.then + ' minutes of work at the ' + f.wage + ' minimum wage. Today, ' + f.now + '. The most common name for a baby girl was ' + f.girl + '.'
                    : 'In ' + y + ' a dozen eggs cost ' + f.eggs + '. There was no federal minimum wage yet; it came in 1938. The most common name for a baby girl was ' + f.girl + '.';
    }
    function update() {
      var y = y1.value || '1953', name = tidy(n1.value) || 'Margaret';
      img.src = '/assets/img/shop/cover-' + y + '.webp';
      cap.textContent = 'For ' + name + ', born ' + y;
      document.getElementById('nameline').textContent = cap.textContent;
      // same rule as the print robot: 22pt, shrinking to 16pt to stay inside the type-safe area (0.5in from the trim)
      var w = cap.parentNode.clientWidth, pt = 22;
      cap.style.fontSize = (pt / 72 / 8.5 * w) + 'px';
      while (cap.offsetLeft + cap.offsetWidth > w * (8.0 / 8.5) && pt > 16) { pt -= 1; cap.style.fontSize = (pt / 72 / 8.5 * w) + 'px'; }
      fact.textContent = y1.value ? line(y1.value) : '';
      var f = facts[y];
      if (big && f && f.then) big.innerHTML = '<span>' + f.then + ' minutes</span> of work at the minimum wage bought a dozen eggs in ' + y + '. <em>Today, ' + f.now + '.</em>';
      var v = n1.value.trim();
      n1.setCustomValidity(!v || ok.test(tidy(v)) ? '' : 'Letters only, please, with spaces, hyphens or apostrophes between them.');
      var two = second.open && (y2.value || n2.value.trim());
      y2.required = n2.required = !!second.open && !!two;
      if (total) total.textContent = two ? '$78' : '$49';
    }
    [y1, n1, y2, n2].forEach(function (el) { el.addEventListener('input', update); el.addEventListener('change', update); });
    second.addEventListener('toggle', update);
    if (location.hash === '#second') second.open = true;
    var err = new URLSearchParams(location.search).get('error');
    if (err) { var p = document.createElement('p'); p.className = 'shop-error'; p.setAttribute('role', 'alert'); p.textContent = err; form.insertBefore(p, form.firstChild); }
    update();
  }
  var v = document.querySelector('.shop-video');
  if (v && 'IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { v.preload = 'auto'; v.play().catch(function () {}); } else v.pause(); }); }, { threshold: 0.35 }).observe(v);
  } else if (v) { v.controls = true; }
  var t = document.getElementById('thanks');
  if (t) {
    var id = new URLSearchParams(location.search).get('order') || '';
    if (/^MID-\d{6}-[0-9A-F]{8}$/.test(id)) {
      document.getElementById('thanks-id').textContent = id;
      fetch((t.getAttribute('data-api') || '') + '/api/order/' + id).then(function (r) { return r.json(); }).then(function (o) {
        var names = (o.lines || []).map(function (l) { return l.name + '’s ' + l.year; }).join(' and ');
        var msg = { paid: 'Paid. ' + names + ' goes to the printer now.', building: 'Paid. ' + names + ' is being set.', built: 'Paid. ' + names + ' is set and being checked.',
          validated: 'Paid. ' + names + ' passed the printer’s file check.', submitted: 'Paid and at the printer: ' + names + '. Allow about 2½ weeks to her door.',
          payment_pending: 'PayPal is still clearing the payment. Nothing prints until it does; we’ll go ahead the moment it clears.',
          held: 'We need to look at this order before it prints. We’ll write to you about it.' }[o.state];
        if (msg) document.getElementById('thanks-line').textContent = msg;
      }).catch(function () {});
    }
  }
})();
