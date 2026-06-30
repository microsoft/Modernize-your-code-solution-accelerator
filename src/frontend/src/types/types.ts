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