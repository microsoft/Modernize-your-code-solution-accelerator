import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/landingPage/landingPage";
import ModernizationPage from "./pages/modernizationPage/modernizationPage";
import BatchViewPage from "./pages/batchViewPage/batchView";
import { initializeIcons } from "@fluentui/react";
import Header from "./components/Header/Header";
import HeaderTools from "./components/Header/HeaderTools";
import PanelRightToggles from "./components/Header/PanelRightToggles";
import { Button, Tooltip } from "@fluentui/react-components";
import {
  HistoryRegular,
  HistoryFilled,
  bundleIcon,
} from "@fluentui/react-icons";
export const History = bundleIcon(HistoryFilled, HistoryRegular);
//import RootState from "./store/store";
import { useSelector, useDispatch } from "react-redux";
import { togglePanel, closePanel } from "./store/historyPanelSlice";
import PanelRightToolbar from "./components/Panels/PanelRightToolbar";
import PanelRight from "./components/Panels/PanelRight";
import BatchHistoryPanel from "./components/batchHistoryPanel/batchHistoryPanel";

initializeIcons();

function App() {
  const dispatch = useDispatch();
  const isPanelOpen = useSelector((state) => state.historyPanel.isOpen);
  const handleLeave = () => {
    if (window.cancelLogoUploads) {
      window.cancelLogoUploads();
    }
  };

  const handleTogglePanel = () => {
    dispatch(togglePanel());
  };

  return (
    <Router>
      <div>
        <div onClick={handleLeave} className="pointerCursor">
          <Header subtitle="Modernize your code">
            <HeaderTools>
              <PanelRightToggles>
                <Tooltip content="View Batch History" relationship="label">
                  <Button
                    appearance="subtle"
                    icon={<History />}
                    //checked={isPanelOpen}
                    onClick={(event) => {
                      event.stopPropagation(); // Prevents the event from bubbling up
                      handleTogglePanel(); // Calls the button click handler
                    }} // Connect toggle to state
                  />
                </Tooltip>
              </PanelRightToggles>
            </HeaderTools>
          </Header>
        </div>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/batch-process/:batchId"
            element={<ModernizationPage />}
          />
          <Route path="/batch-view/:batchId" element={<BatchViewPage />} />
        </Routes>
        {isPanelOpen && (
          <div className="panelRight">
            <PanelRight panelWidth={300} panelResize={true} panelType={"first"}>
              <PanelRightToolbar
                panelTitle="Batch history"
                panelIcon={<History />}
                handleDismiss={handleTogglePanel}
              />
              <BatchHistoryPanel
                isOpen={isPanelOpen}
                onClose={() => dispatch(closePanel())}
              />
            </PanelRight>
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;
