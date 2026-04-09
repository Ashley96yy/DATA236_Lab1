import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import api, { extractApiError } from "../../services/api";

const DEFAULT_FILTERS = {
  name: "",
  cuisine: "",
  keywords: "",
  city: "",
  zip: "",
  sort: "name",
};

export const fetchRestaurants = createAsyncThunk(
  "restaurants/fetchRestaurants",
  async ({ filters, page, limit = 12 }, { rejectWithValue }) => {
    try {
      const params = { page, limit };
      if (filters.name) params.name = filters.name;
      if (filters.cuisine) params.cuisine = filters.cuisine;
      if (filters.keywords) params.keywords = filters.keywords;
      if (filters.city) params.city = filters.city;
      if (filters.zip) params.zip = filters.zip;
      if (filters.sort) params.sort = filters.sort;

      const response = await api.get("/restaurants", { params });
      return response.data;
    } catch (error) {
      return rejectWithValue(extractApiError(error, "Failed to load restaurants."));
    }
  }
);

export const fetchRestaurantDetail = createAsyncThunk(
  "restaurants/fetchRestaurantDetail",
  async (restaurantId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/restaurants/${restaurantId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(extractApiError(error, "Failed to load restaurant."));
    }
  }
);

const restaurantSlice = createSlice({
  name: "restaurants",
  initialState: {
    filters: DEFAULT_FILTERS,
    page: 1,
    results: null,
    loadingList: false,
    listError: "",
    selectedRestaurant: null,
    loadingDetail: false,
    detailError: "",
  },
  reducers: {
    setRestaurantFilter(state, action) {
      const { key, value } = action.payload;
      state.filters[key] = value;
      state.page = 1;
    },
    setRestaurantPage(state, action) {
      state.page = action.payload;
    },
    setSelectedRestaurant(state, action) {
      state.selectedRestaurant = action.payload;
    },
    clearSelectedRestaurant(state) {
      state.selectedRestaurant = null;
      state.detailError = "";
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRestaurants.pending, (state) => {
        state.loadingList = true;
        state.listError = "";
      })
      .addCase(fetchRestaurants.fulfilled, (state, action) => {
        state.loadingList = false;
        state.results = action.payload;
      })
      .addCase(fetchRestaurants.rejected, (state, action) => {
        state.loadingList = false;
        state.listError = action.payload || "Failed to load restaurants.";
        state.results = { items: [], total: 0, page: 1, limit: 12 };
      })
      .addCase(fetchRestaurantDetail.pending, (state) => {
        state.loadingDetail = true;
        state.detailError = "";
      })
      .addCase(fetchRestaurantDetail.fulfilled, (state, action) => {
        state.loadingDetail = false;
        state.selectedRestaurant = action.payload;
      })
      .addCase(fetchRestaurantDetail.rejected, (state, action) => {
        state.loadingDetail = false;
        state.detailError = action.payload || "Failed to load restaurant.";
      });
  },
});

export const {
  setRestaurantFilter,
  setRestaurantPage,
  setSelectedRestaurant,
  clearSelectedRestaurant,
} = restaurantSlice.actions;
export default restaurantSlice.reducer;
