from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import base64

from ..schemas import ChatRequest, ChatResponse, GeneratedImage
from ..services.llm import generate_reply
from ..services.image_gen import detect_image_generation_request, generate_image
from ..db import get_db
from ..models import Conversation, ChatMessage, User, MessageAttachment, GeneratedImageRecord
from .auth import get_current_user

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
	try:
		conversation = None
		if request.conversation_id:
			res = await db.execute(
				select(Conversation).where(Conversation.id == request.conversation_id, Conversation.user_id == user.id)
			)
			conversation = res.scalar_one_or_none()
		if conversation is None:
			conversation = Conversation(user_id=user.id)
			db.add(conversation)
			await db.commit()
			await db.refresh(conversation)

		# Check if user is requesting image generation
		generated_image = None
		last_user_message = request.messages[-1] if request.messages else None
		
		if last_user_message and last_user_message.role == "user":
			image_prompt = detect_image_generation_request(last_user_message.content)
			
			# Check if user has uploaded files - if so, they might want image analysis, not generation
			has_attachments = last_user_message.attachments and len(last_user_message.attachments) > 0
			
			if image_prompt and not has_attachments:
				# Pure image generation request (no files uploaded)
				print(f"[IMAGE GEN] Detected request: '{image_prompt}'")
				try:
					image_url, image_data = await generate_image(image_prompt)
					generated_image = GeneratedImage(
						prompt=image_prompt,
						image_url=image_url,
						image_data=image_data
					)
					assistant_reply = f"I've generated an image for you based on: '{image_prompt}'. You can download it using the button below!"
					print(f"[IMAGE GEN] Success! Image generated.")
				except Exception as img_error:
					print(f"[IMAGE GEN] Error: {str(img_error)}")
					assistant_reply = f"I understand you want me to generate an image of '{image_prompt}', but I encountered an error: {str(img_error)}. Please try again."
			elif image_prompt and has_attachments:
				# User uploaded image + wants generation (image-to-image scenario)
				print(f"[IMAGE GEN] Image-to-image request detected: '{image_prompt}' with {len(last_user_message.attachments)} attachment(s)")
				# For now, use the text prompt to generate a new image based on their description
				# In future, we could implement actual image-to-image transformation
				try:
					# Enhance the prompt with context from their message
					enhanced_prompt = f"{image_prompt} - architectural design concept"
					image_url, image_data = await generate_image(enhanced_prompt)
					generated_image = GeneratedImage(
						prompt=enhanced_prompt,
						image_url=image_url,
						image_data=image_data
					)
					assistant_reply = f"Based on your uploaded floor plan, I've generated a new architectural concept: '{enhanced_prompt}'. You can download it using the button below!"
					print(f"[IMAGE GEN] Success! Image-to-image generated.")
				except Exception as img_error:
					print(f"[IMAGE GEN] Error: {str(img_error)}")
					# Fall back to normal chat with image analysis
					assistant_reply = await generate_reply(request.messages)
			else:
				# Normal text response
				print(f"[CHAT] No image generation detected, using normal chat")
				assistant_reply = await generate_reply(request.messages)
		else:
			assistant_reply = await generate_reply(request.messages)

		# Persist the last user message and assistant reply
		if request.messages:
			last_user = request.messages[-1]
			if last_user.role == "user":
				msg = ChatMessage(conversation_id=conversation.id, role="user", content=last_user.content)
				db.add(msg)
				await db.flush()  # Get message ID
				
				# Save attachments to database
				if last_user.attachments:
					for attachment in last_user.attachments:
						# Decode base64 to bytes
						file_data = base64.b64decode(attachment.data)
						attachment_record = MessageAttachment(
							message_id=msg.id,
							filename=attachment.filename,
							mime_type=attachment.mime_type,
							data=file_data
						)
						db.add(attachment_record)
		assistant_msg = ChatMessage(conversation_id=conversation.id, role="assistant", content=assistant_reply)
		db.add(assistant_msg)
		await db.flush()  # Get assistant message ID
		
		# Save generated image to database if present
		if generated_image:
			image_data_bytes = base64.b64decode(generated_image.image_data)
			image_record = GeneratedImageRecord(
				message_id=assistant_msg.id,
				prompt=generated_image.prompt,
				image_url=generated_image.image_url,
				image_data=image_data_bytes
			)
			db.add(image_record)
		
		await db.commit()

		# Optionally set conversation title from first user message
		if conversation.title == "New Chat" and request.messages:
			first_user = next((m for m in request.messages if m.role == "user"), None)
			if first_user and first_user.content.strip():
				conversation.title = first_user.content.strip()[:40]
				await db.commit()

		return ChatResponse(reply=assistant_reply, conversation_id=conversation.id, generated_image=generated_image)
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(status_code=500, detail=str(exc)) 