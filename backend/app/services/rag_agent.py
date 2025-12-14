import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from agno.agent import Agent
from agno.models.google import Gemini

from .vector_store import VectorStore

# Load environment variables
_THIS_FILE = Path(__file__).resolve()
_BACKEND_DIR = _THIS_FILE.parents[2]
_ENV_DIR_FILE = _BACKEND_DIR / "env" / ".env"
_ROOT_ENV_FILE = _BACKEND_DIR / ".env"

for candidate in (_ENV_DIR_FILE, _ROOT_ENV_FILE):
    if candidate.exists():
        load_dotenv(dotenv_path=candidate, override=False)

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


class CodebaseArchitectAgent:
    """
    An expert Codebase Architect and Senior Developer agent.
    Uses RAG to provide context-aware answers about codebases.
    """
    
    SYSTEM_PROMPT = """# CODEBASE ARCHITECT & SENIOR DEVELOPER

## **YOUR PURPOSE**
You are an expert Codebase Architect and Senior Developer with deep understanding of software architecture, design patterns, and best practices. Your role is to help developers understand, debug, and extend their codebases.

## **CORE PRINCIPLES**
1. **Evidence-Based Reasoning**: Always ground your answers in the actual code provided in the context.
2. **Comprehensive Analysis**: Consider the full architecture, data flow, and dependencies.
3. **Practical Guidance**: Provide specific, actionable advice with code examples when appropriate.
4. **Best Practices**: Suggest improvements following industry standards and the project's existing patterns.

## **YOUR CAPABILITIES**
- **Debugging**: Identify root causes of errors by analyzing code context and data flow
- **Feature Development**: Suggest implementation strategies that integrate seamlessly with existing code
- **Code Explanation**: Provide clear, layered explanations from high-level concepts to implementation details
- **Architecture Review**: Analyze system design and suggest improvements
- **Refactoring**: Recommend code improvements while maintaining functionality

## **RESPONSE GUIDELINES**
- Always cite specific files, functions, and line numbers when referencing code
- Provide step-by-step explanations for complex topics
- When suggesting changes, show before/after code examples
- If context is insufficient, clearly state what additional information would help
- Use markdown formatting for code blocks with appropriate language tags
- Be concise but thorough - avoid superficial answers

## **CONTEXT USAGE**
You will be provided with relevant code chunks from the codebase. Use this context to:
1. Understand the existing architecture and patterns
2. Identify related components and dependencies
3. Ensure your suggestions are compatible with the current codebase
4. Reference specific implementations when answering

Remember: You are a pair programmer helping the developer succeed. Be supportive, precise, and always grounded in the actual code."""

    def __init__(self, vector_store: VectorStore):
        """Initialize the RAG agent with a vector store."""
        self.vector_store = vector_store
        
        if not _GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=_GEMINI_API_KEY)
        
        # Initialize Agno Agent with Gemini model
        self.agent = Agent(
            name="CodebaseArchitect",
            model=Gemini(id="gemini-2.0-flash-exp", api_key=_GEMINI_API_KEY),
            instructions=self.SYSTEM_PROMPT,
            markdown=True
        )
    
    def retrieve_context(self, query: str, n_results: int = 5) -> tuple[str, List[str]]:
        """
        Retrieve relevant code chunks for the query.
        
        Returns:
            Tuple of (formatted_context, list_of_file_paths)
        """
        results = self.vector_store.search(query, n_results=n_results)
        
        if not results['documents'] or not results['documents'][0]:
            return "No relevant code found in the codebase.", []
        
        # Format context
        context_parts = []
        file_paths = set()
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            file_path = metadata.get('file_path', 'unknown')
            file_paths.add(file_path)
            
            context_parts.append(f"""
### File: `{file_path}`
**Relevance Score**: {1 - distance:.2f}

```{metadata.get('file_extension', '').lstrip('.')}
{doc}
```
""")
        
        context = "\n".join(context_parts)
        return context, list(file_paths)
    
    async def analyze(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Analyze a codebase question using RAG.
        
        Args:
            question: The user's question about the codebase
            chat_history: Optional previous messages for context
            
        Returns:
            Dict with 'reply' and 'relevant_files'
        """
        # Retrieve relevant code context
        context, relevant_files = self.retrieve_context(question, n_results=8)
        
        # Build conversation context if history exists
        conversation_context = ""
        if chat_history:
            conversation_context = "\n## CONVERSATION HISTORY\n\n"
            for msg in chat_history[-6:]:  # Last 6 messages for context
                role = "User" if msg['role'] == 'user' else "Assistant"
                conversation_context += f"**{role}**: {msg['content'][:200]}...\n\n"
            conversation_context += "---\n\n"
        
        # Build the prompt with context
        prompt = f"""## RELEVANT CODE CONTEXT

{context}

---

{conversation_context}## USER QUESTION
{question}

---

Please analyze the code context above and provide an answer. Follow these guidelines:

**Response Length:**
- For simple questions (greetings, thanks, clarifications): Give a brief, friendly 1-2 sentence response
- For technical questions: Provide detailed analysis with code examples

**Structure for Technical Answers:**
1. Start with a brief summary/answer
2. Use clear headings (##, ###) to organize sections
3. Reference specific files with backticks: `filename.py`
4. Use code blocks with language tags for code examples
5. Use bullet points or numbered lists for clarity
6. Add emojis sparingly for visual appeal (✅, 🔍, 💡, ⚠️)

**Content Requirements:**
- Match response length to question complexity
- For greetings/thanks: Be brief and friendly
- For technical questions: Reference specific files and provide code examples
- Be precise, actionable, and easy to understand

**Example Format:**
```
## 🔍 Analysis

Brief summary here...

### Key Components

1. **Component Name** (`file.py`)
   - Description
   - Code example in proper blocks

### Implementation Details

\`\`\`python
# Code example with syntax highlighting
def example():
    pass
\`\`\`

### Recommendations

✅ Do this...
⚠️ Avoid that...
```

Now provide your analysis:"""

        try:
            # Use Agno agent for response generation
            response = self.agent.run(prompt)
            
            # Extract content from Agno 2.x response
            if hasattr(response, 'content'):
                reply = response.content
            elif hasattr(response, 'messages') and response.messages:
                reply = response.messages[-1].content if hasattr(response.messages[-1], 'content') else str(response.messages[-1])
            else:
                reply = str(response)
            
            return {
                'reply': reply,
                'relevant_files': relevant_files
            }
            
        except Exception as e:
            # Fallback to direct Gemini call if Agno fails
            print(f"Agno agent error, falling back to direct Gemini: {e}")
            return await self._fallback_gemini_call(prompt, relevant_files)
    
    async def _fallback_gemini_call(self, prompt: str, relevant_files: List[str]) -> Dict[str, Any]:
        """Fallback method using direct Gemini API."""
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp', system_instruction=self.SYSTEM_PROMPT)
            response = await model.generate_content_async(prompt)
            
            return {
                'reply': response.text,
                'relevant_files': relevant_files
            }
        except Exception as e:
            return {
                'reply': f"I apologize, but I encountered an error analyzing the codebase: {str(e)}",
                'relevant_files': relevant_files
            }


def create_rag_agent(vector_store: VectorStore) -> CodebaseArchitectAgent:
    """Factory function to create a RAG agent."""
    return CodebaseArchitectAgent(vector_store)
