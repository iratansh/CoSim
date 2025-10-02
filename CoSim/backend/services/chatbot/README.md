# CoSim RAG Chatbot Service

A RAG (Retrieval-Augmented Generation) powered chatbot for answering questions about the CoSim platform.

## Features

- **Vector Database**: ChromaDB with sentence-transformers embeddings
- **Smart Retrieval**: Semantic search over product documentation
- **LLM Integration**: Optional OpenAI integration (falls back to context-based responses)
- **FAQ Support**: Pre-loaded common questions and answers
- **Conversation History**: Maintains context across messages
- **Health Checks**: Built-in monitoring endpoints

## Architecture

```
User Query
    ↓
FastAPI Service
    ↓
Vector Store (ChromaDB)
    ↓
Retrieve Top-K Relevant Docs
    ↓
Generate Response (OpenAI or Fallback)
    ↓
Return Answer + Sources
```

## Setup

### Local Development

1. **Install Dependencies**:
```bash
cd backend/services/chatbot
pip install -r requirements.txt
```

2. **Initialize Vector Store**:
```bash
python vector_store.py
```

This will:
- Load product documentation from `product_docs.txt`
- Create embeddings using `all-MiniLM-L6-v2`
- Store vectors in ChromaDB (persisted to `./chroma_db`)
- Add FAQ entries

3. **Run the Service**:
```bash
python main.py
```

The service will start on `http://localhost:8006`

### Docker Deployment

The service is included in `docker-compose.yml`:

```bash
# Build and start all services
docker-compose up -d

# View chatbot logs
docker-compose logs -f chatbot-service

# Check health
curl http://localhost:8006/health
```

## API Endpoints

### POST `/chat/query`
Send a question to the chatbot.

**Request**:
```json
{
  "message": "How do I get started with CoSim?",
  "conversation_history": [],
  "max_history": 5
}
```

**Response**:
```json
{
  "response": "To get started: 1) Sign up for a free account...",
  "sources": [
    {
      "section": "Getting Started",
      "content_preview": "Sign up for a free account at...",
      "relevance_score": 0.89
    }
  ],
  "timestamp": "2025-10-01T12:00:00Z"
}
```

### GET `/health`
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "vector_store_stats": {
    "total_documents": 156,
    "collection_name": "cosim_product_docs",
    "persist_directory": "./chroma_db"
  }
}
```

### GET `/chat/suggestions`
Get suggested starter questions.

**Response**:
```json
{
  "suggestions": [
    "How do I get started with CoSim?",
    "What simulators are supported?",
    ...
  ]
}
```

### POST `/chat/feedback`
Submit feedback on a response.

**Request**:
```json
{
  "message_id": "msg_123",
  "helpful": true,
  "comment": "Very helpful answer!"
}
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` (optional): Enable OpenAI GPT-3.5 for better responses
- `PYTHONUNBUFFERED=1`: For better logging in Docker

### Customization

#### Add More Documentation

Edit `product_docs.txt` with your content, then re-run:
```bash
python vector_store.py
```

#### Adjust Chunking

In `vector_store.py`, modify:
```python
chunks = self.chunk_text(section["content"], chunk_size=300, overlap=50)
```

#### Change Embedding Model

In `vector_store.py`:
```python
self.embedding_model = SentenceTransformer('all-mpnet-base-v2')  # Better but slower
```

#### Tune Retrieval

In `main.py`:
```python
retrieved_docs = store.query(request.message, n_results=5)  # Get more/fewer docs
```

## Frontend Integration

The chatbot UI is a React component in `frontend/src/components/ChatBot.tsx`:

### Features
- ✅ Floating button (bottom-right)
- ✅ Glassmorphism design
- ✅ Minimize/Expand animations
- ✅ Message history
- ✅ Typing indicator
- ✅ Suggested questions
- ✅ Smooth scrolling

### Usage

```tsx
import ChatBot from '../components/ChatBot';

function MyPage() {
  return (
    <div>
      {/* Your page content */}
      <ChatBot apiUrl="http://localhost:8006" />
    </div>
  );
}
```

## Vector Store Details

### Document Processing

1. **Chunking**: Documents split into 300-word chunks with 50-word overlap
2. **Sections**: Organized by markdown headers (##)
3. **Metadata**: Each chunk tagged with section name and index
4. **FAQ**: Special FAQ entries for common questions

### Embeddings

- **Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Speed**: ~40ms per query
- **Accuracy**: Good balance of speed and quality

### Storage

- **Engine**: ChromaDB (SQLite + DuckDB backend)
- **Persistence**: Automatic to `./chroma_db`
- **Docker Volume**: `chatbot_data` for persistence

## Response Generation

### Without OpenAI

Simple context-based responses:
- Returns most relevant document chunk
- Adds helpful closing message
- Fast and free

### With OpenAI (Recommended)

Set `OPENAI_API_KEY` environment variable:

```bash
export OPENAI_API_KEY="sk-..."
docker-compose up -d chatbot-service
```

Benefits:
- Natural language responses
- Conversation awareness
- Better understanding of user intent
- Fallback to simple mode if API fails

## Performance

- **Query Time**: 50-100ms (without LLM)
- **With OpenAI**: 1-2 seconds
- **Memory**: ~200MB (includes model)
- **Disk**: ~50MB for vector store

## Monitoring

### Health Check

```bash
curl http://localhost:8006/health
```

### Vector Store Stats

```bash
curl http://localhost:8006/health | jq '.vector_store_stats'
```

### Test Query

```bash
curl -X POST http://localhost:8006/chat/query \
  -H "Content-Type: application/json" \
  -d '{"message": "What simulators are supported?"}'
```

## Troubleshooting

### ChromaDB Errors

If you see ChromaDB errors, delete and recreate:
```bash
rm -rf ./chroma_db
python vector_store.py
```

### Empty Responses

Check vector store has documents:
```bash
python -c "from vector_store import RAGVectorStore; print(RAGVectorStore().get_stats())"
```

### OpenAI Rate Limits

The service automatically falls back to simple responses if OpenAI fails.

## Future Enhancements

- [ ] Conversation memory with Redis
- [ ] User feedback storage
- [ ] A/B testing different prompts
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Integration with support tickets
- [ ] Analytics dashboard
- [ ] Custom training on user interactions

## License

MIT
