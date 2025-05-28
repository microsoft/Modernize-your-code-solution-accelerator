import * as React from "react";
import { useParams } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Content from "../../components/Content/Content";
import Header from "../../components/Header/Header";
import HeaderTools from "../../components/Header/HeaderTools";
import PanelLeft from "../../components/Panels/PanelLeft";
import {
  Button,
  Text,
  Card,
  tokens,
  Spinner,
  Tooltip,
} from "@fluentui/react-components";
import {
  DismissCircle24Regular,
  CheckmarkCircle24Regular,
  DocumentRegular,
  ArrowDownload24Regular,
  bundleIcon,
  HistoryFilled,
  HistoryRegular,
  Warning24Regular,
} from "@fluentui/react-icons";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import sql from "react-syntax-highlighter/dist/esm/languages/hljs/sql";
import { vs } from "react-syntax-highlighter/dist/esm/styles/hljs";
import PanelRightToggles from "../../components/Header/PanelRightToggles";
import PanelRight from "../../components/Panels/PanelRight";
import PanelRightToolbar from "../../components/Panels/PanelRightToolbar";
import BatchHistoryPanel from "../../components/batchHistoryPanel/batchHistoryPanel";
import ConfirmationDialog from "../../commonComponents/ConfirmationDialog/confirmationDialogue";
import {
  determineFileStatus,
  filesLogsBuilder,
  filesErrorCounter,
  completedFiles,
  hasFiles,
  fileErrorCounter,
  fileWarningCounter,
} from "../../utils/utils";
import { useStyles } from "./batchView.styles";
export const History = bundleIcon(HistoryFilled, HistoryRegular);
import { format } from "sql-formatter";
import { FileItem, BatchSummary } from "../../types/types";
import { FileError } from "../../components/../commonComponents/fileError/fileError";
import ErrorComponent from "../../commonComponents/errorsComponent/errorComponent";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from "../../store/store";
import {
  fetchBatchSummary,
  fetchFileFromAPI,
  handleDownloadZip,
} from "../../store/modernizationSlice";

SyntaxHighlighter.registerLanguage("sql", sql);

