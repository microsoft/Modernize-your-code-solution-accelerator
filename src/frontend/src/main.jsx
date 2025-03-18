import { StrictMode, useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import { Provider } from 'react-redux';
import { store } from './store/store';
import AuthProvider from './msal-auth/AuthProvider';
import { setEnvData } from './api/config';
import { initializeMsalInstance } from './msal-auth/msalInstance';

const Main = () => {
  const [isConfigLoaded, setIsConfigLoaded] = useState(false);
  const [msalInstance, setMsalInstance] = useState(null);

  useEffect(() => {
    const initMsal = async () => {
      try {
        const response = await fetch('/config');
        let config = {
          REACT_APP_MSAL_AUTH_CLIENTID: "",
          REACT_APP_MSAL_AUTH_AUTHORITY: "",
          REACT_APP_MSAL_REDIRECT_URL: "",
          REACT_APP_MSAL_POST_REDIRECT_URL: ""
        };
  
        if (response.ok) {
          config = await response.json();
        }
  
        window.appConfig = config;
        setEnvData(config);
  
        // Wait for MSAL to initialize before setting state
        const instance = await initializeMsalInstance(config);
        setMsalInstance(instance);
  
        setIsConfigLoaded(true);
      } catch (error) {
        console.error("Error fetching config:", error);
      }
    };
  
    initMsal(); // Call the async function inside useEffect
  }, []);

  if (!isConfigLoaded || !msalInstance) return <div>Loading...</div>;

  return (
    <StrictMode>
      <Provider store={store}>
        <FluentProvider theme={webLightTheme}>
          <AuthProvider msalInstance={msalInstance}>
            <App />
          </AuthProvider>
        </FluentProvider>
      </Provider>
    </StrictMode>
  );
};

createRoot(document.getElementById('root')).render(<Main />);
