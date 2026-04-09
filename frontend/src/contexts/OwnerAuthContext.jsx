import { createContext, useContext, useEffect, useMemo } from "react";

import { OWNER_TOKEN_KEY } from "../services/api";
import { useAppDispatch, useAppSelector } from "../store/hooks";
import {
  bootstrapOwnerAuth,
  clearOwnerSession,
  markOwnerAuthReady,
  refreshCurrentOwner as refreshCurrentOwnerThunk,
  setOwnerSession,
} from "../store/slices/ownerAuthSlice";

const OwnerAuthContext = createContext(null);

export function OwnerAuthProvider({ children }) {
  const dispatch = useAppDispatch();
  const { ownerToken, owner, isOwnerAuthReady } = useAppSelector((state) => state.ownerAuth);

  useEffect(() => {
    if (!ownerToken) {
      dispatch(markOwnerAuthReady());
      return;
    }
    dispatch(bootstrapOwnerAuth());
  }, [dispatch, ownerToken]);

  const ownerLogin = ({ accessToken, owner: ownerInfo }) => {
    dispatch(setOwnerSession({ token: accessToken, owner: ownerInfo }));
  };

  const ownerLogout = () => {
    dispatch(clearOwnerSession());
  };

  const refreshCurrentOwner = async () => {
    return dispatch(refreshCurrentOwnerThunk()).unwrap();
  };

  const value = useMemo(
    () => ({
      ownerToken,
      owner,
      isOwnerAuthReady,
      isOwnerAuthenticated: Boolean(ownerToken),
      ownerLogin,
      ownerLogout,
      refreshCurrentOwner,
    }),
    [ownerToken, owner, isOwnerAuthReady]
  );

  return (
    <OwnerAuthContext.Provider value={value}>
      {children}
    </OwnerAuthContext.Provider>
  );
}

export function useOwnerAuth() {
  const ctx = useContext(OwnerAuthContext);
  if (!ctx) throw new Error("useOwnerAuth must be inside OwnerAuthProvider");
  return ctx;
}
