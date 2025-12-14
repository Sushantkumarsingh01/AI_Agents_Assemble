import os
import base64
from pathlib import Path
from typing import List

import google.generativeai as genai
from dotenv import load_dotenv

from fastapi import HTTPException

from ..schemas import Message

# Load env from backend/env/.env or backend/.env if present
_THIS_FILE = Path(__file__).resolve()
_BACKEND_DIR = _THIS_FILE.parents[2]  # .../backend
_ENV_DIR_FILE = _BACKEND_DIR / "env" / ".env"
_ROOT_ENV_FILE = _BACKEND_DIR / ".env"

for candidate in (_ENV_DIR_FILE, _ROOT_ENV_FILE):
	if candidate.exists():
		load_dotenv(dotenv_path=candidate, override=False)

# Read API key from env
# Place your Gemini API key in backend/env/.env as:
# GEMINI_API_KEY=your_key_here
_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

_SYSTEM_PROMPT = (
    "You are a highly capable, humble, and extremely helpful AI assistant with full conversation memory. "
    "You have access to the entire conversation history and can recall everything discussed in this chat. "
    "When users reference previous topics with phrases like 'as we discussed', 'you mentioned earlier', "
    "'remember when', or 'what did we talk about', acknowledge that you remember and provide relevant context. "
    "Your primary goal is to ensure that every user query is answered. "
    "If you cannot provide a direct answer, find an indirect way: "
    "use reasoning, general knowledge, related insights, logical deduction, or creative problem-solving "
    "to still provide a meaningful and helpful response. "
    "Never leave a question unanswered. "
    "If the question is unclear, politely ask clarifying questions and still attempt a partial answer. "
    "If information is missing, state the limitation clearly but try your best to infer, approximate, or guide the user. "
    "Always maintain a polite, respectful, and supportive tone. "
    "Keep explanations clear, complete, and accessible. "
    "When useful, provide step-by-step reasoning, structured breakdowns, or examples. "
    "When asked to summarize the conversation, provide a comprehensive summary of all topics discussed. "
    "Do not refuse unless absolutely required (e.g., harmful, unsafe, or disallowed content). "
    "Be concise but avoid being superficial—your answers must feel thoughtful and reliable. "
    "Remember: never let a user feel ignored or left without some form of answer."
)


# Configure the model lazily to surface clear errors when key is missing
_MODEL_NAME = "gemini-flash-latest"

async def generate_reply(messages: List[Message]) -> str:
    """Generate a reply from Gemini given the conversation messages."""
    if not _GEMINI_API_KEY:
        return (
            "I am ready to chat, but the server is missing the Gemini API key. "
            "Please add it in backend/env/.env as GEMINI_API_KEY=YOUR_KEY and restart the server."
        )

    try:
        genai.configure(api_key=_GEMINI_API_KEY)
        model = genai.GenerativeModel(_MODEL_NAME, system_instruction=_SYSTEM_PROMPT)

        history = []
        for m in messages:
            role = m.role
            # Convert OpenAI-style roles to Gemini-compatible roles
            if role == "assistant":
                role = "model"
            elif role == "system":
                role = "user"

            # Build parts for this message
            parts = []
            
            # Add text content
            if m.content:
                parts.append(m.content)
            
            # Add file attachments (images/PDFs)
            if m.attachments:
                for attachment in m.attachments:
                    try:
                        # Decode base64 data
                        file_data = base64.b64decode(attachment.data)
                        
                        # Create inline data for Gemini
                        inline_data = {
                            "mime_type": attachment.mime_type,
                            "data": file_data
                        }
                        parts.append(inline_data)
                    except Exception as e:
                        print(f"Error processing attachment {attachment.filename}: {e}")
                        continue

            if parts:
                history.append({"role": role, "parts": parts})

        response = await model.generate_content_async(history)
        text = (response.text or "").strip()
        if not text:
            return "I'm sorry, I couldn't generate a response just now. Please try again."
        return text
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {exc}")
