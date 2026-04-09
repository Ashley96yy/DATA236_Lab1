from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer

from app.repository import get_owner_by_id
from app.repository import get_user_by_id
from shared.auth.security import decode_access_token
from shared.db.session_store import get_session_by_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _authenticate_token(token: str, allowed_types: set[str]) -> dict:
    unauthorized = _unauthorized()
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise unauthorized from exc

    token_type = payload.get("token_type")
    if token_type not in allowed_types:
        raise unauthorized

    session = get_session_by_token(token)
    if session is None or session.get("role") != token_type:
        raise unauthorized

    subject = payload.get("sub")
    if not subject:
        raise unauthorized

    try:
        actor_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise unauthorized from exc

    if token_type == "user":
        actor = get_user_by_id(actor_id)
    else:
        actor = get_owner_by_id(actor_id)
    if actor is None:
        raise unauthorized

    return {"id": actor_id, "role": token_type, "document": actor}


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    return _authenticate_token(token, {"user"})["document"]


def get_current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise _unauthorized()
    return _authenticate_token(credentials.credentials, {"user", "owner"})
