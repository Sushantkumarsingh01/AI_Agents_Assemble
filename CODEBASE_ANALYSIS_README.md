# 🚀 Codebase Analysis Feature - RAG-Powered AI Architect

## Overview

This feature transforms your AI chatbot into an **expert Codebase Architect and Senior Developer** using **Retrieval-Augmented Generation (RAG)** and the **Agno framework**. It allows users to upload codebases (ZIP files or GitHub repos) and ask intelligent questions about the code structure, architecture, bugs, and implementation details.

---

## 🎯 Key Features

### 1. **Multi-Source Codebase Ingestion**
- **Upload ZIP files**: Drag and drop your project as a ZIP
- **Clone GitHub repositories**: Provide a GitHub URL for instant analysis
- Supports 40+ programming languages and file types

### 2. **Intelligent Code Chunking**
- Uses LangChain's `RecursiveCharacterTextSplitter`
- Splits code by functions, classes, and logical blocks
- Maintains context with 200-character overlap between chunks

### 3. **Semantic Search with Vector Embeddings**
- Powered by **ChromaDB** (persistent vector database)
- Uses **Sentence Transformers** (`all-MiniLM-L6-v2`) for embeddings
- Cosine similarity search for relevant code retrieval

### 4. **RAG-Powered Analysis with Agno**
- **Agno framework** orchestrates the AI agent
- **Gemini 2.0 Flash** as the LLM backend
- Context-aware responses grounded in actual code

