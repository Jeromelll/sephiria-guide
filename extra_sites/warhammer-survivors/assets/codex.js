/* codex.js — lightweight client-side filtering for the codex fan-wiki. */
(function () {
  'use strict';

  const searchBox = document.getElementById('cx-q');
  if (!searchBox) return;

  const form = searchBox.closest('form');
  const cards = Array.from(document.querySelectorAll('.cx-card'));
  const groups = Array.from(document.querySelectorAll('.cx-group'));
  const selects = Array.from(document.querySelectorAll('select[data-filter]'));
  const countEl = document.getElementById('cx-count');
  const emptyEl = document.getElementById('cx-empty');

  /* True when the card matches every active <select> filter. */
  function matchesSelects(card) {
    return selects.every((sel) => {
      const want = sel.value.toLowerCase();
      return !want || (card.dataset[sel.dataset.filter] || '').toLowerCase() === want;
    });
  }

  /* Apply current controls to every card, group, counter and empty note. */
  function apply() {
    const tokens = searchBox.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    let visible = 0;

    for (const card of cards) {
      const haystack = (card.dataset.search || card.textContent).toLowerCase();
      const show = tokens.every((t) => haystack.includes(t)) && matchesSelects(card);
      card.hidden = !show;
      if (show) visible++;
    }

    /* Hide whole groups with no visible cards. */
    for (const group of groups) {
      group.hidden = !group.querySelector('.cx-card:not([hidden])');
    }

    if (countEl) {
      countEl.textContent = visible + ' of ' + cards.length + (cards.length === 1 ? ' entry' : ' entries');
    }
    if (emptyEl) emptyEl.hidden = visible > 0;
  }

  /* Mirror q + filter values into the URL, omitting empty params. */
  function syncUrl() {
    const params = new URLSearchParams();
    if (searchBox.value.trim()) params.set('q', searchBox.value.trim());
    for (const sel of selects) {
      if (sel.value) params.set(sel.dataset.filter, sel.value);
    }
    const qs = params.toString();
    history.replaceState(null, '', qs ? location.pathname + '?' + qs : location.pathname);
  }

  function run() {
    apply();
    syncUrl();
  }

  /* Restore initial state from ?q= and filter params (valid option values only). */
  const initial = new URLSearchParams(location.search);
  if (initial.has('q')) searchBox.value = initial.get('q');
  for (const sel of selects) {
    const v = initial.get(sel.dataset.filter);
    if (v && Array.from(sel.options).some((opt) => opt.value === v)) sel.value = v;
  }

  /* Debounced free-text input; selects react immediately. */
  let timer;
  searchBox.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(run, 120);
  });
  searchBox.addEventListener('change', run);
  for (const sel of selects) sel.addEventListener('change', run);

  /* Keep Enter from reloading; re-filter after the native reset clears controls. */
  form.addEventListener('submit', (e) => e.preventDefault());
  form.addEventListener('reset', () => setTimeout(run, 0));

  apply();
})();
