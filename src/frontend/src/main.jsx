import { StrictMode, useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import { Provider } from 'react-redux';
import { store } from './store/store';
import AuthProvider from './msal-auth/AuthProvider';
import { setEnvData, setApiUrl } from './api/config';
import { initializeMsalInstance } from './msal-auth/msalInstance';

const Main = () => {
  const [isConfigLoaded, setIsConfigLoaded] = useState(false);
  const [msalInstance, setMsalInstance] = useState(null);
  const [config, setConfig] = useState(null);
  useEffect(() => {
    const initMsal = async () => {
      try {
        const response = await fetch('/config');
        let config = {
          API_URL: "http://localhost:8000",
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
        setApiUrl(config.API_URL);
        setConfig(config);
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
  async function checkConnection() {
    if (!config) return;

    const baseURL = config.API_URL.replace(/\/api$/, ''); // Remove '/api' if it appears at the end
    console.log('Checking connection to:', baseURL);
    try {
        const response = await fetch(`${baseURL}/health`);
    } catch (error) {
      console.error('Error connecting to backend:', error);
    }
  }

  useEffect(() => {
    if (config) {
      checkConnection();
    }
  }, [config]);

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
