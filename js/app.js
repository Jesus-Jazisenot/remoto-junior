/* Remoto Junior - lista filtrable. JS puro, sin dependencias. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var state = { jobs: [], meta: null };
  var AREA = {}, FUENTE = {};
  var INGLES = { no_requerido: "Sin inglés", si: "Inglés requerido", intermedio: "Inglés intermedio", avanzado: "Inglés avanzado" };
  var NIVEL = { junior: "Junior / Entry", entrada: "Apto sin mucha experiencia" };
  var ACEPTA = { mundo: "Desde cualquier país", latam: "Abierta a LatAm", pais: "Solo ciertos países" };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fechaCorta(iso) {
    if (!iso) return "fecha no indicada";
    var d = new Date(iso);
    if (isNaN(d)) return "fecha no indicada";
    var dias = Math.floor((Date.now() - d.getTime()) / 864e5);
    if (dias <= 0) return "publicada hoy";
    if (dias === 1) return "publicada ayer";
    return "publicada hace " + dias + " días";
  }
  function fechaLarga(iso) {
    var d = new Date(iso);
    return d.toLocaleString("es-MX", { dateStyle: "long", timeStyle: "short", timeZone: "America/Mazatlan" }) + " (hora de Mazatlán)";
  }

  function card(j) {
    var f = FUENTE[j.fuente] || { nombre: j.fuente, home: "#" };
    var chips = [
      "<li>" + esc(AREA[j.area] || j.area) + "</li>",
      "<li>" + esc(NIVEL[j.nivel] || j.nivel) + "</li>",
      '<li class="' + (j.incluye_mexico ? "mx" : "") + '">' + esc(ACEPTA[j.acepta] || j.acepta) +
        (j.paises && j.paises.length ? ": " + esc(j.paises.slice(0, 4).join(", ")) + (j.paises.length > 4 ? "…" : "") : "") + "</li>",
      "<li>" + esc(INGLES[j.ingles] || j.ingles) + "</li>"
    ];
    if (j.salario_texto) chips.push('<li class="sal">' + esc(j.salario_texto) + "</li>");
    return '<li class="job"><h2>' + esc(j.titulo) + '</h2><p class="co">' + esc(j.empresa || "Empresa no indicada") +
      '</p><ul class="chips">' + chips.join("") + "</ul>" +
      (j.resumen ? '<p class="res">' + esc(j.resumen) + "</p>" : "") +
      '<div class="foot"><span>' + fechaCorta(j.fecha) + " · fuente: " +
      '<a href="' + esc(f.home) + '" rel="noopener">' + esc(f.nombre) + "</a></span>" +
      '<a class="btn" href="' + esc(j.url) + '" target="_blank" rel="noopener">Ver vacante en ' + esc(f.nombre) + " →</a></div>" +
      '<details class="why"><summary>¿Por qué pasó el filtro?</summary>Ubicación: ' + esc(j.motivos.ubicacion) +
      ". Nivel: " + esc(j.motivos.nivel) + ".</details></li>";
  }

  function render() {
    var q = $("q").value.trim().toLowerCase(), area = $("area").value, ing = $("ing").value;
    var sal = $("sal").checked, mx = $("mx").checked, jr = $("jr").checked;
    var out = state.jobs.filter(function (j) {
      if (area && j.area !== area) return false;
      if (ing === "sin" && j.ingles !== "no_requerido") return false;
      if (ing === "hasta_inter" && ["no_requerido", "intermedio", "si"].indexOf(j.ingles) < 0) return false;
      if (ing === "avanzado" && j.ingles !== "avanzado") return false;
      if (sal && !j.salario_texto) return false;
      if (mx && !j.incluye_mexico) return false;
      if (jr && j.nivel !== "junior") return false;
      if (q && (j.titulo + " " + j.empresa).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    $("count").textContent = out.length + " de " + state.jobs.length + " vacantes";
    $("list").innerHTML = out.length ? out.map(card).join("") :
      '<li class="empty">Ninguna vacante cumple esos filtros. Quita alguno; preferimos mostrarte pocas y reales que rellenar.</li>';
  }

  function init(d) {
    state.jobs = d.jobs; state.meta = d.meta;
    AREA = d.meta.areas || {};
    Object.keys(d.meta.fuentes_info).forEach(function (k) { FUENTE[k] = d.meta.fuentes_info[k]; });
    var m = d.meta;
    $("s-ok").textContent = m.sobreviven;
    $("s-in").textContent = m.tras_dedup;
    $("s-upd").textContent = fechaLarga(m.actualizado);
    var a = $("area");
    Object.keys(AREA).forEach(function (k) {
      var n = d.jobs.filter(function (j) { return j.area === k; }).length;
      if (n) a.insertAdjacentHTML("beforeend", '<option value="' + esc(k) + '">' + esc(AREA[k]) + " (" + n + ")</option>");
    });
    $("src").innerHTML = Object.keys(FUENTE).map(function (k) {
      var f = FUENTE[k];
      return '<li><a href="' + esc(f.home) + '" rel="noopener">' + esc(f.nombre) + "</a> — " + esc(f.condiciones) + "</li>";
    }).join("");
    ["q", "area", "ing", "sal", "mx", "jr"].forEach(function (id) {
      $(id).addEventListener(id === "q" ? "input" : "change", render);
    });
    render();
  }

  fetch("data/jobs.json", { cache: "no-cache" }).then(function (r) {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }).then(init).catch(function () {
    $("list").innerHTML = '<li class="empty">No se pudo cargar data/jobs.json. Si abriste el archivo con doble clic, sírvelo con <code>python -m http.server</code> dentro de la carpeta site.</li>';
  });

  /* Suscripcion: por ahora un mailto con asunto prellenado. */
  var form = $("sub-form");
  if (form) form.addEventListener("submit", function (e) {
    e.preventDefault();
    var mail = $("sub-mail").value.trim();
    var body = "Hola, quiero recibir el boletín semanal de Remoto Junior.\n\nMi correo: " + mail + "\n";
    window.location.href = "mailto:bussnestjesus2005@gmail.com?subject=" +
      encodeURIComponent("Suscripción Remoto Junior") + "&body=" + encodeURIComponent(body);
  });
})();
