import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import api, { extractApiError } from "../../services/api";

const EMPTY_FORM = {
  cuisines: [],
  price_range: "",
  location: "",
  search_radius_km: "",
  dietary_needs: [],
  ambiance: [],
  sort_preference: "rating",
};

function preferencesToForm(data) {
  const firstLocation = Array.isArray(data?.preferred_locations)
    ? data.preferred_locations[0] || ""
    : "";

  return {
    cuisines: Array.isArray(data?.cuisines) ? data.cuisines : [],
    price_range: data?.price_range || "",
    location: firstLocation,
    search_radius_km: data?.search_radius_km ?? "",
    dietary_needs: Array.isArray(data?.dietary_needs) ? data.dietary_needs : [],
    ambiance: Array.isArray(data?.ambiance) ? data.ambiance : [],
    sort_preference: data?.sort_preference || "rating",
  };
}

export const fetchPreferences = createAsyncThunk(
  "preferences/fetchPreferences",
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get("/users/me/preferences");
      return preferencesToForm(response.data);
    } catch (error) {
      return rejectWithValue(extractApiError(error, "Failed to load preferences."));
    }
  }
);

export const savePreferences = createAsyncThunk(
  "preferences/savePreferences",
  async (form, { rejectWithValue }) => {
    const payload = {
      cuisines: form.cuisines,
      price_range: form.price_range || null,
      preferred_locations: form.location.trim() ? [form.location.trim()] : [],
      search_radius_km:
        form.search_radius_km === "" ? null : Number.parseInt(form.search_radius_km, 10),
      dietary_needs: form.dietary_needs,
      ambiance: form.ambiance,
      sort_preference: form.sort_preference || "rating",
    };

    try {
      const response = await api.put("/users/me/preferences", payload);
      return preferencesToForm(response.data);
    } catch (error) {
      return rejectWithValue(extractApiError(error, "Failed to update preferences."));
    }
  }
);

const preferencesSlice = createSlice({
  name: "preferences",
  initialState: {
    form: EMPTY_FORM,
    loading: true,
    saving: false,
    error: "",
    success: "",
  },
  reducers: {
    setPreferenceField(state, action) {
      const { name, value } = action.payload;
      state.form[name] = value;
    },
    togglePreferenceValue(state, action) {
      const { fieldName, optionValue } = action.payload;
      const currentValues = state.form[fieldName] || [];
      const exists = currentValues.includes(optionValue);
      state.form[fieldName] = exists
        ? currentValues.filter((value) => value !== optionValue)
        : [...currentValues, optionValue];
    },
    clearPreferenceFeedback(state) {
      state.error = "";
      state.success = "";
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPreferences.pending, (state) => {
        state.loading = true;
        state.error = "";
      })
      .addCase(fetchPreferences.fulfilled, (state, action) => {
        state.loading = false;
        state.form = action.payload;
      })
      .addCase(fetchPreferences.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to load preferences.";
      })
      .addCase(savePreferences.pending, (state) => {
        state.saving = true;
        state.error = "";
        state.success = "";
      })
      .addCase(savePreferences.fulfilled, (state, action) => {
        state.saving = false;
        state.form = action.payload;
        state.success = "Preferences updated.";
      })
      .addCase(savePreferences.rejected, (state, action) => {
        state.saving = false;
        state.error = action.payload || "Failed to update preferences.";
      });
  },
});

export const { setPreferenceField, togglePreferenceValue, clearPreferenceFeedback } =
  preferencesSlice.actions;
export default preferencesSlice.reducer;
