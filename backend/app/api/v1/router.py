from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.favorites import router as favorites_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.owners import router as owners_router
from app.api.v1.endpoints.restaurants import router as restaurants_router
from app.api.v1.endpoints.reviews import router as reviews_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(owners_router)
api_router.include_router(users_router)
api_router.include_router(restaurants_router)
api_router.include_router(reviews_router)
api_router.include_router(favorites_router)