const BatchStoryPage = () => {
  const { batchId } = useParams<{ batchId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const [showLeaveDialog, setShowLeaveDialog] = useState(false);
  const styles = useStyles();
  const [batchTitle, setBatchTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [fileLoading, setFileLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [uploadId, setUploadId] = useState<string>("");
  const isPanelOpen = useSelector(
    (state: RootState) => state.historyPanel.isOpen
  );

  // Files state with a summary file
  const [files, setFiles] = useState<FileItem[]>([]);

  const [selectedFileId, setSelectedFileId] = useState<string>("");
  const [expandedSections, setExpandedSections] = useState(["errors"]);
  const [localBatchSummary, setLocalBatchSummary] =
    useState<BatchSummary | null>(null);
  const [selectedFileContent, setSelectedFileContent] = useState<string>("");
  const [selectedFileTranslatedContent, setSelectedFileTranslatedContent] =
    useState<string>("");
  const { fileContent, batchSummary } = useSelector(
    (state: RootState) => state.modernizationReducer
  );

  // Fetch batch data from API
  useEffect(() => {
    if (!batchId || !(batchId.length === 36)) {
      setError("Invalid batch ID provided");
      setLoading(false);
      return;
    }
    setLoading(true);
    setDataLoaded(false);
    dispatch(fetchBatchSummary(batchId)); // Fetch batch summary from Redux store
  }, [batchId]);

  useEffect(() => {
    if(batchSummary && batchSummary.batch_id !=='' && batchSummary.upload_id !==''){
      setLocalBatchSummary(batchSummary);
      setUploadId(batchSummary.upload_id);

      // Set batch title with date and file count
      const formattedDate = new Date(
        batchSummary.date_created
      ).toLocaleDateString();
      setBatchTitle(
        `${formattedDate} (${batchSummary.total_files} file${
          batchSummary.total_files === 1 ? "" : "s"
        })`
      );
      // Create file list from API response
      const fileItems: FileItem[] = batchSummary.files.map((file) => ({
        id: file.file_id,
        name: file.name, // This is now the original_name from API
        type: "code",
        status: determineFileStatus(file),
        code: "", // Don't store content here, will fetch on demand
        translatedCode: "", // Don't store content here, will fetch on demand
        errorCount: file.error_count,
        file_logs: file.file_logs,
        warningCount: file.warning_count,
      }));

      // Add summary file
      const updatedFiles: FileItem[] = [
        {
          id: "summary",
          name: "Summary",
          type: "summary",
          status: "completed",
          errorCount: batchSummary.error_count,
          warningCount: batchSummary.warning_count,
          file_logs: [],
        },
        ...fileItems,
      ];

      setFiles(updatedFiles as FileItem[]);
      setSelectedFileId("summary"); // Default to summary view
      setDataLoaded(true);
      setLoading(false);
    }
    
  }, [batchSummary]);

  // Fetch file content when a file is selected
  useEffect(() => {
    if (selectedFileId === "summary" || !selectedFileId || fileLoading) {
      return;
    }
    setFileLoading(true);
    dispatch(fetchFileFromAPI(selectedFileId));
  }, [selectedFileId]);

  useEffect(() => {
    if (fileContent) {
      setSelectedFileContent(fileContent.content || "");
      setSelectedFileTranslatedContent(fileContent.translated_content || "");
    }

    setFileLoading(false);
  }, [fileContent]);

  const renderWarningContent = () => {
    if (!expandedSections.includes("warnings")) return null;

    if (!localBatchSummary) return null;

    // Group warnings by file
    const warningFiles = files.filter(
      (file) =>
        file.warningCount && file.warningCount > 0 && file.id !== "summary"
    );

    if (warningFiles.length === 0) {
      return (
        <div className={styles.errorItem}>
          <Text>No warnings found.</Text>
        </div>
      );
    }

    return (
      <div>
        {warningFiles.map((file, fileIndex) => (
          <div key={fileIndex} className={styles.errorItem}>
            <div className={styles.errorTitle}>
              <Text weight="semibold">
                {file.name} ({file.warningCount})
              </Text>
              <Text className={styles.errorSource}>source</Text>
            </div>
            <div className={styles.errorDetails}>
              <Text>Warning in file processing. See file for details.</Text>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderContent = () => {
    // Define header content based on selected file
    const renderHeader = () => {
      const selectedFile = files.find((f) => f.id === selectedFileId);

      if (!selectedFile) return null;

      const title = selectedFile.id === "summary" ? "Summary" : "T-SQL";

      return (
        <div
          className={styles.summaryHeader}
          style={{
            width: isPanelOpen ? "calc(102% - 375px)" : "96%",
          }}
        >
          <Text size={500} weight="semibold">
            {title}
          </Text>
          <Text
            size={200}
            className={`${styles.aiInfoText} ${styles.errorText}`}
          >
            AI-generated content may be incorrect
          </Text>
        </div>
      );
    };

    if (loading) {
      return (
        <>
          {renderHeader()}
          <div className={styles.loadingContainer}>
            <Spinner size="large" />
            <Text size={500}>Loading batch data...</Text>
          </div>
        </>
      );
    }

    if (error) {
      return (
        <>
          {renderHeader()}
          <div className={styles.loadingContainer}>
            <Text size={500} className={styles.errorText}>
              Error: {error}
            </Text>
            <Button appearance="primary" onClick={() => navigate("/")}>
              Return to Home
            </Button>
          </div>
        </>
      );
    }

    if (!dataLoaded || !localBatchSummary) {
      return (
        <>
          {renderHeader()}
          <div className={styles.loadingContainer}>
            <Text size={500}>No data available</Text>
            <Button appearance="primary" onClick={() => navigate("/")}>
              Return to Home
            </Button>
          </div>
        </>
      );
    }

    const selectedFile = files.find((f) => f.id === selectedFileId);
    if (!selectedFile) {
      return (
        <>
          {renderHeader()}
          <div className={styles.loadingContainer}>
            <Text size={500}>No file selected</Text>
          </div>
        </>
      );
    }

    // If a specific file is selected (not summary), show the file content
    if (selectedFile.id !== "summary") {
      return (
        <>
          {renderHeader()}
          <Card
            className={styles.codeCard}
            style={{
              width: isPanelOpen ? "calc(100% - 320px)" : "98%",
            }}
          >
            <div className={styles.codeHeader}>
              <Text weight="semibold">
                {selectedFile.name}{" "}
                {selectedFileTranslatedContent ? "(Translated)" : ""}
              </Text>
            </div>
            {fileLoading ? (
              <div className={styles.spinnerContainer}>
                <Spinner />
                <Text>Loading file content...</Text>
              </div>
            ) : (
              <>
                {!selectedFile.errorCount && selectedFile.warningCount ? (
                  <>
                    <Card className={styles.warningContent}>
                      <Text weight="semibold">
                        File processed with warnings
                      </Text>
                    </Card>
                    <Text className={styles.p_20}>
                      <ErrorComponent file={selectedFile} />
                    </Text>
                  </>
                ) : null}
                {selectedFileTranslatedContent ? (
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
                    {format(selectedFileTranslatedContent, {
                      language: "tsql",
                    })}
                  </SyntaxHighlighter>
                ) : (
                  <>
                    <Card className={styles.errorContent}>
                      <Text weight="semibold">Unable to process the file</Text>
                    </Card>
                    <Text className={styles.p_20}>
                      <ErrorComponent file={selectedFile} />
                    </Text>
                  </>
                )}
              </>
            )}
          </Card>
        </>
      );
    }

    // Show the summary page when summary is selected
    if (selectedFile.id === "summary" && localBatchSummary) {
      // Check if there are no errors and all files are processed successfully
      const noErrors = localBatchSummary.error_count === 0;
      const allFilesProcessed =
        localBatchSummary.completed_files === localBatchSummary.total_files;
      if (noErrors && allFilesProcessed) {
        // Show the success message UI with the green banner and checkmark
        return (
          <>
            {renderHeader()}
            <div
              className={styles.summaryContent}
              style={{
                width: isPanelOpen ? "calc(100% - 340px)" : "96%",
                transition: "width 0.3s ease-in-out",
                overflowX: "hidden",
              }}
            >
              {/* Green success banner */}
              <Card className={styles.summaryCard}>
                <div className={styles.p_8}>
                  <Text weight="semibold">
                    {localBatchSummary.total_files}{" "}
                    {localBatchSummary.total_files === 1 ? "file" : "files"}{" "}
                    processed successfully
                  </Text>
                </div>
              </Card>

              {/* Success checkmark and message */}
              <div className={styles.fileContent}>
                <img
                  src="/images/Checkmark.png"
                  alt="Success checkmark"
                  className={styles.checkMark}
                />
                <Text size={600} weight="semibold" className={styles.mb_16}>
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
      return (
        <>
          {renderHeader()}
          <div
            className={styles.summaryContent}
            style={{
              width: isPanelOpen ? "calc(100% - 340px)" : "96%",
              transition: "width 0.3s ease-in-out",
            }}
          >
            {/* Only show success card if at least one file was successfully completed */}
            {localBatchSummary.completed_files > 0 && (
              <Card className={styles.summaryCard}>
                <div className={styles.p_8}>
                  <Text weight="semibold">
                    {localBatchSummary.completed_files}{" "}
                    {localBatchSummary.completed_files === 1 ? "file" : "files"}{" "}
                    processed successfully
                  </Text>
                </div>
              </Card>
            )}

            {/* Add margin/spacing between cards */}
            <div className={styles.mt_16}>
              <FileError
                batchSummary={localBatchSummary}
                expandedSections={expandedSections}
                setExpandedSections={setExpandedSections}
                styles={styles}
              />
            </div>
          </div>
        </>
      );
    }

    return null;
  };

  const handleLeave = () => {
    setShowLeaveDialog(false);
    navigate("/");
  };
  const downloadZip = async () => {
    if (batchId) {
      dispatch(handleDownloadZip(batchId));
    }
  };

  if (!dataLoaded && loading) {
    return (
      <div className={styles.root}>
        <div className={styles.loadingContainer_flex1}>
          <Spinner size="large" />
          <Text size={500}>Loading batch data...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.root}>
      <div className={styles.content}>
        <PanelLeft panelWidth={400} panelResize={true}>
          <div className={styles.panelHeader}>
            <Text weight="semibold">{batchTitle}</Text>
          </div>

          <div className={styles.fileList}>
            {files.map((file) => (
              <div
                key={file.id}
                className={`${styles.fileCard} ${
                  selectedFileId === file.id ? styles.selectedCard : ""
                }`}
                onClick={() => setSelectedFileId(file.id)}
              >
                {file.id === "summary" ? (
                  // If you have a custom icon, use it here
                  <img
                    src="/images/Docicon.png"
                    alt="Summary icon"
                    className={styles.fileIcon}
                  />
                ) : (
                  <DocumentRegular className={styles.fileIcon} />
                )}
                <Text className={styles.fileName}>{file.name}</Text>
                <div className={styles.statusContainer}>
                  {file.id === "summary" && file.errorCount ? (
                    <>
                      <Text>
                        {file.errorCount}{" "}
                        {file.errorCount === 1 ? "error" : "errors"}
                      </Text>
                    </>
                  ) : file.status?.toLowerCase() === "error" ? (
                    <>
                      <Text>{file.errorCount}</Text>
                      <DismissCircle24Regular className={styles.errorIcon} />
                    </>
                  ) : file.id !== "summary" &&
                    file.status === "completed" &&
                    file.warningCount ? (
                    <>
                      <Text>{file.warningCount}</Text>
                      <Warning24Regular className={styles.warningIcon} />
                    </>
                  ) : file.status?.toLowerCase() === "completed" ? (
                    <CheckmarkCircle24Regular className={styles.successIcon} />
                  ) : // No icon for other statuses
                  null}
                </div>
              </div>
            ))}
          </div>

          <div className={styles.buttonContainer}>
            <Button appearance="secondary" onClick={() => navigate("/")}>
              Return home
            </Button>

            <Button
              appearance="primary"
              onClick={downloadZip}
              className={styles.downloadButton}
              icon={<ArrowDownload24Regular />}
              disabled={!localBatchSummary || localBatchSummary.hasFiles <= 0}
            >
              Download all as .zip
            </Button>
          </div>
        </PanelLeft>
        <Content>
          <div className={styles.mainContent}>{renderContent()}</div>
        </Content>
      </div>
      <ConfirmationDialog
        open={showLeaveDialog}
        setOpen={setShowLeaveDialog}
        title="Return to home page?"
        message="Are you sure you want to navigate away from this batch view?"
        onConfirm={handleLeave}
        onCancel={() => setShowLeaveDialog(false)}
        confirmText="Return to home and lose progress"
        cancelText="Stay here"
      />
    </div>
  );
};

export default BatchStoryPage;
