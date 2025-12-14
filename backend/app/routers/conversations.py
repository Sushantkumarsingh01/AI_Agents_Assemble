from typing import List
import base64

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_db
from ..models import Conversation, ChatMessage, User, MessageAttachment, GeneratedImageRecord
from ..schemas import ConversationOut, ChatMessageOut, FileAttachment, GeneratedImage
from .auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("", response_model=ConversationOut)
async def create_conversation(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    conv = Conversation(user_id=user.id)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv

@router.get("", response_model=List[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.id.desc())
    )
    return list(result.scalars())

@router.get("/{conversation_id}/messages", response_model=List[ChatMessageOut])
async def get_messages(conversation_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Load messages with attachments and generated images
    result = await db.execute(
        select(ChatMessage)
        .options(
            selectinload(ChatMessage.attachments),
            selectinload(ChatMessage.generated_image)
        )
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.id.asc())
    )
    messages = list(result.scalars())
    
    # Convert to response format with attachments and generated images
    message_outs = []
    for msg in messages:
        attachments_list = None
        if msg.attachments:
            attachments_list = [
                FileAttachment(
                    filename=att.filename,
                    mime_type=att.mime_type,
                    data=base64.b64encode(att.data).decode('utf-8')
                )
                for att in msg.attachments
            ]
        
        generated_image = None
        if msg.generated_image:
            generated_image = GeneratedImage(
                prompt=msg.generated_image.prompt,
                image_url=msg.generated_image.image_url,
                image_data=base64.b64encode(msg.generated_image.image_data).decode('utf-8')
            )
        
        message_outs.append(
            ChatMessageOut(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                attachments=attachments_list,
                generated_image=generated_image
            )
        )
    
    return message_outs

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.commit()
    return {"status": "deleted"} 