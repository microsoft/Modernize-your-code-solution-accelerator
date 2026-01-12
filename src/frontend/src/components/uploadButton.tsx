import React, { useCallback, useState, useEffect } from 'react';
// MessageBar styles constants
const messageBarErrorStyles = {
  root: { display: "flex", flexDirection: "column", alignItems: "left", background: "#fff4f4" },
  icon: { display: "none" },
};



const messageBarSuccessStyles = {
  root: { display: "flex", alignItems: "left" },
  icon: { display: "none" },
};

const messageBarWarningStyles = {
  root: { display: "flex", alignItems: "center" },
};
// Helper function to check for .sql extension
const isSqlFile = (file: File): boolean => file.name.toLowerCase().endsWith('.sql');

// ...existing code...
import { useDropzone, FileRejection, DropzoneOptions } from 'react-dropzone';
import { CircleCheck, X } from 'lucide-react';
import {
  Button,
  Toast,
  ToastTitle,
  useToastController,
  Tooltip,
} from "@fluentui/react-components";
import { MessageBar, MessageBarType } from "@fluentui/react";
import { deleteBatch, deleteFileFromBatch, uploadFile, startProcessing } from '../slices/batchSlice';
import { useDispatch } from 'react-redux';
import ConfirmationDialog from '../commonComponents/ConfirmationDialog/confirmationDialogue';
import { AppDispatch } from '../store/store'
import { v4 as uuidv4 } from 'uuid';
import "./uploadStyles.css";
import { useNavigate } from "react-router-dom";

