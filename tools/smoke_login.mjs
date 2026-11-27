/**
 * Core sign-in behavior of assets/login.js.
 *
 * The real script must show auth errors, start the chosen provider, render a
 * signed-in account, and surface a failed log out. A rewritten start URL is
 * loaded as a counterexample and must fail that assertion.
 */
import { readFileSync } from "node:fs";
import { El, installBrowser, loadScript, settle } from "./smoke_dom.mjs";

const SOURCE = readFileSync(new URL("../assets/login.js", import.meta.url), "utf8");

function button(label) {
  const providers = globalThis.document.querySelector("#providers");
  return providers.children.find((node) => node.textContent === label);
}

function dom() {
  const notice = new El("p", { id: "notice" });
  const account = new El("section", { id: "account", hidden: true });
  const providers = new El("div", { id: "providers" });
  globalThis.document = {
    querySelector(sel) {
      return { "#notice": notice, "#account": account, "#providers": providers }[sel] || null;
    },
    createElement(tag) {
      return new El(tag);
    },
  };
  return { notice, account, providers };
}

function jsonResponse(ok, body) {
  return { ok, json: async () => body };
}

async function boot(source, { search = "", fetchImpl }) {
  installBrowser({ search, pathname: "/login.html" });
  dom();
  globalThis.fetch = fetchImpl;
  await loadScript(source);
  await settle();
}

async function assertProviderStart(source) {
  const location = installBrowser({ pathname: "/login.html" });
  dom();
  globalThis.fetch = async (path) => {
    if (path === "/api/auth/providers") {
      return jsonResponse(true, { providers: [{ id: "google" }, { id: "github" }, { id: "unknown" }] });
    }
    if (path === "/api/auth/me") return jsonResponse(true, { user: null });
    return jsonResponse(false, {});
  };
  await loadScript(source);
  await settle();
  const google = button("Continue with Google");
  const github = button("Continue with GitHub");
  if (!google || !github) throw new Error("known providers did not render");
  if (button("unknown")) throw new Error("unknown provider rendered a button");
  google.click();
  if (location.assigned !== "/api/auth/start?provider=google") {
    throw new Error(`start URL was ${location.assigned || "(empty)"}`);
  }
}

async function main() {
  await boot(SOURCE, {
    search: "?auth=error",
    fetchImpl: async (path) => {
      if (path === "/api/auth/providers") return jsonResponse(true, { providers: [{ id: "google" }] });
      if (path === "/api/auth/me") return jsonResponse(true, { user: null });
      return jsonResponse(false, {});
    },
  });
  const errorText = globalThis.document.querySelector("#notice").textContent;
  if (!errorText.includes("Sign-in was not completed")) {
    throw new Error(`auth=error notice was ${JSON.stringify(errorText)}`);
  }
  console.log("PASS auth=error stays visible after providers load");

  await assertProviderStart(SOURCE);
  console.log("PASS provider button starts /api/auth/start?provider=google");

  const broken = SOURCE.replace(
    "/api/auth/start?provider=",
    "/broken-start?provider=",
  );
  if (broken === SOURCE) throw new Error("could not build the login counterexample");
  let counterFailed = false;
  try {
    await assertProviderStart(broken);
  } catch (err) {
    counterFailed = String(err.message || err).includes("start URL was");
  }
  if (!counterFailed) {
    throw new Error("counterexample with a rewritten start URL was accepted");
  }
  console.log("PASS counterexample rewritten start URL failed the assertion");

  await boot(SOURCE, {
    fetchImpl: async (path) => {
      if (path === "/api/auth/providers") return jsonResponse(true, { providers: [{ id: "github" }] });
      if (path === "/api/auth/me") {
        return jsonResponse(true, {
          user: { name: "Ada", provider: "github", email: "ada@example.com" },
        });
      }
      if (path === "/api/auth/logout") return jsonResponse(false, {});
      return jsonResponse(false, {});
    },
  });
  const account = globalThis.document.querySelector("#account");
  const providers = globalThis.document.querySelector("#providers");
  if (account.hidden || !providers.hidden) throw new Error("signed-in view did not hide providers");
  if (!account.textContent.includes("Ada") || !account.textContent.includes("ada@example.com")) {
    throw new Error(`account text was ${JSON.stringify(account.textContent)}`);
  }
  const logout = account.children.find((node) => node.textContent === "Log out");
  if (!logout) throw new Error("log out button missing");
  logout.click();
  await settle();
  const logoutNotice = globalThis.document.querySelector("#notice").textContent;
  if (!logoutNotice.includes("Log out failed")) {
    throw new Error(`logout failure notice was ${JSON.stringify(logoutNotice)}`);
  }
  if (logout.disabled) throw new Error("failed log out left the button disabled");
  console.log("PASS signed-in account renders, and a failed log out asks to retry");

  await boot(SOURCE, {
    fetchImpl: async (path) => {
      if (path === "/api/auth/providers") return jsonResponse(true, { providers: [{ id: "nope" }] });
      if (path === "/api/auth/me") return jsonResponse(true, { user: null });
      return jsonResponse(false, {});
    },
  });
  const empty = globalThis.document.querySelector("#notice").textContent;
  if (!empty.includes("No sign-in options")) {
    throw new Error(`empty providers notice was ${JSON.stringify(empty)}`);
  }
  console.log("PASS no known providers tells the visitor there is nothing to click");

  await boot(SOURCE, {
    fetchImpl: async () => {
      throw new Error("offline");
    },
  });
  const down = globalThis.document.querySelector("#notice").textContent;
  if (!down.includes("sign-in service is unavailable")) {
    throw new Error(`offline notice was ${JSON.stringify(down)}`);
  }
  console.log("PASS a failed session request says the sign-in service is unavailable");
}

main().catch((err) => {
  console.error("FAIL", err && err.stack ? err.stack : err);
  process.exit(1);
});
