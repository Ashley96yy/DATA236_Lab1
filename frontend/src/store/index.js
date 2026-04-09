import { configureStore } from "@reduxjs/toolkit";

import authReducer from "./slices/authSlice";
import favoritesReducer from "./slices/favoritesSlice";
import ownerAuthReducer from "./slices/ownerAuthSlice";
import preferencesReducer from "./slices/preferencesSlice";
import restaurantReducer from "./slices/restaurantSlice";
import reviewReducer from "./slices/reviewSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    favorites: favoritesReducer,
    ownerAuth: ownerAuthReducer,
    preferences: preferencesReducer,
    restaurants: restaurantReducer,
    reviews: reviewReducer,
  },
});

export default store;
