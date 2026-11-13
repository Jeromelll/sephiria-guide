/*
  Client-side guide search for the portal home.

  Loads /assets/search-index.json (title + description + path for every
  indexable page, written by build.py) and filters it as the visitor types.
  No network call happens until the field is focused, so the home page stays
  as light as it was before the search box existed.
*/
(function () {
  var input = document.getElementById("guide-search");
  var list = document.getElementById("guide-search-results");
  var empty = document.getElementById("guide-search-empty");
  if (!input || !list || !empty) return;

  var index = null;
  var loading = null;

  function load() {
    if (index) return Promise.resolve(index);
    if (loading) return loading;
    var url = (document.body.getAttribute("data-root") || "") + "/assets/search-index.json";
    loading = fetch(url, { credentials: "omit" })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (rows) { index = rows; return rows; })
      .catch(function () { index = []; return index; });
    return loading;
  }

  function score(row, q) {
    var t = row.t.toLowerCase();
    var d = (row.d || "").toLowerCase();
    if (t.indexOf(q) === 0) return 3;
    if (t.indexOf(q) !== -1) return 2;
    if (d.indexOf(q) !== -1) return 1;
    return 0;
  }

  function render(rows, q) {
    list.replaceChildren();
    var hits = rows
      .map(function (row) { return { row: row, s: score(row, q) }; })
      .filter(function (h) { return h.s > 0; })
      .sort(function (a, b) { return b.s - a.s || a.row.t.localeCompare(b.row.t); })
      .slice(0, 8);

    if (!hits.length) {
      list.hidden = true;
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    hits.forEach(function (h) {
      var a = document.createElement("a");
      a.href = h.row.p;
      var strong = document.createElement("strong");
      strong.textContent = h.row.t;
      var em = document.createElement("em");
      em.textContent = (h.row.d || "").slice(0, 96);
      a.append(strong, em);
      var li = document.createElement("li");
      li.append(a);
      list.append(li);
    });
    list.hidden = false;
  }

  function run() {
    var q = input.value.trim().toLowerCase();
    if (!q) {
      list.hidden = true;
      empty.hidden = true;
      return;
    }
    load().then(function (rows) { render(rows, q); });
  }

  input.addEventListener("focus", load, { once: true });
  input.addEventListener("input", run);
})();
