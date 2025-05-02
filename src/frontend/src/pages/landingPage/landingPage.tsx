import React, { useEffect, useRef, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../../store/store";
declare global {
  interface Window {
    cancelUploads?: () => void;
    cancelLogoUploads?: () => void;
    startTranslating?: () => Promise<string | null>;
  }
}
import Content from "../../components/Content/Content";
import "./landingPage.scss";

import UploadButton from "../../components/uploadButton/uploadButton";
import BottomBar from "../../components/bottomBar/bottomBar";
import { useNavigate } from "react-router-dom";
import { resetState } from "../../store/uploadFileSlice";

export const LandingPage = (): JSX.Element => {
  const dispatch = useDispatch(); // Add dispatch hook
  const [selectedTargetLanguage, setSelectedTargetLanguage] = useState<
    string[]
  >(["T-SQL"]);
  const [selectedCurrentLanguage, setSelectedCurrentLanguage] = useState<
    string[]
  >(["Informix"]);
  const batchHistoryRef = useRef<{ triggerDeleteAll: () => void } | null>(null);
  const isPanelOpen = useSelector(
    (state: RootState) => state.historyPanel.isOpen
  );
  const navigate = useNavigate();

  useEffect(() => {
    dispatch(resetState());
  }, [dispatch]);

  const [uploadState, setUploadState] = useState<
    "IDLE" | "UPLOADING" | "COMPLETED"
  >("IDLE");

  const handleUploadStateChange = (state) => {
    setUploadState(state);
  };

  const handleCancelUploads = () => {
    // This function will be called from BottomBar
    if (window.cancelUploads) {
      window.cancelUploads();
    }
    setUploadState("IDLE");
  };

  const handleStartTranslating = async () => {
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
      console.error("Error in handleStartTranslating:", error);
      navigate("/batch-process");
    }
  };

  const handleCurrentLanguageChange = (currentlanguage: string[]) => {
    setSelectedCurrentLanguage(currentlanguage);
  };

  const handleTargetLanguageChange = (targetLanguage: string[]) => {
    setSelectedTargetLanguage(targetLanguage);
  };

  return (
    <div className="landing-page flex flex-col relative h-screen">
      {/* Main Content */}
      <main
        className={`main-content ${
          isPanelOpen ? "shifted" : ""
        } flex-1 flex overflow-auto bg-mode-neutral-background-1-rest relative`}
      >
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
            <div className="w-full max-w-[720px] zI-950">
              <UploadButton
                onUploadStateChange={handleUploadStateChange}
                selectedCurrentLanguage={selectedCurrentLanguage}
                selectedTargetLanguage={selectedTargetLanguage}
              />
            </div>
          </Content>
        </div>
      </main>
      <BottomBar
        uploadState={uploadState}
        onCancel={handleCancelUploads}
        onStartTranslating={handleStartTranslating}
        selectedTargetLanguage={selectedTargetLanguage}
        onTargetLanguageChange={handleTargetLanguageChange}
        onCurrentLanguageChange={handleCurrentLanguageChange}
        selectedCurrentLanguage={selectedCurrentLanguage}
      />
    </div>
  );
};

export default LandingPage;
