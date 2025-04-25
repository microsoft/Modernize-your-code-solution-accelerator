import * as React from "react"
import Content from "../components/Content/Content";
import Header from "../components/Header/Header";
import HeaderTools from "../components/Header/HeaderTools";
import PanelLeft from "../components/Panels/PanelLeft";
import webSocketService from "../api/WebSocketService";
import {
  Button,
  Text,
  Card,
  makeStyles,
  tokens,
  Tooltip,
  Spinner,
} from "@fluentui/react-components"
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
} from "@fluentui/react-icons"
import { Light as SyntaxHighlighter } from "react-syntax-highlighter"
import { vs } from "react-syntax-highlighter/dist/esm/styles/hljs"
import sql from "react-syntax-highlighter/dist/cjs/languages/hljs/sql"
import { useNavigate, useParams } from "react-router-dom"
import { useState, useEffect, useCallback, useRef } from "react"
import { getApiUrl, headerBuilder } from '../api/config';
import BatchHistoryPanel from "../components/batchHistoryPanel"
import PanelRight from "../components/Panels/PanelRight";
import PanelRightToolbar from "../components/Panels/PanelRightToolbar";
import PanelRightToggles from "../components/Header/PanelRightToggles";
import { filesLogsBuilder, BatchSummary, completedFiles, filesErrorCounter, hasFiles, renderFileError, fileErrorCounter, renderErrorContent, filesFinalErrorCounter, formatAgent, formatDescription, fileWarningCounter } from "../api/utils";
import { format } from "sql-formatter";

export const History = bundleIcon(HistoryFilled, HistoryRegular);

