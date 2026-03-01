from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai_assistant import AIChatRequest, AIChatResponse
from app.services import ai_assistant_service
from app.services.errors import ServiceBadRequest

router = APIRouter(prefix="/ai-assistant", tags=["ai-assistant"])


@router.post("/chat", response_model=AIChatResponse, summary="Chat with the AI restaurant assistant")
def chat_with_ai_assistant(
    payload: AIChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AIChatResponse:
    try:
        return ai_assistant_service.generate_chat_response(
            db=db,
            user_id=current_user.id,
            message=payload.message,
            conversation_history=payload.conversation_history,
        )
    except ServiceBadRequest as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
