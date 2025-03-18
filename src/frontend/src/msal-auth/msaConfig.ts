// msalConfig.ts
import { Configuration, LogLevel } from '@azure/msal-browser';
import { getConfigData } from '../api/config';


export const createMsalConfig = (configData: any): Configuration => ({
  auth: {
    clientId: configData.REACT_APP_MSAL_AUTH_CLIENTID || import.meta.env.VITE_APP_MSAL_AUTH_CLIENTID as string,
    authority: configData.REACT_APP_MSAL_AUTH_AUTHORITY || import.meta.env.VITE_APP_MSAL_AUTH_AUTHORITY as string,
    redirectUri: configData.REACT_APP_MSAL_REDIRECT_URL || import.meta.env.VITE_APP_MSAL_REDIRECT_URL as string,
    postLogoutRedirectUri: configData.REACT_APP_MSAL_POST_REDIRECT_URL || import.meta.env.VITE_APP_MSAL_POST_REDIRECT_URL as string
  },
  cache: {
    cacheLocation: 'localStorage', 
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        if (level === LogLevel.Error) console.error(message);
        if (level === LogLevel.Info) console.info(message);
        if (level === LogLevel.Verbose) console.debug(message);
        if (level === LogLevel.Warning) console.warn(message);
      },
    },
  },
});

export const loginRequest = {
    scopes: ["user.read"],  // Define the scope you need
};

export const graphConfig = {
  graphMeEndpoint: "https://graph.microsoft.com/v1.0/me",
};

export const tokenRequest = {
    scopes: [],
}