SyntaxHighlighter.registerLanguage("sql", sql)

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    // backgroundColor: tokens.colorNeutralBackground2,
  },
  content: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
  },
  fileIcon: {
    color: tokens.colorNeutralForeground1,
    marginRight: "12px",
    flexShrink: 0,
    fontSize: "20px",
    height: "20px",
    width: "20px",
  },
  statusContainer: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginLeft: "auto",
  },
  fileName: {
    flex: 1,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    fontWeight: "600",
  },
  fileList: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    padding: "16px",
    flex: 1,
    overflow: "auto",
  },
  panelHeader: {
    padding: "16px 20px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  fileCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    borderRadius: "4px",
    padding: "12px",
    display: "flex",
    alignItems: "center",
    cursor: "pointer",
    "&:hover": {
      backgroundColor: tokens.colorNeutralBackground3,
      border: tokens.colorBrandBackground,
    },
  },
  selectedCard: {
    border: "var(--NeutralStroke2.Rest)",
    backgroundColor: "rgb(221, 217, 217)",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#2563EB",
    transition: "width 0.3s ease",
  },
  imageContainer: {
    display: "flex",
    justifyContent: "center",
    marginTop: "24px",
    marginBottom: "24px",
  },
  stepList: {
    marginTop: "48px",
  },
  step: {
    fontSize: "16px", // Increase font size
    fontWeight: "400", // Make text bold (optional)
    marginBottom: "48px", // Add spacing between steps
  },
  codeCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    overflow: "hidden",
    maxHeight: "87vh",
    overflowY: "auto",
  },
  codeHeader: {
    padding: "12px 16px",
  },
  summaryContent: {
    padding: "24px",
  },
  summaryCard: {
    backgroundColor: "#F2FBF2",
    marginBottom: "16px",
    boxShadow: "none"
  },
  errorContent: {
    backgroundColor: "#F8DADB",
    marginBottom: "16px",
    boxShadow: "none"
  },
  errorSection: {
    backgroundColor: "#F8DADB",
    marginBottom: "8px",
    boxShadow: "none"
  },
  warningSection: {
    backgroundColor: tokens.colorStatusWarningBackground1,
    marginBottom: "16px",
    boxShadow: "none"
  },
  warningContent: {
    backgroundColor: tokens.colorStatusWarningBackground1,
    marginBottom: "16px",
    paddingBottom: "22px",
    paddingTop: "8px",
    boxShadow: "none"
  },
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    cursor: "pointer",
  },
  errorItem: {
    marginTop: "16px",
    paddingLeft: "20px",
  },
  errorTitle: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "8px",
  },
  errorDetails: {
    marginTop: "4px",
    color: tokens.colorNeutralForeground2,
    paddingLeft: "20px",
  },
  errorSource: {
    color: tokens.colorNeutralForeground2,
    fontSize: "12px",
  },
  // Styles for the loading overlay
  loadingOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: tokens.colorNeutralBackground1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  loadingCard: {
    width: "100%",
    maxWidth: "500px",
    padding: "32px",
    textAlign: "center",
    boxShadow: tokens.shadow16,
    borderRadius: "8px",
  },
  loadingProgressBar: {
    width: "100%",
    height: "8px",
    backgroundColor: tokens.colorNeutralBackground3,
    borderRadius: "4px",
    marginTop: "24px",
    marginBottom: "8px",
    overflow: "hidden",
  },
  loadingProgressFill: {
    height: "100%",
    backgroundColor: tokens.colorBrandBackground,
    transition: "width 0.5s ease-out",
  },
  mainContent: {
    flex: 1,
    top: "60",
    backgroundColor: "white", // Change from tokens.colorNeutralBackground1 to white
    overflow: "auto",
  },
  progressSection: {
    maxWidth: "800px",
    margin: "20px auto 0", // Add top margin to move it lower in the page
    display: "flex",
    flexDirection: "column",
    paddingTop: "20px", // Add padding at the top
  },
  progressBar: {
    width: "100%",
    height: "4px",
    backgroundColor: "#E5E7EB",
    borderRadius: "2px",
    marginTop: "32px",
    marginBottom: "16px",
    overflow: "hidden",
  },
  buttonContainer: {
    padding: "16px",
    display: "flex",
    justifyContent: "flex-end",
    gap: "8px",
  },
  summaryHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 24px", // Replacing theme.spacing(2) with a fixed value
  },
  summaryTitle: {
    fontSize: "12px",
  },
  aiGeneratedTag: {
    color: "#6b7280", // Replacing theme.palette.text.secondary with a neutral gray
    fontSize: "0.875rem",
    backgroundColor: "#f3f4f6", // Replacing theme.palette.background.default with a light gray
    padding: "4px 8px", // Replacing theme.spacing(0.5, 1)
    borderRadius: "4px", // Replacing theme.shape.borderRadius with a standard value
  },
  queuedFile: {
    borderRadius: "4px",
    backgroundColor: "var(--NeutralBackgroundInvertedDisabled-Rest)", // Correct background color
    opacity: 0.5, // Disabled effect
    pointerEvents: "none", // Prevents clicks
  },
  summaryDisabled: {
    borderRadius: "4px",
    backgroundColor: "var(--NeutralBackgroundInvertedDisabled-Rest)", // Correct background color
    opacity: 0.5, // Disabled effect
    pointerEvents: "none", // Prevents clicks
  },
  inProgressFile: {
    borderRadius: "4px",
    backgroundColor: "var(--NeutralBackground1.Rest)", // Correct background color
    opacity: 0.5, // Disabled effect
  },
  completedFile: {
    borderRadius: "4px",
    backgroundColor: "var(--NeutralBackground1-Rest)", // Correct background color
  },
  downloadButton: {
    marginLeft: "auto",
    display: "flex",
    alignItems: "center",
    gap: "4px",
  },
  errorBanner: {
    backgroundColor: "#F8DADB",
    marginBottom: "16px",
    boxShadow: "none"
  },
  fixedButtonContainer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0, /* Match your panel background color */
    backgroundColor: tokens.colorNeutralBackground2,
    borderTop: "1px solid #e5e7eb", /* Optional: adds a separator line */
    padding: "0px 16px",
    zIndex: "10",
  },
  panelContainer: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    position: "relative",
  },
  fileListContainer: {
    flex: 1,
    overflowY: "auto",
    paddingBottom: "60px", /* Add padding to prevent content from being hidden behind the fixed buttons */
  },
});

type FileType = "summary" | "code"
type FileResult = "info" | "warning" | "error" | null

interface WebSocketMessage {
  batch_id: string;
  file_id: string;
  agent_type: string;
  agent_message: string;
  process_status: string;
  file_result: FileResult;
}

interface FileItem {
  id: string
  name: string
  type: FileType
  status: string
  code?: string
  translatedCode?: string
  errorCount?: number
  warningCount?: number
  file_logs?: any[];
  file_result?: string
  file_track_log?: WebSocketMessage[]
  file_track_percentage: number
  fileId?: string
  batchId?: string
  order?: number
}

