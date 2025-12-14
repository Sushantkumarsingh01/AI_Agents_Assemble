import tempfile
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from .auth import get_current_user
from ..models import User, CodebaseProject, Conversation, ChatMessage
from ..schemas import (
    CodebaseUploadResponse,
    CodebaseProjectOut,
    CodebaseAnalysisRequest,
    CodebaseAnalysisResponse
)
from ..services.codebase_ingestion import get_ingestion_service
from ..services.vector_store import VectorStore, create_collection_name
from ..services.rag_agent import create_rag_agent

router = APIRouter(tags=["codebase"])


@router.post("/codebase/upload", response_model=CodebaseUploadResponse)
async def upload_codebase(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a codebase ZIP file for analysis.
    """
    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = Path(temp_file.name)
    
    try:
        # Ingest codebase
        ingestion_service = get_ingestion_service()
        chunks, metadatas, ids = ingestion_service.ingest_from_zip(temp_path)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No processable code files found in the ZIP")
        
        # Create vector store collection
        collection_name = create_collection_name(current_user.id, name)
        vector_store = VectorStore(collection_name)
        
        # Add documents to vector store
        vector_store.add_documents(chunks, metadatas, ids)
        
        # Count unique files
        unique_files = set(meta['file_path'] for meta in metadatas)
        file_count = len(unique_files)
        
        # Create database record
        project = CodebaseProject(
            user_id=current_user.id,
            name=name,
            description=description,
            source_type='upload',
            vector_store_id=collection_name,
            file_count=file_count,
            total_chunks=len(chunks)
        )
        
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
        return CodebaseUploadResponse(
            project_id=project.id,
            name=project.name,
            file_count=file_count,
            total_chunks=len(chunks),
            message=f"Successfully processed {file_count} files into {len(chunks)} chunks"
        )
        
    finally:
        # Clean up temp file
        temp_path.unlink(missing_ok=True)


@router.post("/codebase/github", response_model=CodebaseUploadResponse)
async def clone_github_repo(
    repo_url: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clone and analyze a GitHub repository.
    """
    try:
        # Ingest codebase from GitHub
        ingestion_service = get_ingestion_service()
        chunks, metadatas, ids = ingestion_service.ingest_from_github(repo_url)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No processable code files found in the repository")
        
        # Create vector store collection
        collection_name = create_collection_name(current_user.id, name)
        vector_store = VectorStore(collection_name)
        
        # Add documents to vector store
        vector_store.add_documents(chunks, metadatas, ids)
        
        # Count unique files
        unique_files = set(meta['file_path'] for meta in metadatas)
        file_count = len(unique_files)
        
        # Create database record
        project = CodebaseProject(
            user_id=current_user.id,
            name=name,
            description=description,
            source_type='github',
            source_url=repo_url,
            vector_store_id=collection_name,
            file_count=file_count,
            total_chunks=len(chunks)
        )
        
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
        return CodebaseUploadResponse(
            project_id=project.id,
            name=project.name,
            file_count=file_count,
            total_chunks=len(chunks),
            message=f"Successfully cloned and processed {file_count} files into {len(chunks)} chunks"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/codebase/projects", response_model=List[CodebaseProjectOut])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all codebase projects for the current user.
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(CodebaseProject)
        .where(CodebaseProject.user_id == current_user.id)
        .order_by(CodebaseProject.created_at.desc())
    )
    projects = result.scalars().all()
    
    return [
        CodebaseProjectOut(
            id=p.id,
            name=p.name,
            description=p.description,
            source_type=p.source_type,
            source_url=p.source_url,
            file_count=p.file_count,
            total_chunks=p.total_chunks,
            created_at=p.created_at.isoformat()
        )
        for p in projects
    ]


@router.delete("/codebase/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a codebase project and its vector store.
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(CodebaseProject).where(
            CodebaseProject.id == project_id,
            CodebaseProject.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete vector store
    vector_store = VectorStore(project.vector_store_id)
    vector_store.delete_collection()
    
    # Delete database record
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted successfully"}


@router.post("/codebase/analyze", response_model=CodebaseAnalysisResponse)
async def analyze_codebase(
    request: CodebaseAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question about a codebase using RAG-based analysis.
    """
    from sqlalchemy import select
    
    # Get project
    result = await db.execute(
        select(CodebaseProject).where(
            CodebaseProject.id == request.project_id,
            CodebaseProject.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create RAG agent
    vector_store = VectorStore(project.vector_store_id)
    agent = create_rag_agent(vector_store)
    
    # Build chat history for context
    chat_context = []
    if request.chat_history:
        for msg in request.chat_history:
            chat_context.append({
                "role": msg.role,
                "content": msg.content
            })
    
    # Analyze question with chat history
    result = await agent.analyze(request.question, chat_history=chat_context)
    
    # Optionally save to conversation
    conversation_id = request.conversation_id
    if conversation_id:
        # Verify conversation belongs to user
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            )
        )
        conversation = conv_result.scalar_one_or_none()
        
        if conversation:
            # Save user message
            user_msg = ChatMessage(
                conversation_id=conversation_id,
                role='user',
                content=request.question
            )
            db.add(user_msg)
            
            # Save assistant message
            assistant_msg = ChatMessage(
                conversation_id=conversation_id,
                role='assistant',
                content=result['reply']
            )
            db.add(assistant_msg)
            
            await db.commit()
    
    return CodebaseAnalysisResponse(
        reply=result['reply'],
        relevant_files=result['relevant_files'],
        conversation_id=conversation_id
    )
