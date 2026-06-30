import { PublicClientApplication } from "@azure/msal-browser";
import { createMsalConfig } from "./msaConfig";

let msalInstance: PublicClientApplication | null = null;

export const initializeMsalInstance = async (configData: any) => {
  if (!msalInstance) {
    msalInstance = new PublicClientApplication(createMsalConfig(configData));
    await msalInstance.initialize();
  }
  return msalInstance;
};

export const getMsalInstance = () => msalInstance;
