import { useState, useEffect } from 'react';
import { InteractionStatus, AccountInfo, PublicClientApplication } from "@azure/msal-browser";
import { getMsalInstance } from "./msalInstance"; // Import MSAL instance dynamically
import { loginRequest, tokenRequest } from "./msaConfig";
import { useIsAuthenticated, useMsal } from "@azure/msal-react"; // Still needed for tracking auth state

declare global {
  interface Window {
    activeUser: any;
    activeAccount: any;
    activeUserId: any;
  }
}

interface User {
  username: string;
  name: string | undefined;
  shortName?: string;
  isInTeams: boolean;
}

const useAuth = () => {
  const msalInstance: PublicClientApplication | null = getMsalInstance(); // ✅ Ensure it's always checked
  const isAuthenticated = useIsAuthenticated();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const accounts = msalInstance ? msalInstance.getAllAccounts() : [];
  const { inProgress } = useMsal();
  const activeAccount: AccountInfo | undefined = accounts[0];

  useEffect(() => {
    if (!msalInstance) {
      console.error("MSAL Instance is not initialized yet.");
      return;
    }

    if (accounts.length > 0) {
      const activeUser = {
        username: accounts[0].username,
        name: accounts[0]?.name,
        isInTeams: false,
        userId: accounts[0].localAccountId
      };

      if(!activeUser){
        setUser(activeUser);
      }
      msalInstance.setActiveAccount(accounts[0]);

      // Store active user globally
      window.activeUser = activeUser;
      window.activeAccount = accounts[0];  
      window.activeUserId = activeUser.userId;

      const activeAccount = msalInstance.getActiveAccount();
      if (activeAccount && !token) {
        console.log("Fetching token...");
        getToken();
      }
    }
  }, [accounts, msalInstance, token]);

  const login = async () => {
    if (!msalInstance) {
      console.error("MSAL Instance is not available for login.");
      return;
    }

    try {
      if (accounts.length === 0 && inProgress === InteractionStatus.None) {
        await msalInstance.loginRedirect(loginRequest);
      }
    } catch (error) {
      console.error("Login failed:", error);
    }
  };

  const logout = async () => {
    if (!msalInstance) {
      console.error("MSAL Instance is not available for logout.");
      return;
    }

    try {
      if (activeAccount) {
        await msalInstance.logoutRedirect({
          account: activeAccount,
        });
        localStorage.removeItem('token');
      } else {
        console.warn("No active account found for logout.");
      }
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const getToken = async () => {
    if (!msalInstance) {
      console.error("MSAL Instance is not available to fetch token.");
      return;
    }

    try {
      const activeAccount = msalInstance.getActiveAccount();

      if (!activeAccount) {
        console.error("No active account set. Please log in.");
        return;
      }

      const accessTokenRequest = {
        scopes: [...tokenRequest.scopes],
        account: activeAccount,
      };

      const response = await msalInstance.acquireTokenSilent(accessTokenRequest);
      const token = response.accessToken;
      localStorage.setItem('token', token);
      setToken(token);
    } catch (error) {
      console.error("Error fetching token:", error);
      if (error.message.includes("interaction_required")) {
        await msalInstance.loginRedirect(loginRequest);
      }
    }
  };

  return {
    isAuthenticated,
    login,
    logout,
    user,
    accounts,
    inProgress,
    token,
    getToken
  };
};

export default useAuth;
