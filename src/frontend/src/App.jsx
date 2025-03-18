import { useState, useEffect } from 'react'
import './App.css'
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/landingPage';

import ModernizationPage from './pages/modernizationPage';
import BatchViewPage from './pages/batchView';
import { initializeIcons } from '@fluentui/react';
import { fetchAuthDetails } from './slices/authSlice';
import { useDispatch } from 'react-redux';
import { setApiUrl, setEnvData } from './api/config';  // Add this import

initializeIcons();

function App() {
  const [config, setConfig] = useState(null);
  const dispatch = useDispatch();

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('/config');
        let configData = {API_URL: "http://localhost:8000",
                          REACT_APP_MSAL_AUTH_CLIENTID : "",
                          REACT_APP_MSAL_AUTH_AUTHORITY : "",
                          REACT_APP_MSAL_REDIRECT_URL : "",
                          REACT_APP_MSAL_POST_REDIRECT_URL : ""
        } ; // Default value NO SLASH AT THE END
        if (response.ok) {
          configData = await response.json();
        }
        // Set window.appConfig for global access
        window.appConfig = configData;

        // Set the API URL
        setApiUrl(configData.API_URL);
        setEnvData(configData);

        setConfig(configData);
      } catch (error) {
        console.error('Failed to fetch config:', error);
      }
    };

    fetchConfig();

    dispatch(fetchAuthDetails())
      .unwrap()
      .catch(error => {
        console.error('Failed to fetch auth details:', error);
      });
  }, [dispatch]);

  async function checkConnection() {
    if (!config) return;

    const baseURL = config.API_URL.replace(/\/api$/, ''); // Remove '/api' if it appears at the end
    console.log('Checking connection to:', baseURL);
    try {
        const response = await axios.get(`${baseURL}/health`);
    } catch (error) {
      console.error('Error connecting to backend:', error);
    }
  }

  useEffect(() => {
    if (config) {
      checkConnection();
    }
  }, [config]);

  // Show a loading state until config is fetched
  if (!config) {
    return <div>Loading...</div>;
  }

  return (
    <Router>
      <div>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/batch-process/:batchId" element={<ModernizationPage />} />
          <Route path="/batch-view/:batchId" element={<BatchViewPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App