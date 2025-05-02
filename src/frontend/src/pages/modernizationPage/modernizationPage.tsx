import * as React from "react";
import Content from "../../components/Content/Content";
import PanelLeft from "../../components/Panels/PanelLeft";
import webSocketService from "../../utils/WebSocketService";
import { useStyles } from "./modernizationPage.styles";
import {
  Button,
  Text,
  Card,
  tokens,
  Spinner,
} from "@fluentui/react-components";
import {
  DismissCircle24Regular,
  Warning24Regular,
  CheckmarkCircle24Regular,
  DocumentRegular,
  ChevronDown16Filled,
  ChevronRight16Regular,
  HistoryFilled,
  bundleIcon,
  HistoryRegular,
  ArrowSyncRegular,
  ArrowDownload24Regular,
} from "@fluentui/react-icons";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import { vs } from "react-syntax-highlighter/dist/esm/styles/hljs";
import sql from "react-syntax-highlighter/dist/cjs/languages/hljs/sql";
import { useNavigate, useParams } from "react-router-dom";
import { useState, useEffect, useCallback, useRef } from "react";
import {
  filesLogsBuilder,
  fileErrorCounter,
  formatAgent,
  formatDescription,
  fileWarningCounter,
} from "../../utils/utils";
import { format } from "sql-formatter";
import { FileItem, WebSocketMessage } from "../../types/types";
import { FileError } from "../../components/../commonComponents/fileError/fileError";
import ErrorComponent from "../../commonComponents/errorsComponent/errorComponent";
import { Agents, ProcessingStage } from "../../utils/constants";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from "../../store/store";
import {
  fetchBatchSummary,
  fetchFileFromAPI,
  handleDownloadZip,
} from "../../store/modernizationSlice";

export const History = bundleIcon(HistoryFilled, HistoryRegular);

SyntaxHighlighter.registerLanguage("sql", sql);

const getTrackPercentage = (
  status: string,
  fileTrackLog: WebSocketMessage[]
): number => {
  switch (status?.toLowerCase()) {
    case "completed":
      return ProcessingStage.Completed;
    case "in_process":
      if (fileTrackLog && fileTrackLog.length > 0) {
        if (fileTrackLog.some((entry) => entry.agent_type === Agents.Checker)) {
          return ProcessingStage.FinalChecks;
        } else if (
          fileTrackLog.some((entry) => entry.agent_type === Agents.Picker)
        ) {
          return ProcessingStage.Processing;
        } else if (
          fileTrackLog.some((entry) => entry.agent_type === Agents.Migrator)
        ) {
          return ProcessingStage.Parsing;
        }
        return ProcessingStage.Starting;
      }
      return ProcessingStage.Queued;
    case "ready_to_process":
      return ProcessingStage.Queued;
    default:
      return ProcessingStage.NotStarted;
  }
};

const getPrintFileStatus = (status: string): string => {
  switch (status) {
    case "completed":
      return "Completed";
    case "in_process":
      return "Processing";
    case "Processing":
      return "Pending";
    case "Pending":
      return "Pending";
    default:
      return "Queued";
  }
};

