from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.repository import get_user_by_id
from shared.auth.security import decode_access_token
from shared.db.session_store import get_session_by_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise unauthorized from exc

    if payload.get("token_type") != "user":
        raise unauthorized

    session = get_session_by_token(token)
    if session is None:
        raise unauthorized

    subject = payload.get("sub")
    if not subject:
        raise unauthorized

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise unauthorized from exc

    user = get_user_by_id(user_id)
    if user is None:
        raise unauthorized
    return user
