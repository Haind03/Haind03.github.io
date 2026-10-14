---
title: CVE Archive
icon: fas fa-bug
order: 1
---

{% assign cves = site.data.cves %}
{% assign crit = 0 %}{% assign high = 0 %}{% assign med = 0 %}{% assign unauth = 0 %}
{% for c in cves %}
  {% if c.cvss >= 9 %}{% assign crit = crit | plus: 1 %}{% elsif c.cvss >= 7 %}{% assign high = high | plus: 1 %}{% else %}{% assign med = med | plus: 1 %}{% endif %}
  {% if c.type contains "Unauthenticated" or c.type contains "Authentication Bypass" %}{% assign unauth = unauth | plus: 1 %}{% endif %}
{% endfor %}
{% assign total = cves.size %}

<style>
  .ca { color: var(--cp-text); }
  .ca a { border-bottom: none !important; }
  .ca p { line-height: 1.8; }
  .ca-kick { font: 500 .72rem var(--cp-mono); letter-spacing: .28em; text-transform: uppercase; color: var(--cp-magenta); margin: .25rem 0 1.25rem; }
  .ca-kick::before { content: ''; display: inline-block; width: 28px; height: 2px; background: var(--cp-magenta); vertical-align: middle; margin-right: .6rem; box-shadow: 0 0 8px var(--cp-magenta); }
  .ca-lead { font-size: 1.08rem; color: #dbe6f3; border-left: 2px solid var(--cp-cyan); padding-left: 1rem; }

  .ca-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .8rem; margin: 2rem 0 1.25rem; }
  .ca-stat { position: relative; background: var(--cp-panel); border: 1px solid var(--cp-line); padding: 1rem 1.1rem .9rem; clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 0 100%); }
  .ca-stat::before { content: ''; position: absolute; left: 0; top: 0; width: 40%; height: 2px; background: var(--c, var(--cp-cyan)); box-shadow: 0 0 10px var(--c, var(--cp-cyan)); }
  .ca-stat b { display: block; font: 700 1.9rem/1.1 var(--cp-display); color: var(--cp-ink); }
  .ca-stat span { font: .68rem var(--cp-mono); color: var(--cp-mute); text-transform: uppercase; letter-spacing: .14em; }

  .ca-dist { display: flex; height: 12px; margin: .4rem 0 .6rem; border: 1px solid var(--cp-line-2); background: var(--cp-bg-2); }
  .ca-dist i { display: block; height: 100%; transform-origin: left; animation: ca-grow 1s cubic-bezier(.2, .7, .2, 1) both; }
  .ca-dist i + i { border-left: 2px solid var(--cp-bg); }
  @keyframes ca-grow { from { transform: scaleX(0); } }
  .ca-legend { display: flex; gap: 1.25rem; flex-wrap: wrap; font: .68rem var(--cp-mono); color: var(--cp-mute); letter-spacing: .1em; text-transform: uppercase; }
  .ca-legend i { display: inline-block; width: 10px; height: 10px; margin-right: .4rem; vertical-align: -1px; }

  .ca-h { display: flex; align-items: center; gap: .9rem; margin: 3rem 0 1.1rem; }
  .ca-h .n { font: 600 .72rem var(--cp-mono); color: var(--cp-bg); background: var(--cp-cyan); padding: .2rem .5rem; clip-path: polygon(5px 0, 100% 0, 100% calc(100% - 5px), calc(100% - 5px) 100%, 0 100%, 0 5px); }
  .ca-h h2 { margin: 0 !important; font: 700 1.4rem var(--cp-display) !important; text-transform: uppercase; letter-spacing: .06em; border: 0 !important; padding: 0 !important; }
  .ca-h h2::before { content: none !important; }
  .ca-h::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, var(--cp-line-2), transparent); }

  .ca-steps { counter-reset: st; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .6rem; margin: 1.25rem 0 .5rem; }
  .ca-steps div { counter-increment: st; position: relative; padding: .8rem .8rem .75rem; background: var(--cp-panel); border: 1px solid var(--cp-line); font: 600 .78rem var(--cp-mono); color: var(--cp-ink); text-transform: uppercase; letter-spacing: .06em; clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 0 100%); }
  .ca-steps div::before { content: '0' counter(st); display: block; font-size: .66rem; color: var(--cp-magenta); margin-bottom: .3rem; }
  .ca-steps div span { display: block; margin-top: .3rem; font: 400 .74rem/1.45 var(--cp-mono); color: var(--cp-mute); text-transform: none; letter-spacing: 0; }

  .ca-filters { display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0 1.1rem; }
  .ca-filters button { font: 600 .7rem var(--cp-mono); letter-spacing: .12em; text-transform: uppercase; color: var(--cp-text); background: var(--cp-panel); border: 1px solid var(--cp-line-2); padding: .45rem .8rem; cursor: pointer; clip-path: polygon(7px 0, 100% 0, 100% calc(100% - 7px), calc(100% - 7px) 100%, 0 100%, 0 7px); transition: background .15s, color .15s, border-color .15s; }
  .ca-filters button:hover { border-color: var(--cp-cyan); color: var(--cp-cyan); }
  .ca-filters button.on { background: var(--cp-cyan); color: var(--cp-bg); border-color: var(--cp-cyan); }
  .ca-filters button b { opacity: .6; margin-left: .35rem; font-weight: 600; }

  .ca-head, .ca-row { display: grid; grid-template-columns: 3.6rem 9.8rem minmax(0, 1.35fr) minmax(0, 1fr); gap: 1rem; align-items: center; }
  .ca-head { font: 500 .66rem var(--cp-mono); letter-spacing: .16em; text-transform: uppercase; color: var(--cp-mute); padding: 0 .9rem .6rem; border-bottom: 1px solid var(--cp-cyan-dim); }
  .ca-row { padding: .75rem .9rem; border-bottom: 1px solid var(--cp-line); transition: background .15s, opacity .25s; }
  .ca-row:hover { background: linear-gradient(90deg, rgb(0 240 255 / 6%), transparent); }
  .ca-row.hide { display: none; }
  .ca-row .id { font: .8rem var(--cp-mono); white-space: nowrap; }
  .ca-row .pl { color: var(--cp-ink); font-size: .92rem; }
  .ca-row .ty { color: var(--cp-mute); font-size: .84rem; }
  .ca-cvss { display: inline-block; width: 3.1rem; text-align: center; font: 700 .78rem var(--cp-mono); padding: .25rem 0; color: #07090f; clip-path: polygon(5px 0, 100% 0, 100% calc(100% - 5px), calc(100% - 5px) 100%, 0 100%, 0 5px); }
  .ca-cvss.crit { background: var(--cp-magenta); color: #fff; }
  .ca-cvss.high { background: #ff8a3d; }
  .ca-cvss.med { background: var(--cp-yellow); }

  .ca-pager { display: flex; justify-content: center; gap: .5rem; margin: 1.25rem 0 0; }
  .ca-pager button { min-width: 2.4rem; font: 600 .8rem var(--cp-mono); color: var(--cp-text); background: var(--cp-panel); border: 1px solid var(--cp-line-2); padding: .45rem .7rem; cursor: pointer; clip-path: polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px); }
  .ca-pager button:hover { border-color: var(--cp-cyan); color: var(--cp-cyan); }
  .ca-pager button.on { background: var(--cp-cyan); color: var(--cp-bg); border-color: var(--cp-cyan); }
  .ca-plat { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 1rem; }
  .ca-plat a { display: block; padding: 1.1rem 1.2rem; background: var(--cp-panel); border: 1px solid var(--cp-line); color: var(--cp-text); clip-path: polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%); transition: border-color .2s, transform .2s; }
  .ca-plat a:hover { border-color: var(--cp-cyan); transform: translateY(-3px); text-shadow: none; }
  .ca-plat strong { display: block; font: 700 1.1rem var(--cp-display); color: var(--cp-ink); text-transform: uppercase; letter-spacing: .04em; }
  .ca-plat span { font-size: .86rem; color: var(--cp-mute); }

  @media (max-width: 1199px) {
    .ca-steps { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  }
  @media (max-width: 767px) {
    .ca-stats { gap: .5rem; }
    .ca-steps, .ca-plat { grid-template-columns: 1fr; }
    .ca-head { display: none; }
    .ca-row { grid-template-columns: 3.4rem minmax(0, 1fr); gap: .3rem .8rem; }
    .ca-row .cv { grid-row: span 3; align-self: start; }
  }
  @media (prefers-reduced-motion: reduce) { .ca-dist i { animation: none; } }
</style>

<div class="ca">

<div class="ca-kick">Bug bounty // Vulnerability research</div>

<p class="ca-lead">These are the CVEs credited to me from bug bounty and vulnerability research on WordPress plugins, web applications and open-source projects. I report through bug bounty programs such as Wordfence and Patchstack, as well as other coordinated disclosure channels. Once the vendor ships a fix, the advisory goes public and the CVE is published.</p>

<p>Most of what I find is in access control and input handling: REST routes or AJAX actions without proper permission checks, SQL built from user input, and stored XSS. I mostly look for bugs that work without logging in. The highest one here is an unauthenticated RCE in Easy Invoice (CVSS 10.0).</p>

<div class="ca-stats">
  <div class="ca-stat"><b>{{ total }}</b><span>CVEs assigned</span></div>
  <div class="ca-stat" style="--c: var(--cp-magenta)"><b>{{ crit }}</b><span>Critical (9.0+)</span></div>
  <div class="ca-stat" style="--c: var(--cp-yellow)"><b>{{ unauth }}</b><span>No login needed</span></div>
</div>

<div class="ca-dist" role="img" aria-label="{{ crit }} critical, {{ high }} high, {{ med }} medium">
  <i style="width: {{ crit | times: 100.0 | divided_by: total }}%; background: var(--cp-magenta)"></i>
  <i style="width: {{ high | times: 100.0 | divided_by: total }}%; background: #ff8a3d"></i>
  <i style="width: {{ med | times: 100.0 | divided_by: total }}%; background: var(--cp-yellow)"></i>
</div>
<div class="ca-legend">
  <span><i style="background: var(--cp-magenta)"></i>Critical · {{ crit }}</span>
  <span><i style="background: #ff8a3d"></i>High · {{ high }}</span>
  <span><i style="background: var(--cp-yellow)"></i>Medium · {{ med }}</span>
</div>

<div class="ca-h"><span class="n">0x01</span><h2>Process</h2></div>

<p>The workflow stays the same whatever the target is: a WordPress plugin, a web application or an open-source project.</p>

<div class="ca-steps">
  <div>Scope<span>Pick a target and check the program scope and rules.</span></div>
  <div>Audit<span>Map the attack surface, then review the source or test what an outside user can reach.</span></div>
  <div>PoC<span>Reproduce it in a lab I control, never on live systems.</span></div>
  <div>Disclose<span>Report privately to the bounty program, the vendor or a CNA, with root cause and impact.</span></div>
  <div>Fix + CVE<span>The vendor ships a patch, then the advisory and CVE go public.</span></div>
</div>

<div class="ca-h"><span class="n">0x02</span><h2>The archive</h2></div>


<div class="ca-filters" id="ca-filters">
  <button class="on" data-f="all">All<b>{{ total }}</b></button>
  <button data-f="crit">Critical</button>
  <button data-f="cat:web">Web</button>
  <button data-f="cat:pwn">Pwn</button>
  <button data-f="cat:crypto">Crypto</button>
  <button data-f="sqli">SQL injection</button>
  <button data-f="xss">XSS</button>
  <button data-f="ssrf">SSRF</button>
  <button data-f="rce">RCE / Auth bypass</button>
  <button data-f="authz">Missing authz</button>
  <button data-f="overflow">Buffer overflow</button>
  <button data-f="oob">Out-of-bounds</button>
  <button data-f="uaf">Use-after-free</button>
  <button data-f="mfree">Double / invalid free</button>
  <button data-f="nullderef">NULL deref</button>
  <button data-f="dos">DoS</button>
  <button data-f="other">Other</button>
</div>

<div class="ca-head"><span>CVSS</span><span>CVE</span><span>Affected plugin</span><span>Type</span></div>
{% for c in cves %}
  {% assign sev = "med" %}{% if c.cvss >= 9 %}{% assign sev = "crit" %}{% elsif c.cvss >= 7 %}{% assign sev = "high" %}{% endif %}
  {% assign cls = "other" %}
  {% if c.type contains "SQL" %}{% assign cls = "sqli" %}
  {% elsif c.type contains "Scripting" or c.type contains "XSS" %}{% assign cls = "xss" %}
  {% elsif c.type contains "SSRF" or c.type contains "Server-Side Request" %}{% assign cls = "ssrf" %}
  {% elsif c.type contains "Remote Code" or c.type contains "Code Injection" or c.type contains "OS Command" or c.type contains "Authentication Bypass" %}{% assign cls = "rce" %}
  {% elsif c.type contains "Authorization" or c.type contains "Unauthorized" or c.type contains "Missing Authentication" %}{% assign cls = "authz" %}
  {% elsif c.type contains "Overflow" %}{% assign cls = "overflow" %}
  {% elsif c.type contains "Out-of-Bounds" or c.type contains "Out of Bounds" %}{% assign cls = "oob" %}
  {% elsif c.type contains "Use After Free" %}{% assign cls = "uaf" %}
  {% elsif c.type contains "Double Free" or c.type contains "Invalid Free" or c.type contains "Uninitialized" %}{% assign cls = "mfree" %}
  {% elsif c.type contains "NULL Pointer" or c.type contains "Dereference" %}{% assign cls = "nullderef" %}
  {% elsif c.type contains "Infinite Loop" or c.type contains "Excessive Iteration" or c.type contains "Divide by Zero" or c.type contains "Resource Exhaustion" or c.type contains "Decompression" %}{% assign cls = "dos" %}
  {% endif %}
  <div class="ca-row" data-sev="{{ sev }}" data-cat="{{ c.class }}" data-cls="{{ cls }}">
    <span class="cv"><span class="ca-cvss {{ sev }}">{{ c.cvss }}</span></span>
    <a class="id" href="{{ c.url }}" target="_blank" rel="noopener">{{ c.id }}</a>
    <span class="pl">{{ c.plugin }}</span>
    <span class="ty">{{ c.type }}</span>
  </div>
{% endfor %}

<div class="ca-pager" id="ca-pager"></div>

<div class="ca-h"><span class="n">0x03</span><h2>Where I report</h2></div>

<div class="ca-plat">
  <a href="https://www.wordfence.com/threat-intel/vulnerabilities/researchers/nguyen-dinh-hai-haind" target="_blank" rel="noopener"><strong>Wordfence</strong><span>Researcher profile with all advisories.</span></a>
  <a href="https://patchstack.com/database/researchers/e27f086e-ad03-440c-aee4-f95fd885527e" target="_blank" rel="noopener"><strong>Patchstack</strong><span>Researcher profile on Patchstack.</span></a>
  <a href="https://vulnerability.circl.lu/credits/HaiND%20from%20the%20Post%20and%20Telecommunication%20Institute%20of%20Technology" target="_blank" rel="noopener"><strong>CIRCL</strong><span>Credits on the CIRCL vulnerability-lookup.</span></a>
  <a href="https://www.vulncheck.com/" target="_blank" rel="noopener"><strong>VulnCheck</strong><span>CNA that assigns CVEs for my open-source reports.</span></a>
</div>

</div>

<script>
  (function () {
    var PER = 20;
    var bar = document.getElementById('ca-filters');
    var pager = document.getElementById('ca-pager');
    if (!bar) return;
    var rows = Array.prototype.slice.call(document.querySelectorAll('.ca-row'));
    var filter = 'all', page = 1;
    function match(r, f) {
      if (f === 'all') return true;
      if (f === 'crit') return r.dataset.sev === 'crit';
      if (f.indexOf('cat:') === 0) return r.dataset.cat === f.slice(4);
      return r.dataset.cls === f;
    }
    function render() {
      var shown = rows.filter(function (r) { return match(r, filter); });
      var pages = Math.max(1, Math.ceil(shown.length / PER));
      if (page > pages) page = pages;
      rows.forEach(function (r) { r.classList.add('hide'); });
      shown.slice((page - 1) * PER, page * PER).forEach(function (r) { r.classList.remove('hide'); });
      pager.innerHTML = '';
      if (pages < 2) return;
      for (var i = 1; i <= pages; i++) {
        var btn = document.createElement('button');
        btn.textContent = i;
        if (i === page) btn.className = 'on';
        btn.addEventListener('click', (function (n) { return function () {
          page = n; render();
          var top = document.querySelector('.ca-head') || bar;
          window.scrollTo({ top: top.getBoundingClientRect().top + window.scrollY - 90, behavior: 'smooth' });
        }; })(i));
        pager.appendChild(btn);
      }
    }
    bar.querySelectorAll('button').forEach(function (b) {
      var f = b.dataset.f;
      if (f !== 'all') {
        var n = rows.filter(function (r) { return match(r, f); }).length;
        b.insertAdjacentHTML('beforeend', '<b>' + n + '</b>');
        if (!n) b.style.display = 'none';
      }
      b.addEventListener('click', function () {
        bar.querySelectorAll('button').forEach(function (x) { x.classList.toggle('on', x === b); });
        filter = f; page = 1; render();
      });
    });
    render();
  })();
</script>
