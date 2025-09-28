"""
RAG-Enhanced Code Review System
Combines retrieval-augmented generation with code analysis for context-aware reviews
"""

import asyncio
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Vector database and embeddings
try:
    import chromadb
    from chromadb.config import Settings
    import openai
    from sentence_transformers import SentenceTransformer
except ImportError:
    # Fallback for when dependencies aren't installed
    chromadb = None
    openai = None
    SentenceTransformer = None

from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs

logger = logging.getLogger(__name__)

@dataclass
class CodeContext:
    """Represents code context for RAG retrieval"""
    file_path: str
    function_name: Optional[str]
    class_name: Optional[str]
    imports: List[str]
    dependencies: List[str]
    language: str
    complexity_score: float

@dataclass
class RetrievedContext:
    """Context retrieved from RAG system"""
    similar_code: List[str]
    documentation: List[str]
    best_practices: List[str]
    common_issues: List[str]
    similarity_scores: List[float]

class RAGCodeReviewEngine:
    """RAG-enhanced code review engine with vector database integration"""

    def __init__(self, vector_db_path: str = "data/vector_db"):
        self.vector_db_path = Path(vector_db_path)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.chroma_client = None
        self.embeddings_model = None
        self.code_collection = None
        self.docs_collection = None

        # Language parsers for code analysis
        self.parsers = {}
        self._init_parsers()

        # Initialize if dependencies are available
        if chromadb and SentenceTransformer:
            self._init_vector_db()
            self._init_embeddings_model()

    def _init_parsers(self):
        """Initialize tree-sitter parsers for different languages"""
        try:
            # Python parser
            py_language = Language(tspython.language(), "python")
            py_parser = Parser()
            py_parser.set_language(py_language)
            self.parsers['python'] = py_parser

            # JavaScript parser
            js_language = Language(tsjs.language(), "javascript")
            js_parser = Parser()
            js_parser.set_language(js_language)
            self.parsers['javascript'] = js_parser

            logger.info("Tree-sitter parsers initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize tree-sitter parsers: {e}")

    def _init_vector_db(self):
        """Initialize ChromaDB vector database"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.vector_db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Create collections
            self.code_collection = self.chroma_client.get_or_create_collection(
                name="code_snippets",
                metadata={"description": "Code snippets and patterns for RAG retrieval"}
            )

            self.docs_collection = self.chroma_client.get_or_create_collection(
                name="documentation",
                metadata={"description": "Documentation and best practices"}
            )

            logger.info("ChromaDB vector database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")

    def _init_embeddings_model(self):
        """Initialize sentence transformer model for embeddings"""
        try:
            # Use a model optimized for code
            self.embeddings_model = SentenceTransformer('microsoft/codebert-base')
            logger.info("Code embeddings model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load embeddings model: {e}")
            # Fallback to general model
            try:
                self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Fallback embeddings model loaded")
            except Exception as fallback_e:
                logger.error(f"Failed to load any embeddings model: {fallback_e}")

    def extract_code_context(self, code: str, language: str, file_path: str = "") -> CodeContext:
        """Extract contextual information from code using AST parsing"""
        context = CodeContext(
            file_path=file_path,
            function_name=None,
            class_name=None,
            imports=[],
            dependencies=[],
            language=language,
            complexity_score=0.0
        )

        if language not in self.parsers:
            logger.warning(f"No parser available for language: {language}")
            return context

        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code, "utf8"))
            root_node = tree.root_node

            # Extract different code elements based on language
            if language == "python":
                context = self._extract_python_context(root_node, code, context)
            elif language == "javascript":
                context = self._extract_js_context(root_node, code, context)

            # Calculate complexity score
            context.complexity_score = self._calculate_complexity(root_node)

        except Exception as e:
            logger.warning(f"Failed to parse code: {e}")

        return context

    def _extract_python_context(self, node, code: str, context: CodeContext) -> CodeContext:
        """Extract Python-specific context"""
        lines = code.split('\n')

        def traverse(node):
            if node.type == 'import_statement' or node.type == 'import_from_statement':
                import_text = code[node.start_byte:node.end_byte]
                context.imports.append(import_text.strip())

            elif node.type == 'function_definition':
                func_name_node = node.child_by_field_name('name')
                if func_name_node:
                    context.function_name = code[func_name_node.start_byte:func_name_node.end_byte]

            elif node.type == 'class_definition':
                class_name_node = node.child_by_field_name('name')
                if class_name_node:
                    context.class_name = code[class_name_node.start_byte:class_name_node.end_byte]

            for child in node.children:
                traverse(child)

        traverse(node)
        return context

    def _extract_js_context(self, node, code: str, context: CodeContext) -> CodeContext:
        """Extract JavaScript-specific context"""
        def traverse(node):
            if node.type == 'import_statement':
                import_text = code[node.start_byte:node.end_byte]
                context.imports.append(import_text.strip())

            elif node.type == 'function_declaration':
                func_name_node = node.child_by_field_name('name')
                if func_name_node:
                    context.function_name = code[func_name_node.start_byte:func_name_node.end_byte]

            elif node.type == 'class_declaration':
                class_name_node = node.child_by_field_name('name')
                if class_name_node:
                    context.class_name = code[class_name_node.start_byte:class_name_node.end_byte]

            for child in node.children:
                traverse(child)

        traverse(node)
        return context

    def _calculate_complexity(self, node) -> float:
        """Calculate cyclomatic complexity of code"""
        complexity = 1  # Base complexity

        def traverse(node):
            nonlocal complexity
            # Add complexity for control flow statements
            if node.type in ['if_statement', 'while_statement', 'for_statement',
                           'try_statement', 'except_clause', 'case_clause']:
                complexity += 1

            for child in node.children:
                traverse(child)

        traverse(node)
        return min(complexity / 10.0, 1.0)  # Normalize to 0-1 range

    async def index_codebase(self, codebase_path: str) -> Dict[str, Any]:
        """Index an entire codebase for RAG retrieval"""
        if not self.chroma_client or not self.embeddings_model:
            return {"error": "RAG system not properly initialized"}

        indexed_files = 0
        failed_files = 0

        codebase_path = Path(codebase_path)

        # Supported file extensions
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs'}
        doc_extensions = {'.md', '.rst', '.txt'}

        for file_path in codebase_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in code_extensions:
                try:
                    await self._index_code_file(file_path)
                    indexed_files += 1
                except Exception as e:
                    logger.warning(f"Failed to index {file_path}: {e}")
                    failed_files += 1

            elif file_path.is_file() and file_path.suffix in doc_extensions:
                try:
                    await self._index_doc_file(file_path)
                    indexed_files += 1
                except Exception as e:
                    logger.warning(f"Failed to index doc {file_path}: {e}")
                    failed_files += 1

        return {
            "indexed_files": indexed_files,
            "failed_files": failed_files,
            "total_code_embeddings": self.code_collection.count(),
            "total_doc_embeddings": self.docs_collection.count()
        }

    def persist_embeddings(self) -> None:
        """Ensure vector stores are flushed to persistent storage."""
        if not self.chroma_client:
            return
        try:
            self.chroma_client.persist()
            logger.info("RAG vector stores persisted to %s", self.vector_db_path)
        except Exception as exc:
            logger.error("Failed to persist RAG embeddings: %s", exc)

    def reset_collections(self) -> None:
        """Remove all stored embeddings (used for force reindex)."""
        if not self.chroma_client:
            return
        try:
            if self.code_collection:
                self.code_collection.delete(where={})
            if self.docs_collection:
                self.docs_collection.delete(where={})
            logger.info("RAG collections cleared for reindex")
        except Exception as exc:
            logger.error("Failed to reset RAG collections: %s", exc)

    async def _index_code_file(self, file_path: Path):
        """Index a single code file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Determine language from file extension
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.jsx': 'javascript',
                '.tsx': 'typescript'
            }

            language = language_map.get(file_path.suffix, 'unknown')

            # Extract context
            context = self.extract_code_context(content, language, str(file_path))

            # Create chunks for large files
            chunks = self._chunk_code(content, max_chunk_size=1000)

            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embeddings_model.encode(chunk).tolist()

                # Create unique ID
                chunk_id = hashlib.md5(f"{file_path}_{i}_{chunk[:100]}".encode()).hexdigest()

                # Store in vector database
                self.code_collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "file_path": str(file_path),
                        "language": language,
                        "function_name": context.function_name or "",
                        "class_name": context.class_name or "",
                        "complexity": context.complexity_score,
                        "chunk_index": i,
                        "imports": json.dumps(context.imports)
                    }],
                    ids=[chunk_id]
                )

        except Exception as e:
            logger.error(f"Failed to index code file {file_path}: {e}")
            raise

    async def _index_doc_file(self, file_path: Path):
        """Index a documentation file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Create chunks for large docs
            chunks = self._chunk_text(content, max_chunk_size=500)

            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embeddings_model.encode(chunk).tolist()

                # Create unique ID
                chunk_id = hashlib.md5(f"{file_path}_{i}_{chunk[:100]}".encode()).hexdigest()

                # Store in vector database
                self.docs_collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "file_path": str(file_path),
                        "file_type": file_path.suffix,
                        "chunk_index": i
                    }],
                    ids=[chunk_id]
                )

        except Exception as e:
            logger.error(f"Failed to index doc file {file_path}: {e}")
            raise

    def _chunk_code(self, code: str, max_chunk_size: int = 1000) -> List[str]:
        """Intelligently chunk code by functions/classes when possible"""
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _chunk_text(self, text: str, max_chunk_size: int = 500) -> List[str]:
        """Chunk text by sentences/paragraphs"""
        # Simple sentence-based chunking
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence) + 2  # +2 for '. '

            if current_size + sentence_size > max_chunk_size and current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        if current_chunk:
            chunks.append('. '.join(current_chunk))

        return chunks

    async def retrieve_context(self, code: str, language: str, query_type: str = "similar") -> RetrievedContext:
        """Retrieve relevant context for code review using RAG"""
        if not self.chroma_client or not self.embeddings_model:
            return RetrievedContext([], [], [], [], [])

        try:
            # Generate query embedding
            query_embedding = self.embeddings_model.encode(code).tolist()

            # Search similar code
            code_results = self.code_collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where={"language": language} if language != "unknown" else None
            )

            # Search relevant documentation
            doc_results = self.docs_collection.query(
                query_embeddings=[query_embedding],
                n_results=3
            )

            # Extract and organize results
            similar_code = code_results['documents'][0] if code_results['documents'] else []
            documentation = doc_results['documents'][0] if doc_results['documents'] else []

            # Extract similarity scores
            code_scores = code_results['distances'][0] if code_results['distances'] else []
            doc_scores = doc_results['distances'][0] if doc_results['distances'] else []

            return RetrievedContext(
                similar_code=similar_code,
                documentation=documentation,
                best_practices=self._extract_best_practices(documentation),
                common_issues=self._extract_common_issues(similar_code),
                similarity_scores=code_scores + doc_scores
            )

        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return RetrievedContext([], [], [], [], [])

    def _extract_best_practices(self, docs: List[str]) -> List[str]:
        """Extract best practices from documentation"""
        best_practices = []
        for doc in docs:
            # Look for common best practice indicators
            if any(keyword in doc.lower() for keyword in ['best practice', 'recommended', 'should', 'avoid']):
                best_practices.append(doc)
        return best_practices[:3]  # Limit to top 3

    def _extract_common_issues(self, code_snippets: List[str]) -> List[str]:
        """Extract common issues from similar code"""
        # This would be enhanced with historical review data
        common_issues = []
        for snippet in code_snippets:
            # Basic pattern matching for common issues
            if 'TODO' in snippet or 'FIXME' in snippet:
                common_issues.append("Code contains TODO/FIXME comments")
            if 'print(' in snippet and 'python' in snippet.lower():
                common_issues.append("Consider using logging instead of print statements")

        return list(set(common_issues))  # Remove duplicates

    async def enhanced_code_review(self, code: str, language: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform RAG-enhanced code review"""
        # Extract code context
        code_context = self.extract_code_context(code, language)

        # Retrieve relevant context
        retrieved_context = await self.retrieve_context(code, language)

        # Combine with traditional analysis
        review_result = {
            "code_context": {
                "function_name": code_context.function_name,
                "class_name": code_context.class_name,
                "complexity_score": code_context.complexity_score,
                "imports": code_context.imports
            },
            "rag_context": {
                "similar_code_found": len(retrieved_context.similar_code),
                "documentation_found": len(retrieved_context.documentation),
                "best_practices": retrieved_context.best_practices,
                "common_issues": retrieved_context.common_issues
            },
            "enhanced_suggestions": await self._generate_enhanced_suggestions(
                code, code_context, retrieved_context
            )
        }

        return review_result

    async def _generate_enhanced_suggestions(self, code: str, code_context: CodeContext,
                                           retrieved_context: RetrievedContext) -> List[Dict[str, Any]]:
        """Generate enhanced suggestions using RAG context"""
        suggestions = []

        # Complexity-based suggestions
        if code_context.complexity_score > 0.7:
            suggestions.append({
                "type": "complexity",
                "severity": "warning",
                "message": f"High complexity detected (score: {code_context.complexity_score:.2f}). Consider refactoring.",
                "context": "Based on cyclomatic complexity analysis"
            })

        # Best practices suggestions
        for practice in retrieved_context.best_practices:
            suggestions.append({
                "type": "best_practice",
                "severity": "info",
                "message": f"Best practice recommendation: {practice[:100]}...",
                "context": "From documentation analysis"
            })

        # Common issues suggestions
        for issue in retrieved_context.common_issues:
            suggestions.append({
                "type": "common_issue",
                "severity": "warning",
                "message": issue,
                "context": "Based on similar code patterns"
            })

        # Similar code suggestions
        if retrieved_context.similar_code:
            suggestions.append({
                "type": "similar_pattern",
                "severity": "info",
                "message": f"Found {len(retrieved_context.similar_code)} similar code patterns in codebase",
                "context": "Consider consistency with existing patterns"
            })

        return suggestions

# Global RAG engine instance
rag_engine = RAGCodeReviewEngine()
