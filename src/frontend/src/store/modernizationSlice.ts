import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import httpUtility from "../utils/httpUtil";
import { BatchSummary } from "../types/types";
import { completedFiles, filesFinalErrorCounter, filesErrorCounter, hasFiles, fileWarningCounter, fileErrorCounter, filesLogsBuilder } from "../utils/utils";

export const fetchFileFromAPI = createAsyncThunk(
  "modernization/fetchFileFromAPI",
  async (fileId: string, { rejectWithValue }) => {
    try {
      const response:any = await httpUtility.get(`/file/${fileId}`);
      return response; // Assuming the API returns the file content directly
    } catch (error) {
      console.error("Error fetching file from API:", error);
      return rejectWithValue({ content: "", translatedContent: "" });
    }
  }
);

export const fetchBatchSummary = createAsyncThunk(
  "modernization/fetchBatchSummary",
  async (batchId: string, { rejectWithValue }) => {
    try {
      const responseData:any = await httpUtility.get(`/batch-summary/${batchId}`);
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
      return rejectWithValue({ content: "", translatedContent: "" });
    }
  }
);

export const handleDownloadZip = createAsyncThunk(
    "modernization/handleDownloadZip",
    async (batchId: string, { rejectWithValue }) => {
        if (batchId) {
            try {
              const response:any = await httpUtility.get(`/download/${batchId}?batch_id=${batchId}`);
      
              
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
    }
  );

const modernizationSlice = createSlice({
  name: "modernizationSlice",
  initialState: { 
    isOpen: false,
    loading: false,
    fileContent: {content: "", translated_content: "",file_result: null, file_track_log: [], file_track_percentage: 0},
    batchSummary: {
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
    },
 },
  reducers: {
    updateBatchSummary: (state, action) => {
        state.batchSummary = action.payload;
    },
  },
  extraReducers: (builder) => {
      // Handle the deleteBatch action
      builder
        .addCase(fetchFileFromAPI.pending, (state) => {
          state.loading = true;
        })
        .addCase(fetchFileFromAPI.fulfilled, (state, action) => {
            state.fileContent = action.payload;
            state.loading = false;
        })
        .addCase(fetchFileFromAPI.rejected, (state, action) => {
          state.loading = false;
        })
        .addCase(fetchBatchSummary.pending, (state) => {
            state.loading = true;
        })
        .addCase(fetchBatchSummary.fulfilled, (state, action) => {
            state.batchSummary = action.payload;
            state.loading = false;
        })
        .addCase(fetchBatchSummary.rejected, (state, action) => {
        state.loading = false;
        })
    }
});

export const { updateBatchSummary} = modernizationSlice.actions;
export default modernizationSlice.reducer;