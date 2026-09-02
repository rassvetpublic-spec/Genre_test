"use strict";

const state = { language: "ru", strings: {}, navigation: [], capabilities: [], activeView: "project" };

function text(key, fallback) { return state.strings[key] || fallback || key; }
function setText(id, value) { const el = document.getElementById(id); if (el) el.textContent = value; }
function na() { return text("status.na", "N/A"); }
function valueOrNa(value, suffix = "") { return value == null ? na() : `${value}${suffix}`; }

async function api(path, options = {}) {
  const response = await fetch(path, { cache: "no-store", headers: { "Content-Type": "application/json" }, ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload?.error?.message || text("error.request", "Request failed"));
  return payload;
}

function reasonKey(reason) {
  return `capability.reason.${String(reason || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "")}`;
}

function renderSurface() {
  const item = state.navigation.find((entry) => entry.id === state.activeView);
  const phase = item?.phase || "deferred";
  const ready = phase === "p1";
  setText("surface-phase", phase.toUpperCase());
  setText("surface-title", text(`nav.${state.activeView}`, state.activeView));
  setText("surface-state", ready ? text("status.ready", "Shell ready") : text("status.deferred", "Deferred"));
  let bodyKey = "panel.deferred.body";
  if (state.activeView === "project") bodyKey = "panel.project.body";
  if (state.activeView === "settings") bodyKey = "panel.settings.body";
  setText("surface-body", text(bodyKey));
  const notice = document.getElementById("deferred-notice");
  if (notice) { notice.hidden = ready; notice.textContent = text("panel.deferred.body"); }
  document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("is-active", button.dataset.view === state.activeView));
}

function renderCapabilities() {
  const list = document.getElementById("capability-list");
  if (!list) return;
  list.replaceChildren();
  for (const capability of state.capabilities) {
    const row = document.createElement("li");
    const name = document.createElement("span");
    const status = document.createElement("span");
    name.textContent = text(`capability.${capability.key}`, capability.key);
    const stateLabel = text(`capability.state.${capability.state}`, capability.state);
    const reason = capability.reason ? text(reasonKey(capability.reason), capability.reason) : null;
    status.className = "capability-state";
    status.textContent = reason ? `${stateLabel} · ${reason}` : stateLabel;
    row.append(name, status);
    list.append(row);
  }
}

function renderRuntime(runtime = {}) {
  setText("cpu-value", valueOrNa(runtime.cpu_percent, "%"));
  setText("ram-value", valueOrNa(runtime.ram?.percent, "%"));
  setText("gpu-value", runtime.gpu?.name || na());
  setText("vram-value", valueOrNa(runtime.gpu?.memory_used_mib, " MiB"));
  setText("temperature-value", valueOrNa(runtime.gpu?.temperature_c, " °C"));
  setText("backend-value", runtime.active_backend || na());
  setText("model-value", runtime.active_model || na());
  setText("job-value", runtime.active_job || na());
}

function renderTranslations() {
  document.documentElement.lang = state.language;
  const ids = {
    "app-title": "app.title", "app-subtitle": "app.subtitle", "connection-state": "status.local",
    "language-label": "settings.language", "runtime-title": "panel.runtime.title", "runtime-refresh": "panel.runtime.refresh",
    "cpu-label": "panel.runtime.cpu", "ram-label": "panel.runtime.ram", "gpu-label": "panel.runtime.gpu",
    "vram-label": "panel.runtime.vram", "temperature-label": "panel.runtime.temperature", "backend-label": "panel.runtime.backend",
    "model-label": "panel.runtime.model", "job-label": "panel.runtime.job", "capabilities-title": "panel.capabilities.title",
    "capabilities-body": "panel.capabilities.body", "api-label": "footer.api"
  };
  for (const [id, key] of Object.entries(ids)) setText(id, text(key));
  document.querySelectorAll("[data-view]").forEach((button) => { button.textContent = text(`nav.${button.dataset.view}`, button.dataset.view); });
  renderSurface();
  renderCapabilities();
}

async function loadLanguage(language) {
  const payload = await api(`/api/v1/i18n?lang=${encodeURIComponent(language)}`);
  state.language = payload.language;
  state.strings = payload.strings || {};
  const select = document.getElementById("language-select");
  if (select) select.value = state.language;
  renderTranslations();
}

async function loadRuntime() {
  const error = document.getElementById("runtime-error");
  try {
    const payload = await api("/api/v1/runtime");
    renderRuntime(payload.runtime || {});
    if (error) error.hidden = true;
  } catch (exc) {
    renderRuntime({});
    if (error) { error.hidden = false; error.textContent = `${text("error.runtime")}: ${exc.message}`; }
  }
}

async function initialize() {
  const [health, settings, navigation, capabilities] = await Promise.all([
    api("/api/v1/health"), api("/api/v1/settings"), api("/api/v1/navigation"), api("/api/v1/capabilities")
  ]);
  setText("api-version", health.api_version || "workstation-v1");
  state.navigation = navigation.items || [];
  state.capabilities = capabilities.items || [];
  await loadLanguage(settings.language || "ru");
  renderRuntime({});
}

document.getElementById("navigation")?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-view]");
  if (!button) return;
  state.activeView = button.dataset.view || "project";
  renderSurface();
});
document.getElementById("runtime-refresh")?.addEventListener("click", () => { void loadRuntime(); });
document.getElementById("language-select")?.addEventListener("change", async (event) => {
  const language = event.target.value;
  await api("/api/v1/settings/language", { method: "PUT", body: JSON.stringify({ language }) });
  await loadLanguage(language);
});
initialize().catch((exc) => {
  const error = document.getElementById("runtime-error");
  if (error) { error.hidden = false; error.textContent = `${text("error.request")}: ${exc.message}`; }
});
