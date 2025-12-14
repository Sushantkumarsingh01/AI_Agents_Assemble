from typing import List, Literal, Optional
from pydantic import BaseModel, Field, EmailStr

Role = Literal["user", "assistant", "system"]

class FileAttachment(BaseModel):
	filename: str
	mime_type: str
	data: str  # base64 encoded

class Message(BaseModel):
	role: Role = Field(..., description="Message role: user, assistant, or system")
	content: str = Field(..., description="Message content")
	attachments: Optional[List[FileAttachment]] = Field(None, description="Optional file attachments")

class ChatRequest(BaseModel):
	messages: List[Message] = Field(..., description="Conversation history including the newest user message")
	conversation_id: Optional[int] = Field(None, description="Existing conversation id to append to")

class GeneratedImage(BaseModel):
	prompt: str = Field(..., description="The prompt used to generate the image")
	image_url: str = Field(..., description="URL or identifier for the generated image")
	image_data: str = Field(..., description="Base64 encoded image data")

class ChatResponse(BaseModel):
	reply: str = Field(..., description="Assistant reply text")
	conversation_id: Optional[int] = Field(None, description="Conversation id used for this reply")
	generated_image: Optional[GeneratedImage] = Field(None, description="Generated image if requested")

class ConversationOut(BaseModel):
	id: int
	title: str

	class Config:
		from_attributes = True

class ChatMessageOut(BaseModel):
	id: int
	conversation_id: int
	role: Literal["user", "assistant"]
	content: str
	attachments: Optional[List[FileAttachment]] = None
	generated_image: Optional[GeneratedImage] = None

	class Config:
		from_attributes = True

# Auth schemas
class SignupRequest(BaseModel):
	email: EmailStr
	password: str

class LoginRequest(BaseModel):
	email: EmailStr
	password: str

class TokenResponse(BaseModel):
	access_token: str
	token_type: str = "bearer"

# Codebase Analysis schemas
class CodebaseUploadResponse(BaseModel):
	project_id: int
	name: str
	file_count: int
	total_chunks: int
	message: str

class CodebaseProjectOut(BaseModel):
	id: int
	name: str
	description: Optional[str]
	source_type: str
	source_url: Optional[str]
	file_count: int
	total_chunks: int
	created_at: str

	class Config:
		from_attributes = True

class ChatHistoryMessage(BaseModel):
	role: str
	content: str
	timestamp: str

class CodebaseAnalysisRequest(BaseModel):
	project_id: int
	question: str
	conversation_id: Optional[int] = None
	chat_history: List[ChatHistoryMessage] = Field(default_factory=list)

class CodebaseAnalysisResponse(BaseModel):
	reply: str
	relevant_files: List[str] = Field(default_factory=list, description="Files referenced in the analysis")
	conversation_id: Optional[int] = None 