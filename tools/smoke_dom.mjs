/** Minimal DOM for the login and codex smoke tests. No packages. */

export class El {
  constructor(tag, attrs = {}) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.parent = null;
    this.classes = new Set();
    this.dataset = {};
    this.listeners = {};
    this.id = attrs.id || "";
    this.type = attrs.type || "";
    this.value = attrs.value || "";
    this.disabled = false;
    this.hidden = Object.prototype.hasOwnProperty.call(attrs, "hidden");
    this._text = "";
    if (attrs.class) {
      for (const name of String(attrs.class).split(/\s+/)) {
        if (name) this.classes.add(name);
      }
    }
    for (const [key, value] of Object.entries(attrs)) {
      if (key.startsWith("data-")) {
        const prop = key
          .slice(5)
          .replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
        this.dataset[prop] = value;
      }
    }
  }

  get textContent() {
    return this._text + this.children.map((child) => child.textContent).join("");
  }

  set textContent(value) {
    this._text = String(value);
    this.children = [];
  }

  get childElementCount() {
    return this.children.length;
  }

  get options() {
    return this.children.filter((child) => child.tagName === "OPTION");
  }

  append(...nodes) {
    for (const node of nodes) {
      node.parent = this;
      this.children.push(node);
    }
  }

  replaceChildren(...nodes) {
    this.children = [];
    if (nodes.length) this.append(...nodes);
  }

  addEventListener(type, fn) {
    (this.listeners[type] ||= []).push(fn);
  }

  dispatch(type) {
    const event = {
      type,
      defaultPrevented: false,
      preventDefault() {
        this.defaultPrevented = true;
      },
    };
    for (const fn of this.listeners[type] || []) fn(event);
    return event;
  }

  click() {
    this.dispatch("click");
  }

  matches(sel) {
    if (sel === "form") return this.tagName === "FORM";
    return matchSelector(this, sel);
  }

  closest(sel) {
    let node = this;
    while (node) {
      if (node.matches(sel)) return node;
      node = node.parent;
    }
    return null;
  }

  querySelector(sel) {
    return this.querySelectorAll(sel)[0] || null;
  }

  querySelectorAll(sel) {
    const found = [];
    const visit = (node) => {
      if (matchSelector(node, sel)) found.push(node);
      for (const child of node.children) visit(child);
    };
    for (const child of this.children) visit(child);
    return found;
  }
}

function matchSelector(node, sel) {
  if (sel.startsWith("#")) return node.id === sel.slice(1);
  if (sel === ".cx-card:not([hidden])") return node.classes.has("cx-card") && !node.hidden;
  if (sel.startsWith(".")) return node.classes.has(sel.slice(1));
  if (sel === "select[data-filter]") return node.tagName === "SELECT" && "filter" in node.dataset;
  return false;
}

export function installBrowser({ search = "", pathname = "/" } = {}) {
  const location = {
    search,
    pathname,
    assigned: "",
    reloaded: false,
    replaced: "",
    assign(url) {
      location.assigned = url;
    },
    reload() {
      location.reloaded = true;
    },
  };
  globalThis.window = { location };
  globalThis.location = location;
  globalThis.history = {
    replaceState(_state, _title, url) {
      location.replaced = url;
    },
  };
  return location;
}

export async function loadScript(source) {
  const { mkdtempSync, writeFileSync } = await import("node:fs");
  const { tmpdir } = await import("node:os");
  const path = await import("node:path");
  const { pathToFileURL } = await import("node:url");
  const dir = mkdtempSync(path.join(tmpdir(), "sephiria-smoke-"));
  const file = path.join(dir, "case.cjs");
  const wrapped = [
    "const document = globalThis.document;",
    "const window = globalThis.window;",
    "const location = globalThis.location;",
    "const history = globalThis.history;",
    "const fetch = globalThis.fetch;",
    source,
  ].join("\n");
  writeFileSync(file, wrapped);
  await import(pathToFileURL(file).href);
}

export async function settle() {
  for (let i = 0; i < 8; i += 1) {
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
}