// Updated function to fetch file content with translated content
const fetchFileFromAPI = async (fileId: string): Promise<any> => {
  const apiUrl = getApiUrl();
  try {
    const response = await fetch(`${apiUrl}/file/${fileId}`, { headers: headerBuilder({}) });
    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.statusText}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching file from API:", error);
    return { content: "", translatedContent: "" };
  }
};

const fetchBatchSummary = async (batchId: string): Promise<any> => {
  try {
    const apiUrl = getApiUrl();
    const response = await fetch(`${apiUrl}/batch-summary/${batchId}`, { headers: headerBuilder({}) });
    if (!response.ok) {
      throw new Error(`Failed to fetch batch data: ${response.statusText}`);
    }

    const responseData = await response.json();
    if (!responseData || !responseData.files) {
      throw new Error("Invalid data format received from server");
    }
    const data: BatchSummary = {
      batch_id: responseData.batch.batch_id,
      upload_id: responseData.batch.id, // Use id as upload_id
      date_created: responseData.batch.created_at,
      total_files: responseData.batch.file_count,
      completed_files: completedFiles(responseData.files),
      error_count: responseData.batch.status === "completed" ? filesFinalErrorCounter(responseData.files) : filesErrorCounter(responseData.files),
      status: responseData.batch.status,
      warning_count: responseData.files.reduce((count, file) => count + (file.syntax_count || 0), 0),
      hasFiles: hasFiles(responseData),
      files: responseData.files.map(file => ({
        file_id: file.file_id,
        name: file.original_name, // Use original_name here
        status: file.status,
        file_result: file.file_result,
        warning_count: fileWarningCounter(file),
        error_count: fileErrorCounter(file),
        translated_content: file.translated_content,
        file_logs: filesLogsBuilder(file),

      }))
    };
    return data;
  } catch (error) {
    console.error("Error fetchBatchSummary:", error);
    return { content: "", translatedContent: "" };
  }
};


enum ProcessingStage {
  NotStarted = 1,
  Queued = 10,
  Starting = 20,
  Parsing = 40,
  Processing = 60,
  FinalChecks = 95,
  Completed = 100
}

enum Agents {
  Verifier = "Semantic Verifier agent",
  Checker = "Syntax Checker agent",
  Picker = "Picker agent",
  Migrator = "Migrator agent",
  Agents = "Agent"
}



