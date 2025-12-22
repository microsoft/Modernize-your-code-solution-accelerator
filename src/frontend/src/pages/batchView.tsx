import * as React from "react"
import { useParams } from "react-router-dom"
import { useNavigate } from "react-router-dom"
import { useState, useEffect } from "react"
import Content from "../components/Content/Content";
import Header from "../components/Header/Header";
import HeaderTools from "../components/Header/HeaderTools";
import PanelLeft from "../components/Panels/PanelLeft";
import { getApiUrl, headerBuilder } from '../api/config';
import {
  Button,
  Text,
  Card,
  tokens,
  Spinner,
  Tooltip,
} from "@fluentui/react-components"
import {
  DismissCircle24Regular,
  CheckmarkCircle24Regular,
  DocumentRegular,
  ArrowDownload24Regular,
  bundleIcon,
  HistoryFilled,
  HistoryRegular,
  Warning24Regular
} from "@fluentui/react-icons"
import { Light as SyntaxHighlighter } from "react-syntax-highlighter"
import sql from "react-syntax-highlighter/dist/esm/languages/hljs/sql"
import { vs } from "react-syntax-highlighter/dist/esm/styles/hljs"
import PanelRightToggles from "../components/Header/PanelRightToggles";
import PanelRight from "../components/Panels/PanelRight";
import PanelRightToolbar from "../components/Panels/PanelRightToolbar";
import BatchHistoryPanel from "../components/batchHistoryPanel";
import ConfirmationDialog from "../commonComponents/ConfirmationDialog/confirmationDialogue";
import { determineFileStatus, filesLogsBuilder, renderErrorSection, useStyles, renderFileError, filesErrorCounter, completedFiles, hasFiles, fileErrorCounter, BatchSummary } from "../api/utils";
export const History = bundleIcon(HistoryFilled, HistoryRegular);
import { format } from "sql-formatter";


SyntaxHighlighter.registerLanguage("sql", sql)



interface FileItem {
  id: string;
  name: string;
  type: "summary" | "code";
  status: string;
  code?: string;
  translatedCode?: string;
  file_logs?: any[];
  errorCount?: number;
  warningCount?: number;
}

