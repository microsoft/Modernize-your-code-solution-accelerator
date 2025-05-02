import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import httpUtility from "../utils/httpUtil";

export const deleteFileFromBatch = createAsyncThunk(
  'batch/deleteFileFromBatch',
  async (fileId: string, { rejectWithValue }) => {
    try {
      
      const response:any = await httpUtility.delete(`/delete-file/${fileId}`);

      // Return the response data
      return response;
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
      
      const response:any = await httpUtility.post(`/upload`, formData);
      return response;
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

export const { resetState } = fileSlice.actions;
export default fileSlice.reducer;
