import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import api from "../../services/api";

export const fetchRestaurantReviews = createAsyncThunk(
  "reviews/fetchRestaurantReviews",
  async ({ restaurantId, limit = 50 }, { rejectWithValue }) => {
    try {
      const response = await api.get(`/restaurants/${restaurantId}/reviews?limit=${limit}`);
      return {
        restaurantId,
        items: response.data.items || [],
        total: response.data.total || 0,
      };
    } catch (_error) {
      return rejectWithValue("Failed to load reviews.");
    }
  }
);

const reviewSlice = createSlice({
  name: "reviews",
  initialState: {
    restaurantId: null,
    items: [],
    total: 0,
    loading: false,
    error: "",
    mutationStatus: "idle",
    mutationMessage: "",
  },
  reducers: {
    clearReviewFeedback(state) {
      state.mutationStatus = "idle";
      state.mutationMessage = "";
      state.error = "";
    },
    setReviewFeedback(state, action) {
      state.mutationStatus = action.payload.status;
      state.mutationMessage = action.payload.message;
    },
    upsertReview(state, action) {
      const incoming = action.payload;
      const index = state.items.findIndex((item) => item.id === incoming.id);
      if (index >= 0) {
        state.items[index] = { ...state.items[index], ...incoming };
      } else {
        state.items.unshift(incoming);
      }
      state.total = state.items.length;
    },
    removeReview(state, action) {
      state.items = state.items.filter((item) => item.id !== action.payload);
      state.total = state.items.length;
    },
    replaceReviews(state, action) {
      state.items = action.payload.items || [];
      state.total = action.payload.total ?? state.items.length;
      if (action.payload.restaurantId !== undefined) {
        state.restaurantId = action.payload.restaurantId;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRestaurantReviews.pending, (state) => {
        state.loading = true;
        state.error = "";
      })
      .addCase(fetchRestaurantReviews.fulfilled, (state, action) => {
        state.loading = false;
        state.restaurantId = action.payload.restaurantId;
        state.items = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchRestaurantReviews.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to load reviews.";
      });
  },
});

export const {
  clearReviewFeedback,
  setReviewFeedback,
  upsertReview,
  removeReview,
  replaceReviews,
} = reviewSlice.actions;
export default reviewSlice.reducer;
