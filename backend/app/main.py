from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.chat import router as chat_router
from .routers.conversations import router as conversations_router
from .routers.auth import router as auth_router
from .routers.codebase import router as codebase_router
from .models import Base
from .db import engine

app = FastAPI(title="AI Chatbot API", version="1.0.0")

# CORS configuration
origins = [
	"http://localhost:5173",  # Vite default
	"http://127.0.0.1:5173",
	"http://localhost:3000",
	"http://127.0.0.1:3000",
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
	# Create tables automatically (simple bootstrap). For production, use migrations.
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health_check():
	return {"status": "ok"}

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(codebase_router, prefix="/api") 