### 5. **Expert System Prompt**
The agent follows the "Codebase Architect & Senior Developer" persona:
- Evidence-based reasoning (cites files and line numbers)
- Comprehensive architectural analysis
- Debugging with root cause identification
- Feature development suggestions
- Code explanation with best practices

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  CodebaseAnalysis Component                            │ │
│  │  - Upload ZIP / Clone GitHub                           │ │
│  │  - Project Management                                  │ │
│  │  - Question Input & Analysis Display                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Codebase Router (/api/codebase/*)                     │ │
│  │  - POST /upload      - POST /github                    │ │
│  │  - GET  /projects    - POST /analyze                   │ │
│  │  - DELETE /projects/{id}                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Services Layer                                         │ │
│  │  ┌──────────────────┐  ┌──────────────────┐           │ │
│  │  │ Ingestion Service│  │  Vector Store    │           │ │
│  │  │ - Extract ZIP    │  │  - ChromaDB      │           │ │
│  │  │ - Clone Git      │  │  - Embeddings    │           │ │
│  │  │ - Parse Files    │  │  - Search        │           │ │
│  │  └──────────────────┘  └──────────────────┘           │ │
│  │              ↓                    ↓                     │ │
│  │  ┌────────────────────────────────────────────────┐   │ │
│  │  │  RAG Agent (Agno Framework)                    │   │ │
│  │  │  - Retrieve relevant code chunks               │   │ │
│  │  │  - Build context prompt                        │   │ │
│  │  │  - Generate analysis with Gemini               │   │ │
│  │  └────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Persistence                          │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  PostgreSQL/     │        │  ChromaDB        │          │
│  │  SQLite          │        │  Vector Store    │          │
│  │  - Users         │        │  - Code Chunks   │          │
│  │  - Projects      │        │  - Embeddings    │          │
│  │  - Conversations │        │  - Metadata      │          │
│  └──────────────────┘        └──────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation & Setup

### 1. **Install Backend Dependencies**

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `agno==0.0.15` - Agentic framework
- `langchain==0.3.7` - Text processing
- `chromadb==0.5.20` - Vector database
- `sentence-transformers==3.3.1` - Embeddings
- `gitpython==3.1.43` - GitHub cloning
- `python-multipart==0.0.12` - File uploads

### 2. **Configure Environment Variables**

Add to `backend/env/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. **Run the Backend**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. **Run the Frontend**

```bash
cd frontend
npm install
npm run dev
```

---

## 🎮 Usage Guide

### **Step 1: Upload a Codebase**

1. Click **"Analyze Codebase"** button in the sidebar
2. Choose upload method:
   - **Upload ZIP**: Click "Upload ZIP" → Select file → Enter project name → Upload
   - **Clone GitHub**: Click "Clone GitHub" → Enter repo URL → Enter project name → Clone

### **Step 2: Select a Project**

- View all your uploaded projects in the left panel
- Click on a project to select it for analysis
- See project metadata: file count, chunk count, source type

### **Step 3: Ask Questions**

Example questions:
- *"How does authentication work in this codebase?"*
- *"Where is the API endpoint for user registration?"*
- *"Explain the database schema and relationships"*
- *"How can I add a new feature to export data as CSV?"*
- *"What's causing the error in the login function?"*
- *"Show me the data flow from frontend to backend"*

### **Step 4: Review Analysis**

- Get detailed, code-grounded responses
- See relevant files referenced in the analysis
- Responses include:
  - Specific file paths and function names
  - Code examples and explanations
  - Implementation suggestions
  - Best practices aligned with the codebase

---

## 🧠 How RAG Works

### **1. Ingestion Phase**
```
Codebase → Extract Files → Filter by Extension → Read Content
    ↓
Split into Chunks (1500 chars, 200 overlap)
    ↓
Generate Embeddings (Sentence Transformers)
    ↓
Store in ChromaDB with Metadata
```

### **2. Query Phase**
```
User Question → Generate Query Embedding
    ↓
Semantic Search in ChromaDB (Top 8 results)
    ↓
Retrieve Relevant Code Chunks + Metadata
    ↓
Build Context Prompt with Code
    ↓
Send to Agno Agent → Gemini LLM
    ↓
Generate Context-Aware Response
```

---

## 🗂️ File Structure

```
backend/
├── app/
│   ├── models.py                    # Added CodebaseProject model
│   ├── schemas.py                   # Added codebase schemas
│   ├── routers/
│   │   └── codebase.py             # NEW: Codebase API endpoints
│   └── services/
│       ├── codebase_ingestion.py   # NEW: File parsing & chunking
│       ├── vector_store.py         # NEW: ChromaDB wrapper
│       └── rag_agent.py            # NEW: Agno-powered RAG agent
├── data/
│   └── chromadb/                   # Vector database storage
└── requirements.txt                # Updated dependencies

frontend/
└── src/
    └── components/
        └── CodebaseAnalysis/       # NEW: Full-featured UI
            ├── CodebaseAnalysis.jsx
            ├── CodebaseAnalysis.css
            └── index.js
```

---

## 🔧 Configuration

### **Supported File Extensions**
Python, JavaScript, TypeScript, Java, C++, Go, Rust, Ruby, PHP, Swift, Kotlin, HTML, CSS, JSON, YAML, Markdown, SQL, Shell scripts, and more.

### **Ignored Directories**
`node_modules`, `__pycache__`, `.git`, `venv`, `dist`, `build`, `coverage`, etc.

### **Chunking Parameters**
- **Chunk Size**: 1500 characters
- **Overlap**: 200 characters
- **Separators**: Prioritizes class/function boundaries

### **Vector Search**
- **Top K Results**: 8 chunks per query
- **Similarity Metric**: Cosine distance
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)

---

## 🚀 Advanced Features

### **1. Multi-Project Management**
- Upload multiple codebases
- Each project has isolated vector store
- Switch between projects seamlessly

### **2. Conversation Integration**
- Analysis can be saved to chat conversations
- Maintain context across multiple questions
- Full chat history with code references

### **3. GitHub Integration**
- Direct repository cloning
- Shallow clone (depth=1) for speed
- Automatic branch detection

### **4. Metadata Tracking**
- File paths and names
- File extensions
- Chunk indices
- Relevance scores

---

## 🎯 Example Use Cases

### **1. Onboarding New Developers**
*"Give me an overview of this codebase architecture"*

### **2. Debugging**
*"Why is the user authentication failing? Show me the relevant code"*

### **3. Feature Planning**
*"How would I add a password reset feature? What files need to be modified?"*

### **4. Code Review**
*"Are there any security vulnerabilities in the authentication flow?"*

### **5. Documentation**
*"Explain how the payment processing works step by step"*

---

## 🛠️ API Endpoints

### **POST /api/codebase/upload**
Upload a ZIP file
- **Body**: `multipart/form-data` (file, name, description)
- **Response**: Project ID, file count, chunk count

### **POST /api/codebase/github**
Clone a GitHub repository
- **Body**: `multipart/form-data` (repo_url, name, description)
- **Response**: Project ID, file count, chunk count

### **GET /api/codebase/projects**
List all user's projects
- **Response**: Array of project objects

### **DELETE /api/codebase/projects/{id}**
Delete a project and its vector store
- **Response**: Success message

### **POST /api/codebase/analyze**
Analyze codebase with a question
- **Body**: `{ project_id, question, conversation_id? }`
- **Response**: `{ reply, relevant_files, conversation_id? }`

---

## 🔐 Security Considerations

1. **User Isolation**: Each user's projects are isolated by user_id
2. **Vector Store Naming**: Unique collection names prevent collisions
3. **File Size Limits**: Files > 1MB are skipped
4. **Authentication**: All endpoints require JWT token
5. **Input Validation**: File types and URLs are validated

---

## 🐛 Troubleshooting

### **Issue: "No processable files found"**
- Ensure ZIP contains code files (not just binaries)
- Check file extensions are supported
- Verify ZIP structure (avoid nested single folders)

### **Issue: "Failed to clone repository"**
- Verify GitHub URL is public or accessible
- Check network connectivity
- Ensure GitPython is installed

### **Issue: "Analysis returns generic responses"**
- Upload more comprehensive code
- Ask more specific questions
- Check if relevant files were indexed

---

## 📈 Performance Optimization

- **Lazy Loading**: Embeddings generated only once during upload
- **Persistent Storage**: ChromaDB persists to disk
- **Shallow Clones**: GitHub repos cloned with depth=1
- **Async Operations**: All I/O operations are async
- **Batch Processing**: Embeddings generated in batches

---

## 🎓 Technical Deep Dive

### **Why Agno Framework?**
- Simplifies agent orchestration
- Built-in prompt management
- Easy integration with multiple LLM providers
- Structured output handling

### **Why ChromaDB?**
- Lightweight and fast
- Persistent storage
- No external dependencies
- Python-native API

### **Why Sentence Transformers?**
- State-of-the-art embeddings
- Fast inference
- Small model size (80MB)
- Optimized for semantic search

---

## 🔮 Future Enhancements

- [ ] Multi-file context (analyze across multiple files)
- [ ] Code diff analysis (compare versions)
- [ ] Automatic documentation generation
- [ ] Integration with IDE plugins
- [ ] Real-time collaboration features
- [ ] Custom embedding models per language
- [ ] Code execution sandbox
- [ ] Automated test generation

---

## 📝 License

This feature is part of the AI Chatbot project. See main LICENSE file.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly
4. Submit a pull request

---

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Check the troubleshooting section
- Review the API documentation

---

**Built with ❤️ using Agno, LangChain, ChromaDB, and Gemini AI**
