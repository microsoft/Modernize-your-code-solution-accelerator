import React, { useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../store/store";
import { togglePanel, closePanel } from "../slices/historyPanelSlice";
declare global {
  interface Window {
    cancelUploads?: () => void;
    cancelLogoUploads?: () => void;
    startTranslating?: () => Promise<string | null>;
  }
}
import {
  Button,
  Tooltip,
} from "@fluentui/react-components";
import Content from "../components/Content/Content";
import Header from "../components/Header/Header";
import HeaderTools from "../components/Header/HeaderTools";
import PanelRightToggles from "../components/Header/PanelRightToggles";
import PanelRightToolbar from "../components/Panels/PanelRightToolbar";
import PanelRight from "../components/Panels/PanelRight";
import "./landingPage.css"

import UploadButton from "../components/uploadButton";
import BatchHistoryPanel from "../components/batchHistoryPanel"
import { HistoryRegular, HistoryFilled, bundleIcon } from "@fluentui/react-icons";
import BottomBar from "../components/bottomBar";
import { useNavigate } from "react-router-dom";
import { resetState } from '../slices/batchSlice';
export const History = bundleIcon(HistoryFilled, HistoryRegular);

export const LandingPage = (): JSX.Element => {
  const dispatch = useDispatch(); // Add dispatch hook
  const [selectedTargetLanguage, setSelectedTargetLanguage] = useState<string[]>(["T-SQL"]);
  const [selectedCurrentLanguage, setSelectedCurrentLanguage] = useState<string[]>(["Informix"]);
  const isPanelOpen = useSelector((state: RootState) => state.historyPanel.isOpen);
  const navigate = useNavigate();

  useEffect(() => {
    dispatch(resetState());
  }, [dispatch]);

  const [uploadState, setUploadState] = useState<"IDLE" | "UPLOADING" | "COMPLETED">('IDLE');

  const handleUploadStateChange = (state) => {
    setUploadState(state);
  };

  const handleCancelUploads = () => {
    // This function will be called from BottomBar
    if (window.cancelUploads) {
      window.cancelUploads();
    }
    setUploadState('IDLE');
  };

  const handleStartTranslating = async () => {
    console.log('Starting translation...');

    try {
      if (window.startTranslating) {
        // Get the batchId from startTranslating first
        const resultBatchId = await window.startTranslating();

        if (resultBatchId) {
          // Once processing is complete, navigate to the modern page
          navigate(`/batch-process/${resultBatchId}`);
        } else {
          // If no batchId returned, just go to modern
          navigate("/batch-process");
        }
      } else {
        // If startTranslating is not available, just navigate to modern
        navigate("/batch-process");
      }
    } catch (error) {
      console.error('Error in handleStartTranslating:', error);
      navigate("/batch-process");
    }
  };



  const handleCurrentLanguageChange = (currentlanguage: string[]) => {
    setSelectedCurrentLanguage(currentlanguage);
  };

  const handleTargetLanguageChange = (targetLanguage: string[]) => {
    setSelectedTargetLanguage(targetLanguage);
  };

  const handleLeave = () => {
    if (window.cancelLogoUploads) {
      window.cancelLogoUploads();
    }
  };

  const handleTogglePanel = () => {
    console.log("Toggling panel from Landing Page"); // Debugging Log
    dispatch(togglePanel());
  };

  return (
    <div className="landing-page flex flex-col relative h-screen">
      {/* Header */}
      <div onClick={handleLeave} style={{ cursor: "pointer" }}>
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
                  }}  // Connect toggle to state
                />
              </Tooltip>
            </PanelRightToggles>
          </HeaderTools>
        </Header>
      </div>
      {/* Main Content */}
      <main className={`main-content ${isPanelOpen ? "shifted" : ""} flex-1 flex overflow-auto bg-mode-neutral-background-1-rest relative`}>
        <div className="container mx-auto flex flex-col items-center justify-center  pb-20">
          {/* <div className="flex flex-col items-center gap-4 mb-[90px] max-w-[604px] text-center">
                      <h1 className="text-2xl font-bold text-neutral-foregroundneutralforegroundrest">
                          Modernize your code
                      </h1>
                      <p className="text-base font-semibold text-neutral-foregroundneutralforegroundrest">
                          Modernize your code by updating the language with AI
                      </p>
                  </div> */}

          <Content>
            <div className="w-full max-w-[720px]" style={{ zIndex: 950 }}>
              <UploadButton onUploadStateChange={handleUploadStateChange} selectedCurrentLanguage={selectedCurrentLanguage} selectedTargetLanguage={selectedTargetLanguage} />
            </div>
          </Content>
        </div>
      </main>

      {/* Side Panel */}
      {/* Side Panel for History */}

      {isPanelOpen && (
        <div
          style={{
            position: "fixed",
            top: "60px", // Adjust based on your header height
            right: 0,
            height: "calc(100vh - 60px)", // Ensure it does not cover the header
            width: "300px", // Set an appropriate width
            zIndex: 1050,
            background: "white",
            //boxShadow: "-2px 0 5px rgba(0, 0, 0, 0.2)", // Optional shadow
            overflowY: "auto",
          }}
        >
          <PanelRight panelWidth={300} panelResize={true} panelType={"first"} >

            <PanelRightToolbar panelTitle="Batch history" panelIcon={<History />} handleDismiss={handleTogglePanel} />
            <BatchHistoryPanel isOpen={isPanelOpen} onClose={() => dispatch(closePanel())} />
          </PanelRight>
        </div>
      )}

      <BottomBar
        uploadState={uploadState}
        onCancel={handleCancelUploads} onStartTranslating={handleStartTranslating} selectedTargetLanguage={selectedTargetLanguage} onTargetLanguageChange={handleTargetLanguageChange} onCurrentLanguageChange={handleCurrentLanguageChange} />
    </div>
  );
};

export default LandingPage;