"use strict";

const state = {
  language: "ru",
  strings: {},
  navigation: [],
  capabilities: new Map(),
  activeView: "project",
};

function text(key, fallback) {
  return state.strings[key] || fallback || key;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    const message = payload?.error?.message || `${text("error.request", "Request failed")} (${response.status})`;
    throw new Error(message);
  }
  return payload;
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function na() {
  return text("status.na", "N/A");
}

function valueOrNa(value, suffix = "") {
  return value === null || value === undefined ? na() : `${value}${suffix}`;
}

function renderTranslations() {
  document.documentElement.lang = state.language;
  setText("app-title", text("app.title", "Genre_test Workstation"));
  setText("app-subtitle", text("app.subtitle", "Local-first studio workspace"));
  setText("connection-state", text("status.local", "Local workstation"));
  setText("language-label", text("settings.language", "Language"));
  setText("runtime-title", text("panel.runtime.title", "Runtime"));
  setText("runtime-refresh", text("panel.runtime.refresh", "Refresh runtime"));
  setText("cpu-label", text("panel.runtime.cpu", "CPU"));
  setText("ram-label", text("panel.runtime.ram", "RAM"));
  setText("gpu-label", text("panel.runtime.gpu", "GPU"));
  setText("vram-label", text("panel.runtime.vram", "VRAM"));
  setText("temperature-label", text("panel.runtime.temperature", "Temperature"));
  setText("backend-label", text("panel.runtime.backend", "Backend"));
  setText("model-label", text("panel.runtime.model", "Model"));
  setText("job-label", text("panel.runtime.job", "Job"));
  setText("capabilities-title", text("panel.capabilities.title", "Capabilities"));
  setText("capabilities-body", text("panel.capabilities.body", "P1 capability status."));
  setText("api-label", text("footer.api", "Workstation API"));

  document.querySelectorAll("[data-view]").forEach((button) => {
    const view = button.dataset.view;
    button.textContent = text(`nav.${view}`, view);
  });
  renderSurface();
  renderCapabilities();
}

function renderSurface() {
  const item = state.navigation.find((entry) => entry.id === state.activeView);
  const phase = item?.phase || "deferred";
  const isReady = phase === "p1";
  setText("surface-phase", phase.toUpperCase());
  setText("surface-title", text(`nav.${state.activeView}`, state.activeView));
  setText("surface-state", isReady ? text("status.ready", "Shell ready") : text("status.deferred", "Deferred"));
  setText(
    "surface-body",
    state.activeView === "project"
      ? text("panel.project.body", "Project service surface")
      : text("panel.deferred.body", "This execution surface is deferred to its owning Workstation phase."),
  );
  const notice = document.getElementById("deferred-notice");
  if (notice) {
    notice.hidden = isReady;
    notice.textContent = text("panel.deferred.body", "Deferred to a later Workstation phase.");
  }
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === state.activeView);
  });
}

function renderCapabilities() {
  const list = document.getElementById("capability-list");
  if (!list) return;
  list.replaceChildren();
  for (const [key, capability] of state.capabilities.entries()) {
    const row = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = key;
    const status = document.createElement("span");
    status.className = "capability-state";
    status.textContent = capability.reason ? `${capability.state} · ${capability.reason}` : capability.state;
    row.append(name, status);
    list.append(row);
  }
}

function renderRuntime(runtime) {
  setText("cpu-value", valueOrNa(runtime.cpu_percent, "%"));
  setText("ram-value", valueOrNa(runtime.ram?.percent, "%"));
  setText("gpu-value", runtime.gpu?.name || na());
  setText("vram-value", valueOrNa(runtime.gpu?.memory_used_mib, " MiB"));
  setText("temperature-value", valueOrNa(runtime.gpu?.temperature_c, " °C"));
  setText("backend-value", runtime.active_backend || na());
  setText("model-value", runtime.active_model || na());
  setText("job-value", runtime.active_job || na());
}

async function loadRuntime() {
  const error = document.getElementById("runtime-error");
  try {
    const payload = await api("/api/v1/runtime");
    renderRuntime(payload.runtime || {});
    if (error) error.hidden = true;
  } catch (exc) {
    renderRuntime({});
    if (error) {
      error.hidden = false;
      error.textContent = `${text("error.runtime", "Runtime telemetry is unavailable")}: ${exc.message}`;
    }
  }
}

async function loadLanguage(language) {
  const payload = await api(`/api/v1/i18n?lang=${encodeURIComponent(language)}`);
  state.language = payload.language;
  state.strings = payload.strings || {};
  const select = document.getElementById("language-select");
  if (select) select.value = state.language;
  renderTranslations();
}

async function initialize() {
  const [health, settings, navigation, capabilities] = await Promise.all([
    api("/api/v1/health"),
    api("/api/v1/settings"),
    api("/api/v1/navigation"),
    api("/api/v1/capabilities"),
  ]);
  setText("api-version", health.api_version || "workstation-v1");
  state.navigation = navigation.items || [];
  state.capabilities = new Map((capabilities.items || []).map((item) => [item.key, item]));
  await loadLanguage(settings.language || "ru");
  await loadRuntime();
}

document.getElementById("navigation")?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-view]");
  if (!button) return;
  state.activeView = button.dataset.view || "project";
  renderSurface();
});

document.getElementById("runtime-refresh")?.addEventListener("click", () => {
  void loadRuntime();
});

document.getElementById("language-select")?.addEventListener("change", async (event) => {
  const language = event.target.value;
  try {
    await api("/api/v1/settings/language", {
      method: "PUT",
      body: JSON.stringify({ language }),
    });
    await loadLanguage(language);
  } catch (exc) {
    const error = document.getElementById("runtime-error");
    if (error) {
      error.hidden = false;
      error.textContent = `${text("error.request", "Request failed")}: ${exc.message}`;
    }
  }
});

initialize().catch((exc) => {
  const error = document.getElementById("runtime-error");
  if (error) {
    error.hidden = false;
    error.textContent = `${text("error.request", "Request failed")}: ${exc.message}`;
  }
});