const ModernizationPage = () => {
  const { batchId } = useParams<{ batchId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const [selectedFilebg, setSelectedFile] = useState<string | null>(null);

  const handleClick = (file: string) => {
    setSelectedFile(file === selectedFilebg ? null : file);
  };

  //const [batchSummary, setBatchSummary] = useState<BatchSummary | null>(null);
  const styles = useStyles();
  const [text, setText] = useState("");
  const isPanelOpen = useSelector(
    (state: RootState) => state.historyPanel.isOpen
  );

  // Get batchId and fileList from Redux
  const [reduxFileList, setReduxFileList] = useState<FileItem[]>([]);

  // State for the loading component
  const [showLoading, setShowLoading] = useState(true);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  const [selectedFileId, setSelectedFileId] = React.useState<string>("");
  const [fileId, setFileId] = React.useState<string>("");
  const [expandedSections, setExpandedSections] = useState(["errors"]);
  const [progressPercentage, setProgressPercentage] = useState(0);
  const [allFilesCompleted, setAllFilesCompleted] = useState(false);
  const [isZipButtonDisabled, setIsZipButtonDisabled] = useState(true);
  const [fileLoading, setFileLoading] = useState(false);
  const [selectedFileTranslatedContent, setSelectedFileTranslatedContent] =
    useState<string>("");

  const { fileContent, batchSummary } = useSelector(
    (state: RootState) => state.modernizationReducer
  );

  const fetchBatchData = async (batchId) => {
    try {
      setShowLoading(true);
      dispatch(fetchBatchSummary(batchId));
    } catch (err) {
      console.error("Error fetching batch data:", err);
      setLoadingError(
        err instanceof Error ? err.message : "An unknown error occurred"
      );
      setShowLoading(false);
    }
  };

  useEffect(() => {
    if (batchSummary  && batchSummary.batch_id !=='' && batchSummary.upload_id !=='') {
      const batchCompleted =
        batchSummary?.status?.toLowerCase() === "completed" ||
        batchSummary?.status === "failed";
      if (batchCompleted) {
        setAllFilesCompleted(true);
        if (batchSummary?.hasFiles > 0) {
          setIsZipButtonDisabled(false);
        }
      }
      // Transform the server response to an array of your FileItem objects
      const fileItems: FileItem[] = batchSummary?.files.map(
        (file: any, index: number) => ({
          id: `file${index}`,
          name: file.name,
          type: "code",
          status: file.status?.toLowerCase(),
          file_result: file.file_result,
          errorCount:
            file.status.toLowerCase() === "completed" ? file.error_count : 0,
          warningCount: file.warning_count || 0,
          code: "",
          translatedCode: file.translated_content || "",
          file_logs: file.file_logs,
          fileId: file.file_id,
          batchId: file.batch_id,
        })
      );
      const updatedFiles: FileItem[] = [
        {
          id: "summary",
          name: "Summary",
          type: "summary",
          status:
            batchSummary?.status?.toLowerCase() === "in_process"
              ? "Pending"
              : batchSummary?.status,
          errorCount: batchCompleted ? batchSummary?.error_count : 0,
          file_track_percentage: 0,
          warningCount: 0,
        },
        ...fileItems,
      ];

      // Store it in local state, not Redux
      setReduxFileList(updatedFiles);
    } else {
      setLoadingError("No data received from server");
    }
    setShowLoading(false);
  }, [batchSummary]);

  useEffect(() => {
    if (!batchId || batchId.length !== 36) {
      setLoadingError("No valid batch ID provided");
      setShowLoading(false);
      return;
    }

    fetchBatchData(batchId);
  }, [batchId]);

  const downloadZip = async () => {
    if (batchId) {
      dispatch(handleDownloadZip(batchId));
    }
  };

  // Initialize files state with a summary file
  const [files, setFiles] = useState<FileItem[]>([
    {
      id: "summary",
      name: "Summary",
      type: "summary",
      status: "Pending",
      errorCount: 0,
      warningCount: 0,
      file_track_percentage: 0,
    },
  ]);

  useEffect(() => {
    // This handles the browser's refresh button and keyboard shortcuts
    const handleBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = "";

      // You could store a flag in sessionStorage here
      sessionStorage.setItem("refreshAttempt", "true");
    };

    // This will execute when the page loads
    const checkForRefresh = () => {
      if (sessionStorage.getItem("refreshAttempt") === "true") {
        // Clear the flag
        sessionStorage.removeItem("refreshAttempt");
        // Handle the "after refresh" behavior here
        console.log("Page was refreshed, restore state...");
        // You could restore form data or UI state here
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    checkForRefresh(); // Check on component mount

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  useEffect(() => {
    const handleBeforeUnload = (event) => {
      // Completely prevent browser's default dialog
      event.preventDefault();
      event.stopPropagation();

      // Show your custom dialog
      //setShowLeaveDialog(true);

      // Modern browsers require this to suppress their own dialog
      event.returnValue =
        "You have unsaved changes. Are you sure you want to leave?";
      return "";
    };

    // Add event listeners for maximum coverage
    window.addEventListener("beforeunload", handleBeforeUnload);

    // Cleanup event listener on component unmount
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []); // Empty dependency array means this runs once on component mount

  useEffect(() => {
    // Prevent default refresh behavior
    const handleKeyDown = (event) => {
      // Prevent Ctrl+R, Cmd+R, and F5 refresh
      if (
        ((event.ctrlKey || event.metaKey) && event.key === "r") ||
        event.key === "F5"
      ) {
        event.preventDefault();

        // Optional: Show a dialog or toast to inform user
        event.returnValue =
          "You have unsaved changes. Are you sure you want to leave?";
        return "";
      }
    };

    // Prevent accidental page unload
    const handleBeforeUnload = (event) => {
      event.preventDefault();
      event.returnValue = ""; // Required for Chrome
    };

    // Add event listeners
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("beforeunload", handleBeforeUnload);

    // Cleanup event listeners on component unmount
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  // Update files state when Redux fileList changes
  useEffect(() => {
    if (reduxFileList && reduxFileList.length > 0) {
      // Map the Redux fileList to our FileItem format
      const fileItems: FileItem[] = reduxFileList
        .filter((file) => file.type !== "summary")
        .map((file: any, index: number) => ({
          id: file.id,
          name: file.name,
          type: "code",
          status: file.status, // Initial status
          file_result: file.file_result,
          fileId: file.fileId,
          batchId: file.batchId,
          file_logs: file.file_logs,
          file_track_percentage: file.status === "completed" ? 100 : 0,
          code: "",
          translatedCode: file.translatedCode || "",
          errorCount: file.errorCount || 0,
          warningCount: file.warningCount || 0,
        }));

      // Add summary file at the beginning
      const summaryFile = reduxFileList.find((file) => file.type === "summary");
      setFiles([
        summaryFile || {
          id: "summary",
          name: "Summary",
          type: "summary",
          status: "Pending",
          errorCount: 0,
          warningCount: 0,
          file_track_percentage: 0,
        },
        ...fileItems,
      ]);

      // If no file is selected, select the first file
      if (!selectedFileId && fileItems.length > 0) {
        if (summaryFile && summaryFile.status === "completed") {
          setSelectedFileId(summaryFile.id);
        } else {
          setSelectedFileId(fileItems[0].id);
        }
      }

      // Update text with file count
      setText(`${new Date().toLocaleDateString()} (${fileItems.length} files)`);
    }
  }, [reduxFileList, batchId]);

  // Set up WebSocket connection using the WebSocketService
  useEffect(() => {
    if (batchId?.length === 36) {
      console.log(`Connecting to WebSocket with batchId: ${batchId}`);
      webSocketService.connect(batchId);

      const onOpen = () => console.log("WebSocket connection established");
      webSocketService.on("open", onOpen);

      return () => {
        console.log("Cleaning up WebSocket connection");
        webSocketService.off("open", onOpen);
        webSocketService.disconnect(); // Uncomment this!
      };
    } else {
      console.log(
        "The page you are looking for does not exist. Redirected to Home"
      );
      navigate("/");
    }
  }, [batchId]);

  const highestProgressRef = useRef(0);
  const currentProcessingFileRef = useRef<string | null>(null);

  //new PT FR ends
  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback(
    async (data: WebSocketMessage) => {
      console.log("Received WebSocket message:", data);

      if (!data || !data.file_id) {
        console.warn("Received invalid WebSocket message:", data);
        return;
      }

      if (data.file_id) {
        currentProcessingFileRef.current = data.file_id;
      }
      // Update process steps dynamically from agent_type
      const agent = formatAgent(data.agent_type);
      const message = formatDescription(data.agent_message);
      setFileId(data.file_id);

      // Update file status based on the message
      setFiles((prevFiles) => {
        const fileIndex = prevFiles.findIndex(
          (file) => file.fileId === data.file_id
        );

        if (fileIndex === -1) {
          console.warn(
            `File with ID ${data.file_id} not found in the file list`
          );
          return prevFiles;
        }
        data.agent_message = message;
        data.agent_type = agent;
        const updatedFiles = [...prevFiles];
        const newTrackLog = updatedFiles[fileIndex].file_track_log?.some(
          (entry) =>
            entry.agent_type === data.agent_type &&
            entry.agent_message === data.agent_message
        )
          ? updatedFiles[fileIndex].file_track_log
          : [data, ...(updatedFiles[fileIndex].file_track_log || [])];
        updatedFiles[fileIndex] = {
          ...updatedFiles[fileIndex],
          status: data.process_status,
          file_track_log: newTrackLog,
          file_track_percentage: getTrackPercentage(
            data.process_status,
            newTrackLog
          ),
        };

        // Update summary status
        const summaryIndex = updatedFiles.findIndex(
          (file) => file.id === "summary"
        );
        if (summaryIndex !== -1) {
          const totalFiles = updatedFiles.filter(
            (file) => file.id !== "summary"
          ).length;
          const completedFiles = updatedFiles.filter(
            (file) => file.status === "completed" && file.id !== "summary"
          ).length;
          const newAllFilesCompleted =
            completedFiles === totalFiles && totalFiles > 0;
          setAllFilesCompleted(newAllFilesCompleted);

          updatedFiles[summaryIndex] = {
            ...updatedFiles[summaryIndex],
            status: newAllFilesCompleted ? "completed" : "Processing",
          };
        }

        return updatedFiles;
      });

      // Fetch file content if processing is completed
      if (data.process_status === "completed") {
        try {
          dispatch(fetchFileFromAPI(data.file_id || ""));
          //const newFileUpdate = await fetchFileFromAPI123(data.file_id);
          //const batchSumamry = await fetchBatchSummary123(data.batch_id);
          dispatch(fetchBatchSummary(data.batch_id));
          //setBatchSummary(batchSumamry);
          setFiles((currentFiles) => {
            const c = currentFiles.map((f) =>
              f.fileId === data.file_id
                ? {
                    ...f,
                    code: fileContent?.content,
                    status: data.process_status,
                    translatedCode: fileContent?.translated_content,
                    errorCount: fileErrorCounter(fileContent),
                    warningCount: fileWarningCounter(fileContent),
                    file_result: fileContent.file_result || undefined,
                    file_logs: filesLogsBuilder(fileContent),
                  }
                : f
            );
            // Update summary status
            const summaryIndex = c.findIndex((file) => file.id === "summary");
            if (summaryIndex !== -1) {
              setAllFilesCompleted(batchSummary?.status === "completed");
              if (
                batchSummary?.status === "completed" &&
                batchSummary?.hasFiles > 0
              ) {
                setIsZipButtonDisabled(false);
              }

              c[summaryIndex] = {
                ...c[summaryIndex],
                errorCount: batchSummary?.error_count,
                warningCount: batchSummary?.warning_count,
                status:
                  batchSummary?.status === "completed"
                    ? batchSummary?.status
                    : "Processing",
              };
            }
            return c;
          });
          // updateProgressPercentage();
        } catch (error) {
          console.error("Error fetching completed file:", error);
        }
      } else {
        // updateProgressPercentage();
      }
    },
    [files, fileId]
  );

  // Listen for WebSocket messages using the WebSocketService
  useEffect(() => {
    webSocketService.on("message", handleWebSocketMessage);

    webSocketService.on("error", (error) => {
      console.error("WebSocket error:", error);
      setLoadingError("Connection error occurred. Please try again.");
    });

    webSocketService.on("close", () => {
      console.log("WebSocket connection closed");
    });

    return () => {
      webSocketService.off("message", handleWebSocketMessage);
    };
  }, [handleWebSocketMessage]);

  useEffect(() => {
    const messageHandler = (data: WebSocketMessage) => {
      console.log("WebSocket message received:", data);
      handleWebSocketMessage(data);
    };

    webSocketService.on("message", messageHandler);

    return () => {
      webSocketService.off("message", messageHandler);
    };
  }, [handleWebSocketMessage]);

  // Set a timeout for initial loading - if no progress after 30 seconds, show error
  useEffect(() => {
    const loadingTimeout = setTimeout(() => {
      if (progressPercentage < 5 && showLoading) {
        setLoadingError(
          "Processing is taking longer than expected. You can continue waiting or try again later."
        );
      }
    }, 30000);

    return () => clearTimeout(loadingTimeout);
  }, [progressPercentage, showLoading]);

  useEffect(() => {}, [files, selectedFileId, allFilesCompleted]);

  // Auto-select next processing file
  useEffect(() => {
    // If no file is selected, try to select one
    if (!selectedFileId && files.length > 1) {
      const processingFile = files.find((f) => f.status === "in_process");
      if (processingFile) {
        setSelectedFileId(processingFile.id);
      } else {
        // Select first non-summary file
        const firstFile = files.find((f) => f.id !== "summary");
        if (firstFile) {
          setSelectedFileId(firstFile.id);
        }
      }
    }
  }, [files, selectedFileId, allFilesCompleted]);

  const renderBottomButtons = () => {
    return (
      <div className={styles.buttonContainer}>
        <Button appearance="secondary" onClick={() => navigate("/")}>
          Return home
        </Button>
        <Button
          appearance="primary"
          onClick={downloadZip}
          className={styles.downloadButton}
          icon={<ArrowDownload24Regular />}
          disabled={isZipButtonDisabled}
        >
          Download all as .zip
        </Button>
      </div>
    );
  };

  const selectedFile = files.find((f) => f.id === selectedFileId);

  // Fix for the Progress tracker title, positioning and background color
  const renderContent = () => {
    const renderHeader = () => {
      const selectedFile = files.find((f) => f.id === selectedFileId);

      if (!selectedFile) return null;

      const title = selectedFile.id === "summary" ? "Summary" : "T-SQL";

      return (
        <div className={styles.summaryHeader}>
          <Text size={500} weight="semibold">
            {title}
          </Text>
          <Text size={200} className={styles.textColor}>
            AI-generated content may be incorrect
          </Text>
        </div>
      );
    };
    const processingStarted = files.some(
      (file) =>
        file.id !== "summary" &&
        (file.status === "in_process" || file.status === "completed")
    );

    // Show spinner if processing hasn't started yet
    if (!processingStarted) {
      return (
        <div
          className="loading-container"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "50vh",
          }}
        >
          <Spinner size="large" />
          <Text
            className={styles.gettingRedayInfo}
          >
            Getting things ready
          </Text>
        </div>
      );
    }
    // Always show the progress bar until all files are completed
    if (!allFilesCompleted || selectedFile?.id !== "summary") {
      // If a specific file is selected (not summary) and it's completed, show the file content
      if (
        selectedFile &&
        selectedFile.id !== "summary" &&
        selectedFile.status === "completed"
      ) {
        return (
          <>
            {renderHeader()}
            <Card className={styles.codeCard}>
              <div className={styles.codeHeader}>
                <Text weight="semibold">
                  {selectedFile.name}{" "}
                  {selectedFile.translatedCode ? "(Translated)" : ""}
                </Text>
              </div>
              {!selectedFile.errorCount && selectedFile.warningCount ? (
                <>
                  <Card className={styles.warningContent}>
                    <Text weight="semibold">File processed with warnings</Text>
                  </Card>
                  <Text className={styles.p_20}>
                    <ErrorComponent file={selectedFile} />
                  </Text>
                </>
              ) : null}
              {selectedFile.translatedCode ? (
                <SyntaxHighlighter
                  language="sql"
                  style={vs}
                  showLineNumbers
                  customStyle={{
                    margin: 0,
                    padding: "16px",
                    backgroundColor: tokens.colorNeutralBackground1,
                  }}
                >
                  {format(selectedFile.translatedCode, { language: "tsql" })}
                </SyntaxHighlighter>
              ) : selectedFile.status === "completed" &&
                !selectedFile.translatedCode &&
                !selectedFile.errorCount ? (
                <div className={styles.spinnerCon}>
                  <Spinner />
                  <Text>Loading file content...</Text>
                </div>
              ) : null}
              {selectedFile.errorCount ? (
                <>
                  <Card className={styles.errorContent}>
                    <Text weight="semibold">Unable to process the file</Text>
                  </Card>
                  <Text className={styles.p_20}>
                    <ErrorComponent file={selectedFile} />
                  </Text>
                </>
              ) : null}
            </Card>
          </>
        );
      }
      // Otherwise, show the progress view with summary information
      const fileIndex = files.findIndex((file) => file.fileId === fileId);
      const currentFile = files[fileIndex];
      return (
        <>
          {currentFile?.file_track_percentage ? (
            <div className={styles.progressSection}>
              <Text
                size={600}
                weight="semibold"
                className={styles.progressText}
              >
                Progress tracker
              </Text>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{
                    width: `${currentFile?.file_track_percentage ?? 0}%`,
                    transition: "width 0.5s ease-out",
                  }}
                />
              </div>
              <div className={styles.percentageTextContainer}>
                <Text className={styles.percentageText}>
                  {Math.floor(currentFile?.file_track_percentage ?? 0)}%
                </Text>
              </div>

              <div className={styles.imageContainer}>
                <img
                  src="/images/progress.png"
                  alt="Progress illustration"
                  className={styles.progressIcon}
                />
              </div>

              <div className={styles.stepList}>
                {currentFile?.file_track_log?.map((step, index) => (
                  <div
                    key={index}
                    className={styles.step}
                    style={{ display: "flex", alignItems: "center" }}
                  >
                    <Text
                      className={styles.fileLogText1}
                    >
                      •
                    </Text>
                    <Text
                      className={styles.fileLogText2}
                    >
                      {step.agent_type}: {step.agent_message}
                    </Text>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className={styles.loadingText}>
              <Spinner />
              <Text>Loading file status...</Text>
            </div>
          )}
        </>
      );
    }

    // Show the full summary page only when all files are completed and summary is selected
    if (allFilesCompleted && selectedFile?.id === "summary") {
      const completedCount = files.filter(
        (file) =>
          file.status === "completed" &&
          file.file_result !== "error" &&
          file.id !== "summary"
      ).length;
      const totalCount = files.filter((file) => file.id !== "summary").length;
      const errorCount = selectedFile.errorCount || 0;

      // Check if there are no errors and all files are processed successfully
      const noErrors = errorCount === 0;
      const allFilesProcessed = completedCount === totalCount;
      if (noErrors && allFilesProcessed) {
        // Show the success message UI with the green banner and checkmark
        return (
          <>
            {renderHeader()}
            <div className={styles.summaryContent}>
              {/* Green success banner */}
              <Card className={styles.summaryCard}>
                <Text weight="semibold">
                  {totalCount} {totalCount === 1 ? "file" : "files"} processed
                  successfully
                </Text>
              </Card>

              {/* Success checkmark and message */}
              <div
                className={styles.successContainer}
              >
                <img
                  src="/images/Checkmark.png"
                  alt="Success checkmark"
                />
                <Text
                  size={600}
                  weight="semibold"
                  className={styles.mb_16}
                >
                  No errors! Your files are ready to download.
                </Text>
                <Text className={styles.mb_24}>
                  Your code has been successfully translated with no errors. All
                  files are now ready for download. Click 'Download' to save
                  them to your local drive.
                </Text>
              </div>
            </div>
          </>
        );
      }

      // Otherwise show the regular summary view with errors/warnings
      if (noErrors && allFilesProcessed) {
        return (
          <>
            {renderHeader()}
            <div
              className={styles.summaryContent}
              style={{
                width: isPanelOpen ? "calc(100% - 375px)" : "96%",
                transition: "width 0.3s ease-in-out",
              }}
            >
              <Card className={styles.summaryCard}>
                <Text weight="semibold">
                  {completedCount} of {totalCount}{" "}
                  {totalCount === 1 ? "file" : "files"} processed successfully
                </Text>
              </Card>
              <Card className={styles.errorSection}>
                <div
                  className={styles.sectionHeader}
                  onClick={() =>
                    setExpandedSections((prev) =>
                      prev.includes("errors")
                        ? prev.filter((id) => id !== "errors")
                        : [...prev, "errors"]
                    )
                  }
                >
                  <Text weight="semibold">Errors ({errorCount})</Text>
                  {expandedSections.includes("errors") ? (
                    <ChevronDown16Filled />
                  ) : (
                    <ChevronRight16Regular />
                  )}
                </div>
              </Card>
            </div>
          </>
        );
      } else {
        return (
          <>
            {renderHeader()}
            <div className={styles.summaryContent}>
              {batchSummary && batchSummary.completed_files > 0 ? (
                <Card className={styles.summaryCard}>
                  <Text weight="semibold">
                    {batchSummary.completed_files} of {batchSummary.total_files}{" "}
                    {batchSummary.total_files === 1 ? "file" : "files"}{" "}
                    processed successfully
                  </Text>
                </Card>
              ) : null}

              <FileError 
                batchSummary={batchSummary} 
                expandedSections={expandedSections}
                setExpandedSections={setExpandedSections}
                styles={styles}
              />
            </div>
          </>
        );
      }
    }

    return null;
  };

  return (
    <div className={styles.root}>
      <div className={styles.content}>
        <PanelLeft panelWidth={400} panelResize={true}>
          <div className={styles.panelContainer}>
            <div className={styles.panelHeader}>
              <Text weight="semibold">{text}</Text>
            </div>
            <div className={styles.fileListContainer}>
              <div className={styles.fileList}>
                {files.map((file, index) => {
                  // Determine styling classes dynamically
                  const isQueued =
                    file.status === "Pending" ||
                    file.status === "Queued" ||
                    file.status === "ready_to_process";
                  const isInProgress = file.status === "in_process";
                  const isCompleted = file.status === "completed";
                  const isSummary = file.id === "summary";
                  const isSummaryDisabled =
                    isSummary && file.status !== "completed";
                  const displayStatus = getPrintFileStatus(file.status);
                  const isProcessing = displayStatus === "Processing";
                  const fileClass = `${styles.fileCard} 
                                       ${
                                         selectedFileId === file.id
                                           ? styles.selectedCard
                                           : ""
                                       } 
                                       ${isQueued ? styles.queuedFile : ""} 
                                       ${
                                         isInProgress
                                           ? styles.completedFile
                                           : ""
                                       } 
                                       ${
                                         isCompleted ? styles.completedFile : ""
                                       } 
                                       ${
                                         isSummaryDisabled
                                           ? styles.summaryDisabled
                                           : ""
                                       }
                                      `;
                  return (
                    <div
                      key={file.id}
                      className={fileClass}
                      onClick={() => {
                        // Only allow selecting summary if all files are completed
                        if (
                          file.id === "summary" &&
                          file.status !== "completed"
                        )
                          return;
                        // Don't allow selecting queued files
                        if (file.status === "ready_to_process") return;
                        setSelectedFileId(file.id);
                        handleClick(file.id);
                      }}
                      style={{
                        backgroundColor: selectedFilebg === file.id ? "#EBEBEB" : "var(--NeutralBackground1-Rest)",
                      }}
                    >
                      {isSummary ? (
                        <DocumentRegular className={styles.fileIcon} />
                      ) : isInProgress ? (
                        // Use the Fluent arrow sync icon for processing files
                        <ArrowSyncRegular className={styles.fileIcon} />
                      ) : (
                        <DocumentRegular className={styles.fileIcon} />
                      )}
                      <Text className={styles.fileName}>{file.name}</Text>
                      <div className={styles.statusContainer}>
                        {file.id === "summary" &&
                        allFilesCompleted &&
                        file.errorCount === 0 ? (
                          <>
                            <CheckmarkCircle24Regular
                              className={styles.checkMarkIcon}
                            />
                          </>
                        ) : file.id === "summary" &&
                          file.errorCount &&
                          file.errorCount > 0 &&
                          allFilesCompleted ? (
                          <>
                            <Text>
                              {file.errorCount.toLocaleString()}{" "}
                              {file.errorCount === 1 ? "error" : "errors"}
                            </Text>
                          </>
                        ) : file.status === "completed" && file.errorCount ? (
                          <>
                            <Text>{file.errorCount}</Text>
                            <DismissCircle24Regular
                              className={styles.dismissIcon}
                            />
                          </>
                        ) : file.status === "completed" && file.warningCount ? (
                          <>
                            <Text>{file.warningCount}</Text>
                            <Warning24Regular
                              className={styles.warningIcon}
                            />
                          </>
                        ) : file.status === "completed" ? (
                          <CheckmarkCircle24Regular
                            className={styles.completedIcon}
                          />
                        ) : (
                          <Text weight={isProcessing ? "semibold" : "regular"}>
                            {displayStatus}
                          </Text>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className={styles.fixedButtonContainer}>
              {renderBottomButtons()}
            </div>
          </div>
        </PanelLeft>

        <Content>
          <div
            className={styles.mainContent}
            style={{
              width: isPanelOpen ? "calc(100% - 300px)" : "100%",
              transition: "width 0.3s ease-in-out",
            }}
          >
            {renderContent()}
          </div>
        </Content>
      </div>
    </div>
  );
};

export default ModernizationPage;
