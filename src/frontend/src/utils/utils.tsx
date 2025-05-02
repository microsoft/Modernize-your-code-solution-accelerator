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
    .replace(/[^a-zA-Z\s]/g, " ") 
    .replace(/\s+/g, " ")         
    .trim()
    .replace(/\bAgents\b/i, "Agent"); 

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

