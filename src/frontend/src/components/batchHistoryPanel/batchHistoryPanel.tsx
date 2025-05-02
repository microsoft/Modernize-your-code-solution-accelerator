import React, { useState, useEffect, useRef } from "react";

import { useDispatch, useSelector } from 'react-redux';
import { Card, Spinner, Tooltip } from "@fluentui/react-components";
import { useNavigate } from "react-router-dom";
import ConfirmationDialog from "../../commonComponents/ConfirmationDialog/confirmationDialogue";
import "./batchHistoryPanel.scss"
import { deleteBatch, fetchBatchHistory, deleteAllBatches } from '../../store/batchSlice';
import { AppDispatch } from '../../store/store';
import { updateBatchSummary } from "../../store/modernizationSlice";

interface HistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
}
interface BatchHistoryItem {
  batch_id: string;
  user_id: string;
  file_count: number;
  created_at: string;
  updated_at: string;
  status: string;
}
const HistoryPanel: React.FC<HistoryPanelProps> = ({ isOpen, onClose }) => {
  const headers = {}
  const [batchHistory, setBatchHistory] = useState<BatchHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteAllDialog, setShowDeleteAllDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedBatchId, setSelectedBatchId] = useState("");
  const [hoveredBatchId, setHoveredBatchId] = useState<string | null>(null);
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const hasFetched = useRef(false);
  const handleBatchNavigation = (batch: BatchHistoryItem) => {
    onClose(); // Ensure panel closes before navigation
    dispatch(updateBatchSummary({
      batch_id: "",
      upload_id: "",
      date_created: "",
      total_files: 0,
      completed_files: 0,
      error_count: 0,
      status: "",
      warning_count: 0,
      hasFiles: 0,
      files: [] as {
        file_id: string;
        name: string;
        status: string;
        error_count: number;
        warning_count: number;
        file_logs: any[];
        content?: string;
        translated_content?: string;
      }[],
    })); // Reset batch summary in Redux store
    requestAnimationFrame(() => {
      if (batch.status?.toLowerCase() === "completed") {
        navigate(`/batch-view/${batch.batch_id}`);
      } else {
        navigate(`/batch-process/${batch.batch_id}`);
      }
    });
  };

  useEffect(() => {
    if (isOpen && !hasFetched.current) {
      fetchBatchHistoryFromPanel();
      hasFetched.current = true;
    }
  }, [isOpen]);

  useEffect(() => {
    if (!headers) return;
  }, [headers]);

  const fetchBatchHistoryFromPanel = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dispatch(fetchBatchHistory({ headers })).unwrap();

      // Check if data is an array
      if (Array.isArray(data)) {
        setBatchHistory(data);
      } else if (data.status_code === 404) {
        // Handle the "no history" case specifically
        setBatchHistory([]);
        // You might want to show a more specific message
        // setError("No batch history found.");
      } else {
        // Handle other non-array responses
        console.error('Unexpected API response format:', data);
        setBatchHistory([]);
        setError("Unable to load batch history due to unexpected data format.");
      }
    } catch (err) {
      setError("Unable to load batch history. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  // Function to categorize batches
  const categorizeBatches = () => {
    const now = new Date();
    const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    // Get start of "Today", "Past 7 days", and "Past 30 days" in LOCAL time
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const past7DaysStart = new Date(todayStart);
    const past30DaysStart = new Date(todayStart);

    past7DaysStart.setDate(todayStart.getDate() - 7);
    past30DaysStart.setDate(todayStart.getDate() - 30);

    const todayBatches: BatchHistoryItem[] = [];
    const past7DaysBatches: BatchHistoryItem[] = [];
    const past30DaysBatches: BatchHistoryItem[] = [];

    batchHistory.forEach(batch => {
      // Convert UTC timestamp to user's local date
      const updatedAtUTC = new Date(batch.created_at);
      const updatedAtLocal = new Date(updatedAtUTC.toLocaleString("en-US", { timeZone: userTimeZone }));

      // Extract only the local **date** part for comparison
      const updatedDate = new Date(updatedAtLocal.getFullYear(), updatedAtLocal.getMonth(), updatedAtLocal.getDate());

      // Categorize based on **exact day comparison**
      if (updatedDate.getTime() === todayStart.getTime()) {
        todayBatches.push(batch);
      } else if (updatedDate.getTime() >= past7DaysStart.getTime()) {
        past7DaysBatches.push(batch);
      } else if (updatedDate.getTime() >= past30DaysStart.getTime()) {
        past30DaysBatches.push(batch);
      }
    });

    return { todayBatches, past7DaysBatches, past30DaysBatches };
  };

  // const { todayBatches, past7DaysBatches, past30DaysBatches } = categorizeBatches();

  const deleteBatchFromHistory = (batchId: string) => {
    // Get the current URL path
    const currentPath = window.location.pathname;

    // Check if the current URL contains the batch ID being deleted
    const isCurrentBatch = currentPath.includes(`/batch-view/${batchId}`) ||
      currentPath.includes(`/batch-process/${batchId}`);

    const headers = {
      "Content-Type": "application/json"
    };

    try {
      dispatch(deleteBatch({ batchId, headers })).unwrap();
      const updatedBatchHistory = batchHistory.filter(batch => batch.batch_id !== batchId);
      setBatchHistory(updatedBatchHistory);

      // If the deleted batch is the current one, navigate to home page
      if (isCurrentBatch) {
        onClose(); // Close the panel first
        requestAnimationFrame(() => {
          navigate('/'); // Navigate to homepage
        });
      }
    } catch (error) {
      console.error("Batch deletion failed:", error);
    }
  };

  const deleteAllBatchesFromHistory = async () => {
    // Get the current URL path
    const currentPath = window.location.pathname;

    // Check if the current URL contains "/batch-view/" or "/batch-process/"
    const isViewingBatch = currentPath.includes("/batch-view/") ||
      currentPath.includes("/batch-process/");

    try {
      const headers = { "Content-Type": "application/json" };
      await dispatch(deleteAllBatches({ headers })).unwrap();
      setBatchHistory([]);

      // If the user is currently viewing any batch, navigate to home page
      if (isViewingBatch) {
        onClose(); // Close the panel first
        requestAnimationFrame(() => {
          navigate('/'); // Navigate to homepage
        });
      }
    } catch (error) {
      setError("Failed to clear batch history. Please try again later.");
      setTimeout(() => {
        fetchBatchHistoryFromPanel(); // Restore original batch history
      }, 5000);
    } finally {
      setShowDeleteAllDialog(false);
    }
  };

  const formatToLocaleTime = (dateString: string) => {
    return new Date(dateString).toLocaleString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  return (
    <div className={`history-panel ${isOpen ? "open" : "closed"}`}>
      {/* <div className="panel-header">
        Batch History
        <Button icon={<DeleteRegular />} onClick={() => setShowDeleteAllDialog(true)} appearance="subtle" />
    </div> */}

      {loading ? (
        <div className="loading-container loader">
          <Spinner size="large" label="Loading..." labelPosition="below" />
        </div>
      ) : error ? (
        <p className="errorContainer">{error}</p>
      ) : batchHistory.length === 0 ? (
        <p className="infoContainer">No batch history available.</p>
      ) : (
        <div className="batch-list">
          {batchHistory.map(batch => (
            <Card
              key={batch.batch_id}
              className="batch-item"
              onMouseEnter={() => setHoveredBatchId(batch.batch_id)}
              onMouseLeave={() => setHoveredBatchId(null)}
              style={{
                backgroundColor: hoveredBatchId === batch.batch_id ? "#e1e1e1" : "transparent",
              }}
            >
              <div className="batch-details">
                <span className="batch-details-name" onClick={() => handleBatchNavigation(batch)}>
                  {(() => {
                    const date = new Date(batch.created_at);
                    const userLocale = navigator.language;
                    const dateFormatter = new Intl.DateTimeFormat(userLocale, {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                    });
                    return dateFormatter.format(date);
                  })()} ({batch.file_count} {batch.file_count === 1 ? "file" : "files"})
                </span>
                {hoveredBatchId === batch.batch_id && batch.status === "completed" ? (
                  <Tooltip content="Delete Batch" relationship="label">
                    <button className="delete-button"
                      onClick={() => {
                        setSelectedBatchId(batch.batch_id);
                        setShowDeleteDialog(true);
                      }}
                      >
                      ✕
                    </button>
                  </Tooltip>
                ) : (
                  <span className="batch-details-time">
                    {formatToLocaleTime(batch.updated_at + '+00:00')}
                  </span>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Confirmation dialog for deleting all batches */}
      <ConfirmationDialog
        open={showDeleteAllDialog}
        setOpen={setShowDeleteAllDialog}
        title="Delete All History?"
        message="Are you sure you want to delete all batch history?"
        onConfirm={deleteAllBatchesFromHistory}
        onCancel={() => setShowDeleteAllDialog(false)}
        confirmText="Delete All"
        cancelText="Cancel"
      />

      {/* Confirmation dialog for deleting a single batch */}
      <ConfirmationDialog
        open={showDeleteDialog}
        setOpen={setShowDeleteDialog}
        title="Delete Batch?"
        message="Are you sure you want to delete this batch?"
        onConfirm={() => deleteBatchFromHistory(selectedBatchId)}
        onCancel={() => setShowDeleteDialog(false)}
        confirmText="Delete"
        cancelText="Cancel"
      />
    </div>
  );
};

export default HistoryPanel;