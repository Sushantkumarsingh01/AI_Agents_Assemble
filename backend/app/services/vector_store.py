import os
import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

# Initialize ChromaDB client based on environment
CHROMA_CLOUD_API_KEY = os.getenv("CHROMA_CLOUD_API_KEY")
CHROMA_CLOUD_TENANT = os.getenv("CHROMA_CLOUD_TENANT")
CHROMA_CLOUD_DATABASE = os.getenv("CHROMA_CLOUD_DATABASE", "default_database")
CHROMA_HOST = os.getenv("CHROMA_HOST")  # e.g., "http://localhost:8000"
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")  # For self-hosted server auth

if CHROMA_CLOUD_API_KEY and CHROMA_CLOUD_TENANT:
    # Option 1: Use Chroma Cloud (managed service)
    print(f"Connecting to Chroma Cloud (Tenant: {CHROMA_CLOUD_TENANT}, DB: {CHROMA_CLOUD_DATABASE})")
    _chroma_client = chromadb.CloudClient(
        tenant=CHROMA_CLOUD_TENANT,
        database=CHROMA_CLOUD_DATABASE,
        api_key=CHROMA_CLOUD_API_KEY
    )
elif CHROMA_HOST:
    # Option 2: Use self-hosted ChromaDB server
    print(f"Connecting to ChromaDB server at {CHROMA_HOST}")
    _chroma_client = chromadb.HttpClient(
        host=CHROMA_HOST.replace("http://", "").replace("https://", "").split(":")[0],
        port=int(CHROMA_HOST.split(":")[-1]) if ":" in CHROMA_HOST.split("//")[-1] else 8000,
        settings=Settings(
            anonymized_telemetry=False,
            chroma_client_auth_provider="chromadb.auth.token.TokenAuthClientProvider" if CHROMA_API_KEY else None,
            chroma_client_auth_credentials=CHROMA_API_KEY if CHROMA_API_KEY else None
        )
    )
else:
    # Option 3: Use local persistent storage (development)
    print("Using local ChromaDB storage")
    _CHROMA_DIR = Path(__file__).parents[2] / "data" / "chromadb"
    _CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    
    _chroma_client = chromadb.PersistentClient(
        path=str(_CHROMA_DIR),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )

# Initialize embedding model
_embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


class VectorStore:
    """Manages vector embeddings and semantic search for codebase chunks."""
    
    def __init__(self, collection_name: str):
        """Initialize or get existing collection."""
        self.collection_name = collection_name
        self.collection = _chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to the vector store with embeddings."""
        # Generate embeddings
        embeddings = _embedding_model.encode(texts, show_progress_bar=False).tolist()
        
        # Add to ChromaDB
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(
        self,
        query: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """Search for relevant documents using semantic similarity."""
        # Generate query embedding
        query_embedding = _embedding_model.encode([query], show_progress_bar=False).tolist()[0]
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        return results
    
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        try:
            _chroma_client.delete_collection(name=self.collection_name)
        except Exception as e:
            print(f"Error deleting collection {self.collection_name}: {e}")
    
    def get_count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()


def create_collection_name(user_id: int, project_name: str) -> str:
    """Generate a unique collection name for a user's project."""
    import hashlib
    import time
    
    # Create a unique identifier
    unique_str = f"{user_id}_{project_name}_{int(time.time())}"
    hash_suffix = hashlib.md5(unique_str.encode()).hexdigest()[:8]
    
    # ChromaDB collection names must be 3-63 characters, alphanumeric + underscores/hyphens
    safe_name = project_name.lower().replace(" ", "_")[:30]
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-")
    
    return f"user{user_id}_{safe_name}_{hash_suffix}"
