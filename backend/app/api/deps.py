from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.owner import Owner
from app.models.user import User

oauth2_scheme_user = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/user/login")
oauth2_scheme_owner = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/owner/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise unauthorized_exception from exc

    token_type = payload.get("token_type", "user")
    if token_type != "user":
        raise unauthorized_exception

    subject = payload.get("sub")
    if not subject:
        raise unauthorized_exception

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise unauthorized_exception from exc

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise unauthorized_exception
    return user


def get_current_owner(
    token: Annotated[str, Depends(oauth2_scheme_owner)],
    db: Annotated[Session, Depends(get_db)],
) -> Owner:
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise unauthorized_exception from exc

    token_type = payload.get("token_type")
    if token_type != "owner":
        raise unauthorized_exception

    subject = payload.get("sub")
    if not subject:
        raise unauthorized_exception

    try:
        owner_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise unauthorized_exception from exc

    owner = db.execute(select(Owner).where(Owner.id == owner_id)).scalar_one_or_none()
    if owner is None:
        raise unauthorized_exception
    return owner
