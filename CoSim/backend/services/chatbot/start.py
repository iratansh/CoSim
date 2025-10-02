#!/usr/bin/env python3
"""
Quick start script for CoSim Chatbot
Initializes vector store and starts the service
"""
import sys
import os

def main():
    print("=" * 60)
    print("🤖 CoSim RAG Chatbot - Quick Start")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("vector_store.py"):
        print("❌ Error: Please run this script from backend/services/chatbot/")
        sys.exit(1)
    
    # Initialize vector store
    print("📚 Step 1: Initializing vector store...")
    try:
        from vector_store import initialize_vector_store
        store = initialize_vector_store()
        stats = store.get_stats()
        print(f"✅ Vector store ready with {stats['total_documents']} documents")
    except Exception as e:
        print(f"❌ Failed to initialize vector store: {e}")
        sys.exit(1)
    
    print()
    print("🚀 Step 2: Starting FastAPI service...")
    print()
    print("The chatbot will be available at: http://localhost:8006")
    print("Health check: http://localhost:8006/health")
    print("API docs: http://localhost:8006/docs")
    print()
    print("Press Ctrl+C to stop the service")
    print("=" * 60)
    print()
    
    # Start the service
    try:
        import uvicorn
        from main import app
        uvicorn.run(app, host="0.0.0.0", port=8006, log_level="info")
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down chatbot service...")
        print("Thanks for using CoSim RAG Chatbot!")
    except Exception as e:
        print(f"❌ Failed to start service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
