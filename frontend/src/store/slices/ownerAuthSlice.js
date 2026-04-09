import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { OWNER_TOKEN_KEY, ownerApi } from "../../services/api";

const OWNER_PROFILE_KEY = "yelp_lab1_owner";

function getStoredOwner() {
  const raw = localStorage.getItem(OWNER_PROFILE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (_error) {
    localStorage.removeItem(OWNER_PROFILE_KEY);
    return null;
  }
}

function persistOwnerSession(token, owner) {
  if (token) {
    localStorage.setItem(OWNER_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(OWNER_TOKEN_KEY);
  }

  if (owner) {
    localStorage.setItem(OWNER_PROFILE_KEY, JSON.stringify(owner));
  } else {
    localStorage.removeItem(OWNER_PROFILE_KEY);
  }
}

export const bootstrapOwnerAuth = createAsyncThunk(
  "ownerAuth/bootstrap",
  async (_, { rejectWithValue }) => {
    try {
      const response = await ownerApi.get("/owners/me");
      return response.data;
    } catch (_error) {
      return rejectWithValue("Owner session expired.");
    }
  }
);

export const refreshCurrentOwner = createAsyncThunk(
  "ownerAuth/refreshCurrentOwner",
  async (_, { rejectWithValue }) => {
    try {
      const response = await ownerApi.get("/owners/me");
      return response.data;
    } catch (_error) {
      return rejectWithValue("Failed to refresh owner.");
    }
  }
);

const initialToken = localStorage.getItem(OWNER_TOKEN_KEY) || "";

const ownerAuthSlice = createSlice({
  name: "ownerAuth",
  initialState: {
    ownerToken: initialToken,
    owner: getStoredOwner(),
    isOwnerAuthReady: !initialToken,
    status: "idle",
    error: "",
  },
  reducers: {
    setOwnerSession(state, action) {
      state.ownerToken = action.payload.token;
      state.owner = action.payload.owner;
      state.isOwnerAuthReady = true;
      state.status = "authenticated";
      state.error = "";
      persistOwnerSession(action.payload.token, action.payload.owner);
    },
    clearOwnerSession(state) {
      state.ownerToken = "";
      state.owner = null;
      state.isOwnerAuthReady = true;
      state.status = "idle";
      state.error = "";
      persistOwnerSession("", null);
    },
    markOwnerAuthReady(state) {
      state.isOwnerAuthReady = true;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(bootstrapOwnerAuth.pending, (state) => {
        state.status = "loading";
        state.error = "";
      })
      .addCase(bootstrapOwnerAuth.fulfilled, (state, action) => {
        state.owner = action.payload;
        state.isOwnerAuthReady = true;
        state.status = "authenticated";
        state.error = "";
        persistOwnerSession(state.ownerToken, action.payload);
      })
      .addCase(bootstrapOwnerAuth.rejected, (state, action) => {
        state.ownerToken = "";
        state.owner = null;
        state.isOwnerAuthReady = true;
        state.status = "idle";
        state.error = action.payload || "Owner session expired.";
        persistOwnerSession("", null);
      })
      .addCase(refreshCurrentOwner.fulfilled, (state, action) => {
        state.owner = action.payload;
        state.status = state.ownerToken ? "authenticated" : "idle";
        persistOwnerSession(state.ownerToken, action.payload);
      })
      .addCase(refreshCurrentOwner.rejected, (state, action) => {
        state.error = action.payload || "Failed to refresh owner.";
      });
  },
});

export const { setOwnerSession, clearOwnerSession, markOwnerAuthReady } =
  ownerAuthSlice.actions;
export default ownerAuthSlice.reducer;
