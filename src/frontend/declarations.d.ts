declare module "*.png" {
    const value: string;
    export default value;
  }

interface AppConfig {
  API_URL?: string;
  REACT_APP_MSAL_AUTH_CLIENTID?: string;
  REACT_APP_MSAL_AUTH_AUTHORITY?: string;
  REACT_APP_MSAL_REDIRECT_URL?: string;
  REACT_APP_MSAL_POST_REDIRECT_URL?: string;
  ENABLE_AUTH?: boolean;
}

interface Window {
  appConfig?: AppConfig;
}
