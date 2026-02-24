import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { ownerApi } from "../services/api";

export const OWNER_TOKEN_KEY = "yelp_lab1_owner_token";
const OWNER_PROFILE_KEY = "yelp_lab1_owner";

const OwnerAuthContext = createContext(null);

function getStoredOwner() {
  const raw = localStorage.getItem(OWNER_PROFILE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(OWNER_PROFILE_KEY);
    return null;
  }
}

export function OwnerAuthProvider({ children }) {
  const [ownerToken, setOwnerToken] = useState(
    () => localStorage.getItem(OWNER_TOKEN_KEY) || ""
  );
  const [owner, setOwner] = useState(() => getStoredOwner());
  const [isOwnerAuthReady, setIsOwnerAuthReady] = useState(false);

  const clearOwnerSession = () => {
    setOwnerToken("");
    setOwner(null);
    localStorage.removeItem(OWNER_TOKEN_KEY);
    localStorage.removeItem(OWNER_PROFILE_KEY);
  };

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      if (!ownerToken) {
        if (active) {
          setOwner(null);
          setIsOwnerAuthReady(true);
        }
        return;
      }
      try {
        const resp = await ownerApi.get("/owners/me");
        if (!active) return;
        setOwner(resp.data);
        localStorage.setItem(OWNER_PROFILE_KEY, JSON.stringify(resp.data));
      } catch {
        if (active) clearOwnerSession();
      } finally {
        if (active) setIsOwnerAuthReady(true);
      }
    }

    bootstrap();
    return () => {
      active = false;
    };
  }, [ownerToken]);

  const ownerLogin = ({ accessToken, owner: ownerInfo }) => {
    setOwnerToken(accessToken);
    setOwner(ownerInfo);
    localStorage.setItem(OWNER_TOKEN_KEY, accessToken);
    localStorage.setItem(OWNER_PROFILE_KEY, JSON.stringify(ownerInfo));
  };

  const ownerLogout = () => {
    clearOwnerSession();
  };

  const refreshCurrentOwner = async () => {
    const resp = await ownerApi.get("/owners/me");
    setOwner(resp.data);
    localStorage.setItem(OWNER_PROFILE_KEY, JSON.stringify(resp.data));
    return resp.data;
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
