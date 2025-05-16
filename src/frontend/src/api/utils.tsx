import {
  Accordion, AccordionHeader, AccordionItem, AccordionPanel, List, ListItem, makeStyles,
  tokens, Text,
  Card
} from "@fluentui/react-components";
import React from "react";
import { ChevronDown, ChevronRight } from "lucide-react"; // or whatever icon library you're using
import { TbSql } from "react-icons/tb";
import {
  InfoRegular,
  DismissCircle24Regular,
  Warning24Regular,

} from "@fluentui/react-icons"

export const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
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
    paddingBottom: "70px",
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
    backgroundColor: "#EBEBEB",
  },
  mainContent: {
    flex: 1,
    backgroundColor: tokens.colorNeutralBackground1,
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
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  summaryContent: {
    padding: "24px",
    width: "100%", // Add this
    maxWidth: "100%", // Add this
    overflowX: "hidden", // Add this
  },
  summaryCard: {
    height: "40px",
    width: "100%",
    maxWidth: "100%", // Add this
    padding: "2px",
    backgroundColor: "#F2FBF2",
    marginBottom: "16px",
    marginLeft: "0", // Change from marginleft
    marginRight: "0",
    boxShadow: "none",
    overflowX: "hidden", // Add this
    boxSizing: "border-box", // Add this
  },
  errorSection: {
    backgroundColor: "#F8DADB",
    marginBottom: "8px",
    height: "40px",
    boxShadow: "none"
  },
  warningSection: {
    backgroundColor: tokens.colorStatusWarningBackground1,
    marginBottom: "16px",
    boxShadow: "none"
  },
  sectionHeader: {
    display: "flex",
    height: "40px",
    alignItems: "center",
    justifyContent: "space-between",
    cursor: "pointer",
    boxSizing: "border-box",
    padding: "0",
    textAlign: "left"
  },
  errorItem: {
    marginTop: "16px",
    paddingLeft: "20px",
    paddingBottom: "16px",
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
  loadingContainer: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    gap: "16px",
  },
  buttonContainer: {
    display: "flex",
    justifyContent: "flex-end",
    gap: "8px",
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: tokens.colorNeutralBackground2,
    borderTop: "1px solid #e5e7eb", /* Optional: adds a separator line */
    padding: "16px 20px",
    zIndex: "10",
  },
  downloadButton: {
    marginLeft: "auto",
    display: "flex",
    alignItems: "center",
    gap: "4px",
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

  noContentAvailable: {
    fontSize: "20px",
    padding: "16px",
    color: "inherit",
    textAlign: "center",
  },
  errorContentScrollable: {
    maxHeight: '450px',
    overflowY: 'auto',
    paddingRight: '8px',
    borderBottom: '1px solid #eaeaea'
  },
  errorContent: {
    backgroundColor: "#F8DADB",
    marginBottom: "16px",
    boxShadow: "none"
  },
  warningContent: {
    backgroundColor: tokens.colorStatusWarningBackground1,
    marginBottom: "16px",
    paddingBottom: "22px",
    paddingTop: "8px",
    boxShadow: "none"
  }
});
export interface BatchSummary {
  batch_id: string;
  upload_id: string; // Added upload_id to the interface
  date_created: string;
  total_files: number;
  status: string;
  completed_files: number;
  error_count: number;
  warning_count: number;
  hasFiles: number;
  files: {
    file_id: string;
    name: string;
    status: string;
    error_count: number;
    warning_count: number;
    file_logs: any[];
    content?: string;
    translated_content?: string;
  }[];
}
export const filesErrorCounter = (files) => {
  return files.reduce((count, file) => {
    const logs = filesLogsBuilder(file);
    const errorCount = logs.filter(log => log.logType === "error").length;
    return count + errorCount;
  }, 0);
};

export const filesFinalErrorCounter = (files) => {
  return files.reduce((count, file) => {
    const logs = filesLogsBuilder(file);
    const errorCount = logs.filter(log => log.logType === "error").length;
    if (file.status !== "completed") { // unfinished or failed file without error entry
      return count + (errorCount > 0 ? errorCount : 1);
    }
    return count + errorCount;
  }, 0);
};
export const completedFiles = (files) => {
  return files.filter(f => f.status?.toLowerCase() === "completed" && f.file_result !== "error").length;
};

export const hasFiles = (responseData) => {
  return completedFiles(responseData.files)
};

export const fileErrorCounter = (file) => {
  const logs = filesLogsBuilder(file);
  return logs.filter(log => log.logType === "error").length;
};

export const fileWarningCounter = (file) => {
  const logs = filesLogsBuilder(file);
  const value = logs.filter(log => log.logType === "warning").length
  return value;
};

export const determineFileStatus = (file) => {
  // If file.status is not "completed", it's an error.
  if (file.status?.toLowerCase() !== "completed") return "error";
  // If file.status is "completed" but file_result is "error", it's an error.
  if (file.file_result === "error") return "error";
  // If file.status is "completed" and file_result is "success", it's completed.
  if (file.file_result === "success") return "completed";
  // Fallback to error if none of the above conditions are met.
  return "error";
};
// Function to format agent type strings
export const formatAgent = (str = "Agent") => {
  if (!str) return "agent";

  const cleaned = str
    .replace(/[^a-zA-Z\s]/g, " ") // Remove non-alphabetic characters
    .replace(/\s+/g, " ")         // Collapse multiple spaces
    .trim()
    .replace(/\bAgents\b/i, "Agent"); // Singularize "Agents" if it's the only word

  const words = cleaned
    .split(" ")
    .filter(Boolean)
    .map(w => w.toLowerCase());

  const hasAgent = words.includes("agent");

  // Capitalize all except "agent" (unless it's the only word)
  const result = words.map((word, index) => {
    if (word === "agent") {
      return words.length === 1 ? "Agent" : "agent"; // Capitalize if it's the only word
    }
    return word.charAt(0).toUpperCase() + word.slice(1);
  });

  if (!hasAgent) {
    result.push("agent");
  }

  return result.join(" ");
};

