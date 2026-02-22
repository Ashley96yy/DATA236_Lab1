from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_owner
from app.models.owner import Owner
from app.schemas.auth import AuthOwnerResponse

router = APIRouter(prefix="/owners", tags=["owners"])


@router.get("/me", response_model=AuthOwnerResponse)
def get_owner_me(current_owner: Annotated[Owner, Depends(get_current_owner)]) -> AuthOwnerResponse:
    return AuthOwnerResponse.model_validate(current_owner)
