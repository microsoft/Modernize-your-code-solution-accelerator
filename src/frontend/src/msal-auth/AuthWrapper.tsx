
import React, { useEffect } from "react";
import { msalInstance } from "./msalInstance";
import { loginRequest } from "./msaConfig";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { InteractionStatus } from "@azure/msal-browser";

import useAuth from './useAuth';

const AuthWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {

  const { isAuthenticated, login,inProgress } = useAuth();

  useEffect(() => {
    if (!isAuthenticated && inProgress === InteractionStatus.None) {
      login();
    }
  }, [isAuthenticated, inProgress]);

  return <>{isAuthenticated && children}</>
};

export default AuthWrapper;

