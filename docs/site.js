/* Eco Green: Menue, Bohrung zum Scrollen, Einblenden, Foerderrechner. Ohne Bibliotheken. */
(function () {
  "use strict";
  var d = document;
  var ruhig = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Menue */
  var menue = d.getElementById("menue"), auf = d.querySelector(".menuknopf"), zu = d.querySelector(".menue-zu");
  function setze(offen) {
    if (!menue) return;
    menue.classList.toggle("offen", offen);
    menue.setAttribute("aria-hidden", offen ? "false" : "true");
    if (offen) { menue.removeAttribute("inert"); } else { menue.setAttribute("inert", ""); }
    auf.setAttribute("aria-expanded", offen ? "true" : "false");
    d.body.classList.toggle("gesperrt", offen);
    (offen ? zu : auf).focus();
  }
  if (menue && auf && zu) {
    auf.addEventListener("click", function () { setze(true); });
    zu.addEventListener("click", function () { setze(false); });
    d.addEventListener("keydown", function (e) { if (e.key === "Escape" && menue.classList.contains("offen")) setze(false); });
    menue.addEventListener("click", function (e) { if (e.target.closest("a")) setze(false); });
  }

  /* Einblenden */
  var teile = d.querySelectorAll(".auf");
  if ("IntersectionObserver" in window && !ruhig) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("da"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    teile.forEach(function (t) { io.observe(t); });
  } else { teile.forEach(function (t) { t.classList.add("da"); }); }

  /* Bohrung zum Scrollen */
  var schnitt = d.getElementById("schnitt");
  if (schnitt) {
    var schritte = schnitt.querySelectorAll(".schritt");
    var rohr = d.getElementById("sonde"), kopf = d.getElementById("bohrkopf");
    var tiefe = d.querySelectorAll("[data-tiefe]"), temp = d.querySelectorAll("[data-temp]"), balken = d.querySelector(".tiefenleiste i");
    var ZIEL = 220, PRO_M = 2.2, laeuft = false;
    function temperatur(m) { return m < 15 ? 10 : 10 + (m - 15) * 0.03; }
    var parzelle = d.getElementById("parzelle"), stempel = d.getElementById("stempel");
    function zeichne() {
      laeuft = false;
      var vh = window.innerHeight, mitte = vh * 0.5;
      /* Gebohrt wird erst in Schritt 03, bis Schritt 04 ist die Sonde unten */
      var a = schritte[2].getBoundingClientRect().top, b = schritte[3].getBoundingClientRect().top;
      var p = (mitte - a) / Math.max(1, b - a);
      p = Math.min(1, Math.max(0, p));
      var m = Math.round(p * ZIEL);
      if (rohr) { rohr.setAttribute("height", Math.max(0, m * PRO_M)); }
      if (kopf) { kopf.setAttribute("transform", "translate(0," + (m * PRO_M) + ")"); }
      tiefe.forEach(function (t) { t.textContent = String(m).padStart(3, "0") + " m"; });
      temp.forEach(function (t) { t.textContent = temperatur(m).toFixed(1).replace(".", ",") + " °C"; });
      if (balken) balken.style.width = (p * 100) + "%";
      var aktiv = -1;
      schritte.forEach(function (s, i) { if (s.getBoundingClientRect().top < mitte) aktiv = i; });
      schritte.forEach(function (s, i) { s.classList.toggle("aktiv", i === aktiv); });
      if (parzelle) parzelle.setAttribute("opacity", aktiv === 0 ? "1" : "0");
      if (stempel) stempel.setAttribute("opacity", aktiv >= 1 ? "1" : "0");
    }
    function anstoss() { if (!laeuft) { laeuft = true; requestAnimationFrame(zeichne); } }
    window.addEventListener("scroll", anstoss, { passive: true });
    window.addEventListener("resize", anstoss);
    requestAnimationFrame(zeichne);
  }

  /* Mailvorlage kopieren, fuer Webmail ohne Mailprogramm */
  d.querySelectorAll(".kopieren").forEach(function (k) {
    k.addEventListener("click", function () {
      var meldung = d.querySelector(".kopiert");
      var fertig = function () { if (meldung) meldung.textContent = "Vorlage kopiert. Fügen Sie sie in eine neue E-Mail an info@eco-green.ch ein."; };
      if (navigator.clipboard) { navigator.clipboard.writeText(k.getAttribute("data-text")).then(fertig, function () {}); }
    });
  });

  /* Foerderrechner, Saetze Kanton Zuerich */
  var rechner = d.getElementById("rechner");
  if (rechner) {
    var kw = d.getElementById("kw"), zusatz = d.getElementById("zusatz");
    var aus = d.getElementById("betrag"), z1 = d.getElementById("r-grund"), z2 = d.getElementById("r-mehr"), z3 = d.getElementById("r-zusatz");
    function chf(n) { return "CHF " + Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, "'"); }
    function rechne() {
      var k = parseFloat(String(kw.value).replace(",", "."));
      if (!isFinite(k) || k <= 0) { aus.textContent = "CHF 0"; z1.textContent = z2.textContent = z3.textContent = "CHF 0"; return; }
      var ueber = Math.max(0, k - 15);
      var grund = 6800, mehr = 420 * ueber, extra = zusatz.checked ? 3000 + 100 * ueber : 0;
      z1.textContent = chf(grund); z2.textContent = chf(mehr); z3.textContent = chf(extra);
      aus.textContent = chf(grund + mehr + extra);
    }
    kw.addEventListener("input", rechne); zusatz.addEventListener("change", rechne); rechne();
  }
})();
