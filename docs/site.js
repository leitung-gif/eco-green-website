/* Eco Green: Menue, Sonde im Schema, Mailvorlage, Foerderrechner. Ohne Bibliotheken. */
(function () {
  "use strict";
  var d = document;
  var ruhig = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Menue */
  var menue = d.getElementById("menue"), auf = d.querySelector(".menuknopf"), zu = d.querySelector(".menue-zu");
  function setze(offen) {
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

  /* Sonde im Schema: wird einmal in die Tiefe gezeichnet, sobald das Schema sichtbar ist */
  var schema = d.querySelector(".schema"), sonde = d.getElementById("sonde");
  if (schema && sonde && "IntersectionObserver" in window && !ruhig) {
    var ziel = sonde.getAttribute("height");
    sonde.setAttribute("height", "0");
    var io = new IntersectionObserver(function (es) {
      if (es[0].isIntersecting) {
        schema.classList.add("bereit");
        requestAnimationFrame(function () { sonde.setAttribute("height", ziel); sonde.style.height = ziel + "px"; });
        io.disconnect();
      }
    }, { threshold: 0.35 });
    io.observe(schema);
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
