import { MsalProvider } from '@azure/msal-react';
import AuthWrapper from './AuthWrapper';
import React from 'react';

interface AuthProviderProps {
  children: React.ReactNode;
  msalInstance: any; // Accept MSAL instance dynamically
}

const AuthProvider: React.FC<AuthProviderProps> = ({ children, msalInstance }) => {
  if (!msalInstance) return null; // Ensure msalInstance is ready

  return (
    <MsalProvider instance={msalInstance}>
      <AuthWrapper>
        {children}
      </AuthWrapper>
    </MsalProvider>
  );
};

export default AuthProvider;
