const labels = {
  google: "Continue with Google",
  github: "Continue with GitHub",
  x: "Continue with X",
};
const notice = document.querySelector("#notice");
const providersNode = document.querySelector("#providers");
const accountNode = document.querySelector("#account");

function showError(message) {
  notice.textContent = message;
}

async function getJson(path, options) {
  const response = await fetch(path, { cache: "no-store", ...options });
  if (!response.ok) throw new Error("request_failed");
  return response.json();
}

function addProviderButton(provider) {
  if (!labels[provider.id]) return;
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = labels[provider.id];
  button.addEventListener("click", () => {
    window.location.assign(`/api/auth/start?provider=${encodeURIComponent(provider.id)}`);
  });
  providersNode.append(button);
}

function renderAccount(user) {
  accountNode.replaceChildren();
  accountNode.hidden = !user;
  providersNode.hidden = Boolean(user);
  if (!user) return;

  const title = document.createElement("strong");
  title.textContent = user.name || "Signed in";
  accountNode.append(title);

  const provider = document.createElement("p");
  provider.textContent = `Sign-in method: ${user.provider || "Unknown"}`;
  accountNode.append(provider);
  if (user.email) {
    const email = document.createElement("p");
    email.textContent = `Email: ${user.email}`;
    accountNode.append(email);
  }

  const logout = document.createElement("button");
  logout.type = "button";
  logout.textContent = "Log out";
  logout.addEventListener("click", async () => {
    logout.disabled = true;
    try {
      await getJson("/api/auth/logout", { method: "POST" });
      window.location.reload();
    } catch {
      logout.disabled = false;
      showError("Log out failed. Please try again.");
    }
  });
  accountNode.append(logout);
}

async function initialize() {
  const result = new URLSearchParams(window.location.search).get("auth");
  if (result === "error") showError("Sign-in was not completed. Please try again or choose another option.");
  else if (result === "unavailable") showError("This sign-in option is not available right now. Choose another option.");

  try {
    const [{ providers }, { user }] = await Promise.all([
      getJson("/api/auth/providers"),
      getJson("/api/auth/me"),
    ]);
    for (const provider of providers) addProviderButton(provider);
    renderAccount(user);
    if (!user && providersNode.childElementCount === 0) {
      showError("No sign-in options are currently available.");
    }
  } catch {
    showError("The sign-in service is unavailable. Please try again later.");
  }
}

initialize();
