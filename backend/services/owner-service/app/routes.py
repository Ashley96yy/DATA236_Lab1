from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.deps import get_current_owner
from app.repository import (
    claim_restaurant,
    create_owner,
    get_owner_by_email,
    get_owner_dashboard,
    get_restaurant_by_id,
    update_owner_profile,
)
from app.schemas import (
    ClaimRestaurantResponse,
    OwnerDashboardResponse,
    OwnerLoginResponse,
    OwnerProfileUpdateRequest,
    OwnerResponse,
    OwnerSignupRequest,
)
from shared.auth.security import create_access_token, verify_password
from shared.db.session_store import build_session_document, store_session
from shared.schemas import LoginRequest
from shared.utils import conflict, not_found, unauthorized

router = APIRouter()


def _serialize_owner(owner: dict) -> OwnerResponse:
    return OwnerResponse(
        id=int(owner["_id"]),
        name=owner["name"],
        email=owner["email"],
        restaurant_location=owner["restaurant_location"],
    )


@router.post("/auth/owner/signup", response_model=OwnerResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: OwnerSignupRequest) -> OwnerResponse:
    if get_owner_by_email(payload.email) is not None:
        raise conflict("Email already exists.")
    owner = create_owner(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        restaurant_location=payload.restaurant_location,
    )
    return _serialize_owner(owner)


@router.post("/auth/owner/login", response_model=OwnerLoginResponse)
def login(payload: LoginRequest) -> OwnerLoginResponse:
    owner = get_owner_by_email(payload.email)
    if owner is None or not verify_password(payload.password, owner["password_hash"]):
        raise unauthorized("Invalid email or password.")
    token = create_access_token(subject=str(owner["_id"]), token_type="owner")
    store_session(build_session_document(subject_id=int(owner["_id"]), role="owner", token=token))
    return OwnerLoginResponse(access_token=token, owner=_serialize_owner(owner))


@router.post("/auth/owner/token", response_model=OwnerLoginResponse, include_in_schema=False)
def login_token(form_data: OAuth2PasswordRequestForm = Depends()) -> OwnerLoginResponse:
    return login(LoginRequest(email=form_data.username, password=form_data.password))


@router.get("/owners/me", response_model=OwnerResponse)
def read_me(current_owner: dict = Depends(get_current_owner)) -> OwnerResponse:
    return _serialize_owner(current_owner)


@router.put("/owners/me", response_model=OwnerResponse)
def update_me(
    payload: OwnerProfileUpdateRequest,
    current_owner: dict = Depends(get_current_owner),
) -> OwnerResponse:
    owner = update_owner_profile(int(current_owner["_id"]), payload.model_dump(exclude_none=True))
    return _serialize_owner(owner)


@router.get("/owner/dashboard", response_model=OwnerDashboardResponse)
def dashboard(current_owner: dict = Depends(get_current_owner)) -> OwnerDashboardResponse:
    return OwnerDashboardResponse(**get_owner_dashboard(int(current_owner["_id"])))


@router.post("/owner/restaurants/{restaurant_id}/claim", response_model=ClaimRestaurantResponse)
def claim(
    restaurant_id: int,
    current_owner: dict = Depends(get_current_owner),
) -> ClaimRestaurantResponse:
    restaurant = get_restaurant_by_id(restaurant_id)
    if restaurant is None:
        raise not_found("Restaurant not found.")
    if restaurant.get("claimed_by_owner_id") is not None:
        raise conflict("Restaurant is already claimed.")
    claim_restaurant(int(current_owner["_id"]), restaurant_id)
    return ClaimRestaurantResponse(
        restaurant_id=restaurant_id,
        claimed_by_owner_id=int(current_owner["_id"]),
    )
