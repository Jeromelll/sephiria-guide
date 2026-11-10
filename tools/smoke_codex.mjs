/**
 * Core codex behavior: search and faction filters hide non-matching cards.
 * A script that never hides cards must fail the same assertion.
 */
import { readFileSync } from "node:fs";
import { El, installBrowser, loadScript, settle } from "./smoke_dom.mjs";

const SOURCE = readFileSync(
  new URL("../extra_sites/warhammer-survivors/assets/codex.js", import.meta.url),
  "utf8",
);

function card(id, faction, search, label) {
  const node = new El("article", {
    id,
    class: "cx-card",
    "data-faction": faction,
    "data-search": search,
  });
  node.textContent = label;
  return node;
}

function mount() {
  const search = new El("input", { id: "cx-q", type: "search" });
  const faction = new El("select");
  faction.dataset.filter = "faction";
  for (const value of ["", "40K", "AoS"]) {
    const option = new El("option", { value });
    option.value = value;
    faction.append(option);
  }
  const count = new El("output", { id: "cx-count" });
  const empty = new El("p", { id: "cx-empty", hidden: true });
  const form = new El("form");
  form.append(search, faction);
  const caedo = card("malum-caedo", "40K", "malum caedo chainsword", "Malum Caedo");
  const neave = card("neave-blacktalon", "AoS", "neave blacktalon axes", "Neave Blacktalon");
  const group40 = new El("section", { class: "cx-group" });
  group40.append(caedo);
  const groupAoS = new El("section", { class: "cx-group" });
  groupAoS.append(neave);
  const root = new El("div");
  root.append(form, empty, group40, groupAoS);
  const byId = { "cx-q": search, "cx-count": count, "cx-empty": empty };
  globalThis.document = {
    getElementById(id) {
      return byId[id] || null;
    },
    querySelector(sel) {
      return root.querySelector(sel);
    },
    querySelectorAll(sel) {
      return root.querySelectorAll(sel);
    },
    createElement(tag) {
      return new El(tag);
    },
  };
  return { search, faction, count, empty, form, caedo, neave, group40, groupAoS };
}

async function runCase(source) {
  installBrowser({ pathname: "/codex/characters/" });
  const ui = mount();
  await loadScript(source);
  await settle();
  return ui;
}

function visible(ui) {
  return [ui.caedo, ui.neave].filter((node) => !node.hidden).map((node) => node.id);
}

async function assertFilters(source) {
  const ui = await runCase(source);
  if (visible(ui).join(",") !== "malum-caedo,neave-blacktalon") {
    throw new Error(`initial visible cards: ${visible(ui).join(",")}`);
  }
  if (ui.count.textContent !== "2 of 2 entries") {
    throw new Error(`initial count was ${JSON.stringify(ui.count.textContent)}`);
  }
  const submit = ui.form.dispatch("submit");
  if (!submit.defaultPrevented) throw new Error("search submit reloads the page");

  ui.search.value = "caedo";
  ui.search.dispatch("change");
  if (visible(ui).join(",") !== "malum-caedo") {
    throw new Error(`search visible cards: ${visible(ui).join(",") || "(none)"}`);
  }
  if (!ui.groupAoS.hidden || ui.group40.hidden) {
    throw new Error("search did not collapse the empty faction group");
  }
  if (ui.empty.hidden !== true) throw new Error("empty note showed while a card matched");

  ui.search.value = "";
  ui.faction.value = "AoS";
  ui.faction.dispatch("change");
  if (visible(ui).join(",") !== "neave-blacktalon") {
    throw new Error(`faction visible cards: ${visible(ui).join(",") || "(none)"}`);
  }

  ui.faction.value = "";
  ui.search.value = "no-such-champion";
  ui.search.dispatch("change");
  if (visible(ui).length !== 0 || ui.empty.hidden) {
    throw new Error("a miss did not show the empty note");
  }
  if (ui.count.textContent !== "0 of 2 entries") {
    throw new Error(`empty count was ${JSON.stringify(ui.count.textContent)}`);
  }
}

async function main() {
  await assertFilters(SOURCE);
  console.log("PASS codex search, faction filter, empty note, and submit stay on the page");

  const broken = SOURCE.replace("card.hidden = !show", "card.hidden = false");
  if (broken === SOURCE) throw new Error("could not build the codex counterexample");
  let counterFailed = false;
  try {
    await assertFilters(broken);
  } catch (err) {
    counterFailed = /visible cards|empty note|empty count/.test(String(err.message || err));
  }
  if (!counterFailed) {
    throw new Error("counterexample that never hides cards was accepted");
  }
  console.log("PASS counterexample that never hides cards failed the assertion");
}

main().catch((err) => {
  console.error("FAIL", err && err.stack ? err.stack : err);
  process.exit(1);
});