// Function to handle rate limit errors and ensure descriptions end with a dot
export const formatDescription = (description) => {
  if (!description) return "No description provided.";

  let sanitizedDescription = description.includes("RateLimitError")
    ? "Rate limit error."
    : description;

  // Ensure it ends with a dot
  if (!sanitizedDescription.endsWith(".")) {
    sanitizedDescription += ".";
  }

  return sanitizedDescription.replace(/_/g, ' ');
};

// Function to build log entries from file logs
export const filesLogsBuilder = (file) => {
  if (!file || !file.logs || file.logs.length === 0) {
    return [];
  }

  return file.logs
    .filter(log => log.agent_type !== "human") // Exclude human logs
    .map((log, index) => {
      let parsedDescription;
      const description = log.description;

      try {
        const json_desc = typeof description === "object" ? description : JSON.parse(description);
        try {
          if (json_desc.differences && Array.isArray(json_desc.differences)) {
            parsedDescription = json_desc.differences.toString();
          }else {
            if(Array.isArray(json_desc.content)){
              parsedDescription = json_desc.content.toString(); // Fallback to json_desc content
            }else{  
              const json_desc2 =  typeof json_desc.content === "object" ? json_desc.content : JSON.parse(json_desc.content);
              parsedDescription = json_desc2.source_summary ?? json_desc2.input_summary?? json_desc2.thought ?? json_desc2.toString(); // Fallback to json_desc content
            }

          }
        } catch {
          parsedDescription = json_desc.content; // Fallback to json_desc content
        }
      } catch {
        parsedDescription = description; // Fallback to raw description
      }

      return {
        id: index,
        agentType: formatAgent(log.agent_type), // Apply improved formatSentence function
        description: formatDescription(parsedDescription), // Apply sanitizeRateLimitError function
        logType: log.log_type,
        timestamp: log.timestamp,
      };
    });
};

export const renderErrorSection = (batchSummary, expandedSections, setExpandedSections, styles) => {
  const isExpanded = expandedSections.includes("errors");

  return (
    <>
      <Card className={styles.errorSection}>
        <div
          className={styles.sectionHeader}
          onClick={() => setExpandedSections((prev) =>
            prev.includes("errors") ? prev.filter((id) => id !== "errors") : [...prev, "errors"]
          )}
        >
          <Text weight="semibold">Errors ({batchSummary.error_count || 0})</Text>
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </div>
      </Card>

      {isExpanded && <div className={styles.errorContentScrollable}>
        {renderErrorContent(batchSummary)}
      </div>}
    </>
  );
};

// To ensure it's expanded by default, you need to initialize your expandedSections state with "errors"
// In your component:
// const [expandedSections, setExpandedSections] = useState(["errors"]);

export const renderErrorContent = (batchSummary) => {
  // Group errors by file
  const errorFiles = batchSummary.files.filter(file => file.error_count && file.error_count);
  if (errorFiles.length === 0) {
    return (
      <div className={useStyles().errorItem}>
        <Text>No errors found.</Text>
      </div>
    );
  }

  return (
    <div>
      <Accordion collapsible multiple defaultValue={errorFiles.map(file => file.file_id)}>
        {errorFiles.map((file, idx) => (
          <AccordionItem key={idx} value={file.file_id}>
            <AccordionHeader>
              <TbSql style={{ fontSize: 16, color: "#519ABA" }} />
              {file.name} ({file.error_count})
            </AccordionHeader>
            <AccordionPanel>
              {renderFileError(file)}
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
};
export const renderFileError = (file) => {
  return (
    <>
      {file.file_logs.length > 0 ? (
        <List style={{ paddingLeft: "16px" }}>
          {file.file_logs.map((log, logIdx) => (
            <ListItem key={logIdx} style={{ marginLeft: "8px" }}>
              <Text style={{ display: "flex", alignItems: "flex-start" }}>
                <span style={{
                  flexShrink: 0,
                  display: "inline-block",
                  width: "16px",
                  height: "16px",
                  marginRight: "8px",
                  marginTop: "3px" // Adjust this value to vertically align with first line of text
                }}>
                  {log.logType === "error" ? (
                    <DismissCircle24Regular style={{
                      color: tokens.colorStatusDangerForeground1,
                      width: "16px",
                      height: "16px"
                    }} />
                  ) : log.logType === "warning" ? (
                      <Warning24Regular style={{ color: "#B89500", width: "16px", height: "16px" }} />
                  ) : (
                        <InfoRegular style={{
                          color: "#007ACC",
                          width: "16px",
                          height: "16px"
                        }} />
                      )}
                </span>
                <span>{log.agentType}: {log.description}</span>
              </Text>
            </ListItem>
          ))}
        </List>
      ) : (
        <p style={{ paddingLeft: "24px" }}>No detailed logs available.</p>
      )}
    </>
  );
};