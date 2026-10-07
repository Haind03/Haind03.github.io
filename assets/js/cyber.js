/* Cyberpunk effects: boot screen, scroll reveal, text scramble, count-up,
   reading progress, GoatCounter totals. All of it is skipped when the
   visitor prefers reduced motion. */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var root = document.documentElement;

  function store(key, val) {
    try {
      if (val === undefined) return sessionStorage.getItem(key);
      sessionStorage.setItem(key, val);
    } catch (e) { return null; }
  }

  /* ---------- boot screen (once per session) ---------- */
  function boot() {
    if (reduce || store('cp-booted')) return;
    store('cp-booted', '1');
    var lines = [
      '[ <b>OK</b> ] mounting /dev/haind ...',
      '[ <b>OK</b> ] loading disassembler modules',
      '[ <b>OK</b> ] attaching debugger to pid 1337',
      '[ <i>!!</i> ] anti-debug check bypassed',
      '[ <b>OK</b> ] decrypting notes ... done',
      '<u>ACCESS GRANTED</u>'
    ];
    var el = document.createElement('div');
    el.id = 'cp-boot';
    el.innerHTML = '<div class="cp-boot-inner"><div class="cp-boot-logo">HAIND<span>_</span></div><div class="cp-boot-log"></div><div class="cp-boot-bar"><span></span></div></div>';
    document.body.appendChild(el);
    var log = el.querySelector('.cp-boot-log');
    lines.forEach(function (l, i) {
      setTimeout(function () {
        var p = document.createElement('div');
        p.innerHTML = l;
        log.appendChild(p);
      }, 120 + i * 170);
    });
    setTimeout(function () { el.classList.add('done'); }, 120 + lines.length * 170 + 250);
    setTimeout(function () { el.remove(); }, 120 + lines.length * 170 + 900);
  }

  /* ---------- scroll reveal ---------- */
  function reveal() {
    var sel = [
      '.about .sec', '.about .stat', '.about .cards a', '.about .cve', '.about .hon', '.about .tl li', '.about .ls li',
      '#archives .year', '#archives li', '#post-list .card-wrapper', '.categories.card', '#tags .tag',
      '#page-category li', '.content > h2', '.content > figure', '.content > div.highlighter-rouge',
      '.content > p > img', '.lab-box', '.lab-solution', '#related-posts .card'
    ].join(',');
    var items = Array.prototype.slice.call(document.querySelectorAll(sel));
    if (reduce || !('IntersectionObserver' in window)) return;
    items.forEach(function (n) { n.classList.add('cp-rv'); });
    var io = new IntersectionObserver(function (entries) {
      var batch = 0;
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.style.transitionDelay = Math.min(batch++ * 45, 400) + 'ms';
        e.target.classList.add('cp-in');
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.05 });
    items.forEach(function (n) { io.observe(n); });
  }

  /* ---------- text scramble ---------- */
  var GLYPHS = '!<>-_\\/[]{}=+*^?#01ABCDEF';
  function scramble(el) {
    if (el.dataset.cpBusy) return;
    var target = el.dataset.cpText || el.textContent;
    el.dataset.cpText = target;
    el.dataset.cpBusy = '1';
    var frame = 0, total = 16;
    (function step() {
      var out = '';
      for (var i = 0; i < target.length; i++) {
        var ch = target[i];
        if (ch === ' ' || i < (frame / total) * target.length) out += ch;
        else out += GLYPHS[(Math.random() * GLYPHS.length) | 0];
      }
      el.textContent = out;
      if (frame++ < total) requestAnimationFrame(step);
      else { el.textContent = target; delete el.dataset.cpBusy; }
    })();
  }
  function bindScramble() {
    if (reduce) return;
    var els = document.querySelectorAll('#sidebar .nav-link span, .about .sec-h h2, .dynamic-title, #archives .year, .cards strong');
    Array.prototype.forEach.call(els, function (el) {
      if (el.children.length) return;
      var host = el.closest('a, .sec-h, .nav-link') || el;
      host.addEventListener('mouseenter', function () { scramble(el); });
    });
    var title = document.querySelector('.about .name');
    if (title) {
      var span = title.querySelector('span');
      if (span) setTimeout(function () { scramble(span); }, 400);
    }
  }

  /* ---------- count-up ---------- */
  function countUp() {
    var els = document.querySelectorAll('.about .stat b');
    Array.prototype.forEach.call(els, function (el) {
      var m = el.textContent.match(/^(#?)(\d+)$/);
      if (!m || reduce) return;
      var end = +m[2], start = performance.now(), dur = 1100;
      el.textContent = m[1] + '0';
      (function tick(now) {
        var t = Math.min(1, (now - start) / dur);
        el.textContent = m[1] + Math.round(end * (1 - Math.pow(1 - t, 3)));
        if (t < 1) requestAnimationFrame(tick);
      })(start);
    });
  }

  /* ---------- reading progress on posts ---------- */
  function progress() {
    if (!document.querySelector('article .content') || document.querySelector('.about')) return;
    var bar = document.createElement('div');
    bar.id = 'cp-progress';
    document.body.appendChild(bar);
    function update() {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.transform = 'scaleX(' + (max > 0 ? h.scrollTop / max : 0) + ')';
    }
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* ---------- site-wide view total ---------- */
  function totals() {
    var els = document.querySelectorAll('[data-cp-total]');
    if (!els.length) return;
    fetch('https://haind03.goatcounter.com/counter/TOTAL.json')
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (d) {
        Array.prototype.forEach.call(els, function (el) { el.textContent = d.count; });
      })
      .catch(function () {
        Array.prototype.forEach.call(els, function (el) { el.closest('[data-cp-total-wrap]') && (el.closest('[data-cp-total-wrap]').style.display = 'none'); });
      });
  }

  function init() {
    root.classList.add('cp-js');
    boot();
    reveal();
    bindScramble();
    countUp();
    progress();
    totals();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
