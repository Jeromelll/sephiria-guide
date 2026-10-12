import { PROVIDERS, fetchOAuthProfile } from "./oauth.js";

const SESSION_COOKIE = "site_auth_sid";
const STATE_COOKIE = "site_auth_state";
const SESSION_SECONDS = 30 * 24 * 60 * 60;
const STATE_SECONDS = 30 * 60;

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}

function canonicalOrigin(env) {
  let origin;
  try {
    origin = new URL(env?.AUTH_ORIGIN);
  } catch {
    throw new Error("AUTH_ORIGIN must be a canonical HTTPS origin");
  }
  if (origin.protocol !== "https:" || origin.origin !== env.AUTH_ORIGIN || origin.pathname !== "/" || origin.search || origin.hash) {
    throw new Error("AUTH_ORIGIN must be a canonical HTTPS origin");
  }
  return origin.origin;
}

function cookieValue(request, name) {
  const cookie = request.headers.get("cookie") ?? "";
  for (const part of cookie.split(";")) {
    const separator = part.indexOf("=");
    if (separator < 0 || part.slice(0, separator).trim() !== name) continue;
    return part.slice(separator + 1).trim();
  }
  return null;
}

function randomToken(bytes = 32) {
  const raw = new Uint8Array(bytes);
  crypto.getRandomValues(raw);
  let binary = "";
  for (const value of raw) binary += String.fromCharCode(value);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

async function pkceChallenge(verifier) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  let binary = "";
  for (const value of new Uint8Array(digest)) binary += String.fromCharCode(value);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

function cookie(name, value, maxAge) {
  return `${name}=${value}; Path=/; Max-Age=${maxAge}; HttpOnly; Secure; SameSite=Lax`;
}

function loginRedirect(origin, result) {
  const location = new URL("/login.html", origin);
  if (result) location.searchParams.set("auth", result);
  return new Response(null, {
    status: 302,
    headers: {
      location: location.href,
      "cache-control": "no-store",
      "referrer-policy": "no-referrer",
    },
  });
}

function configuredProviders(env) {
  const credentialNames = {
    google: ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
    github: ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"],
    x: ["X_CLIENT_ID", "X_CLIENT_SECRET"],
  };
  return Object.keys(PROVIDERS).filter((id) =>
    credentialNames[id].every((key) => typeof env?.[key] === "string" && env[key].length > 0),
  );
}

function encodeKeyPart(value) {
  return encodeURIComponent(value);
}

function accountKey(provider, sub) {
  return `user:${encodeKeyPart(provider)}:${encodeKeyPart(sub)}`;
}

function profileForStorage(profile, provider) {
  return {
    provider,
    sub: profile.sub,
    name: profile.name,
    email: profile.email,
    picture: profile.picture,
  };
}

function publicUser(user) {
  return {
    provider: user.provider,
    name: user.name,
    email: user.email ?? null,
    picture: user.picture ?? null,
  };
}

async function handleStart(request, env, url, origin, kv) {
  const providerId = url.searchParams.get("provider");
  const providers = configuredProviders(env);
  if (!providers.includes(providerId)) return loginRedirect(origin, "unavailable");

  let requestOrigin;
  try {
    requestOrigin = new URL(request.url).origin;
  } catch {
    return json({ error: "invalid_request" }, 400);
  }
  if (requestOrigin !== origin) {
    const canonicalStart = new URL("/api/auth/start", origin);
    canonicalStart.searchParams.set("provider", providerId);
    return new Response(null, {
      status: 302,
      headers: { location: canonicalStart.href, "cache-control": "no-store", "referrer-policy": "no-referrer" },
    });
  }

  const state = randomToken();
  const record = { provider: providerId, createdAt: Date.now() };
  const authorize = new URL(PROVIDERS[providerId].authorizeUrl);
  authorize.searchParams.set("client_id", env[`${providerId.toUpperCase()}_CLIENT_ID`]);
  authorize.searchParams.set("redirect_uri", `${origin}/api/auth/callback`);
  authorize.searchParams.set("response_type", "code");
  authorize.searchParams.set("scope", PROVIDERS[providerId].scope);
  authorize.searchParams.set("state", state);

  if (providerId === "x") {
    const verifier = randomToken(48);
    const challenge = await pkceChallenge(verifier);
    record.verifier = verifier;
    authorize.searchParams.set("code_challenge", challenge);
    authorize.searchParams.set("code_challenge_method", "S256");
  }
  await kv.put(`state:${state}`, JSON.stringify(record), { expirationTtl: STATE_SECONDS });
  return new Response(null, {
    status: 302,
    headers: {
      location: authorize.href,
      "set-cookie": cookie(STATE_COOKIE, state, STATE_SECONDS),
      "cache-control": "no-store",
      "referrer-policy": "no-referrer",
    },
  });
}

async function handleCallback(request, env, url, origin, kv) {
  const state = url.searchParams.get("state");
  const code = url.searchParams.get("code");
  const cookieState = cookieValue(request, STATE_COOKIE);
  if (!state || !cookieState || state !== cookieState || !code || url.searchParams.has("error")) {
    return loginRedirect(origin, "error");
  }

  const rawState = await kv.get(`state:${state}`);
  if (!rawState) return loginRedirect(origin, "error");
  await kv.delete(`state:${state}`);

  let stateRecord;
  try {
    stateRecord = JSON.parse(rawState);
  } catch {
    return loginRedirect(origin, "error");
  }
  if (
    !stateRecord ||
    !Object.hasOwn(PROVIDERS, stateRecord.provider) ||
    !configuredProviders(env).includes(stateRecord.provider) ||
    !Number.isFinite(stateRecord.createdAt) ||
    Date.now() - stateRecord.createdAt > STATE_SECONDS * 1000 ||
    Date.now() < stateRecord.createdAt
  ) {
    return loginRedirect(origin, "error");
  }

  try {
    const profile = await fetchOAuthProfile(
      stateRecord.provider,
      env,
      code,
      `${origin}/api/auth/callback`,
      stateRecord.verifier,
    );
    if (
      typeof profile?.sub !== "string" || profile.sub.trim() === "" ||
      (profile.name !== null && typeof profile.name !== "string") ||
      (profile.email !== null && typeof profile.email !== "string") ||
      (profile.picture !== null && typeof profile.picture !== "string")
    ) {
      return loginRedirect(origin, "error");
    }

    const user = profileForStorage(profile, stateRecord.provider);
    const sid = randomToken();
    await kv.put(accountKey(user.provider, user.sub), JSON.stringify(user));
    await kv.put(`session:${sid}`, JSON.stringify(user), { expirationTtl: SESSION_SECONDS });
    const response = loginRedirect(origin, "success");
    response.headers.append("set-cookie", cookie(SESSION_COOKIE, sid, SESSION_SECONDS));
    response.headers.append("set-cookie", cookie(STATE_COOKIE, "", 0));
    return response;
  } catch {
    return loginRedirect(origin, "error");
  }
}

export async function handleAuth(request, env) {
  let url;
  try {
    url = new URL(request.url);
  } catch {
    return null;
  }
  if (!url.pathname.startsWith("/api/auth/")) return null;

  if (!env?.AUTH_USERS || typeof env.AUTH_USERS.get !== "function" || typeof env.AUTH_USERS.put !== "function") {
    return json({ error: "auth_unavailable" }, 503);
  }

  let origin;
  try {
    origin = canonicalOrigin(env);
  } catch {
    return json({ error: "auth_unavailable" }, 503);
  }

  const kv = env.AUTH_USERS;
  const path = url.pathname;
  const method = request.method.toUpperCase();

  if (path === "/api/auth/providers" && method === "GET") {
    return json({ providers: configuredProviders(env).map((id) => ({ id, name: PROVIDERS[id].name })) });
  }
  if (path === "/api/auth/start" && method === "GET") {
    return handleStart(request, env, url, origin, kv);
  }
  if (path === "/api/auth/callback" && method === "GET") {
    if (url.origin !== origin) return loginRedirect(origin, "error");
    return handleCallback(request, env, url, origin, kv);
  }
  if (path === "/api/auth/me" && method === "GET") {
    const sid = cookieValue(request, SESSION_COOKIE);
    if (!sid) return json({ user: null });
    const raw = await kv.get(`session:${sid}`);
    if (!raw) return json({ user: null });
    try {
      return json({ user: publicUser(JSON.parse(raw)) });
    } catch {
      return json({ user: null });
    }
  }
  if (path === "/api/auth/logout" && method === "POST") {
    const requestOrigin = request.headers.get("origin");
    if (requestOrigin !== null && requestOrigin !== origin) {
      return json({ error: "forbidden" }, 403);
    }
    const sid = cookieValue(request, SESSION_COOKIE);
    if (sid) await kv.delete(`session:${sid}`);
    const response = json({ ok: true });
    response.headers.append("set-cookie", cookie(SESSION_COOKIE, "", 0));
    return response;
  }

  return json({ error: "not_found" }, 404);
}
