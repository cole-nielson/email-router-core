import { n as noop, c as create_ssr_component, v as validate_component, f as get_store_value, b as subscribe, h as assign, i as identity, j as createEventDispatcher, d as escape, m as missing_component, o as onDestroy, e as each } from "../../chunks/ssr.js";
import "../../chunks/client.js";
import { d as derived, w as writable } from "../../chunks/index.js";
import { I as Icon, A as Alert_triangle, C as Check_circle, X as X_circle } from "../../chunks/x-circle.js";
import { formatDistanceToNow } from "date-fns";
const is_client = typeof window !== "undefined";
let now = is_client ? () => window.performance.now() : () => Date.now();
let raf = is_client ? (cb) => requestAnimationFrame(cb) : noop;
const tasks = /* @__PURE__ */ new Set();
function run_tasks(now2) {
  tasks.forEach((task) => {
    if (!task.c(now2)) {
      tasks.delete(task);
      task.f();
    }
  });
  if (tasks.size !== 0) raf(run_tasks);
}
function loop(callback) {
  let task;
  if (tasks.size === 0) raf(run_tasks);
  return {
    promise: new Promise((fulfill) => {
      tasks.add(task = { c: callback, f: fulfill });
    }),
    abort() {
      tasks.delete(task);
    }
  };
}
function cubicOut(t) {
  const f = t - 1;
  return f * f * f + 1;
}
const Activity = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "M22 12h-4l-3 9L9 3l-3 9H2" }]];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "activity" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Bar_chart_3 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M3 3v18h18" }],
    ["path", { "d": "M18 17V9" }],
    ["path", { "d": "M13 17V5" }],
    ["path", { "d": "M8 17v-3" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "bar-chart-3" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Clock = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["polyline", { "points": "12 6 12 12 16 14" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "clock" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Globe = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    [
      "path",
      {
        "d": "M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"
      }
    ],
    ["path", { "d": "M2 12h20" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "globe" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Mail = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "rect",
      {
        "width": "20",
        "height": "16",
        "x": "2",
        "y": "4",
        "rx": "2"
      }
    ],
    [
      "path",
      {
        "d": "m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"
      }
    ]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "mail" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Minus = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "M5 12h14" }]];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "minus" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const More_horizontal = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "1" }],
    ["circle", { "cx": "19", "cy": "12", "r": "1" }],
    ["circle", { "cx": "5", "cy": "12", "r": "1" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "more-horizontal" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Plus = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "M5 12h14" }], ["path", { "d": "M12 5v14" }]];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "plus" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Refresh_cw = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"
      }
    ],
    ["path", { "d": "M21 3v5h-5" }],
    [
      "path",
      {
        "d": "M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"
      }
    ],
    ["path", { "d": "M8 16H3v5" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "refresh-cw" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Settings = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
      }
    ],
    ["circle", { "cx": "12", "cy": "12", "r": "3" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "settings" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Trending_down = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["polyline", { "points": "22 17 13.5 8.5 8.5 13.5 2 7" }],
    ["polyline", { "points": "16 17 22 17 22 11" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "trending-down" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Trending_up = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["polyline", { "points": "22 7 13.5 15.5 8.5 10.5 2 17" }],
    ["polyline", { "points": "16 7 22 7 22 13" }]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "trending-up" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Zap = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "polygon",
      {
        "points": "13 2 3 14 12 14 11 22 21 10 12 10 13 2"
      }
    ]
  ];
  return `  ${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "zap" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
class ApiError extends Error {
  constructor(message, status, response) {
    super(message);
    this.status = status;
    this.response = response;
    this.name = "ApiError";
  }
}
class ApiClient {
  baseUrl;
  token = null;
  constructor(baseUrl) {
    this.baseUrl = baseUrl || (typeof window !== "undefined" ? window.location.origin : "http://localhost:8080");
  }
  setToken(token) {
    this.token = token;
  }
  clearToken() {
    this.token = null;
  }
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}/api/v1${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...options.headers || {}
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    try {
      const response = await fetch(url, {
        ...options,
        headers
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }
      const data = await response.json();
      return data;
    } catch (error2) {
      if (error2 instanceof ApiError) {
        throw error2;
      }
      throw new ApiError(`Network error: ${error2 instanceof Error ? error2.message : "Unknown error"}`, 0);
    }
  }
  // Authentication methods
  async login(email, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
  }
  async refreshToken(refreshToken) {
    return this.request("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken })
    });
  }
  async logout() {
    return this.request("/auth/logout", {
      method: "POST"
    });
  }
  // Client methods
  async getClients(page = 1, pageSize = 20) {
    return this.request(`/clients?page=${page}&page_size=${pageSize}`);
  }
  async getClient(clientId2) {
    return this.request(`/clients/${clientId2}`);
  }
  async validateClient(clientId2) {
    return this.request(`/clients/${clientId2}/validate`, {
      method: "POST"
    });
  }
  // Metrics and analytics methods
  async getClientMetrics(clientId2, timeframe = "24h") {
    return this.request(`/clients/${clientId2}/metrics?timeframe=${timeframe}`);
  }
  async getClientActivity(clientId2, limit = 50, offset = 0) {
    return this.request(`/clients/${clientId2}/activity?limit=${limit}&offset=${offset}`);
  }
  async getSystemStatus() {
    return this.request("/status");
  }
  // Integration methods
  async getIntegrations(clientId2) {
    return this.request(`/clients/${clientId2}/integrations`);
  }
  async testIntegration(clientId2, integrationId) {
    return this.request(`/clients/${clientId2}/integrations/${integrationId}/test`, {
      method: "POST"
    });
  }
  // Automation methods
  async getAutomations(clientId2) {
    return this.request(`/clients/${clientId2}/automations`);
  }
  async getAutomationStatus(clientId2, automationId) {
    return this.request(`/clients/${clientId2}/automations/${automationId}/status`);
  }
  async pauseAutomation(clientId2, automationId) {
    return this.request(`/clients/${clientId2}/automations/${automationId}/pause`, {
      method: "POST"
    });
  }
  async resumeAutomation(clientId2, automationId) {
    return this.request(`/clients/${clientId2}/automations/${automationId}/resume`, {
      method: "POST"
    });
  }
  // Alert methods
  async getAlerts(clientId2, resolved = false) {
    return this.request(`/clients/${clientId2}/alerts?resolved=${resolved}`);
  }
  async resolveAlert(clientId2, alertId) {
    return this.request(`/clients/${clientId2}/alerts/${alertId}/resolve`, {
      method: "POST"
    });
  }
  // Domain resolution
  async resolveDomain(domain) {
    return this.request(`/domain/resolve?domain=${encodeURIComponent(domain)}`, {
      method: "POST"
    });
  }
}
const apiClient = new ApiClient();
async function withRetry(operation, maxRetries = 3, delay = 1e3) {
  let lastError;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error2) {
      lastError = error2 instanceof Error ? error2 : new Error("Unknown error");
      if (attempt === maxRetries) {
        throw lastError;
      }
      await new Promise((resolve) => setTimeout(resolve, delay * Math.pow(2, attempt - 1)));
    }
  }
  throw lastError;
}
function formatApiError(error2) {
  if (error2 instanceof ApiError) {
    return error2.message;
  }
  if (error2 instanceof Error) {
    return error2.message;
  }
  return "An unexpected error occurred";
}
class DashboardWebSocket {
  ws = null;
  url;
  clientId;
  token;
  reconnectAttempts = 0;
  maxReconnectAttempts = 10;
  reconnectDelay = 1e3;
  handlers = /* @__PURE__ */ new Map();
  isConnecting = false;
  shouldReconnect = true;
  constructor(clientId2, token, baseUrl) {
    this.clientId = clientId2;
    this.token = token;
    if (typeof window !== "undefined") {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = baseUrl ? new URL(baseUrl).host : window.location.host;
      this.url = `${protocol}//${host}/ws/client/${clientId2}`;
    } else {
      this.url = `ws://localhost:8080/ws/client/${clientId2}`;
    }
  }
  connect() {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }
      if (this.isConnecting) {
        reject(new Error("Connection already in progress"));
        return;
      }
      this.isConnecting = true;
      try {
        const wsUrl = new URL(this.url);
        wsUrl.searchParams.set("token", this.token);
        this.ws = new WebSocket(wsUrl.toString());
        this.ws.onopen = () => {
          console.log(`🔗 WebSocket connected to ${this.url}`);
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.emit("connected", null);
          resolve();
        };
        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error2) {
            console.error("Failed to parse WebSocket message:", error2);
          }
        };
        this.ws.onclose = (event) => {
          console.log(`🔌 WebSocket disconnected: ${event.code} ${event.reason}`);
          this.isConnecting = false;
          this.ws = null;
          this.emit("disconnected", null);
          if (this.shouldReconnect && !event.wasClean) {
            this.scheduleReconnect();
          }
        };
        this.ws.onerror = (error2) => {
          console.error("WebSocket error:", error2);
          this.isConnecting = false;
          this.emit("error", null);
          if (this.ws?.readyState !== WebSocket.OPEN) {
            reject(new Error("WebSocket connection failed"));
          }
        };
        setTimeout(() => {
          if (this.isConnecting) {
            this.isConnecting = false;
            this.ws?.close();
            reject(new Error("WebSocket connection timeout"));
          }
        }, 1e4);
      } catch (error2) {
        this.isConnecting = false;
        reject(error2);
      }
    });
  }
  disconnect() {
    this.shouldReconnect = false;
    if (this.ws) {
      this.ws.close(1e3, "Client disconnecting");
      this.ws = null;
    }
  }
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      this.emit("max_reconnect_attempts", null);
      return;
    }
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect().catch((error2) => {
          console.error("Reconnection failed:", error2);
        });
      }
    }, delay);
  }
  handleMessage(message) {
    this.emit(message.type, message);
    this.emit("message", message);
  }
  emit(eventType, message) {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message);
        } catch (error2) {
          console.error(`Error in WebSocket handler for ${eventType}:`, error2);
        }
      });
    }
  }
  // Event subscription methods
  on(eventType, handler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, /* @__PURE__ */ new Set());
    }
    this.handlers.get(eventType).add(handler);
  }
  off(eventType, handler) {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.handlers.delete(eventType);
      }
    }
  }
  // Send message to server
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket not connected, unable to send message");
    }
  }
  // Utility methods
  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
  get connectionState() {
    if (!this.ws) return "disconnected";
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return "connecting";
      case WebSocket.OPEN:
        return "connected";
      case WebSocket.CLOSING:
        return "closing";
      case WebSocket.CLOSED:
        return "disconnected";
      default:
        return "unknown";
    }
  }
}
const initialState = {
  client: null,
  metrics: null,
  automations: [],
  activities: [],
  integrations: [],
  alerts: [],
  analytics: null,
  websocket_connected: false,
  last_updated: "",
  loading: false,
  error: null
};
const dashboardState = writable(initialState);
let websocketClient = null;
const client = derived(dashboardState, ($state) => $state.client);
const metrics = derived(dashboardState, ($state) => $state.metrics);
derived(dashboardState, ($state) => $state.automations);
const activities = derived(dashboardState, ($state) => $state.activities);
derived(dashboardState, ($state) => $state.integrations);
const alerts = derived(dashboardState, ($state) => $state.alerts);
derived(dashboardState, ($state) => $state.analytics);
derived(dashboardState, ($state) => $state.websocket_connected);
const isLoading = derived(dashboardState, ($state) => $state.loading);
const error = derived(dashboardState, ($state) => $state.error);
derived(
  alerts,
  ($alerts) => $alerts.filter((alert) => !alert.resolved).length
);
derived(
  alerts,
  ($alerts) => $alerts.filter((alert) => alert.severity === "critical" && !alert.resolved).length
);
derived(
  activities,
  ($activities) => $activities.slice(0, 10)
);
class DashboardStore {
  updateState(updates) {
    dashboardState.update((state) => ({
      ...state,
      ...updates,
      last_updated: (/* @__PURE__ */ new Date()).toISOString()
    }));
  }
  setLoading(loading) {
    this.updateState({ loading });
  }
  setError(error2) {
    this.updateState({ error: error2 });
  }
  // Initialize dashboard for a specific client
  async initialize(clientId2, token) {
    this.setLoading(true);
    this.setError(null);
    try {
      if (token) {
        apiClient.setToken(token);
      }
      const [
        clientResponse,
        metricsResponse,
        activitiesResponse,
        alertsResponse,
        automationsResponse,
        integrationsResponse
      ] = await Promise.allSettled([
        withRetry(() => apiClient.getClient(clientId2)),
        withRetry(() => apiClient.getClientMetrics(clientId2)),
        withRetry(() => apiClient.getClientActivity(clientId2)),
        withRetry(() => apiClient.getAlerts(clientId2)),
        withRetry(() => apiClient.getAutomations(clientId2)),
        withRetry(() => apiClient.getIntegrations(clientId2))
      ]);
      const client2 = clientResponse.status === "fulfilled" ? clientResponse.value.data : null;
      const metrics2 = metricsResponse.status === "fulfilled" ? metricsResponse.value.data : null;
      const activities2 = activitiesResponse.status === "fulfilled" ? activitiesResponse.value.data : [];
      const alerts2 = alertsResponse.status === "fulfilled" ? alertsResponse.value.data : [];
      const automations2 = automationsResponse.status === "fulfilled" ? automationsResponse.value.data : [];
      const integrations2 = integrationsResponse.status === "fulfilled" ? integrationsResponse.value.data : [];
      this.updateState({
        client: client2,
        metrics: metrics2,
        activities: activities2,
        alerts: alerts2,
        automations: automations2,
        integrations: integrations2,
        loading: false
      });
      if (token) {
        await this.connectWebSocket(clientId2, token);
      }
      console.log("✅ Dashboard initialized successfully for client:", clientId2);
    } catch (error2) {
      console.error("❌ Failed to initialize dashboard:", error2);
      this.setError(formatApiError(error2));
      this.setLoading(false);
    }
  }
  // WebSocket connection management
  async connectWebSocket(clientId2, token) {
    try {
      if (websocketClient) {
        websocketClient.disconnect();
      }
      websocketClient = new DashboardWebSocket(clientId2, token);
      websocketClient.on("connected", () => {
        console.log("🔗 Dashboard WebSocket connected");
        this.updateState({ websocket_connected: true });
      });
      websocketClient.on("disconnected", () => {
        console.log("🔌 Dashboard WebSocket disconnected");
        this.updateState({ websocket_connected: false });
      });
      websocketClient.on("error", () => {
        console.error("❌ Dashboard WebSocket error");
        this.updateState({ websocket_connected: false });
      });
      websocketClient.on("metrics_update", (message) => {
        if (message.data && message.type === "metric_update") {
          this.updateState({ metrics: message.data });
        }
      });
      websocketClient.on("activity_update", (message) => {
        if (message.data && message.type === "activity_feed") {
          const currentState = get_store_value(dashboardState);
          const newActivities = [message.data, ...currentState.activities].slice(0, 100);
          this.updateState({ activities: newActivities });
        }
      });
      websocketClient.on("alert_update", (message) => {
        if (message.data && message.type === "system_alert") {
          const alertData = message.data;
          const currentState = get_store_value(dashboardState);
          const existingIndex = currentState.alerts.findIndex((a) => a.id === alertData.id);
          let newAlerts;
          if (existingIndex >= 0) {
            newAlerts = [...currentState.alerts];
            newAlerts[existingIndex] = alertData;
          } else {
            newAlerts = [alertData, ...currentState.alerts];
          }
          this.updateState({ alerts: newAlerts });
        }
      });
      websocketClient.on("client_update", (message) => {
        if (message.data) {
          try {
            const clientData = message.data;
            if (clientData.id && clientData.name) {
              this.updateState({ client: clientData });
            }
          } catch (error2) {
            console.warn("Failed to update client data:", error2);
          }
        }
      });
      await websocketClient.connect();
    } catch (error2) {
      console.error("❌ Failed to connect WebSocket:", error2);
      this.updateState({ websocket_connected: false });
    }
  }
  // Manual refresh
  async refresh(clientId2) {
    const currentState = get_store_value(dashboardState);
    if (currentState.loading) return;
    this.setLoading(true);
    try {
      const [metricsResponse, activitiesResponse, alertsResponse] = await Promise.allSettled([
        apiClient.getClientMetrics(clientId2),
        apiClient.getClientActivity(clientId2),
        apiClient.getAlerts(clientId2)
      ]);
      const updates = {};
      if (metricsResponse.status === "fulfilled") {
        updates.metrics = metricsResponse.value.data;
      }
      if (activitiesResponse.status === "fulfilled") {
        updates.activities = activitiesResponse.value.data;
      }
      if (alertsResponse.status === "fulfilled") {
        updates.alerts = alertsResponse.value.data;
      }
      this.updateState({ ...updates, loading: false });
    } catch (error2) {
      console.error("❌ Failed to refresh dashboard:", error2);
      this.setError(formatApiError(error2));
      this.setLoading(false);
    }
  }
  // Resolve alert
  async resolveAlert(clientId2, alertId) {
    try {
      await apiClient.resolveAlert(clientId2, alertId);
      const currentState = get_store_value(dashboardState);
      const updatedAlerts = currentState.alerts.map(
        (alert) => alert.id === alertId ? { ...alert, resolved: true } : alert
      );
      this.updateState({ alerts: updatedAlerts });
    } catch (error2) {
      console.error("❌ Failed to resolve alert:", error2);
      this.setError(formatApiError(error2));
    }
  }
  // Cleanup
  destroy() {
    if (websocketClient) {
      websocketClient.disconnect();
      websocketClient = null;
    }
    apiClient.clearToken();
    dashboardState.set(initialState);
  }
  // Utility methods
  async loadMoreActivities(clientId2, offset = 0) {
    try {
      const response = await apiClient.getClientActivity(clientId2, 50, offset);
      const currentState = get_store_value(dashboardState);
      const newActivities = [...currentState.activities, ...response.data];
      this.updateState({ activities: newActivities });
    } catch (error2) {
      console.error("❌ Failed to load more activities:", error2);
      this.setError(formatApiError(error2));
    }
  }
  async updateTimeframe(clientId2, timeframe) {
    this.setLoading(true);
    try {
      const response = await apiClient.getClientMetrics(clientId2, timeframe);
      this.updateState({
        metrics: response.data,
        loading: false
      });
    } catch (error2) {
      console.error("❌ Failed to update timeframe:", error2);
      this.setError(formatApiError(error2));
      this.setLoading(false);
    }
  }
}
const dashboardStore = new DashboardStore();
const DashboardLayout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$unsubscribe_client;
  $$unsubscribe_client = subscribe(client, (value) => value);
  let { clientId: clientId2 } = $$props;
  let { user = null } = $$props;
  if ($$props.clientId === void 0 && $$bindings.clientId && clientId2 !== void 0) $$bindings.clientId(clientId2);
  if ($$props.user === void 0 && $$bindings.user && user !== void 0) $$bindings.user(user);
  $$unsubscribe_client();
  return ` <div class="min-h-screen bg-white">${slots.default ? slots.default({}) : ``}</div>`;
});
function is_date(obj) {
  return Object.prototype.toString.call(obj) === "[object Date]";
}
function get_interpolator(a, b) {
  if (a === b || a !== a) return () => a;
  const type = typeof a;
  if (type !== typeof b || Array.isArray(a) !== Array.isArray(b)) {
    throw new Error("Cannot interpolate values of different type");
  }
  if (Array.isArray(a)) {
    const arr = b.map((bi, i) => {
      return get_interpolator(a[i], bi);
    });
    return (t) => arr.map((fn) => fn(t));
  }
  if (type === "object") {
    if (!a || !b) throw new Error("Object cannot be null");
    if (is_date(a) && is_date(b)) {
      a = a.getTime();
      b = b.getTime();
      const delta = b - a;
      return (t) => new Date(a + t * delta);
    }
    const keys = Object.keys(b);
    const interpolators = {};
    keys.forEach((key) => {
      interpolators[key] = get_interpolator(a[key], b[key]);
    });
    return (t) => {
      const result = {};
      keys.forEach((key) => {
        result[key] = interpolators[key](t);
      });
      return result;
    };
  }
  if (type === "number") {
    const delta = b - a;
    return (t) => a + t * delta;
  }
  throw new Error(`Cannot interpolate ${type} values`);
}
function tweened(value, defaults = {}) {
  const store = writable(value);
  let task;
  let target_value = value;
  function set(new_value, opts) {
    if (value == null) {
      store.set(value = new_value);
      return Promise.resolve();
    }
    target_value = new_value;
    let previous_task = task;
    let started = false;
    let {
      delay = 0,
      duration = 400,
      easing = identity,
      interpolate = get_interpolator
    } = assign(assign({}, defaults), opts);
    if (duration === 0) {
      if (previous_task) {
        previous_task.abort();
        previous_task = null;
      }
      store.set(value = target_value);
      return Promise.resolve();
    }
    const start = now() + delay;
    let fn;
    task = loop((now2) => {
      if (now2 < start) return true;
      if (!started) {
        fn = interpolate(value, new_value);
        if (typeof duration === "function") duration = duration(value, new_value);
        started = true;
      }
      if (previous_task) {
        previous_task.abort();
        previous_task = null;
      }
      const elapsed = now2 - start;
      if (elapsed > /** @type {number} */
      duration) {
        store.set(value = new_value);
        return false;
      }
      store.set(value = fn(easing(elapsed / duration)));
      return true;
    });
    return task.promise;
  }
  return {
    set,
    update: (fn, opts) => set(fn(target_value, value), opts),
    subscribe: store.subscribe
  };
}
const MetricsCard = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let displayValue;
  let $$unsubscribe_animatedValue;
  let { title } = $$props;
  let { value } = $$props;
  let { subtitle = "" } = $$props;
  let { trend = null } = $$props;
  let { trendValue = "" } = $$props;
  let { icon = null } = $$props;
  let { color = "primary" } = $$props;
  let { loading = false } = $$props;
  let { clickable = false } = $$props;
  createEventDispatcher();
  const animatedValue = tweened(0, { duration: 1200, easing: cubicOut });
  $$unsubscribe_animatedValue = subscribe(animatedValue, (value2) => value2);
  function getTrendIcon() {
    switch (trend) {
      case "up":
        return Trending_up;
      case "down":
        return Trending_down;
      default:
        return Minus;
    }
  }
  function getTrendColor() {
    switch (trend) {
      case "up":
        return "text-emerald-600";
      case "down":
        return "text-red-600";
      default:
        return "text-gray-500";
    }
  }
  function getColorClasses() {
    const colors = {
      primary: "border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100",
      secondary: "border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100",
      success: "border-emerald-200 bg-gradient-to-br from-emerald-50 to-green-50 hover:from-emerald-100 hover:to-green-100",
      warning: "border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 hover:from-amber-100 hover:to-orange-100",
      error: "border-red-200 bg-gradient-to-br from-red-50 to-rose-50 hover:from-red-100 hover:to-rose-100",
      info: "border-cyan-200 bg-gradient-to-br from-cyan-50 to-sky-50 hover:from-cyan-100 hover:to-sky-100"
    };
    return colors[color];
  }
  function getIconColor() {
    const colors = {
      primary: "text-blue-600",
      secondary: "text-purple-600",
      success: "text-emerald-600",
      warning: "text-amber-600",
      error: "text-red-600",
      info: "text-cyan-600"
    };
    return colors[color];
  }
  function getValueColor() {
    const colors = {
      primary: "text-blue-900",
      secondary: "text-purple-900",
      success: "text-emerald-900",
      warning: "text-amber-900",
      error: "text-red-900",
      info: "text-cyan-900"
    };
    return colors[color];
  }
  if ($$props.title === void 0 && $$bindings.title && title !== void 0) $$bindings.title(title);
  if ($$props.value === void 0 && $$bindings.value && value !== void 0) $$bindings.value(value);
  if ($$props.subtitle === void 0 && $$bindings.subtitle && subtitle !== void 0) $$bindings.subtitle(subtitle);
  if ($$props.trend === void 0 && $$bindings.trend && trend !== void 0) $$bindings.trend(trend);
  if ($$props.trendValue === void 0 && $$bindings.trendValue && trendValue !== void 0) $$bindings.trendValue(trendValue);
  if ($$props.icon === void 0 && $$bindings.icon && icon !== void 0) $$bindings.icon(icon);
  if ($$props.color === void 0 && $$bindings.color && color !== void 0) $$bindings.color(color);
  if ($$props.loading === void 0 && $$bindings.loading && loading !== void 0) $$bindings.loading(loading);
  if ($$props.clickable === void 0 && $$bindings.clickable && clickable !== void 0) $$bindings.clickable(clickable);
  displayValue = typeof value === "number" ? value.toLocaleString() : value;
  $$unsubscribe_animatedValue();
  return `${clickable ? `<div class="${"relative overflow-hidden rounded-xl border " + escape(getColorClasses(), true) + " p-6 transition-all duration-300 hover:shadow-lg hover:shadow-" + escape(color, true) + "-100/50 cursor-pointer hover:scale-[1.02]"}" role="button" tabindex="0"> <div class="absolute top-0 right-0 w-20 h-20 opacity-5"><svg viewBox="0 0 24 24" fill="currentColor" class="${"w-full h-full " + escape(getIconColor(), true)}"><path d="M12 2L2 7v10c0 5.55 3.84 9.739 9 9.739s9-4.189 9-9.739V7l-10-5z"></path></svg></div> ${loading ? ` <div class="animate-pulse" data-svelte-h="svelte-ackv3k"><div class="flex items-center justify-between mb-4"><div class="h-4 bg-gray-300 rounded w-1/3"></div> <div class="h-4 bg-gray-300 rounded w-4"></div></div> <div class="h-8 bg-gray-300 rounded w-1/2 mb-2"></div> <div class="h-3 bg-gray-300 rounded w-1/4"></div></div>` : ` <div class="flex items-center justify-between mb-4"><div class="flex items-center space-x-2">${icon ? `<div class="p-2 rounded-lg bg-white/80 shadow-sm">${validate_component(icon || missing_component, "svelte:component").$$render($$result, { class: "w-4 h-4 " + getIconColor() }, {}, {})}</div>` : ``} <h3 class="text-sm font-semibold text-gray-700 uppercase tracking-wide">${escape(title)}</h3></div> <button class="p-1 rounded-md hover:bg-white/60 transition-colors opacity-0 group-hover:opacity-100" aria-label="More options">${validate_component(More_horizontal, "MoreHorizontal").$$render($$result, { class: "w-4 h-4 text-gray-500" }, {}, {})}</button></div>  <div class="mb-3"><div class="${"text-3xl font-bold " + escape(getValueColor(), true) + " tracking-tight"}">${escape(displayValue)}</div></div>  <div class="flex items-center justify-between"><div class="text-sm text-gray-600">${escape(subtitle)}</div> ${trend && trendValue ? `<div class="${"flex items-center space-x-1 " + escape(getTrendColor(), true)}">${validate_component(getTrendIcon() || missing_component, "svelte:component").$$render($$result, { class: "w-3 h-3" }, {}, {})} <span class="text-xs font-medium">${escape(trendValue)}</span></div>` : ``}</div>`}</div>` : `<div class="${"relative overflow-hidden rounded-xl border " + escape(getColorClasses(), true) + " p-6 transition-all duration-300 hover:shadow-lg hover:shadow-" + escape(color, true) + "-100/50"}"> <div class="absolute top-0 right-0 w-20 h-20 opacity-5"><svg viewBox="0 0 24 24" fill="currentColor" class="${"w-full h-full " + escape(getIconColor(), true)}"><path d="M12 2L2 7v10c0 5.55 3.84 9.739 9 9.739s9-4.189 9-9.739V7l-10-5z"></path></svg></div> ${loading ? ` <div class="animate-pulse" data-svelte-h="svelte-ackv3k"><div class="flex items-center justify-between mb-4"><div class="h-4 bg-gray-300 rounded w-1/3"></div> <div class="h-4 bg-gray-300 rounded w-4"></div></div> <div class="h-8 bg-gray-300 rounded w-1/2 mb-2"></div> <div class="h-3 bg-gray-300 rounded w-1/4"></div></div>` : ` <div class="flex items-center justify-between mb-4"><div class="flex items-center space-x-2">${icon ? `<div class="p-2 rounded-lg bg-white/80 shadow-sm">${validate_component(icon || missing_component, "svelte:component").$$render($$result, { class: "w-4 h-4 " + getIconColor() }, {}, {})}</div>` : ``} <h3 class="text-sm font-semibold text-gray-700 uppercase tracking-wide">${escape(title)}</h3></div></div>  <div class="mb-3"><div class="${"text-3xl font-bold " + escape(getValueColor(), true) + " tracking-tight"}">${escape(displayValue)}</div></div>  <div class="flex items-center justify-between"><div class="text-sm text-gray-600">${escape(subtitle)}</div> ${trend && trendValue ? `<div class="${"flex items-center space-x-1 " + escape(getTrendColor(), true)}">${validate_component(getTrendIcon() || missing_component, "svelte:component").$$render($$result, { class: "w-3 h-3" }, {}, {})} <span class="text-xs font-medium">${escape(trendValue)}</span></div>` : ``}</div>`}</div>`}`;
});
function getActivityColor(type, status) {
  if (status === "success") return "text-green-600 bg-green-50";
  if (status === "error") return "text-red-600 bg-red-50";
  if (status === "processing") return "text-blue-600 bg-blue-50";
  switch (type) {
    case "email_received":
      return "text-blue-600 bg-blue-50";
    case "classification_complete":
      return "text-green-600 bg-green-50";
    case "routing_complete":
      return "text-purple-600 bg-purple-50";
    case "delivery_complete":
      return "text-green-600 bg-green-50";
    case "error":
      return "text-red-600 bg-red-50";
    default:
      return "text-gray-600 bg-gray-50";
  }
}
function getStatusBadge(status) {
  const badges = {
    "success": "bg-green-100 text-green-800",
    "error": "bg-red-100 text-red-800",
    "processing": "bg-blue-100 text-blue-800",
    "pending": "bg-yellow-100 text-yellow-800",
    "completed": "bg-green-100 text-green-800",
    "failed": "bg-red-100 text-red-800"
  };
  return badges[status || "pending"] || badges.pending;
}
const LiveFeed = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let displayActivities;
  let { activities: activities2 = [] } = $$props;
  let { loading = false } = $$props;
  let { maxItems = 10 } = $$props;
  let { autoRefresh = false } = $$props;
  let { refreshInterval = 3e4 } = $$props;
  createEventDispatcher();
  onDestroy(() => {
  });
  function getActivityIcon(type, status) {
    switch (type) {
      case "email_received":
      case "email_processing":
        return Mail;
      case "classification_complete":
        return status === "success" ? Check_circle : X_circle;
      case "routing_complete":
        return Check_circle;
      case "delivery_complete":
        return status === "success" ? Check_circle : X_circle;
      case "error":
        return Alert_triangle;
      default:
        return Clock;
    }
  }
  function formatTime(timestamp) {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return "Unknown time";
    }
  }
  if ($$props.activities === void 0 && $$bindings.activities && activities2 !== void 0) $$bindings.activities(activities2);
  if ($$props.loading === void 0 && $$bindings.loading && loading !== void 0) $$bindings.loading(loading);
  if ($$props.maxItems === void 0 && $$bindings.maxItems && maxItems !== void 0) $$bindings.maxItems(maxItems);
  if ($$props.autoRefresh === void 0 && $$bindings.autoRefresh && autoRefresh !== void 0) $$bindings.autoRefresh(autoRefresh);
  if ($$props.refreshInterval === void 0 && $$bindings.refreshInterval && refreshInterval !== void 0) $$bindings.refreshInterval(refreshInterval);
  displayActivities = activities2.length > 0 ? activities2.slice(0, maxItems) : [
    {
      id: "1",
      type: "email_received",
      status: "success",
      message: "New email received from john@example.com",
      timestamp: new Date(Date.now() - 1e3 * 60 * 5).toISOString(),
      metadata: {
        from: "john@example.com",
        category: "inquiry"
      }
    },
    {
      id: "2",
      type: "classification_complete",
      status: "success",
      message: "Email classified as customer inquiry",
      timestamp: new Date(Date.now() - 1e3 * 60 * 10).toISOString(),
      metadata: { category: "inquiry", confidence: 0.95 }
    },
    {
      id: "3",
      type: "routing_complete",
      status: "success",
      message: "Email routed to sales team",
      timestamp: new Date(Date.now() - 1e3 * 60 * 15).toISOString(),
      metadata: { route: "sales@company.com" }
    },
    {
      id: "4",
      type: "delivery_complete",
      status: "success",
      message: "Response sent to customer",
      timestamp: new Date(Date.now() - 1e3 * 60 * 20).toISOString(),
      metadata: { delivery_time: "2.3s" }
    },
    {
      id: "5",
      type: "email_received",
      status: "processing",
      message: "Processing email from sarah@company.com",
      timestamp: new Date(Date.now() - 1e3 * 60 * 2).toISOString(),
      metadata: { from: "sarah@company.com" }
    }
  ];
  return `<div class="h-full">${loading ? ` <div class="space-y-4">${each(Array(5), (_) => {
    return `<div class="animate-pulse flex items-start space-x-3" data-svelte-h="svelte-19xswc"><div class="w-10 h-10 bg-gray-200 rounded-full"></div> <div class="flex-1 space-y-2"><div class="h-4 bg-gray-200 rounded w-3/4"></div> <div class="h-3 bg-gray-200 rounded w-1/2"></div></div> </div>`;
  })}</div>` : `${displayActivities.length === 0 ? ` <div class="text-center py-8"><div class="w-12 h-12 mx-auto mb-4 text-gray-400">${validate_component(Clock, "Clock").$$render($$result, { class: "w-full h-full" }, {}, {})}</div> <p class="text-gray-500 text-sm" data-svelte-h="svelte-156owk3">No recent activity</p> <button class="mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium" data-svelte-h="svelte-k8rjsu">Refresh to check for updates</button></div>` : ` <div class="space-y-4">${each(displayActivities, (activity) => {
    return `<div class="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer border border-transparent hover:border-gray-200" role="button" tabindex="0"> <div class="flex-shrink-0"><div class="${"w-10 h-10 rounded-full flex items-center justify-center " + escape(getActivityColor(activity.type, activity.status), true)}">${validate_component(getActivityIcon(activity.type, activity.status) || missing_component, "svelte:component").$$render($$result, { class: "w-5 h-5" }, {}, {})} </div></div>  <div class="flex-1 min-w-0"><div class="flex items-center justify-between"><p class="text-sm font-medium text-gray-900 truncate">${escape(activity.message)}</p> <span class="${"inline-flex items-center px-2 py-1 rounded-full text-xs font-medium " + escape(getStatusBadge(activity.status), true)}">${escape(activity.status || "pending")} </span></div> <div class="mt-1 flex items-center space-x-2 text-xs text-gray-500"><span>${escape(formatTime(activity.timestamp))}</span> ${activity.metadata?.from ? `<span data-svelte-h="svelte-7hh8jk">•</span> <span class="truncate">from ${escape(activity.metadata.from)}</span>` : ``} ${activity.metadata?.category ? `<span data-svelte-h="svelte-7hh8jk">•</span> <span class="capitalize">${escape(activity.metadata.category)}</span>` : ``} ${activity.metadata?.processing_time ? `<span data-svelte-h="svelte-7hh8jk">•</span> <span>${escape(activity.metadata.processing_time)}</span>` : ``} </div></div> </div>`;
  })}</div>  <div class="mt-6 pt-4 border-t border-gray-200 flex items-center justify-between"><button class="flex items-center text-sm text-gray-600 hover:text-gray-900 transition-colors">${validate_component(Refresh_cw, "RefreshCw").$$render($$result, { class: "w-4 h-4 mr-1" }, {}, {})}
        Refresh</button> <button class="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors" data-svelte-h="svelte-ta2n3c">View all activity →</button></div>`}`}</div>`;
});
const clientId = "client-001-cole-nielson";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $error, $$unsubscribe_error;
  let $metrics, $$unsubscribe_metrics;
  let $isLoading, $$unsubscribe_isLoading;
  let $activities, $$unsubscribe_activities;
  $$unsubscribe_error = subscribe(error, (value) => $error = value);
  $$unsubscribe_metrics = subscribe(metrics, (value) => $metrics = value);
  $$unsubscribe_isLoading = subscribe(isLoading, (value) => $isLoading = value);
  $$unsubscribe_activities = subscribe(activities, (value) => $activities = value);
  let user = {
    name: "Cole Nielson",
    email: "cole@colesportfolio.com"
  };
  onDestroy(() => {
    dashboardStore.destroy();
  });
  $$unsubscribe_error();
  $$unsubscribe_metrics();
  $$unsubscribe_isLoading();
  $$unsubscribe_activities();
  return `${validate_component(DashboardLayout, "DashboardLayout").$$render($$result, { clientId, user }, {}, {
    default: () => {
      return `<div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"> <div class="mb-8"><div class="flex items-center justify-between"><div data-svelte-h="svelte-154th8w"><h1 class="text-3xl font-bold text-gray-900">Dashboard Overview</h1> <p class="text-gray-600 mt-2">Monitor your AI automation performance and activity</p></div> <div class="flex items-center space-x-3"><button class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">${validate_component(Settings, "Settings").$$render($$result, { class: "w-4 h-4 mr-2" }, {}, {})}
              Settings</button> <button class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm">${validate_component(Plus, "Plus").$$render($$result, { class: "w-4 h-4 mr-2" }, {}, {})}
              New Automation</button></div></div></div>  ${$error ? `<div class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4"><div class="flex items-center">${validate_component(Alert_triangle, "AlertTriangle").$$render($$result, { class: "w-5 h-5 text-red-600 mr-3" }, {}, {})} <div><h3 class="text-sm font-medium text-red-800" data-svelte-h="svelte-1473de6">Failed to load dashboard</h3> <p class="text-sm text-red-700 mt-1">${escape($error)}</p></div> <button class="ml-auto bg-red-100 text-red-600 px-3 py-1 rounded-md text-sm hover:bg-red-200 transition-colors" data-svelte-h="svelte-1e0lgdk">Retry</button></div></div>` : ``}  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">${validate_component(MetricsCard, "MetricsCard").$$render(
        $$result,
        {
          title: "Emails Processed",
          value: $metrics?.emails_processed_24h ?? 0,
          subtitle: "Last 24 hours",
          trend: "up",
          trendValue: "+12%",
          icon: Mail,
          color: "primary",
          loading: $isLoading,
          clickable: true
        },
        {},
        {}
      )} ${validate_component(MetricsCard, "MetricsCard").$$render(
        $$result,
        {
          title: "Classification Accuracy",
          value: $metrics ? `${($metrics.classification_accuracy * 100).toFixed(1)}%` : "0%",
          subtitle: "AI confidence score",
          trend: "up",
          trendValue: "+2.3%",
          icon: Check_circle,
          color: "success",
          loading: $isLoading,
          clickable: true
        },
        {},
        {}
      )} ${validate_component(MetricsCard, "MetricsCard").$$render(
        $$result,
        {
          title: "Avg Response Time",
          value: $metrics ? `${$metrics.average_response_time.toFixed(1)}s` : "0s",
          subtitle: "End-to-end processing",
          trend: "down",
          trendValue: "-0.3s",
          icon: Clock,
          color: "info",
          loading: $isLoading,
          clickable: true
        },
        {},
        {}
      )} ${validate_component(MetricsCard, "MetricsCard").$$render(
        $$result,
        {
          title: "Active Automations",
          value: $metrics?.active_automations ?? 0,
          subtitle: "Running workflows",
          trend: "neutral",
          icon: Zap,
          color: "secondary",
          loading: $isLoading,
          clickable: true
        },
        {},
        {}
      )}</div>  <div class="grid grid-cols-1 lg:grid-cols-3 gap-8"> <div class="lg:col-span-2"><div class="bg-white rounded-xl border border-gray-200 shadow-sm"><div class="px-6 py-4 border-b border-gray-200"><div class="flex items-center justify-between"><h2 class="text-lg font-semibold text-gray-900" data-svelte-h="svelte-1pv01ns">Recent Activity</h2> <button class="text-sm text-blue-600 hover:text-blue-700 font-medium" data-svelte-h="svelte-qtejq8">View all →</button></div></div> <div class="p-6">${validate_component(LiveFeed, "LiveFeed").$$render(
        $$result,
        {
          activities: $activities,
          loading: $isLoading,
          maxItems: 15,
          autoRefresh: true
        },
        {},
        {}
      )}</div></div></div>  <div class="space-y-6"> <div class="bg-white rounded-xl border border-gray-200 shadow-sm"><div class="px-6 py-4 border-b border-gray-200"><h3 class="text-lg font-semibold text-gray-900 flex items-center">${validate_component(Bar_chart_3, "BarChart3").$$render($$result, { class: "w-5 h-5 mr-2 text-blue-600" }, {}, {})}
                Performance</h3></div> <div class="p-6"><div class="space-y-4"><div class="flex justify-between items-center" data-svelte-h="svelte-xmta49"><span class="text-sm font-medium text-gray-600">Uptime</span> <span class="text-sm font-semibold text-emerald-600">99.8%</span></div> <div class="flex justify-between items-center" data-svelte-h="svelte-1aw2yy5"><span class="text-sm font-medium text-gray-600">Success Rate</span> <span class="text-sm font-semibold text-emerald-600">98.2%</span></div> <div class="flex justify-between items-center"><span class="text-sm font-medium text-gray-600" data-svelte-h="svelte-1fal5ed">Avg Processing</span> <span class="text-sm font-semibold text-blue-600">${escape($metrics ? `${$metrics.average_response_time.toFixed(1)}s` : "0s")}</span></div> <div class="flex justify-between items-center" data-svelte-h="svelte-1gesqf9"><span class="text-sm font-medium text-gray-600">Peak Today</span> <span class="text-sm font-semibold text-amber-600">156 emails/hr</span></div></div></div></div>  <div class="bg-white rounded-xl border border-gray-200 shadow-sm"><div class="px-6 py-4 border-b border-gray-200"><h3 class="text-lg font-semibold text-gray-900 flex items-center">${validate_component(Activity, "Activity").$$render($$result, { class: "w-5 h-5 mr-2 text-green-600" }, {}, {})}
                System Status</h3></div> <div class="p-6"><div class="space-y-3" data-svelte-h="svelte-1kjmp3z"><div class="flex items-center justify-between"><span class="text-sm font-medium text-gray-600">Email Router</span> <div class="flex items-center space-x-2"><div class="w-2 h-2 bg-green-500 rounded-full"></div> <span class="text-xs font-medium text-green-700">Healthy</span></div></div> <div class="flex items-center justify-between"><span class="text-sm font-medium text-gray-600">AI Classifier</span> <div class="flex items-center space-x-2"><div class="w-2 h-2 bg-green-500 rounded-full"></div> <span class="text-xs font-medium text-green-700">Online</span></div></div> <div class="flex items-center justify-between"><span class="text-sm font-medium text-gray-600">Email Delivery</span> <div class="flex items-center space-x-2"><div class="w-2 h-2 bg-green-500 rounded-full"></div> <span class="text-xs font-medium text-green-700">Operational</span></div></div> <div class="flex items-center justify-between"><span class="text-sm font-medium text-gray-600">WebSocket</span> <div class="flex items-center space-x-2"><div class="w-2 h-2 bg-green-500 rounded-full"></div> <span class="text-xs font-medium text-green-700">Connected</span></div></div></div> <button class="w-full mt-4 bg-gray-50 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors border border-gray-200" data-svelte-h="svelte-ttolqj">View Detailed Status</button></div></div>  <div class="bg-white rounded-xl border border-gray-200 shadow-sm"><div class="px-6 py-4 border-b border-gray-200" data-svelte-h="svelte-vvxeo1"><h3 class="text-lg font-semibold text-gray-900">Quick Actions</h3></div> <div class="p-6"><div class="space-y-3"><button class="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">${validate_component(Plus, "Plus").$$render($$result, { class: "w-4 h-4 mr-2" }, {}, {})}
                  Create Automation</button> <button class="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">${validate_component(Bar_chart_3, "BarChart3").$$render($$result, { class: "w-4 h-4 mr-2" }, {}, {})}
                  View Analytics</button> <button class="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">${validate_component(Globe, "Globe").$$render($$result, { class: "w-4 h-4 mr-2" }, {}, {})}
                  Manage Integrations</button></div></div></div></div></div></div></div>`;
    }
  })}`;
});
export {
  Page as default
};
//# sourceMappingURL=_page.svelte.js.map
