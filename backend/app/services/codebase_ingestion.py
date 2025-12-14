import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Tuple
import git
from langchain_text_splitters import RecursiveCharacterTextSplitter

# File extensions to process
CODE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r',
    '.html', '.css', '.scss', '.sass', '.vue', '.svelte',
    '.json', '.yaml', '.yml', '.toml', '.xml', '.md', '.txt',
    '.sql', '.sh', '.bash', '.ps1', '.dockerfile'
}

# Directories to ignore
IGNORE_DIRS = {
    'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env',
    'dist', 'build', 'target', '.next', '.nuxt', 'out',
    'coverage', '.pytest_cache', '.mypy_cache', '.tox',
    'vendor', 'packages', 'bin', 'obj'
}

# Files to ignore
IGNORE_FILES = {
    '.DS_Store', 'package-lock.json', 'yarn.lock', 'poetry.lock',
    'Pipfile.lock', '.gitignore', '.env', '.env.local'
}


class CodebaseIngestion:
    """Handles codebase ingestion from various sources."""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\nclass ", "\n\ndef ", "\n\nfunction ", "\n\n", "\n", " ", ""]
        )
    
    def extract_zip(self, zip_path: Path, extract_to: Path) -> Path:
        """Extract a ZIP file to a directory."""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        # Find the root directory (handle single-folder zips)
        items = list(extract_to.iterdir())
        if len(items) == 1 and items[0].is_dir():
            return items[0]
        return extract_to
    
    def clone_github_repo(self, repo_url: str, clone_to: Path) -> Path:
        """Clone a GitHub repository."""
        try:
            git.Repo.clone_from(repo_url, clone_to, depth=1)
            return clone_to
        except Exception as e:
            raise ValueError(f"Failed to clone repository: {str(e)}")
    
    def should_process_file(self, file_path: Path) -> bool:
        """Check if a file should be processed."""
        # Check extension
        if file_path.suffix.lower() not in CODE_EXTENSIONS:
            return False
        
        # Check filename
        if file_path.name in IGNORE_FILES:
            return False
        
        # Check if in ignored directory
        for parent in file_path.parents:
            if parent.name in IGNORE_DIRS:
                return False
        
        # Check file size (skip files > 1MB)
        try:
            if file_path.stat().st_size > 1_000_000:
                return False
        except:
            return False
        
        return True
    
    def read_file_content(self, file_path: Path) -> str:
        """Read file content with encoding fallback."""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # If all encodings fail, return empty string
        return ""
    
    def process_codebase(self, root_path: Path) -> Tuple[List[str], List[Dict], List[str]]:
        """
        Process all files in a codebase directory.
        
        Returns:
            Tuple of (chunks, metadatas, ids)
        """
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        file_count = 0
        chunk_id = 0
        
        # Walk through directory
        for file_path in root_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            if not self.should_process_file(file_path):
                continue
            
            # Read file content
            content = self.read_file_content(file_path)
            if not content.strip():
                continue
            
            file_count += 1
            
            # Get relative path for metadata
            try:
                relative_path = file_path.relative_to(root_path)
            except ValueError:
                relative_path = file_path.name
            
            # Split content into chunks
            chunks = self.text_splitter.split_text(content)
            
            # Create metadata for each chunk
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadatas.append({
                    'file_path': str(relative_path),
                    'file_name': file_path.name,
                    'file_extension': file_path.suffix,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
                all_ids.append(f"chunk_{chunk_id}")
                chunk_id += 1
        
        return all_chunks, all_metadatas, all_ids
    
    def ingest_from_zip(self, zip_path: Path) -> Tuple[List[str], List[Dict], List[str]]:
        """Ingest codebase from a ZIP file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ZIP
            root_path = self.extract_zip(zip_path, temp_path)
            
            # Process codebase
            return self.process_codebase(root_path)
    
    def ingest_from_github(self, repo_url: str) -> Tuple[List[str], List[Dict], List[str]]:
        """Ingest codebase from a GitHub repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "repo"
            
            # Clone repository
            root_path = self.clone_github_repo(repo_url, temp_path)
            
            # Process codebase
            return self.process_codebase(root_path)


# Singleton instance
_ingestion_service = CodebaseIngestion()


def get_ingestion_service() -> CodebaseIngestion:
    """Get the singleton ingestion service."""
    return _ingestion_service
