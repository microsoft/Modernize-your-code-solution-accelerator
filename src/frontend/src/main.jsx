import { StrictMode, useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import { Provider } from 'react-redux';
import { store } from './store/store';
import AuthProvider from './msal-auth/AuthProvider';
import { setEnvData, setApiUrl, config as defaultConfig } from './utils/config.js';
import { initializeMsalInstance } from './msal-auth/msalInstance';
import {updateUrl} from './utils/httpUtil.js';

const Main = () => {
  const [isConfigLoaded, setIsConfigLoaded] = useState(false);
  const [msalInstance, setMsalInstance] = useState(null);
  const toBoolean = (value) => {
    if (typeof value !== 'string') {
      return false;
    }
    return value.trim().toLowerCase() === 'true';
  };
  const [config, setConfig] = useState(null);
  useEffect(() => {
    const initMsal = async () => {
      try {
        const response = await fetch('/config');
        let config = defaultConfig;
        if (response.ok) {
          config = await response.json();
          config.ENABLE_AUTH = toBoolean(config.ENABLE_AUTH);
        }

        window.appConfig = config;
        setEnvData(config);
        setApiUrl(config.API_URL);
        setConfig(config);
        // Wait for MSAL to initialize before setting state
        const instance = config.ENABLE_AUTH ? await initializeMsalInstance(config) : {};
        setMsalInstance(instance);
        setIsConfigLoaded(true);
        updateUrl();
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
          {config && config.ENABLE_AUTH ? (

            <AuthProvider msalInstance={msalInstance}>
              <App />
            </AuthProvider>
          ) : (

            <App />
          )}
        </FluentProvider>
      </Provider>
    </StrictMode>
  );
};

createRoot(document.getElementById('root')).render(<Main />);