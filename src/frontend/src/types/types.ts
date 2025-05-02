export interface StepProps {
    icon: string;
    title: string;
    status: string;
    isLast?: boolean;
  }
  
  export interface ProgressStepProps {
    steps: StepProps[];
    timeRemaining: string;
  }

  export interface FileItemProps {
    name: string;
    count?: number;
    type: 'error' | 'warning' | 'success';
    icon: string;
    details?: string;
  }
  
  export interface FileGroupProps {
    date: string;
    fileCount: number;
    files: FileItemProps[];
  }
  
  export interface ErrorWarningProps {
    title: string;
    count: number;
    type: 'error' | 'warning';
    items: Array<{
      fileName: string;
      count: number;
      messages: Array<{
        code: string;
        message: string;
        location: string;
      }>;
    }>;
  }
  type FileType = "summary" | "code"
  type FileResult = "info" | "warning" | "error" | null
  
  export interface WebSocketMessage {
    batch_id: string;
    file_id: string;
    agent_type: string;
    agent_message: string;
    process_status: string;
    file_result: FileResult;
  }

 export interface FileItem {
    id: string
    name: string
    type: FileType;
    status: string
    code?: string
    translatedCode?: string
    errorCount?: number
    warningCount?: number
    file_logs?: any[];
    file_result?: string
    file_track_log?: WebSocketMessage[]
    file_track_percentage?: number
    fileId?: string
    batchId?: string
    order?: number
  }

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