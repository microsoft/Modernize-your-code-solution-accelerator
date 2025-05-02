export let API_URL= null;
export let USER_ID= null;

export let config = {
  API_URL: "http://localhost:8000",
  REACT_APP_MSAL_AUTH_CLIENTID: "",
  REACT_APP_MSAL_AUTH_AUTHORITY: "",
  REACT_APP_MSAL_REDIRECT_URL: "",
  REACT_APP_MSAL_POST_REDIRECT_URL: "",
  ENABLE_AUTH: false,
};

export function setApiUrl(url) {
  if (url) {
    API_URL = `${url}/api`;
  }
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
    console.warn('API URL not yet configured');
    return null;
  }

  return API_URL;
}

export function getUserId() {
  USER_ID = window.activeUserId ?? null;
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