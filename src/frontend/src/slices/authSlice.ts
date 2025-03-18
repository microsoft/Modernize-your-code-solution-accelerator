import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { getUserInfo, UserInfo } from '../api/auth';

// Define the type for headers
interface AuthHeaders {
  "Content-Type": string;
  "X-Ms-Client-Principal": string;
  "X-Ms-Client-Principal-Id": string;
  "X-Ms-Client-Principal-Name": string;
  "X-Ms-Client-Principal-Idp": string;
  [key: string]: string; // allowing additional string properties
}

// Define the payload type for the fulfilled action
interface AuthPayload {
  user: UserInfo | null;
  headers: AuthHeaders | null;
}

// Define the state type
interface AuthState {
  user: UserInfo | null;
  headers: AuthHeaders | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

export const fetchAuthDetails = createAsyncThunk('auth/fetchAuthDetails', async () => {
  const userInfo = await getUserInfo();
  if (!userInfo) return { user: null, headers: null };

  // Generate headers from user info
  const headers = {
    "Content-Type": "application/json",
    "X-Ms-Client-Principal": userInfo.id_token || "",
    "X-Ms-Client-Principal-Id": userInfo.user_claims?.find(
      (claim) => claim.typ === "http://schemas.microsoft.com/identity/claims/objectidentifier"
    )?.val || "",
    "X-Ms-Client-Principal-Name": userInfo.user_claims?.find(
      (claim) => claim.typ === "name"
    )?.val || "",
    "X-Ms-Client-Principal-Idp": userInfo.provider_name || "",
  };

  return { user: userInfo, headers };
});

// Initial state with proper typing
const initialState: AuthState = {
  user: null,
  headers: null, // Changed from {} to null
  status: "idle",
  error: null,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAuthDetails.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchAuthDetails.fulfilled, (state, action: PayloadAction<AuthPayload>) => {
        state.status = "succeeded";
        state.user = action.payload.user;
        state.headers = action.payload.headers;
      })
      .addCase(fetchAuthDetails.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message || "Unknown error";
      });
  },
});

// Selector to access auth headers from any component
export const selectAuthHeaders = (state: { auth: AuthState }) => state.auth.headers || {};
export const {  } = authSlice.actions;
export default authSlice.reducer;