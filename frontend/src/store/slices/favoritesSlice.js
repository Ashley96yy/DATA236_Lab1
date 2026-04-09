import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { favoritesApi } from "../../services/api";

export const loadFavorites = createAsyncThunk(
  "favorites/loadFavorites",
  async (_, { rejectWithValue }) => {
    try {
      const response = await favoritesApi.list(1, 100);
      return response.data.items || [];
    } catch (_error) {
      return rejectWithValue("Failed to load favorites.");
    }
  }
);

export const fetchFavoritesPage = createAsyncThunk(
  "favorites/fetchFavoritesPage",
  async ({ page = 1, limit = 10 }, { rejectWithValue }) => {
    try {
      const response = await favoritesApi.list(page, limit);
      return response.data;
    } catch (_error) {
      return rejectWithValue("Failed to load favorites.");
    }
  }
);

export const fetchHistory = createAsyncThunk(
  "favorites/fetchHistory",
  async (_, { rejectWithValue }) => {
    try {
      const response = await favoritesApi.history();
      return response.data;
    } catch (_error) {
      return rejectWithValue("Failed to load history.");
    }
  }
);

const favoritesSlice = createSlice({
  name: "favorites",
  initialState: {
    ids: [],
    isLoaded: false,
    paged: null,
    page: 1,
    limit: 10,
    listLoading: false,
    listError: "",
    history: null,
    historyLoading: false,
    historyError: "",
  },
  reducers: {
    resetFavorites(state) {
      state.ids = [];
      state.isLoaded = false;
      state.paged = null;
      state.page = 1;
      state.listLoading = false;
      state.listError = "";
      state.history = null;
      state.historyLoading = false;
      state.historyError = "";
    },
    optimisticToggleFavorite(state, action) {
      const restaurantId = action.payload;
      if (state.ids.includes(restaurantId)) {
        state.ids = state.ids.filter((id) => id !== restaurantId);
      } else {
        state.ids = [...state.ids, restaurantId];
      }
    },
    rollbackToggleFavorite(state, action) {
      const { restaurantId, wasFavorited } = action.payload;
      const exists = state.ids.includes(restaurantId);
      if (wasFavorited && !exists) {
        state.ids = [...state.ids, restaurantId];
      }
      if (!wasFavorited && exists) {
        state.ids = state.ids.filter((id) => id !== restaurantId);
      }
    },
    setFavoritesPage(state, action) {
      state.page = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadFavorites.fulfilled, (state, action) => {
        state.ids = action.payload.map((restaurant) => restaurant.id);
        state.isLoaded = true;
      })
      .addCase(loadFavorites.rejected, (state) => {
        state.isLoaded = true;
      })
      .addCase(fetchFavoritesPage.pending, (state) => {
        state.listLoading = true;
        state.listError = "";
      })
      .addCase(fetchFavoritesPage.fulfilled, (state, action) => {
        state.listLoading = false;
        state.paged = action.payload;
        state.page = action.payload.page || state.page;
      })
      .addCase(fetchFavoritesPage.rejected, (state, action) => {
        state.listLoading = false;
        state.listError = action.payload || "Failed to load favorites.";
      })
      .addCase(fetchHistory.pending, (state) => {
        state.historyLoading = true;
        state.historyError = "";
      })
      .addCase(fetchHistory.fulfilled, (state, action) => {
        state.historyLoading = false;
        state.history = action.payload;
      })
      .addCase(fetchHistory.rejected, (state, action) => {
        state.historyLoading = false;
        state.historyError = action.payload || "Failed to load history.";
      });
  },
});

export const {
  resetFavorites,
  optimisticToggleFavorite,
  rollbackToggleFavorite,
  setFavoritesPage,
} = favoritesSlice.actions;
export default favoritesSlice.reducer;
