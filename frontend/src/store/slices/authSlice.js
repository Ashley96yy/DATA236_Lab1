import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import api, { TOKEN_KEY, extractApiError } from "../../services/api";

const USER_KEY = "yelp_lab1_user";

function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (_error) {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

function persistSession(token, user) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }

  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
}

export const bootstrapAuth = createAsyncThunk(
  "auth/bootstrap",
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get("/auth/me");
      return response.data;
    } catch (error) {
      return rejectWithValue(extractApiError(error, "Session expired."));
    }
  }
);

export const refreshCurrentUser = createAsyncThunk(
  "auth/refreshCurrentUser",
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get("/auth/me");
      return response.data;
    } catch (error) {
      return rejectWithValue(extractApiError(error, "Failed to refresh user."));
    }
  }
);

const initialToken = localStorage.getItem(TOKEN_KEY) || "";

const authSlice = createSlice({
  name: "auth",
  initialState: {
    token: initialToken,
    user: getStoredUser(),
    isAuthReady: !initialToken,
    status: "idle",
    error: "",
  },
  reducers: {
    setSession(state, action) {
      state.token = action.payload.token;
      state.user = action.payload.user;
      state.isAuthReady = true;
      state.status = "authenticated";
      state.error = "";
      persistSession(action.payload.token, action.payload.user);
    },
    clearSession(state) {
      state.token = "";
      state.user = null;
      state.isAuthReady = true;
      state.status = "idle";
      state.error = "";
      persistSession("", null);
    },
    markAuthReady(state) {
      state.isAuthReady = true;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(bootstrapAuth.pending, (state) => {
        state.status = "loading";
        state.error = "";
      })
      .addCase(bootstrapAuth.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthReady = true;
        state.status = "authenticated";
        state.error = "";
        persistSession(state.token, action.payload);
      })
      .addCase(bootstrapAuth.rejected, (state, action) => {
        state.token = "";
        state.user = null;
        state.isAuthReady = true;
        state.status = "idle";
        state.error = action.payload || "Session expired.";
        persistSession("", null);
      })
      .addCase(refreshCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload;
        state.status = state.token ? "authenticated" : "idle";
        persistSession(state.token, action.payload);
      })
      .addCase(refreshCurrentUser.rejected, (state, action) => {
        state.error = action.payload || "Failed to refresh user.";
      });
  },
});

export const { setSession, clearSession, markAuthReady } = authSlice.actions;
export default authSlice.reducer;
