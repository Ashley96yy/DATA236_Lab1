import { createContext, useContext, useEffect, useMemo } from "react";

import { useAppDispatch, useAppSelector } from "../store/hooks";
import {
  bootstrapAuth,
  clearSession,
  markAuthReady,
  refreshCurrentUser as refreshCurrentUserThunk,
  setSession,
} from "../store/slices/authSlice";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const dispatch = useAppDispatch();
  const { token, user, isAuthReady } = useAppSelector((state) => state.auth);

  useEffect(() => {
    if (!token) {
      dispatch(markAuthReady());
      return;
    }
    dispatch(bootstrapAuth());
  }, [dispatch, token]);

  const login = ({ accessToken, user: userInfo }) => {
    dispatch(setSession({ token: accessToken, user: userInfo }));
  };

  const logout = () => {
    dispatch(clearSession());
  };

  const refreshCurrentUser = async () => {
    return dispatch(refreshCurrentUserThunk()).unwrap();
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
