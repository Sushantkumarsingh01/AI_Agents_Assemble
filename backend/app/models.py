from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
	pass

class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
	password_hash: Mapped[str] = mapped_column(String(255))
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

	conversations: Mapped[List[Conversation]] = relationship("Conversation", back_populates="user")

class Conversation(Base):
	__tablename__ = "conversations"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
	title: Mapped[str] = mapped_column(String(255), default="New Chat")
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

	user: Mapped[Optional[User]] = relationship("User", back_populates="conversations")
	messages: Mapped[List[ChatMessage]] = relationship(
		"ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.id"
	)

class ChatMessage(Base):
	__tablename__ = "messages"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
	role: Mapped[str] = mapped_column(String(16))  # user | assistant
	content: Mapped[str] = mapped_column(Text())
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

	conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")
	attachments: Mapped[List["MessageAttachment"]] = relationship(
		"MessageAttachment", back_populates="message", cascade="all, delete-orphan"
	)
	generated_image: Mapped[Optional["GeneratedImageRecord"]] = relationship(
		"GeneratedImageRecord", back_populates="message", cascade="all, delete-orphan", uselist=False
	)

class MessageAttachment(Base):
	__tablename__ = "message_attachments"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
	filename: Mapped[str] = mapped_column(String(255))
	mime_type: Mapped[str] = mapped_column(String(100))
	data: Mapped[bytes] = mapped_column(LargeBinary)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

	message: Mapped[ChatMessage] = relationship("ChatMessage", back_populates="attachments")

class GeneratedImageRecord(Base):
	__tablename__ = "generated_images"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), unique=True)
	prompt: Mapped[str] = mapped_column(String(500))
	image_url: Mapped[str] = mapped_column(String(500))
	image_data: Mapped[bytes] = mapped_column(LargeBinary)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

	message: Mapped[ChatMessage] = relationship("ChatMessage", back_populates="generated_image")

class CodebaseProject(Base):
	__tablename__ = "codebase_projects"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
	name: Mapped[str] = mapped_column(String(255))
	description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
	source_type: Mapped[str] = mapped_column(String(50))  # 'upload' or 'github'
	source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
	vector_store_id: Mapped[str] = mapped_column(String(255), unique=True)  # ChromaDB collection name
	file_count: Mapped[int] = mapped_column(Integer, default=0)
	total_chunks: Mapped[int] = mapped_column(Integer, default=0)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

	user: Mapped[User] = relationship("User", backref="codebase_projects") 