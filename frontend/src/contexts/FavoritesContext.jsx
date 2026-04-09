import { createContext, useContext, useEffect } from "react";

import { favoritesApi } from "../services/api";
import { useAuth } from "./AuthContext";
import { useAppDispatch, useAppSelector } from "../store/hooks";
import {
  loadFavorites,
  optimisticToggleFavorite,
  resetFavorites,
  rollbackToggleFavorite,
} from "../store/slices/favoritesSlice";

const FavoritesContext = createContext(null);

/**
 * Loads all favorited restaurant IDs on login and exposes:
 *   isFavorited(id)  — boolean
 *   toggle(id)       — optimistic add/remove with rollback on error
 *   isLoaded         — true once the initial fetch has completed
 */
export function FavoritesProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const dispatch = useAppDispatch();
  const favoriteIds = useAppSelector((state) => state.favorites.ids);
  const isLoaded = useAppSelector((state) => state.favorites.isLoaded);

  useEffect(() => {
    if (!isAuthenticated) {
      dispatch(resetFavorites());
      return;
    }
    dispatch(loadFavorites());
  }, [dispatch, isAuthenticated]);

  async function toggle(restaurantId) {
    const wasFavorited = favoriteIds.includes(restaurantId);
    dispatch(optimisticToggleFavorite(restaurantId));

    try {
      if (wasFavorited) {
        await favoritesApi.remove(restaurantId);
      } else {
        await favoritesApi.add(restaurantId);
      }
    } catch {
      dispatch(rollbackToggleFavorite({ restaurantId, wasFavorited }));
    }
  }

  function isFavorited(restaurantId) {
    return favoriteIds.includes(restaurantId);
  }

  return (
    <FavoritesContext.Provider value={{ isFavorited, toggle, isLoaded }}>
      {children}
    </FavoritesContext.Provider>
  );
}

export function useFavorites() {
  const ctx = useContext(FavoritesContext);
  if (!ctx) throw new Error("useFavorites must be used inside FavoritesProvider");
  return ctx;
}
