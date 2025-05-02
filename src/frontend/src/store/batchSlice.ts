import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import httpUtility from '../utils/httpUtil';

// Dummy API call for batch deletion
export const deleteBatch = createAsyncThunk<
  any, // The type of returned response data (can be updated to match API response)
  { batchId: string; headers?: Record<string, string> | null }, // Payload type
  { rejectValue: string } // Type for rejectWithValue
>(
  'batch/deleteBatch',
  async ({ batchId, headers }: { batchId: string; headers?: Record<string, string> | null }, { rejectWithValue }) => {
    try {
      
      const response:any = await httpUtility.delete(`/delete-batch/${batchId}`);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || 'Failed to delete batch');
    }
  }
);


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
      
      const response:any = await httpUtility.post(`/start-processing`, requestData);

      const data = response

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
      

      const response:any = await httpUtility.get(`/batch-history`);
      return response;
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
 
      const response:any = await httpUtility.delete(`/delete_all`);
      return response;
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
export default batchSlice.reducer;