const getTrackPercentage = (status: string, fileTrackLog: WebSocketMessage[]): number => {
  switch (status?.toLowerCase()) {
    case "completed":
      return ProcessingStage.Completed;
    case "in_process":
      if (fileTrackLog && fileTrackLog.length > 0) {
        if (fileTrackLog.some(entry => entry.agent_type === Agents.Checker)) {
          return ProcessingStage.FinalChecks;
        } else if (fileTrackLog.some(entry => entry.agent_type === Agents.Picker)) {
          return ProcessingStage.Processing;
        } else if (fileTrackLog.some(entry => entry.agent_type === Agents.Migrator)) {
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
  const navigate = useNavigate()

  const [batchSummary, setBatchSummary] = useState<BatchSummary | null>(null);
  const styles = useStyles()
  const [text, setText] = useState("");
  const [isPanelOpen, setIsPanelOpen] = React.useState(false); // Add state management

  // Get batchId and fileList from Redux
  const [reduxFileList, setReduxFileList] = useState<FileItem[]>([]);

  // State for the loading component
  const [showLoading, setShowLoading] = useState(true);
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [selectedFilebg, setSelectedFile] = useState<string | null>(null);
  const [selectedFileId, setSelectedFileId] = React.useState<string>("")
  const [fileId, setFileId] = React.useState<string>("");
  const [expandedSections, setExpandedSections] = React.useState<string[]>([])
  const [progressPercentage, setProgressPercentage] = useState(0);
  const [allFilesCompleted, setAllFilesCompleted] = useState(false);
  const [isZipButtonDisabled, setIsZipButtonDisabled] = useState(true);
  const [fileLoading, setFileLoading] = useState(false);
  const [selectedFileTranslatedContent, setSelectedFileTranslatedContent] = useState<string>("");

  // Fetch file content when a file is selected
  useEffect(() => {
    if (selectedFileId === "summary" || !selectedFileId || fileLoading) {
      return;
    }
    const fetchFileContent = async () => {
      try {

        const selectedFile = files.find((f) => f.id === selectedFileId);
        if (!selectedFile || !selectedFile.translatedCode) {
          setFileLoading(true);
          const newFileUpdate = await fetchFileFromAPI(selectedFile?.fileId || "");
          setSelectedFileTranslatedContent(newFileUpdate.translatedContent);
          setFileLoading(false);
        } else {

          setSelectedFileTranslatedContent(selectedFile.translatedCode);
        }

      } catch (err) {
        console.error("Error fetching file content:", err);
        setFileLoading(false);
      }
    };

    fetchFileContent();
  }, [selectedFileId]);

  const fetchBatchData = async (batchId) => {
    try {
      setShowLoading(true);
      const data = await fetchBatchSummary(batchId);
      setBatchSummary(data);
      if (data) {

        const batchCompleted = data.status?.toLowerCase() === "completed" || data.status === "failed";
        if (batchCompleted) {
          setAllFilesCompleted(true);
          if (data.hasFiles > 0) {
            setIsZipButtonDisabled(false);
          }
        }
        // Transform the server response to an array of your FileItem objects
        const fileItems: FileItem[] = data.files.map((file: any, index: number) => ({
          id: `file${index}`,
          name: file.name,
          type: "code",
          status: file.status?.toLowerCase(),
          file_result: file.file_result,
          errorCount: file.status.toLowerCase() === "completed" ? file.error_count : 0,
          warningCount: file.warning_count || 0,
          code: "",
          translatedCode: file.translated_content || "",
          file_logs: file.file_logs,
          fileId: file.file_id,
          batchId: file.batch_id
        }));
        const updatedFiles: FileItem[] = [
          {
            id: "summary",
            name: "Summary",
            type: "summary",
            status: data.status?.toLowerCase() === "in_process" ? "Pending" : data.status,
            errorCount: batchCompleted ? data.error_count : 0,
            file_track_percentage: 0,
            warningCount: 0
          },
          ...fileItems
        ];

        // Store it in local state, not Redux
        setReduxFileList(updatedFiles);

      } else {
        setLoadingError("No data received from server");
      }
      setShowLoading(false);
    } catch (err) {
      console.error("Error fetching batch data:", err);
      setLoadingError(err instanceof Error ? err.message : "An unknown error occurred");
      setShowLoading(false);
    }
  };

  useEffect(() => {
    if (!batchId || batchId.length !== 36) {
      setLoadingError("No valid batch ID provided");
      setShowLoading(false);
      return;
    }

    fetchBatchData(batchId);
  }, [batchId]);

  const handleDownloadZip = async () => {
    if (batchId) {
      try {
        const apiUrl = getApiUrl();
        const response = await fetch(`${apiUrl}/download/${batchId}?batch_id=${batchId}`, { headers: headerBuilder({}) });

        if (!response.ok) {
          throw new Error("Failed to download file");
        }

        // Create a blob from the response
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        // Create a temporary <a> element and trigger download
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "download.zip"); // Specify a filename
        document.body.appendChild(link);
        link.click();

        // Cleanup
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Download failed:", error);
      }
    }
  };

  // Initialize files state with a summary file
  const [files, setFiles] = useState<FileItem[]>([
    { id: "summary", name: "Summary", type: "summary", status: "Pending", errorCount: 0, warningCount: 0, file_track_percentage: 0 },
  ]);



  useEffect(() => {
    // This handles the browser's refresh button and keyboard shortcuts
    const handleBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = '';

      // You could store a flag in sessionStorage here
      sessionStorage.setItem('refreshAttempt', 'true');
    };

    // This will execute when the page loads
    const checkForRefresh = () => {
      if (sessionStorage.getItem('refreshAttempt') === 'true') {
        // Clear the flag
        sessionStorage.removeItem('refreshAttempt');
        // Handle the "after refresh" behavior here
        console.log('Page was refreshed, restore state...');
        // You could restore form data or UI state here
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    checkForRefresh(); // Check on component mount

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
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
      event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
      return '';
    };

    // Add event listeners for maximum coverage
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup event listener on component unmount
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []); // Empty dependency array means this runs once on component mount


  useEffect(() => {
    // Prevent default refresh behavior
    const handleKeyDown = (event) => {
      // Prevent Ctrl+R, Cmd+R, and F5 refresh
      if (
        (event.ctrlKey || event.metaKey) && event.key === 'r' ||
        event.key === 'F5'
      ) {
        event.preventDefault();

        // Optional: Show a dialog or toast to inform user
        event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return '';
      }
    };

    // Prevent accidental page unload
    const handleBeforeUnload = (event) => {
      event.preventDefault();
      event.returnValue = ''; // Required for Chrome
    };

    // Add event listeners
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup event listeners on component unmount
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  // Update files state when Redux fileList changes
  useEffect(() => {
    if (reduxFileList && reduxFileList.length > 0) {
      setAllFilesCompleted(false);
      // Map the Redux fileList to our FileItem format
      const fileItems: FileItem[] = reduxFileList.filter(file => file.type !== 'summary').map((file: any, index: number) => ({

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
      const summaryFile = reduxFileList.find(file => file.type === 'summary');
      setFiles([
        summaryFile || { id: "summary", name: "Summary", type: "summary", status: "Pending", errorCount: 0, warningCount: 0, file_track_percentage: 0 },
        ...fileItems
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

      const onOpen = () => console.log('WebSocket connection established');
      webSocketService.on('open', onOpen);

      return () => {
        console.log('Cleaning up WebSocket connection');
        webSocketService.off('open', onOpen);
        webSocketService.disconnect(); // Uncomment this!
      };
    } else {
      console.log("The page you are looking for does not exist. Redirected to Home")
      navigate("/")
    }
  }, [batchId]);

  const highestProgressRef = useRef(0);
  const currentProcessingFileRef = useRef<string | null>(null);


  //new PT FR ends
  const updateSummaryStatus = async () => {
    try {
      const latestBatch = await fetchBatchSummary(batchId!);
      setBatchSummary(latestBatch);
      const allFilesDone = latestBatch.files.every(file =>
        ["completed", "failed", "error"].includes(file.status?.toLowerCase() || "")
      );
  
      if (allFilesDone) {
        setAllFilesCompleted(true);
        const hasUsableFile = latestBatch.files.some(file =>
          file.status?.toLowerCase() === "completed" &&
          file.file_result !== "error" &&
          !!file.translated_content?.trim()
        );
  
        setIsZipButtonDisabled(!hasUsableFile);
  
        setFiles(prevFiles => {
          const updated = [...prevFiles];
          const summaryIndex = updated.findIndex(f => f.id === "summary");
  
          if (summaryIndex !== -1) {
            updated[summaryIndex] = {
              ...updated[summaryIndex],
              status: "completed", 
              errorCount: latestBatch.error_count,
              warningCount: latestBatch.warning_count,
            };
          }
  
          return updated;
        });
      }
    } catch (err) {
      console.error("Failed to update summary status:", err);
    }
  };

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback(async (data: WebSocketMessage) => {
    console.log('Received WebSocket message:', data);
  
    if (!data || !data.file_id) {
      console.warn('Received invalid WebSocket message:', data);
      return;
    }
  
    setFileId(data.file_id);
  
    const agent = formatAgent(data.agent_type);
    const message = formatDescription(data.agent_message);
    data.agent_type = agent;
    data.agent_message = message;
  
    setFiles(prevFiles => {
      const fileIndex = prevFiles.findIndex(file => file.fileId === data.file_id);
      if (fileIndex === -1) return prevFiles;
  
      const newTrackLog = prevFiles[fileIndex].file_track_log?.some(entry =>
        entry.agent_type === data.agent_type && entry.agent_message === data.agent_message
      )
        ? prevFiles[fileIndex].file_track_log
        : [data, ...(prevFiles[fileIndex].file_track_log || [])];
  
      const updatedFiles = [...prevFiles];
      updatedFiles[fileIndex] = {
        ...updatedFiles[fileIndex],
        status: data.process_status,
        file_track_log: newTrackLog,
        file_track_percentage: getTrackPercentage(data.process_status, newTrackLog),
      };
  
      return updatedFiles;
    });
  
    if (data.process_status === 'completed') {
      try {
        const newFileUpdate = await fetchFileFromAPI(data.file_id);
  
        setFiles(prevFiles =>
          prevFiles.map(file =>
            file.fileId === data.file_id
              ? {
                  ...file,
                  code: newFileUpdate.content,
                  translatedCode: newFileUpdate.translated_content,
                  status: data.process_status,
                  errorCount: fileErrorCounter(newFileUpdate),
                  warningCount: fileWarningCounter(newFileUpdate),
                  file_result: newFileUpdate.file_result,
                  file_logs: filesLogsBuilder(newFileUpdate),
                }
              : file
          )
        );
  
        //Check and update summary + download status
        await updateSummaryStatus();
  
      } catch (err) {
        console.error("Error updating after file completion:", err);
      }
    }
  }, [updateSummaryStatus]);

useEffect(() => {
    const areAllFilesTerminal = files.every(file =>
      file.id === "summary" || // skip summary
      ["completed", "failed", "error"].includes(file.status?.toLowerCase() || "")
    );
  
    if (files.length > 1 && areAllFilesTerminal && !allFilesCompleted) {
      updateSummaryStatus(); 
    }
  }, [files, allFilesCompleted]);

  
useEffect(() => {
  const nonSummaryFiles = files.filter(f => f.id !== "summary");
  const completedCount = nonSummaryFiles.filter(f => f.status === "completed").length;

  if (
    nonSummaryFiles.length > 0 &&
    completedCount === nonSummaryFiles.length &&
    !allFilesCompleted
  ) {
    updateSummaryStatus(); //single source of truth
  }
}, [files, allFilesCompleted, batchId]);
  //new end
  // Listen for WebSocket messages using the WebSocketService
  useEffect(() => {
    webSocketService.on('message', handleWebSocketMessage);

    webSocketService.on('error', (error) => {
      console.error('WebSocket error:', error);
      setLoadingError('Connection error occurred. Please try again.');
    });

    webSocketService.on('close', () => {
      console.log('WebSocket connection closed');
    });

    return () => {
      webSocketService.off('message', handleWebSocketMessage);
    };
  }, [handleWebSocketMessage]);

  useEffect(() => {
    const messageHandler = (data: WebSocketMessage) => {
      console.log('WebSocket message received:', data);
      handleWebSocketMessage(data);
    };

    webSocketService.on('message', messageHandler);

    return () => {
      webSocketService.off('message', messageHandler);
    };
  }, [handleWebSocketMessage]);

  // Set a timeout for initial loading - if no progress after 30 seconds, show error
  useEffect(() => {
    const loadingTimeout = setTimeout(() => {
      if (progressPercentage < 5 && showLoading) {
        setLoadingError('Processing is taking longer than expected. You can continue waiting or try again later.');
      }
    }, 30000);

    return () => clearTimeout(loadingTimeout);
  }, [progressPercentage, showLoading]);


  useEffect(() => {
    console.log('Current files state:', files);
    console.log('Selected file ID:', selectedFileId);
    console.log('All files completed:', allFilesCompleted);
  }, [files, selectedFileId, allFilesCompleted]);


  // Auto-select next processing file
  useEffect(() => {
    // If no file is selected, try to select one
    if (!selectedFileId && files.length > 1) {
      const processingFile = files.find((f) => f.status === "in_process");
      if (processingFile) {
        setSelectedFileId(processingFile.id);
      } else {
        // Select first non-summary file
        const firstFile = files.find(f => f.id !== "summary");
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
          onClick={handleDownloadZip}
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
          <Text size={500} weight="semibold">{title}</Text>
          <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
            AI-generated content may be incorrect
          </Text>
        </div>
      );
    };
    const processingStarted = files.some(file =>
      file.id !== "summary" && (file.status === "in_process" || file.status === "completed")
    );

    // Show spinner if processing hasn't started yet
    if (!processingStarted) {
      return (
        <div className="loading-container" style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '50vh'
        }}>
          <Spinner size="large" />
          <Text style={{ marginTop: '16px', fontSize: "24px", fontWeight: "600" }}>Getting things ready</Text>
        </div>
      );
    }
    // Always show the progress bar until all files are completed
    if (!allFilesCompleted || selectedFile?.id !== "summary") {
      // If a specific file is selected (not summary) and it's completed, show the file content
      if (selectedFile && selectedFile.id !== "summary" && selectedFile.status === "completed") {
        return (
          <>
            {renderHeader()}
            <Card className={styles.codeCard}>

              <div className={styles.codeHeader}>
                <Text weight="semibold">
                  {selectedFile.name} {selectedFile.translatedCode ? "(Translated)" : ""}
                </Text>
              </div>
              {!selectedFile.errorCount && selectedFile.warningCount ? (
                <>
                  <Card className={styles.warningContent}>
                    <Text weight="semibold">File processed with warnings</Text>
                  </Card>
                  <Text style={{ padding: "20px" }}>
                    {renderFileError(selectedFile)}
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
              ) : selectedFile.status === "completed" && !selectedFile.translatedCode && !selectedFile.errorCount ? (
                <div style={{ padding: "20px", textAlign: "center" }}>
                  <Spinner />
                  <Text>Loading file content...</Text>
                </div>
              ) : null}
              {selectedFile.errorCount ? (
                <>
                  <Card className={styles.errorContent}>
                    <Text weight="semibold">Unable to process the file</Text>
                  </Card>
                  <Text style={{ padding: "20px" }}>
                    {renderFileError(selectedFile)}
                  </Text>
                </>
              ) : null}
            </Card>
          </>
        );
      }
      // Otherwise, show the progress view with summary information
      const fileIndex = files.findIndex(file => file.fileId === fileId);
      const currentFile = files[fileIndex];
      return (
        <>
          {currentFile?.file_track_percentage ? (
            <div className={styles.progressSection}>
              <Text size={600} weight="semibold" style={{ marginBottom: "20px", marginTop: "40px" }}>
                Progress tracker
              </Text>
              <div className={styles.progressBar}>
                <div className={styles.progressFill} style={{ width: `${currentFile?.file_track_percentage ?? 0}%`, transition: "width 0.5s ease-out" }} />
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <Text style={{ fontWeight: "bold", color: "#333" }}>
                  {Math.floor(currentFile?.file_track_percentage ?? 0)}/100%
                </Text>
              </div>

              <div className={styles.imageContainer}>
                <img src="/images/progress.png" alt="Progress illustration" style={{ width: "160px", height: "160px" }} />
              </div>

              <div className={styles.stepList}>
                {currentFile?.file_track_log?.map((step, index) => (
                  <div key={index} className={styles.step} style={{ display: "flex", alignItems: "center" }}>
                    <Text style={{ fontSize: "16px", marginRight: "4px", alignSelf: 'flex-start' }}>•</Text>
                    <Text style={{ fontSize: "16px", color: "#333", marginLeft: "4px" }}>
                      {step.agent_type}: {step.agent_message}
                    </Text>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ padding: "20px", textAlign: "center" }}>
              <Spinner />
              <Text>Loading file status...</Text>
            </div>
          )
          }

        </>
      );
    }

    // Show the full summary page only when all files are completed and summary is selected
    if (allFilesCompleted && selectedFile?.id === "summary") {
      const completedCount = files.filter(file => file.status === "completed" && file.file_result !== "error" && file.id !== "summary").length;
      const totalCount = files.filter(file => file.id !== "summary").length;
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
                <Text weight="semibold">{totalCount} {totalCount === 1 ? 'file' : 'files'} processed successfully</Text>
              </Card>

              {/* Success checkmark and message */}
              <div style={{
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                marginTop: '60px',
                height: '50vh'
              }}>
                <img
                  src="/images/Checkmark.png"
                  alt="Success checkmark"
                  style={{ width: '100px', height: '100px', marginBottom: '24px' }}
                />
                <Text size={600} weight="semibold" style={{ marginBottom: '16px' }}>
                  No errors! Your files are ready to download.
                </Text>
                <Text style={{ marginBottom: '24px' }}>
                  Your code has been successfully translated with no errors. All files are now ready for download. Click 'Download' to save them to your local drive.
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
            <div className={styles.summaryContent}
              style={{
                width: isPanelOpen ? "calc(100% - 340px)" : "96%",
                transition: "width 0.3s ease-in-out",
              }}>
              <Card className={styles.summaryCard}>
                <Text weight="semibold">{completedCount} of {totalCount} {totalCount === 1 ? 'file' : 'files'} processed successfully</Text>
              </Card>
              <Card className={styles.errorSection}>
                <div className={styles.sectionHeader} onClick={() =>
                  setExpandedSections((prev) =>
                    prev.includes("errors") ? prev.filter((id) => id !== "errors") : [...prev, "errors"]
                  )
                }>
                  <Text weight="semibold">Errors ({errorCount})</Text>
                  {expandedSections.includes("errors") ? <ChevronDown16Filled /> : <ChevronRight16Regular />}
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
                  <Text weight="semibold">{batchSummary.completed_files} of {batchSummary.total_files} {batchSummary.total_files === 1 ? 'file' : 'files'} processed successfully</Text>
                </Card>
              ) : null
              }
              <Card className={styles.errorSection}>
                <div className={styles.sectionHeader} onClick={() =>
                  setExpandedSections((prev) =>
                    prev.includes("errors") ? prev.filter((id) => id !== "errors") : [...prev, "errors"]
                  )
                }>
                  <Text weight="semibold">Errors ({errorCount})</Text>
                  {expandedSections.includes("errors") ? <ChevronDown16Filled /> : <ChevronRight16Regular />}
                </div>

              </Card>
              {renderErrorContent(batchSummary)}
            </div>
          </>
        );
      }
    }

    return null;
  };

  const handleTogglePanel = () => {
    console.log("Toggling panel Modernization Page"); // Debugging Log
    setIsPanelOpen((prev) => !prev);
  };


  const handleHeaderClick = () => {
    //setShowLeaveDialog(true);
    navigate("/");
  };

  const handleClick = (file: string) => {
    setSelectedFile(file === selectedFilebg ? null : file);
  };

  return (
    <div className={styles.root}>
      <div onClick={handleHeaderClick} style={{ cursor: "pointer" }}>
        <Header subtitle="Modernize your code">
          <HeaderTools>
            <PanelRightToggles>
              <Tooltip content="View batch history" relationship="label">
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

      <div className={styles.content}>
        <PanelLeft panelWidth={400} panelResize={true}>
          <div className={styles.panelContainer}>
            <div className={styles.panelHeader}>
              <Text weight="semibold">{text}</Text>
            </div>
            <div className={styles.fileListContainer}>
              <div className={styles.fileList}>
                {
                  files.map((file, index) => {
                    // Determine styling classes dynamically
                    const isQueued = file.status === "Pending" || file.status === "Queued" || file.status === "ready_to_process";
                    const isInProgress = file.status === "in_process";
                    const isCompleted = file.status === "completed";
                    const isSummary = file.id === "summary";
                    const isSummaryDisabled = isSummary && file.status !== "completed";
                    const displayStatus = getPrintFileStatus(file.status);
                    const isProcessing = displayStatus === "Processing";
                    const fileClass = `${styles.fileCard} 
                                       ${selectedFileId === file.id ? styles.selectedCard : ""} 
                                       ${isQueued ? styles.queuedFile : ""} 
                                       ${isInProgress ? styles.completedFile : ""} 
                                       ${isCompleted ? styles.completedFile : ""} 
                                       ${isSummaryDisabled ? styles.summaryDisabled : ""}
                                      `;
                    return (
                      <div
                        key={file.id}
                        className={fileClass}
                        onClick={() => {
                          // Only allow selecting summary if all files are completed
                          if (file.id === "summary" && file.status !== "completed") return;
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
                          {file.id === "summary" && allFilesCompleted && file.errorCount === 0 ? (
                            <>
                              <CheckmarkCircle24Regular style={{ color: "#0B6A0B", width: "16px", height: "16px" }} />
                            </>
                          )
                            : file.id === "summary" && file.errorCount && file.errorCount > 0 && allFilesCompleted ? (
                              <>
                                <Text>{file.errorCount.toLocaleString()} {file.errorCount === 1 ? 'error' : 'errors'}</Text>
                              </>
                            ) : file.status === "completed" && file.errorCount ? (
                              <>
                                <Text>{file.errorCount}</Text>
                                <DismissCircle24Regular style={{ color: "#BE1100", width: "16px", height: "16px" }} />
                              </>
                            ) : file.status === "completed" && file.warningCount ? (
                              <>
                                <Text>{file.warningCount}</Text>
                                <Warning24Regular style={{ color: "#B89500", width: "16px", height: "16px" }} />
                              </>
                            ) : file.status === "completed" ? (
                              <CheckmarkCircle24Regular style={{ color: "#0B6A0B", width: "16px", height: "16px" }} />
                            ) : (
                              <Text weight={isProcessing ? "semibold" : "regular"}>{displayStatus}</Text>
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
          <div className={styles.mainContent}
            style={{
              width: isPanelOpen ? "calc(100% - 300px)" : "100%",
              transition: "width 0.3s ease-in-out",
            }}>
            {renderContent()}
          </div>
        </Content>
      </div>
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
            overflowY: "auto",
          }}
        >
          <PanelRight panelWidth={300} panelResize={true} panelType={"first"} >
            <PanelRightToolbar panelTitle="Batch history" panelIcon={<History />} handleDismiss={handleTogglePanel} />
            <BatchHistoryPanel isOpen={isPanelOpen} onClose={() => setIsPanelOpen(false)} />
          </PanelRight>
        </div>
      )}
    </div>
  );
};

export default ModernizationPage;
