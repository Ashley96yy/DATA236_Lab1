import { createContext, useContext, useEffect, useMemo, useState } from "react";

import api, { TOKEN_KEY } from "../services/api";

const USER_KEY = "yelp_lab1_user";
const AuthContext = createContext(null);

function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (_error) {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(() => getStoredUser());
  const [isAuthReady, setIsAuthReady] = useState(false);

  const clearSessionState = () => {
    setToken("");
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  useEffect(() => {
    let active = true;

    async function bootstrapAuth() {
      if (!token) {
        if (active) {
          setUser(null);
          setIsAuthReady(true);
        }
        return;
      }

      try {
        const response = await api.get("/auth/me");
        if (!active) {
          return;
        }
        setUser(response.data);
        localStorage.setItem(USER_KEY, JSON.stringify(response.data));
      } catch (_error) {
        if (active) {
          clearSessionState();
        }
      } finally {
        if (active) {
          setIsAuthReady(true);
        }
      }
    }

    bootstrapAuth();
    return () => {
      active = false;
    };
  }, [token]);

  const login = ({ accessToken, user: userInfo }) => {
    setToken(accessToken);
    setUser(userInfo);
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo));
  };

  const logout = () => {
    clearSessionState();
  };

  const refreshCurrentUser = async () => {
    const response = await api.get("/auth/me");
    setUser(response.data);
    localStorage.setItem(USER_KEY, JSON.stringify(response.data));
    return response.data;
  };

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthReady,
      isAuthenticated: Boolean(token),
      login,
      logout,
      refreshCurrentUser
    }),
    [token, user, isAuthReady]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}
