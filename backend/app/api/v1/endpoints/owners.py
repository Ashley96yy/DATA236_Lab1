from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_owner
from app.db.session import get_db
from app.models.owner import Owner
from app.schemas.auth import AuthOwnerResponse
from app.schemas.owner import OwnerProfileResponse, OwnerProfileUpdate
from app.services import owner_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/owners", tags=["owners"])


@router.get("/me", response_model=AuthOwnerResponse)
def get_owner_me(current_owner: Annotated[Owner, Depends(get_current_owner)]) -> AuthOwnerResponse:
    return AuthOwnerResponse.model_validate(current_owner)


@router.put("/me", response_model=OwnerProfileResponse, summary="Update owner profile")
def update_owner_me(
    payload: OwnerProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_owner: Annotated[Owner, Depends(get_current_owner)],
) -> OwnerProfileResponse:
    return owner_service.update_owner_profile(db, current_owner, payload)