const BatchStoryPage = () => {
  const { batchId } = useParams<{ batchId: string }>();
  const navigate = useNavigate();
  const [showLeaveDialog, setShowLeaveDialog] = useState(false);
  const styles = useStyles();
  const [batchTitle, setBatchTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [fileLoading, setFileLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [uploadId, setUploadId] = useState<string>("");
  const [isPanelOpen, setIsPanelOpen] = React.useState(false);

  // Files state with a summary file
  const [files, setFiles] = useState<FileItem[]>([]);

  const [selectedFileId, setSelectedFileId] = useState<string>("");
  const [expandedSections, setExpandedSections] = useState(["errors"]);
  const [batchSummary, setBatchSummary] = useState<BatchSummary | null>(null);
  const [selectedFileTranslatedContent, setSelectedFileTranslatedContent] = useState<string>("");


  // Fetch batch data from API
  useEffect(() => {
    if (!batchId || !(batchId.length === 36)) {
      setError("Invalid batch ID provided");
      setLoading(false);
      return;
    }

    const fetchBatchData = async () => {
      try {
        setLoading(true);
        setDataLoaded(false);
        const apiUrl = getApiUrl();

        const response = await fetch(`${apiUrl}/batch-summary/${batchId}`, { headers: headerBuilder({}) });

        if (!response.ok) {
          throw new Error(`Failed to fetch batch data: ${response.statusText}`);
        }

        const responseData = await response.json();

        // Handle the new response format
        if (!responseData || !responseData.files) {
          throw new Error("Invalid data format received from server");
        }

        // Adapt the new response format to match our expected BatchSummary format
        const data: BatchSummary = {
          batch_id: responseData.batch.batch_id,
          upload_id: responseData.batch.id, // Use id as upload_id
          date_created: responseData.batch.created_at,
          total_files: responseData.batch.file_count,
          status: responseData.batch.status,
          completed_files: completedFiles(responseData.files),
          error_count: filesErrorCounter(responseData.files),
          warning_count: responseData.files.reduce((count, file) => count + (file.syntax_count || 0), 0),
          hasFiles: hasFiles(responseData),
          files: responseData.files.map(file => ({
            file_id: file.file_id,
            name: file.original_name, // Use original_name here
            status: file.status,
            file_result: file.file_result,
            error_count: fileErrorCounter(file),
            warning_count: file.syntax_count || 0,
            file_logs: filesLogsBuilder(file),
          }))
        };

        setBatchSummary(data);
        setUploadId(data.upload_id);

        // Set batch title with date and file count
        const formattedDate = new Date(data.date_created).toLocaleDateString();
        setBatchTitle(
          `${formattedDate} (${data.total_files} file${data.total_files === 1 ? '' : 's'})`
        );


        // Create file list from API response
        const fileItems: FileItem[] = data.files.map(file => ({
          id: file.file_id,
          name: file.name, // This is now the original_name from API
          type: "code",
          status: determineFileStatus(file),
          code: "", // Don't store content here, will fetch on demand
          translatedCode: "", // Don't store content here, will fetch on demand
          errorCount: file.error_count,
          file_logs: file.file_logs,
          warningCount: file.warning_count
        }));

        // Add summary file
        const updatedFiles: FileItem[] = [
          {
            id: "summary",
            name: "Summary",
            type: "summary",
            status: "completed",
            errorCount: data.error_count,
            warningCount: data.warning_count,
            file_logs: []
          },
          ...fileItems
        ];

        setFiles(updatedFiles as FileItem[]);
        setSelectedFileId("summary"); // Default to summary view
        setDataLoaded(true);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching batch data:", err);
        setError(err instanceof Error ? err.message : "An unknown error occurred");
        setLoading(false);
      }
    };

    fetchBatchData();
  }, [batchId]);

  // Fetch file content when a file is selected
  useEffect(() => {
    if (selectedFileId === "summary" || !selectedFileId || fileLoading) {
      return;
    }

    const fetchFileContent = async () => {
      try {
        setFileLoading(true);
        const apiUrl = getApiUrl();
        const response = await fetch(`${apiUrl}/file/${selectedFileId}`, { headers: headerBuilder({}) });
        if (!response.ok) {
          throw new Error(`Failed to fetch file content: ${response.statusText}`);
        }

        const data = await response.json();

        if (data) {
          setSelectedFileContent(data.content || "");
          setSelectedFileTranslatedContent(data.translated_content || "");
        }

        setFileLoading(false);
      } catch (err) {
        console.error("Error fetching file content:", err);
        setFileLoading(false);
      }
    };

    fetchFileContent();
  }, [selectedFileId]);

  const renderContent = () => {
    // Define header content based on selected file
    const renderHeader = () => {
      const selectedFile = files.find((f) => f.id === selectedFileId);

      if (!selectedFile) return null;

      const title = selectedFile.id === "summary" ? "Summary" : "T-SQL";

      return (
        <div className={styles.summaryHeader}
          style={{
            width: isPanelOpen ? "calc(102% - 340px)" : "96%",
            transition: "width 0.3s ease-in-out",
          }}
        >
          <Text size={500} weight="semibold">{title}</Text>
          <Text size={200} style={{ color: tokens.colorNeutralForeground3, paddingRight: "20px" }}>
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
            <Text size={500} style={{ color: tokens.colorStatusDangerForeground1 }}>
              Error: {error}
            </Text>
            <Button appearance="primary" onClick={() => navigate("/")}>
              Return to Home
            </Button>
          </div>
        </>
      );
    }

    if (!dataLoaded || !batchSummary) {
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
          <Card className={styles.codeCard}
            style={{
              width: isPanelOpen ? "calc(100% - 320px)" : "98%",
              transition: "width 0.3s ease-in-out",
            }}>
            <div className={styles.codeHeader}>
              <Text weight="semibold">
                {selectedFile.name} {selectedFileTranslatedContent ? "(Translated)" : ""}
              </Text>
            </div>
            {fileLoading ? (
              <div style={{ padding: "20px", textAlign: "center" }}>
                <Spinner />
                <Text>Loading file content...</Text>
              </div>
            ) : (
              <>
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
                    {format(selectedFileTranslatedContent, { language: "tsql" })}
                  </SyntaxHighlighter>
                ) : (
                  <>
                    <Card className={styles.errorContent}>
                      <Text weight="semibold">Unable to process the file</Text>
                    </Card>
                    <Text style={{ padding: "20px" }}>
                      {renderFileError(selectedFile)}
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
    if (selectedFile.id === "summary") {
      // Check if there are no errors and all files are processed successfully
      const noErrors = (batchSummary.error_count === 0);
      const allFilesProcessed = (batchSummary.completed_files === batchSummary.total_files);
      if (noErrors && allFilesProcessed) {
        // Show the success message UI with the green banner and checkmark
        return (
          <>
            {renderHeader()}
            <div className={styles.summaryContent}
              style={{
                width: isPanelOpen ? "calc(100% - 340px)" : "96%",
                transition: "width 0.3s ease-in-out",
                overflowX: "hidden",
              }}>
              {/* Green success banner */}
              <Card className={styles.summaryCard}>
                <div style={{ padding: "8px" }}>
                  <Text weight="semibold">
                    {batchSummary.total_files} {batchSummary.total_files === 1 ? 'file' : 'files'} processed successfully
                  </Text>
                </div>
              </Card>

              {/* Success checkmark and message */}
              <div className="file-content"
                style={{
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginTop: '60px',
                  height: '70vh',
                  width: "100%", // Ensures full visibility
                  maxWidth: "800px", // Prevents content from stretching
                  margin: "auto", // Keeps it centered
                  transition: "width 0.3s ease-in-out",
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
      return (
        <>
          {renderHeader()}
          <div className={styles.summaryContent}
            style={{
              width: isPanelOpen ? "calc(100% - 340px)" : "96%",
              transition: "width 0.3s ease-in-out",
            }}>
            {/* Only show success card if at least one file was successfully completed */}
            {batchSummary.completed_files > 0 && (
              <Card className={styles.summaryCard}>
                <div style={{ padding: "8px" }}>
                  <Text weight="semibold">
                    {batchSummary.completed_files} {batchSummary.completed_files === 1 ? 'file' : 'files'} processed successfully
                  </Text>
                </div>
              </Card>
            )}

            {/* Add margin/spacing between cards */}
            <div style={{ marginTop: "16px" }}>
              {renderErrorSection(batchSummary, expandedSections, setExpandedSections, styles)}
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

  const handleHeaderClick = () => {
    setShowLeaveDialog(true);
    navigate("/");
  };

  const handleTogglePanel = () => {
    console.log("Toggling panel from BatchView"); // Debugging Log
    setIsPanelOpen((prev) => !prev);
  };

  const handleDownloadZip = async () => {
    if (batchId) {
      try {
        const apiUrl = getApiUrl();
        const response = await fetch(`${apiUrl}/download/${uploadId}?batch_id=${batchId}`, { headers: headerBuilder({}) });

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



  if (!dataLoaded && loading) {
    return (
      <div className={styles.root}>
        <div onClick={handleHeaderClick} style={{ cursor: "pointer" }}>
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
        <div className={styles.loadingContainer} style={{ flex: 1 }}>
          <Spinner size="large" />
          <Text size={500}>Loading batch data...</Text>
        </div>
      </div>
    );
  }

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
          <div className={styles.panelHeader}>
            <Text weight="semibold">{batchTitle}</Text>
          </div>

          <div className={styles.fileList}>
            {files.map((file) => (
              <div
                key={file.id}
                className={`${styles.fileCard} ${selectedFileId === file.id ? styles.selectedCard : ""}`}
                onClick={() => setSelectedFileId(file.id)}
              >
                {file.id === "summary" ? (
                  // If you have a custom icon, use it here
                  <img src="/images/Docicon.png" alt="Summary icon" className={styles.fileIcon} />
                ) : (
                  <DocumentRegular className={styles.fileIcon} />
                )}
                <Text className={styles.fileName}>{file.name}</Text>
                <div className={styles.statusContainer}>
                  {file.id === "summary" && file.errorCount ? (
                    <>
                      <Text>{file.errorCount} {file.errorCount === 1 ? 'error' : 'errors'}</Text>
                    </>
                  ) : file.status?.toLowerCase() === "error" ? (
                    <>
                      <Text>{file.errorCount}</Text>
                      <DismissCircle24Regular style={{ color: tokens.colorStatusDangerForeground1, width: "16px", height: "16px" }} />
                    </>
                  ) : file.id !== "summary" && file.status === "completed" && file.warningCount ? (
                    <>
                      <Text>{file.warningCount}</Text>
                      <Warning24Regular style={{ color: "#B89500", width: "16px", height: "16px" }} />
                    </>
                  ) : file.status?.toLowerCase() === "completed" ? (
                    <CheckmarkCircle24Regular style={{ color: "0B6A0B", width: "16px", height: "16px" }} />
                  ) : (
                    // No icon for other statuses
                    null
                  )}
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
              onClick={handleDownloadZip}
              className={styles.downloadButton}
              icon={<ArrowDownload24Regular />}
              disabled={!batchSummary || batchSummary.hasFiles <= 0}
            >
              Download all as .zip
            </Button>

          </div>
        </PanelLeft>
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
        cancelText="Continue"
      />
    </div>
  );
};

export default BatchStoryPage;