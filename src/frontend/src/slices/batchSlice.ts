import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';
import { getApiUrl, headerBuilder } from '../api/config';

// Dummy API call for batch deletion
export const deleteBatch = createAsyncThunk<
  any, // The type of returned response data (can be updated to match API response)
  { batchId: string; headers?: Record<string, string> | null }, // Payload type
  { rejectValue: string } // Type for rejectWithValue
>(
  'batch/deleteBatch',
  async ({ batchId, headers }: { batchId: string; headers?: Record<string, string> | null }, { rejectWithValue }) => {
    try {
      const apiUrl = getApiUrl();
      const response = await axios.delete(`${apiUrl}/delete-batch/${batchId}`, { headers: headerBuilder(headers) });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || 'Failed to delete batch');
    }
  }
);

export const deleteFileFromBatch = createAsyncThunk(
  'batch/deleteFileFromBatch',
  async (fileId: string, { rejectWithValue }) => {
    try {
      const apiUrl = getApiUrl();
      const response = await axios.delete(`${apiUrl}/delete-file/${fileId}`, { headers: headerBuilder({}) });

      // Return the response data
      return response.data;
    } catch (error) {
      // Handle the error
      return rejectWithValue(error.response?.data || 'Failed to delete batch');
    }
  }
);

// API call for uploading single file in batch
export const uploadFile = createAsyncThunk('/upload', // Updated action name
  async (payload: { file: File; batchId: string }, { rejectWithValue }) => {
    try {
      const formData = new FormData();

      // Append batch_id
      formData.append("batch_id", payload.batchId);

      // Append the single file 
      formData.append("file", payload.file);
      //formData.append("file_uuid", payload.uuid);
      const apiUrl = getApiUrl();
      const response = await axios.post(`${apiUrl}/upload`, formData, {
        headers: headerBuilder({
          "Content-Type": "multipart/form-data"
        })
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Failed to upload file');
    }
  }
);

interface FileState {
  batchId: string | null;
  fileList: { fileId: string; originalName: string }[]; // Store file_id & name
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

// Initial state
const initialFileState: FileState = {
  batchId: null,
  fileList: [],
  status: 'idle',
  error: null,
};

const fileSlice = createSlice({
  name: 'fileUpload',
  initialState: initialFileState,
  reducers: {
    resetState: (state) => {
      state.batchId = null;
      state.fileList = [];
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadFile.fulfilled, (state, action: PayloadAction<{ batch: { batch_id: string }; file: { file_id: string; original_name: string } }>) => {
        state.batchId = action.payload.batch.batch_id; // Store batch ID
        state.fileList.push({
          fileId: action.payload.file.file_id, // Store file ID
          originalName: action.payload.file.original_name, // Store file name
        });
        state.status = 'succeeded';
      })
      .addCase(uploadFile.rejected, (state, action: PayloadAction<any>) => {
        state.error = action.payload;
        state.status = 'failed';
      })
      .addCase(deleteFileFromBatch.fulfilled, (state, action) => {
        state.fileList = state.fileList.filter(file => file.fileId !== action.meta.arg);
      });
  },
});


//API call for Batch Start Processing
export const startProcessing = createAsyncThunk(
  "batch/startProcessing",
  async (payload: { batchId: string; translateFrom: string; translateTo: string }, { rejectWithValue }) => {
    try {
      // Constructing the request payload
      const requestData = {
        batch_id: payload.batchId,
        translate_from: payload.translateFrom, // Empty for now
        translate_to: payload.translateTo, // Either "sql" or "postgress"
      };
      const apiUrl = getApiUrl();
      const response = await axios.post(`${apiUrl}/start-processing`, requestData, { headers: headerBuilder({}) });

      const data = response.data

      return await data;
    } catch (error) {
      return rejectWithValue(error.response?.data || "Failed to start processing");
    }
  }
);

interface FetchBatchHistoryPayload {
  headers?: Record<string, string>;
}

// Async thunk to fetch batch history with headers
export const fetchBatchHistory = createAsyncThunk(
  "batch/fetchBatchHistory",
  async ({ headers }: FetchBatchHistoryPayload, { rejectWithValue }) => {
    try {
      const apiUrl = getApiUrl();

      const response = await axios.get(`${apiUrl}/batch-history`, { headers: headerBuilder(headers) });
      return response.data;
    } catch (error) {
      if (error.response && error.response.status === 404) {
        return [];
      }
      return rejectWithValue(error.response?.data || "Failed to load batch history");
    }
  }
);

export const deleteAllBatches = createAsyncThunk(
  "batch/deleteAllBatches",
  async ({ headers }: { headers: Record<string, string> }, { rejectWithValue }) => {
    try {
      const apiUrl = getApiUrl();
      const response = await axios.delete(`${apiUrl}/delete_all`, { headers: headerBuilder(headers) });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || "Failed to delete all batch history");
    }
  }
);

//

// Initial state for the batch slice
const initialState: {
  batches: string[],
  batchId: string | null;
  fileId: string | null;
  message: string;
  loading: boolean;
  error: string | null;
  uploadingFiles: boolean;
  files: {
    file_id: string;
    batch_id: string;
    original_name: string;
    blob_path: string;
    translated_path: string;
    status: string;
    error_count: number;
    created_at: string;
    updated_at: string;
  }[];
} = {
  batchId: null,
  fileId: null,
  message: '',
  loading: false,
  error: null,
  uploadingFiles: false,
  files: [],
  batches: []
};

export const batchSlice = createSlice({
  name: 'batch',
  initialState,
  reducers: {
    resetBatch: (state) => {
      state.batchId = null;
      state.fileId = null
      state.message = '';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Handle the deleteBatch action
    builder
      .addCase(deleteBatch.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteBatch.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload) {
          state.batchId = action.payload.batch_id;
          state.message = action.payload.message;
        } else {
          state.error = "Unexpected response: Payload is undefined.";
        }
      })
      .addCase(deleteBatch.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
    //delete file from batch
    builder
      .addCase(deleteFileFromBatch.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteFileFromBatch.fulfilled, (state, action) => {
        state.loading = false;
        //state.files = state.files.filter(file => file.file_id !== action.payload.fileId);
        if (action.payload) {
          state.fileId = action.payload.file_id;
          state.message = action.payload.message;
        } else {
          state.error = "Unexpected response: Payload is undefined.";
        }
      })
      .addCase(deleteFileFromBatch.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
    // Handle the uploadFilesInBatch action
    builder
      .addCase(uploadFile.pending, (state) => {
        state.uploadingFiles = true;
        state.error = null;
      })
      .addCase(uploadFile.fulfilled, (state, action) => {
        state.uploadingFiles = false;
        if (action.payload) {
          state.batchId = action.payload.batch.batch_id;
          state.message = "File uploaded successfully";

          // Ensure files array exists before pushing
          if (!state.files) {
            state.files = [];
          }

          // Add the newly uploaded file to state.files
          state.files.push(action.payload.file);
        } else {
          state.error = "Unexpected response: Payload is undefined.";
        }
      })
      .addCase(uploadFile.rejected, (state, action) => {
        state.uploadingFiles = false;
        state.error = action.payload as string;
      });
    //Start Processing Action Handle  
    builder
      .addCase(startProcessing.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(startProcessing.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload) {
          console.log("Action Payload", action.payload);
          state.batchId = action.payload.batch_id;
          state.message = "Processing started successfully";
        } else {
          state.error = "Unexpected response: Payload is undefined.";
        }
      })
      .addCase(startProcessing.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
    //Fetch Batch History Action Handle
    builder
      .addCase(fetchBatchHistory.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBatchHistory.fulfilled, (state, action) => {
        state.loading = false;
        state.batches = action.payload;
      })
      .addCase(fetchBatchHistory.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string | null;
      });
    builder
      .addCase(deleteAllBatches.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteAllBatches.fulfilled, (state) => {
        state.loading = false;
        state.batches = [];
      })
      .addCase(deleteAllBatches.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string | null;
      });
  },
});

export const { } = batchSlice.actions;
export const batchReducer = batchSlice.reducer;
export const fileReducer = fileSlice.reducer;
export const { resetState } = fileSlice.actions;