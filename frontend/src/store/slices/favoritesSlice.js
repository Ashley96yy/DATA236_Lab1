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

const favoritesSlice = createSlice({
  name: "favorites",
  initialState: {
    ids: [],
    isLoaded: false,
  },
  reducers: {
    resetFavorites(state) {
      state.ids = [];
      state.isLoaded = false;
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
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadFavorites.fulfilled, (state, action) => {
        state.ids = action.payload.map((restaurant) => restaurant.id);
        state.isLoaded = true;
      })
      .addCase(loadFavorites.rejected, (state) => {
        state.isLoaded = true;
      });
  },
});

export const { resetFavorites, optimisticToggleFavorite, rollbackToggleFavorite } =
  favoritesSlice.actions;
export default favoritesSlice.reducer;
