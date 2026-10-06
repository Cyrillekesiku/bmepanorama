/* Biomedical Data Analysis Lab — site behaviour (vanilla JS, no dependencies) */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  /* ---------- Theme ---------- */
  var root = document.documentElement;
  function applyTheme(t) { root.setAttribute("data-theme", t); }
  var saved = store.get("bda-theme");
  applyTheme(saved || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  var themeBtn = $("#themeBtn");
  if (themeBtn) themeBtn.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    applyTheme(next); store.set("bda-theme", next);
  });

  /* ---------- Sidebar (mobile) ---------- */
  var sb = $("#sbToggle");
  if (sb) sb.addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
  var scrim = $(".scrim");
  if (scrim) scrim.addEventListener("click", function () { document.body.classList.remove("nav-open"); });
  var cur = $(".sidebar a.current");
  if (cur && cur.scrollIntoView) { var sbEl = $(".sidebar"); sbEl.scrollTop = Math.max(0, cur.offsetTop - 160); }

  /* ---------- Fullscreen / print / top ---------- */
  var fsBtn = $("#fsBtn");
  if (fsBtn) fsBtn.addEventListener("click", function () {
    document.body.classList.toggle("fullscreen");
    if (document.body.classList.contains("fullscreen") && root.requestFullscreen) { root.requestFullscreen().catch(function () {}); }
    else if (document.fullscreenElement && document.exitFullscreen) { document.exitFullscreen(); }
  });
  var prBtn = $("#printBtn");
  if (prBtn) prBtn.addEventListener("click", function () { window.print(); });
  var top = $(".totop");
  window.addEventListener("scroll", function () {
    if (top) top.classList.toggle("show", window.scrollY > 700);
    spy();
  }, { passive: true });
  if (top) top.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });

  /* ---------- Right-hand contents: scroll spy ---------- */
  var heads = $$("article h2[id], article h3[id]");
  var tocLinks = $$(".toc a");
  function spy() {
    if (!heads.length || !tocLinks.length) return;
    var idx = 0;
    for (var i = 0; i < heads.length; i++) { if (heads[i].getBoundingClientRect().top < 120) idx = i; }
    var id = heads[idx].id;
    tocLinks.forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === "#" + id); });
  }
  spy();

  /* ---------- Copy buttons ---------- */
  $$(".copybtn").forEach(function (b) {
    b.addEventListener("click", function () {
      var pre = b.parentNode.querySelector("pre");
      var txt = pre ? pre.innerText : "";
      var done = function () { b.textContent = "Copied"; b.classList.add("done"); setTimeout(function () { b.textContent = "Copy"; b.classList.remove("done"); }, 1400); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(done, done);
      else { var ta = document.createElement("textarea"); ta.value = txt; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); } catch (e) {} ta.remove(); done(); }
    });
  });

  /* ---------- Lightbox ---------- */
  var lb = document.createElement("div"); lb.className = "lightbox"; lb.innerHTML = "<img alt=''>"; document.body.appendChild(lb);
  lb.addEventListener("click", function () { lb.classList.remove("open"); });
  $$(".fig_out img, figure.plain img").forEach(function (im) {
    im.addEventListener("click", function () { $("img", lb).src = im.src; lb.classList.add("open"); });
  });

  /* ---------- Search (Ctrl/Cmd+K) ---------- */
  var modal = $("#searchModal"), input = $("#searchInput"), list = $("#searchResults"), sel = 0, hits = [];
  function openSearch() { if (!modal) return; modal.classList.add("open"); input.value = ""; render(""); setTimeout(function () { input.focus(); }, 20); }
  function closeSearch() { if (modal) modal.classList.remove("open"); }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function render(q) {
    var data = window.SEARCH_INDEX || [];
    var toks = q.toLowerCase().split(/\s+/).filter(Boolean);
    hits = [];
    if (toks.length) {
      data.forEach(function (d) {
        var t = d.t.toLowerCase(), x = d.x.toLowerCase(), s = 0, ok = true;
        toks.forEach(function (k) {
          var inT = t.indexOf(k) > -1, inX = x.indexOf(k) > -1;
          if (!inT && !inX) ok = false; else s += (inT ? 5 : 0) + (inX ? 1 : 0);
        });
        if (ok) hits.push({ d: d, s: s });
      });
      hits.sort(function (a, b) { return b.s - a.s; });
      hits = hits.slice(0, 12);
    } else {
      hits = data.filter(function (d) { return d.lvl === 1; }).map(function (d) { return { d: d, s: 0 }; });
    }
    sel = 0;
    list.innerHTML = hits.length ? hits.map(function (h, i) {
      return '<li><a href="' + h.d.u + '" class="' + (i === 0 ? "sel" : "") + '">' + esc(h.d.t) + "<small>" + esc(h.d.p) + "</small></a></li>";
    }).join("") : '<li class="empty">No results. Try “Welch”, “quality”, “Nyquist”, “t-test”…</li>';
  }
  function move(d) {
    var as = $$("a", list); if (!as.length) return;
    as[sel].classList.remove("sel"); sel = (sel + d + as.length) % as.length; as[sel].classList.add("sel"); as[sel].scrollIntoView({ block: "nearest" });
  }
  if (modal) {
    $$(".searchBtn").forEach(function (b) { b.addEventListener("click", openSearch); });
    input.addEventListener("input", function () { render(input.value); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") { var as = $$("a", list); if (as[sel]) window.location.href = as[sel].getAttribute("href"); }
    });
    modal.addEventListener("click", function (e) { if (e.target === modal) closeSearch(); });
  }
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openSearch(); }
    else if (e.key === "Escape") { closeSearch(); lb.classList.remove("open"); document.body.classList.remove("nav-open"); }
    else if (e.key === "/" && !/input|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); openSearch(); }
  });

  /* ---------- Self-check quizzes ---------- */
  $$(".quiz").forEach(function (qz) {
    var correct = parseInt(qz.getAttribute("data-correct"), 10), why = qz.getAttribute("data-explain") || "";
    var btns = $$("button", qz), fb = $(".fb", qz);
    btns.forEach(function (b, i) {
      b.addEventListener("click", function () {
        btns.forEach(function (x) { x.disabled = true; });
        btns[correct].classList.add("ok");
        if (i === correct) { fb.innerHTML = "<b>Correct.</b> " + why; }
        else { b.classList.add("bad"); fb.innerHTML = "<b>Not quite.</b> " + why; }
        if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise([fb]);
      });
    });
  });

  /* ---------- Canvas helpers for widgets ---------- */
  function setup(c) {
    var dpr = 2, w = +c.getAttribute("data-w") || 900, h = +c.getAttribute("data-h") || 260;
    c.width = w * dpr; c.height = h * dpr; var g = c.getContext("2d"); g.scale(dpr, dpr); return { g: g, w: w, h: h };
  }
  function axisBox(g, w, h, m) { g.strokeStyle = "#cfd4da"; g.lineWidth = 1; g.strokeRect(m.l, m.t, w - m.l - m.r, h - m.t - m.b); }
  function txt(g, s, x, y, col, al, sz) { g.fillStyle = col || "#555"; g.textAlign = al || "left"; g.font = (sz || 11) + "px sans-serif"; g.fillText(s, x, y); }

  /* ---------- Widget 1: aliasing ---------- */
  var al = $("#aliasCanvas");
  if (al) {
    var A = setup(al), fR = $("#aliasF"), sR = $("#aliasFs"), fO = $("#aliasFv"), sO = $("#aliasFsv"), ro = $("#aliasOut");
    var drawAlias = function () {
      var f = +fR.value, fs = +sR.value; fO.textContent = f.toFixed(1); sO.textContent = fs;
      var g = A.g, w = A.w, h = A.h, m = { l: 40, r: 12, t: 14, b: 26 }, T = 0.25;
      g.clearRect(0, 0, w, h); axisBox(g, w, h, m);
      var X = function (t) { return m.l + t / T * (w - m.l - m.r); }, Y = function (v) { return m.t + (1 - (v + 1.2) / 2.4) * (h - m.t - m.b); };
      g.strokeStyle = "#eef0f2"; g.beginPath(); g.moveTo(m.l, Y(0)); g.lineTo(w - m.r, Y(0)); g.stroke();
      var k = Math.round(f / fs), fa = Math.abs(f - fs * k);
      // alias sinusoid (reconstruction): same samples as the true signal
      var ph = (f - fs * k >= 0) ? 1 : -1;
      g.strokeStyle = "#e03131"; g.lineWidth = 2; g.beginPath();
      for (var i = 0; i <= 600; i++) { var t = i / 600 * T, v = Math.sin(2 * Math.PI * (f - fs * k) * t); i ? g.lineTo(X(t), Y(v)) : g.moveTo(X(t), Y(v)); }
      g.stroke();
      g.strokeStyle = "#1f62b8"; g.lineWidth = 1.2; g.beginPath();
      for (var j = 0; j <= 2400; j++) { var tt = j / 2400 * T, vv = Math.sin(2 * Math.PI * f * tt); j ? g.lineTo(X(tt), Y(vv)) : g.moveTo(X(tt), Y(vv)); }
      g.stroke();
      g.fillStyle = "#111"; g.strokeStyle = "#111"; g.lineWidth = 1;
      for (var n = 0; n / fs <= T; n++) { var ts = n / fs, vs = Math.sin(2 * Math.PI * f * ts); g.beginPath(); g.moveTo(X(ts), Y(0)); g.lineTo(X(ts), Y(vs)); g.stroke(); g.beginPath(); g.arc(X(ts), Y(vs), 3, 0, 7); g.fill(); }
      txt(g, "time (s) — window of 0.25 s", w / 2, h - 7, "#555", "center");
      txt(g, "0", m.l, h - 7, "#555", "center"); txt(g, "0.25", w - m.r, h - 7, "#555", "right");
      txt(g, "blue: true signal at " + f.toFixed(1) + " Hz   black: samples at " + fs + " Hz   red: what the samples look like", m.l + 6, m.t + 12, "#333");
      var ny = fs / 2, msg;
      if (f <= ny) msg = "<b>No aliasing.</b> " + f.toFixed(1) + " Hz ≤ Nyquist (" + ny + " Hz): the samples identify the true frequency.";
      else msg = "<b>Aliasing!</b> " + f.toFixed(1) + " Hz &gt; Nyquist (" + ny + " Hz). The samples are indistinguishable from a sinusoid at <b>" + fa.toFixed(1) + " Hz</b> (f<sub>alias</sub> = |f − k·f<sub>s</sub>| with k = " + k + ").";
      ro.innerHTML = msg;
    };
    fR.addEventListener("input", drawAlias); sR.addEventListener("input", drawAlias); drawAlias();
  }

  /* ---------- Widget 2: spectrum builder (time signal + DFT) ---------- */
  var sp = $("#specTime");
  if (sp) {
    var Tt = setup(sp), Ff = setup($("#specFreq"));
    var FS = 128, N = 512;
    var cosT = [], sinT = [];
    for (var kk = 0; kk <= N / 2; kk++) { var c = new Float32Array(N), s = new Float32Array(N); for (var n2 = 0; n2 < N; n2++) { c[n2] = Math.cos(2 * Math.PI * kk * n2 / N); s[n2] = Math.sin(2 * Math.PI * kk * n2 / N); } cosT.push(c); sinT.push(s); }
    var ids = ["sd", "sth", "sa", "sb", "sm", "sn", "saf"];
    var el = {}; ids.forEach(function (i) { el[i] = $("#" + i); });
    var sw = $("#swin"), seed = 7, rnd = function () { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
    var noise = new Float32Array(N); for (var q = 0; q < N; q++) { var u1 = rnd() || 1e-6, u2 = rnd(); noise[q] = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2); }
    var drawSpec = function () {
      var amp = { d: +el.sd.value, th: +el.sth.value, a: +el.sa.value, b: +el.sb.value, m: +el.sm.value, nz: +el.sn.value }, fa = +el.saf.value;
      $("#sdv").textContent = amp.d; $("#sthv").textContent = amp.th; $("#sav").textContent = amp.a; $("#sbv").textContent = amp.b; $("#smv").textContent = amp.m; $("#snv").textContent = amp.nz; $("#safv").textContent = fa.toFixed(1);
      var x = new Float32Array(N), i;
      for (i = 0; i < N; i++) { var t = i / FS; x[i] = amp.d * Math.sin(2 * Math.PI * 2 * t) + amp.th * Math.sin(2 * Math.PI * 6 * t + 1) + amp.a * Math.sin(2 * Math.PI * fa * t + 2) + amp.b * Math.sin(2 * Math.PI * 20 * t + 3) + amp.m * Math.sin(2 * Math.PI * 50 * t) + amp.nz * noise[i]; }
      var hann = sw.value === "hann", xw = new Float32Array(N), cg = 0;
      for (i = 0; i < N; i++) { var wv = hann ? 0.5 - 0.5 * Math.cos(2 * Math.PI * i / N) : 1; xw[i] = x[i] * wv; cg += wv; }
      var mag = new Float32Array(N / 2 + 1), mx = 0;
      for (var k = 0; k <= N / 2; k++) { var re = 0, im = 0, cc = cosT[k], ss = sinT[k]; for (i = 0; i < N; i++) { re += xw[i] * cc[i]; im -= xw[i] * ss[i]; } mag[k] = (k === 0 || k === N / 2 ? 1 : 2) * Math.sqrt(re * re + im * im) / cg; if (mag[k] > mx) mx = mag[k]; }
      // time plot (first 2 s)
      var g = Tt.g, w = Tt.w, h = Tt.h, m = { l: 40, r: 12, t: 12, b: 24 }; g.clearRect(0, 0, w, h); axisBox(g, w, h, m);
      var peak = 1; for (i = 0; i < N; i++) peak = Math.max(peak, Math.abs(x[i]));
      var X = function (tt) { return m.l + tt / 2 * (w - m.l - m.r); }, Y = function (v) { return m.t + (1 - (v / peak + 1) / 2) * (h - m.t - m.b); };
      g.strokeStyle = "#1f62b8"; g.lineWidth = 1.3; g.beginPath(); for (i = 0; i < 256; i++) { i ? g.lineTo(X(i / FS), Y(x[i])) : g.moveTo(X(i / FS), Y(x[i])); } g.stroke();
      txt(g, "±" + peak.toFixed(0) + " µV", 4, m.t + 10, "#555"); txt(g, "time (s): first 2 s of 4 s", w / 2, h - 6, "#555", "center");
      // spectrum
      g = Ff.g; w = Ff.w; h = Ff.h; g.clearRect(0, 0, w, h); axisBox(g, w, h, m);
      var ymax = Math.max(10, Math.ceil(mx / 5) * 5);
      var XF = function (f) { return m.l + f / 64 * (w - m.l - m.r); }, YF = function (v) { return m.t + (1 - v / ymax) * (h - m.t - m.b); };
      g.strokeStyle = "#e03131"; g.lineWidth = 1.4; g.beginPath(); for (k = 0; k <= N / 2; k++) { var fq = k * FS / N; k ? g.lineTo(XF(fq), YF(mag[k])) : g.moveTo(XF(fq), YF(mag[k])); } g.stroke();
      [[0.5, 4, "δ"], [4, 8, "θ"], [8, 13, "α"], [13, 30, "β"]].forEach(function (b, bi) { g.fillStyle = ["rgba(112,72,232,.08)", "rgba(47,128,237,.08)", "rgba(47,158,68,.12)", "rgba(232,89,12,.08)"][bi]; g.fillRect(XF(b[0]), m.t, XF(b[1]) - XF(b[0]), h - m.t - m.b); txt(g, b[2], (XF(b[0]) + XF(b[1])) / 2, m.t + 12, "#555", "center", 12); });
      for (var f0 = 0; f0 <= 64; f0 += 8) txt(g, f0, XF(f0), h - 8, "#555", "center");
      txt(g, "x: frequency (Hz) · y: amplitude (µV)", w - m.r - 4, m.t + 26, "#555", "right", 10); txt(g, ymax + "", 4, m.t + 10, "#555");
      $("#specOut").innerHTML = "Resolution Δf = f<sub>s</sub>/N = " + FS + "/" + N + " = <b>" + (FS / N).toFixed(3) + " Hz</b>. " + (hann ? "Hann window: main lobe is wider but side-lobe leakage is much lower." : "Rectangular window: sharp lines only when the frequency fits an integer number of cycles; otherwise energy leaks into neighbouring bins.");
    };
    ids.concat(["swin"]).forEach(function (i) { $("#" + i).addEventListener("input", drawSpec); });
    drawSpec();
  }
})();