interface FileUploadZoneProps {
  onFileUpload?: (acceptedFiles: File[]) => void;
  onFileReject?: (fileRejections: FileRejection[]) => void;
  onUploadStateChange?: (state: 'IDLE' | 'UPLOADING' | 'COMPLETED') => void;
  maxSize?: number;
  acceptedFileTypes?: Record<string, string[]>;
  selectedCurrentLanguage: string[];
  selectedTargetLanguage: string[];
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  id: string;
  batchId: string;
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFileUpload,
  onFileReject,
  onUploadStateChange,
  maxSize = 200 * 1024 * 1024,
  acceptedFileTypes = { 'application/sql': ['.sql'] }, // Accept only .sql files by extension
  selectedCurrentLanguage,
  selectedTargetLanguage
}) => {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [uploadIntervals, setUploadIntervals] = useState<{ [key: string]: ReturnType<typeof setTimeout> }>({});
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showLogoCancelDialog, setShowLogoCancelDialog] = useState(false);
  const [batchId, setBatchId] = useState<string>(uuidv4());
  const [allUploadsComplete, setAllUploadsComplete] = useState(false);
  const [fileLimitExceeded, setFileLimitExceeded] = useState(false);
  const [fileRejectionErrors, setFileRejectionErrors] = useState<string[]>([]);
  const [showFileLimitDialog, setShowFileLimitDialog] = useState(false);
  const navigate = useNavigate();

  const MAX_FILES = 20;
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    if (uploadingFiles.length === 0) {
      setAllUploadsComplete(false);
    }
  });

  useEffect(() => {
    let newState: 'IDLE' | 'UPLOADING' | 'COMPLETED' = 'IDLE';

    if (uploadingFiles.length > 0) {
      const activeFiles = uploadingFiles.filter(f => f.status !== 'error');
      if (activeFiles.length > 0 && activeFiles.every(f => f.status === 'completed')) {
        newState = 'COMPLETED';
        setAllUploadsComplete(true);
      } else {
        newState = 'UPLOADING';
      }
    }

    onUploadStateChange?.(newState);
  }, [uploadingFiles, onUploadStateChange]);

  const startNewBatch = () => {
    setBatchId(uuidv4()); // Generate a new batchId for each new batch of uploads
  };

  const simulateFileUpload = (file: File) => {
    if (batchId == "") {
      startNewBatch(); // Ensure batchId is set before starting any upload
    }

    const frontendFileId = uuidv4();
    const newFile: UploadingFile = {
      file,
      progress: 0,
      status: 'uploading',
      id: frontendFileId,
      batchId: batchId
    };

    setUploadingFiles(prev => [...prev, newFile]);

    const duration = 6000 + Math.random() * 2000;;
    const steps = 50;
    const increment = 100 / steps;
    const stepDuration = duration / steps;

    let currentProgress = 0;
    let hasStartedUpload = false; // To ensure dispatch is called once
    const intervalId = setInterval(() => {
      currentProgress += increment;

      setUploadingFiles(prev =>
        prev.map(f =>
          f.id === frontendFileId
            ? {
              ...f,
              progress: Math.min(currentProgress, 99),
              status: 'uploading'
            }
            : f
        )
      );

      if (currentProgress >= 1 && !hasStartedUpload) {
        hasStartedUpload = true;

        dispatch(uploadFile({ batchId, file }))
          .unwrap()
          .then((response) => {
            if (response?.file.file_id) {
              // Update the file list with the correct fileId from backend
              setUploadingFiles((prev) =>
                prev.map((f) =>
                  f.id === frontendFileId ? { ...f, id: response.file.file_id, progress: 100, status: 'completed' } : f
                )
              );
            }
            clearInterval(intervalId);
          })
          .catch((error) => {
            console.error("Upload failed:", error);

            // Mark the file upload as failed
            setUploadingFiles((prev) =>
              prev.map((f) =>
                f.id === frontendFileId ? { ...f, status: 'error' } : f
              )
            );
            clearInterval(intervalId);
          });

        setUploadIntervals(prev => {
          const next = { ...prev };
          delete next[frontendFileId];
          return next;
        });
      }
    }, stepDuration);
  };

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      // Use helper for .sql extension check
      const validFiles = acceptedFiles.filter(isSqlFile);
      const invalidFiles = acceptedFiles.filter(file => !isSqlFile(file));

      // Check current files count and determine how many more can be added
      const remainingSlots = MAX_FILES - uploadingFiles.length;

      if (validFiles.length > 0) {
        setFileRejectionErrors([]); // Clear error notification when valid file is selected
      }

      if (remainingSlots <= 0) {
        setShowFileLimitDialog(true);
        return;
      }

      // If more files are dropped than slots available
      if (validFiles.length > remainingSlots) {
        const filesToUpload = validFiles.slice(0, remainingSlots);
        filesToUpload.forEach(file => simulateFileUpload(file));
        if (onFileUpload) onFileUpload(filesToUpload);
        setShowFileLimitDialog(true);
      } else {
        validFiles.forEach(file => simulateFileUpload(file));
        if (onFileUpload) onFileUpload(validFiles);
      }

      // Efficient error array construction
      const errors: string[] = [
        ...invalidFiles.map(file =>
          `File '${file.name}' is not a valid SQL file. Only .sql files are allowed.`
        ),
        ...fileRejections.flatMap(rejection =>
          rejection.errors.map(err => {
            if (err.code === "file-too-large") {
              return `File '${rejection.file.name}' exceeds the 200MB size limit. Please upload a file smaller than 200MB.`;
            } else if (err.code === "file-invalid-type") {
              return `File '${rejection.file.name}' is not a valid SQL file. Only .sql files are allowed.`;
            } else {
              return `File '${rejection.file.name}': ${err.message}`;
            }
          })
        )
      ];

      if (fileRejections.length > 0 && onFileReject) {
        onFileReject(fileRejections);
      }
      if (errors.length > 0) {
        setFileRejectionErrors(errors);
      }
    },
    [onFileUpload, onFileReject, uploadingFiles.length]
  );

  const dropzoneOptions: DropzoneOptions = {
    onDrop,
    noClick: true,
    maxSize,
    accept: acceptedFileTypes, // Only .sql files regardless of mime type
    //maxFiles: MAX_FILES,
  };

  const { getRootProps, getInputProps, open } = useDropzone(dropzoneOptions);

  const removeFile = (fileId: string) => {
    setUploadingFiles((prev) => {
      const updatedFiles = prev.filter((f) => f.id !== fileId);
      console.log("Updated uploadingFiles:", updatedFiles);
      return updatedFiles;
    });

    // Clear any running upload interval
    if (uploadIntervals[fileId]) {
      clearInterval(uploadIntervals[fileId]);
      setUploadIntervals((prev) => {
        const { [fileId]: _, ...rest } = prev;
        return rest;
      });
    }

    // Backend deletion only if file was uploaded successfully
    const fileToRemove = uploadingFiles.find((f) => f.id === fileId);
    if (fileToRemove && fileToRemove.status !== "error") {
      dispatch(deleteFileFromBatch(fileToRemove.id))
        .unwrap()
        .catch((error) => console.error("Failed to delete file:", error));
    }
  };

  const cancelAllUploads = useCallback(() => {
  // Clear all upload intervals
  dispatch(deleteBatch({ batchId, headers: null }));

  Object.values(uploadIntervals).forEach(interval => clearInterval(interval));
  setUploadIntervals({});
  setUploadingFiles([]);
  setUploadState('IDLE');
  onUploadStateChange?.('IDLE');
  setShowCancelDialog(false);
  setShowLogoCancelDialog(false);
  setFileRejectionErrors([]); // Clear error notification when cancel is clicked
  //setBatchId();
  startNewBatch();
  }, [uploadIntervals, onUploadStateChange]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Store the original function if it exists
      const originalCancelLogoUploads = (window as any).cancelLogoUploads;

      // Override with our new function that shows the dialog
      (window as any).cancelLogoUploads = () => {
        // Show dialog regardless of upload state
        if (uploadingFiles.length > 0) {  // Only show if there are files
          setShowLogoCancelDialog(true);
        }
      };
      // Cleanup: Restore original function on unmount
      return () => {
        (window as any).cancelLogoUploads = originalCancelLogoUploads;
      };
    }
  }, [uploadingFiles.length]); // Runs when uploadingFiles.length changes

  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Store the original function if it exists
      const originalCancelUploads = (window as any).cancelUploads;

      // Override with our new function that shows the dialog
      (window as any).cancelUploads = () => {
        // Show dialog regardless of upload state
        if (uploadingFiles.length > 0) {  // Only show if there are files
          setShowCancelDialog(true);
        }
      };
      // Cleanup
      return () => {
        (window as any).cancelUploads = originalCancelUploads;
      };
    }
  }, [uploadingFiles.length]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const originalStartTranslating = (window as any).startTranslating;

      (window as any).startTranslating = async () => {
        const payload = {
          batchId: batchId,
          translateFrom: selectedCurrentLanguage[0],
          translateTo: selectedTargetLanguage[0],
        };

        if (uploadingFiles.length > 0) {
          // First navigate to modernization page to show progress
          navigate(`/batch-process/${batchId}`);

          // Then dispatch the action
          try {
            dispatch(startProcessing(payload));
            return batchId;
          } catch (error) {
            console.error('Processing failed:', error);
            return batchId;
          }
        }
        return null;
      };

      // Cleanup
      return () => {
        (window as any).startTranslating = originalStartTranslating;
      };
    }
  }, [uploadingFiles.length, selectedTargetLanguage, selectedCurrentLanguage, batchId, dispatch, navigate]);

  const toasterId = "uploader-toast";
  const { dispatchToast } = useToastController(toasterId);

  useEffect(() => {
    if (allUploadsComplete) {
      // Show success toast when uploads are complete
      dispatchToast(
        <Toast>
          <ToastTitle>
            All files uploaded successfully!
          </ToastTitle>
        </Toast>,
        { intent: "success" }
      );
    }
  }, [allUploadsComplete, dispatchToast]);

  // Auto-hide file limit exceeded alert after 5 seconds
  useEffect(() => {
    if (fileLimitExceeded) {
      const timer = setTimeout(() => {
        setFileLimitExceeded(false);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [fileLimitExceeded]);

  return (
    <div style={{ width: '100%', minWidth: '720px', maxWidth: '800px', margin: '0 auto', marginTop: '0', padding: '16px', paddingBottom: '60px' }}>
      <ConfirmationDialog
        open={showCancelDialog}
        setOpen={setShowCancelDialog}
        title="Cancel upload?"
        message="If you cancel the upload, all the files and any progress will be deleted."
        onConfirm={cancelAllUploads}
        onCancel={() => setShowCancelDialog(false)}
        confirmText="Cancel upload"
        cancelText="Continue upload"
      />

      <ConfirmationDialog
        open={showLogoCancelDialog}
        setOpen={setShowLogoCancelDialog}
        title="Leave without completing?"
        message="If you leave this page, you'll land on the homepage and lose all progress"
        onConfirm={cancelAllUploads}
        onCancel={() => setShowLogoCancelDialog(false)}
        confirmText="Leave and lose progress"
        cancelText="Continue"
      />
      <ConfirmationDialog
        open={showFileLimitDialog}
        setOpen={setShowFileLimitDialog}
        title="File Limit Exceeded"
        message={`Maximum of ${MAX_FILES} files allowed. Only the first ${MAX_FILES} files were uploaded.`}
        onConfirm={() => setShowFileLimitDialog(false)}
        onCancel={() => setShowFileLimitDialog(false)}
        confirmText="OK"
        cancelText=""
      />

      {uploadingFiles.length === 0 && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '90px',
          textAlign: 'center'
        }}>
          <h1 style={{
            fontSize: '24px',
            fontWeight: 'bold',
            margin: 0
          }}>
            Modernize your code
          </h1>
          <p style={{
            fontSize: '16px',
            fontWeight: '600',
            margin: 0
          }}>
            Modernize your code by updating the language with AI
          </p>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '16px', margin: 0 }}>
          {uploadingFiles.length > 0
            ? `Uploading (${uploadingFiles.filter(f => f.status === 'completed').length}/${uploadingFiles.length})`
            : 'Upload files in batch'
          }
        </h2>
      </div>

      <div
        {...getRootProps()}
        style={{
          width: '100%',
          border: "2px dashed #ccc",
          borderRadius: "4px",
          padding: uploadingFiles.length > 0 ? "16px" : "40px",
          backgroundColor: '#FAFAFA',
          display: 'flex',
          flexDirection: uploadingFiles.length > 0 ? 'row' : 'column',
          alignItems: 'center',
          justifyContent: uploadingFiles.length > 0 ? 'space-between' : 'center',
          height: uploadingFiles.length > 0 ? '80px' : '251px',
          marginBottom: '16px',
        }}
      >
        <input {...getInputProps()} />

        {uploadingFiles.length > 0 ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <img
                src="/images/Arrow-Upload.png"
                alt="Upload Icon"
                style={{ width: 32, height: 32 }}
              />
              <div>
                <p style={{
                  margin: '0',
                  fontSize: '16px',
                  color: '#333'
                }}>
                  Drag and drop files here
                </p>
                <p style={{
                  margin: '4px 0 0 0',
                  fontSize: '12px',
                  color: '#666'
                }}>
                  Limit {Math.floor(maxSize / (1024 * 1024))}MB per file • SQL Only • {uploadingFiles.length}/{MAX_FILES} files
                </p>
              </div>
            </div>
            <Button
              appearance="secondary"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                open();
              }}
              style={{
                minWidth: '120px',
                backgroundColor: 'white',
                border: '1px solid grey',
                borderRadius: '4px',
                height: '32px'
              }}
            >
              Browse files
            </Button>
          </>
        ) : (
          <>
            <img
              src="/images/Arrow-Upload.png"
              alt="Upload Icon"
              style={{ width: 64, height: 64 }}
            />
            <p style={{
              margin: '16px 0 0 0',
              fontSize: '18px',
              color: '#333',
              fontWeight: '600'
            }}>
              Drag and drop files here
            </p>
            <p style={{ margin: '8px 0', fontSize: '14px', color: '#666' }}>
              or
            </p>
            <Button
              appearance="secondary"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                open();
              }}
              style={{
                minWidth: '120px',
                backgroundColor: 'white',
                border: '1px solid grey',
                borderRadius: '4px',
              }}
            >
              Browse files
            </Button>
            <p style={{
              margin: '8px 0 0 0',
              fontSize: '12px',
              color: '#666'
            }}>
              Limit {Math.floor(maxSize / (1024 * 1024))}MB per file • SQL Only • {MAX_FILES} files max
            </p>
          </>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '13px', width: '837px', paddingBottom: 10, borderRadius: '4px', }}>
        {/* Show file rejection errors for invalid type or size */}
         {fileRejectionErrors.length > 0 && (
            <MessageBar
              messageBarType={MessageBarType.error}
              isMultiline={true}
              styles={messageBarErrorStyles}
            >
              <div style={{ display: "flex", alignItems: "center" }}>
                <X strokeWidth="2.5px" color="#d83b01" size="16px" style={{ marginRight: "8px" }} />
                <span>{fileRejectionErrors[0]}</span>
              </div>
              {fileRejectionErrors.slice(1).map((err, idx) => (
                <div key={idx} style={{ marginLeft: "24px", marginTop: "2px" }}>{err}</div>
              ))}
            </MessageBar>
        )}
        {/* Show network error message bar if any file has error */}
        {uploadingFiles.some(f => f.status === 'error') && (
          <MessageBar
            messageBarType={MessageBarType.error}
            isMultiline={false}
            styles={messageBarErrorStyles}
          >
            <div style={{ display: "flex", alignItems: "left" }}>
              <X
                strokeWidth="2.5px"
                color="#d83b01"
                size="16px"
                style={{ marginRight: "8px" }}
              />
              <span>Unable to connect to the server. Please try again later.</span>
            </div>
          </MessageBar>
        )}

        {/* Success message bar if all uploads complete and no errors */}
        {allUploadsComplete && !uploadingFiles.some(f => f.status === 'error') && (
          <MessageBar
            messageBarType={MessageBarType.success}
            isMultiline={false}
            styles={messageBarSuccessStyles}
          >
            <div style={{ display: "flex", alignItems: "left" }}>
              <CircleCheck
                strokeWidth="2.5px"
                color="#37a04c"
                size="16px"
                style={{ marginRight: "8px" }}
              />
              <span>All valid files uploaded successfully!</span>
            </div>
          </MessageBar>
        )}

        {fileLimitExceeded && (
          <MessageBar
            messageBarType={MessageBarType.warning}
            isMultiline={false}
            onDismiss={() => setFileLimitExceeded(false)}
            dismissButtonAriaLabel="Close"
            styles={messageBarWarningStyles}
          >
            <X
              strokeWidth="2.5px"
              color='#d83b01'
              size='14px'
              style={{ marginRight: "12px", paddingTop: 3 }}
            />
            Maximum of {MAX_FILES} files allowed. Some files were not uploaded.
          </MessageBar>
        )}
      </div>

      {uploadingFiles.length > 0 && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          width: '837px',
          maxHeight: '300px',
          overflowY: 'auto',
          scrollbarWidth: 'thin'
        }}>
          {uploadingFiles.map((file) => (
            <div
              key={file.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '8px 12px',
                backgroundColor: 'white',
                borderRadius: '4px',
                border: '1px solid #eee',
                position: 'relative'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', width: '24px' }}>
                📄
              </div>
              <Tooltip content={file.file.name} relationship="label">
                <div
                  style={{
                    width: 80,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    fontSize: "14px",
                    alignItems: "left",
                    cursor: "pointer",
                    textAlign: "left",
                  }}
                >
                  {file.file.name}
                </div>
              </Tooltip>
              <div style={{
                flex: 1,
                height: '4px',
                backgroundColor: '#eee',
                borderRadius: '2px',
                overflow: 'hidden'
              }}>
                <div
                  style={{
                    width: `${file.progress}%`,
                    height: '100%',
                    backgroundColor: file.status === 'error' ? '#ff4444' :
                      file.status === 'completed' ? '#4CAF50' :
                        '#2196F3',
                    transition: 'width 0.3s ease'
                  }}
                />
              </div>
              <Tooltip content="Remove file" relationship="label">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(file.id);
                  }}
                  style={{
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                    padding: '4px',
                    color: file.status === 'error' ? '#d83b01' : '#666',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '24px',
                    height: '24px'
                  }}
                >
                  ✕
                </button>
              </Tooltip>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUploadZone;