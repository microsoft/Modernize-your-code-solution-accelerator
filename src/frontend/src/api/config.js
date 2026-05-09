// src/config.js

export let API_URL = null;
export let USER_ID = null;

export let config = {
  API_URL: "http://localhost:8000",
  REACT_APP_MSAL_AUTH_CLIENTID: "",
  REACT_APP_MSAL_AUTH_AUTHORITY: "",
  REACT_APP_MSAL_REDIRECT_URL: "",
  REACT_APP_MSAL_POST_REDIRECT_URL: "",
  ENABLE_AUTH: false,
};

function resolveBrowserApiUrl(url) {
  if (!url || typeof url !== "string") {
    return null;
  }

  const trimmedUrl = url.trim();
  if (!trimmedUrl) {
    return null;
  }

  const normalizedInput = trimmedUrl.replace(/\/+$/, "");

  try {
    const parsed = new URL(normalizedInput, window.location.origin);

    if (parsed.origin !== window.location.origin) {
      const backendIsLocal = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";
      const browserIsLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

      // In deployed environments, enforce same-origin API access so requests
      // flow through the frontend reverse proxy instead of direct backend calls.
      if (!(backendIsLocal && browserIsLocal)) {
        return null;
      }
    }

    const normalizedParsed = parsed.toString().replace(/\/+$/, "");
    return normalizedParsed.endsWith("/api") ? normalizedParsed : `${normalizedParsed}/api`;
  } catch {
    return null;
  }
}

export function setApiUrl(url) {
  API_URL = resolveBrowserApiUrl(url);
}

export function setEnvData(configData) {
  if (configData) {
    config.API_URL = configData.API_URL || "";
    config.REACT_APP_MSAL_AUTH_CLIENTID = configData.REACT_APP_MSAL_AUTH_CLIENTID || "";
    config.REACT_APP_MSAL_AUTH_AUTHORITY = configData.REACT_APP_MSAL_AUTH_AUTHORITY || "";
    config.REACT_APP_MSAL_REDIRECT_URL = configData.REACT_APP_MSAL_REDIRECT_URL || "";
    config.REACT_APP_MSAL_POST_REDIRECT_URL = configData.REACT_APP_MSAL_POST_REDIRECT_URL || "";
    config.ENABLE_AUTH = configData.ENABLE_AUTH || false;
  }
}

export function getConfigData() {
  if (!config.REACT_APP_MSAL_AUTH_CLIENTID || !config.REACT_APP_MSAL_AUTH_AUTHORITY || !config.REACT_APP_MSAL_REDIRECT_URL || !config.REACT_APP_MSAL_POST_REDIRECT_URL) {
    // Check if window.appConfig exists
    if (window.appConfig) {
      setEnvData(window.appConfig);
    }
  }

  return { ...config };
}

export function getApiUrl() {
  if (!API_URL) {
    // Check if window.appConfig exists
    if (window.appConfig && window.appConfig.API_URL) {
      setApiUrl(window.appConfig.API_URL);
    }
  }

  if (!API_URL) {
    // API_URL is not configured (e.g. WAF deployment where the backend is
    // internal-only). Fall back to the browser's own origin so that all
    // /api/* requests are routed through the frontend server's reverse proxy
    // instead of attempting to reach the internal backend URL directly.
    return `${window.location.origin}/api`;
  }

  return API_URL;
}

export function getUserId() {
  USER_ID = window.activeUserId;
  const userId = USER_ID ?? "00000000-0000-0000-0000-000000000000";
  return userId;
}

export function headerBuilder(headers) {
  let userId = getUserId();
  let defaultHeaders = {
    "x-ms-client-principal-id": String(userId) || "",  // Custom header
  };
  return {
    ...defaultHeaders, ...(headers ? headers : {})
  };
}

export default {
  setApiUrl,
  getApiUrl,
  getUserId,
  getConfigData,
  setEnvData,
  config,
  USER_ID,
  API_URL
};