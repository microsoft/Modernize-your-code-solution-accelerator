
import './App.css'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/landingPage';
import ModernizationPage from './pages/modernizationPage';
import BatchViewPage from './pages/batchView';
import { initializeIcons } from '@fluentui/react';

initializeIcons();

function App() {

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