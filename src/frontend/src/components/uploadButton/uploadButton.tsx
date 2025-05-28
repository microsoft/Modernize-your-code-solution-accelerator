import React, { useCallback, useState, useEffect } from 'react';
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
import { deleteBatch, startProcessing } from '../../store/batchSlice';
import {deleteFileFromBatch, uploadFile} from '../../store/uploadFileSlice';
import { useDispatch } from 'react-redux';
import ConfirmationDialog from '../../commonComponents/ConfirmationDialog/confirmationDialogue';
import { AppDispatch } from '../../store/store'
import { v4 as uuidv4 } from 'uuid';
import "./uploadStyles.scss";
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
  acceptedFileTypes = { 'application/sql': ['.sql'] },
  selectedCurrentLanguage,
  selectedTargetLanguage
}) => {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [uploadIntervals, setUploadIntervals] = useState<{ [key: string]: ReturnType<typeof setTimeout> }>({});
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showLogoCancelDialog, setShowLogoCancelDialog] = useState(false);
  const [uploadState, setUploadState] = useState<'IDLE' | 'UPLOADING' | 'COMPLETED'>('IDLE');
  const [batchId, setBatchId] = useState<string>(uuidv4());
  const [allUploadsComplete, setAllUploadsComplete] = useState(false);
  const [fileLimitExceeded, setFileLimitExceeded] = useState(false);
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

    setUploadState(newState);
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
      // Check current files count and determine how many more can be added
      const remainingSlots = MAX_FILES - uploadingFiles.length;

      if (remainingSlots <= 0) {
        // Already at max files, show dialog
        setShowFileLimitDialog(true);
        return;
      }

      // If more files are dropped than slots available
      if (acceptedFiles.length > remainingSlots) {
        // Take only the first `remainingSlots` files
        const filesToUpload = acceptedFiles.slice(0, remainingSlots);
        filesToUpload.forEach(file => simulateFileUpload(file));

        if (onFileUpload) onFileUpload(filesToUpload);

        // Show dialog about exceeding limit
        setShowFileLimitDialog(true);
      } else {
        // Normal case, upload all files
        acceptedFiles.forEach(file => simulateFileUpload(file));
        if (onFileUpload) onFileUpload(acceptedFiles);
      }

      if (onFileReject && fileRejections.length > 0) {
        onFileReject(fileRejections);
      }
    },
    [onFileUpload, onFileReject, uploadingFiles.length]
  );

  const dropzoneOptions: DropzoneOptions = {
    onDrop,
    noClick: true,
    maxSize,
    accept: acceptedFileTypes,
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
          // First navigate to loading page before starting processing
          navigate(`/batch-process/${batchId}`);

          // Then dispatch the action and wait for it to complete
          try {
            dispatch(startProcessing(payload));
            return batchId; // Return the batchId after processing completes
          } catch (error) {
            console.error('Processing failed:', error);
            // Still return the batchId even if processing failed
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
    <div className='containerClass'>
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
        cancelText="Stay here"
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
        <div className='uploadContainer' >
          <h1 className='title'>
            Modernize your code
          </h1>
          <p className='label'>
            Modernize your code by updating the language with AI
          </p>
        </div>
      )}

      <div className='informationContainer'>
        <h2 className='infoMessage'>
          {uploadingFiles.length > 0
            ? `Uploading (${uploadingFiles.filter(f => f.status === 'completed').length}/${uploadingFiles.length})`
            : 'Upload files in batch'
          }
        </h2>
      </div>

      <div
        {...getRootProps()}
        className='uploadingFilesInfo'
        style={{
          padding: uploadingFiles.length > 0 ? "16px" : "0px",
          flexDirection: uploadingFiles.length > 0 ? 'row' : 'column',
          justifyContent: uploadingFiles.length > 0 ? 'space-between' : 'center',
          height: uploadingFiles.length > 0 ? '80px' : '251px',
        }}
      >
        <input {...getInputProps()} />

        {uploadingFiles.length > 0 ? (
          <>
            <div className='fileUploadContainer'>
              <img
                src="/images/Arrow-Upload.png"
                alt="Upload Icon"
                className='uploadImage'
              />
              <div>
                <p className='uploadInfoMsg'>
                  Drag and drop files here
                </p>
                <p className='uploadLimitInfoMsg'>
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
              className='browseBtn'
            >
              Browse files
            </Button>
          </>
        ) : (
          <>
            <img
              src="/images/Arrow-Upload.png"
              alt="Upload Icon"
              className='uploadIcon'
            />
            <p className='dragdropMsg'>
              Drag and drop files here
            </p>
            <p className='dragdropMsg2'>
              or
            </p>
            <Button
              appearance="secondary"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                open();
              }}
              className='browseBtn2'
            >
              Browse files
            </Button>
            <p className='uploadLimitInfoMsg2'>
              Limit {Math.floor(maxSize / (1024 * 1024))}MB per file • SQL Only • {MAX_FILES} files max
            </p>
          </>
        )}
      </div>

      <div className='messagebarContainer'>
        {allUploadsComplete && (
          <MessageBar
            messageBarType={MessageBarType.success}
            isMultiline={false}
            styles={{
              root: { display: "flex", alignItems: "left" }, // Align the icon and text
              icon: { display: "none" },
            }}
          >
            <div className='iconContainer2'>
              <CircleCheck
                strokeWidth="2.5px"
                color="#37a04c"
                size="16px" // Slightly larger for better balance
                className='mr_8'
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
            styles={{
              root: { display: "flex", alignItems: "center" },
            }}
          >
            <X
              strokeWidth="2.5px"
              color='#d83b01'
              size='14px'
              className='xBtn'
            />
            Maximum of {MAX_FILES} files allowed. Some files were not uploaded.
          </MessageBar>
        )}
      </div>

      {uploadingFiles.length > 0 && (
        <div className='uploadedFilesContainer'>
          {uploadingFiles.map((file) => (
            <div
              key={file.id}
              className='fileMainContainer'
            >
              <div className='fileImageContainer'>
                📄
              </div>
              <Tooltip content={file.file.name} relationship="label">
                <div
                  className='tooltipClass'
                >
                  {file.file.name}
                </div>
              </Tooltip>
              <div className='statusContainer'>
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
                  className='removeBtn'
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