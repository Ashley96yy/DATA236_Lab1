import { createContext, useContext, useEffect, useState } from "react";

import { favoritesApi } from "../services/api";
import { useAuth } from "./AuthContext";

const FavoritesContext = createContext(null);

/**
 * Loads all favorited restaurant IDs on login and exposes:
 *   isFavorited(id)  — boolean
 *   toggle(id)       — optimistic add/remove with rollback on error
 *   isLoaded         — true once the initial fetch has completed
 */
export function FavoritesProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [favoriteIds, setFavoriteIds] = useState(new Set());
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setFavoriteIds(new Set());
      setIsLoaded(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        // Fetch up to 100 favorites (backend max per request)
        const resp = await favoritesApi.list(1, 100);
        if (!cancelled) {
          setFavoriteIds(new Set(resp.data.items.map((r) => r.id)));
        }
      } catch {
        // Non-blocking: user just won't see heart state until retry
      } finally {
        if (!cancelled) setIsLoaded(true);
      }
    })();
    return () => { cancelled = true; };
  }, [isAuthenticated]);

  async function toggle(restaurantId) {
    const wasFavorited = favoriteIds.has(restaurantId);

    // Optimistic update
    setFavoriteIds((prev) => {
      const next = new Set(prev);
      if (wasFavorited) next.delete(restaurantId);
      else next.add(restaurantId);
      return next;
    });

    try {
      if (wasFavorited) {
        await favoritesApi.remove(restaurantId);
      } else {
        await favoritesApi.add(restaurantId);
      }
    } catch {
      // Rollback on error
      setFavoriteIds((prev) => {
        const next = new Set(prev);
        if (wasFavorited) next.add(restaurantId);
        else next.delete(restaurantId);
        return next;
      });
    }
  }

  function isFavorited(restaurantId) {
    return favoriteIds.has(restaurantId);
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
