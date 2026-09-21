"use strict";
const statusLine = document.getElementById("status");
const csrf = document.querySelector('meta[name="coach-csrf"]').content;
let busy = false;
let hasHistory = false;
function announce(message, failure = false) {
  statusLine.textContent = message;
  statusLine.className = failure ? "notice error" : "";
}
async function api(path, value) {
  const response = await fetch("/coach/" + path, {
    method: value === undefined ? "GET" : "POST",
    credentials: "same-origin", cache: "no-store",
    headers: {"Content-Type": "application/json", "X-Coach-CSRF": csrf},
    body: value === undefined ? undefined : JSON.stringify(value)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The coach is unavailable. Please try again.");
  return data;
}
function showMessage(role, text) {
  const article = document.createElement("article");
  article.className = "message " + role;
  const label = document.createElement("strong");
  label.textContent = role === "user" ? "You" : "Kitchen Coach";
  const content = document.createElement("p");
  content.textContent = text; // Never render model or user input as HTML.
  article.append(label, content);
  document.getElementById("conversation").append(article);
}
function setBusy(value) {
  busy = value;
  document.querySelectorAll("button").forEach(button => button.disabled = value);
  const input = document.getElementById("message");
  if (input) input.readOnly = value;
  document.querySelectorAll("#context-form textarea").forEach(field => field.readOnly = value || hasHistory);
  document.getElementById("message-form")?.setAttribute("aria-busy", String(value));
}
function lockContext() {
  document.getElementById("context-hint").textContent = hasHistory
    ? "Context stays with this conversation. Explain changes in a follow-up, or start another situation to edit it."
    : "Review your context, including any restrictions from earlier follow-ups, before starting.";
  setBusy(false);
}
document.getElementById("login-form")?.addEventListener("submit", async event => {
  event.preventDefault();
  if (busy) return;
  setBusy(true);
  try {
    await api("login", {code: document.getElementById("code").value});
    document.getElementById("code").value = "";
    location.reload();
  } catch (error) { announce(error.message, true); setBusy(false); }
});
document.getElementById("message-form")?.addEventListener("submit", async event => {
  event.preventDefault();
  if (busy || !document.getElementById("context-form").reportValidity()) return;
  const input = document.getElementById("message");
  const text = input.value.trim();
  if (!text) return;
  const profile = Object.fromEntries(new FormData(document.getElementById("context-form")));
  setBusy(true);
  announce("Thinking through your cooking situation…");
  try {
    const data = await api("message", {message: text, profile});
    showMessage("user", text);
    showMessage("assistant", data.reply);
    input.value = "";
    hasHistory = true;
    announce("Ready for your next question.");
  } catch (error) { announce(error.message, true); }
  finally { lockContext(); input.focus(); }
});
document.getElementById("reset")?.addEventListener("click", async () => {
  if (busy) return;
  if (!confirm("Clear this conversation? Household context stays. Carry forward any restrictions or changes from your follow-ups before continuing.")) return;
  setBusy(true);
  try {
    await api("reset", {});
    document.getElementById("conversation").replaceChildren();
    document.getElementById("message").value = "";
    hasHistory = false;
    announce("Ready for another situation. Review your context first.");
  } catch (error) { announce(error.message, true); }
  finally { lockContext(); }
});
document.getElementById("logout")?.addEventListener("click", async () => {
  if (busy) return;
  setBusy(true);
  try { await api("logout", {}); location.reload(); }
  catch (error) { announce(error.message, true); setBusy(false); }
});
if (document.getElementById("context-form")) {
  setBusy(true);
  api("state").then(data => {
    for (const [key, value] of Object.entries(data.profile)) {
      const field = document.getElementById(key);
      if (field) field.value = value;
    }
    data.history.forEach(item => showMessage(item.role, item.content));
    hasHistory = data.history.length > 0;
    lockContext();
  }).catch(error => { announce(error.message, true); setBusy(false); });
}
