import { configureStore } from "@reduxjs/toolkit";

import authReducer from "./slices/authSlice";
import favoritesReducer from "./slices/favoritesSlice";
import restaurantReducer from "./slices/restaurantSlice";
import reviewReducer from "./slices/reviewSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    favorites: favoritesReducer,
    restaurants: restaurantReducer,
    reviews: reviewReducer,
  },
});

export default store;
