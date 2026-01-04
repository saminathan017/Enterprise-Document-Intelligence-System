"""
RAG query endpoint with tools and session memory.
Main intelligence endpoint.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import time

from app.models.requests import QueryRequest
from app.models.responses import QueryResponse, ErrorResponse
from app.vectorstore.store import get_vector_store
from app.vectorstore.retrieval import Retriever
from app.rag.chain import RAGChain
from app.memory.session_manager import get_session_manager
from app.memory.conversation_memory import ConversationMemory
from app.tools.web_synthesis import WebSynthesisTool


router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query documents using RAG with citations, tools, and session memory.
    
    Features:
    - RAG retrieval with citations
    - Optional web augmentation
    - Optional table generation
    - Multi-turn conversation memory
    
    Args:
        request: QueryRequest with query, session_id, and tool flags
        
    Returns:
        QueryResponse with answer and citations
    """
    start_time = time.time()
    
    try:
        # Initialize components
        vector_store = get_vector_store()
        retriever = Retriever(vector_store)
        rag_chain = RAGChain(retriever)
        session_manager = get_session_manager()
        
        # Get or create session
        session_data = session_manager.get_session(request.session_id)
        if not session_data:
            # Session doesn't exist, create it
            created_id = session_manager.create_session()
            # But use the requested ID for consistency
            if request.session_id != created_id:
                # Update the session file name
                session_manager.delete_session(created_id)
                session_manager._save_session(
                    request.session_id,
                    {
                        "session_id": request.session_id,
                        "created_at": datetime.utcnow().isoformat(),
                        "last_activity": datetime.utcnow().isoformat(),
                        "message_count": 0,
                        "history": []
                    }
                )
        
        # Initialize conversation memory
        conv_memory = ConversationMemory(request.session_id, session_manager)
        
        # Add user message to memory
        conv_memory.add_user_message(request.query)
        
        # Check if this is a conversational message (not a document query)
        conversational_phrases = [
            "thanks", "thank you", "great", "awesome", "ok", "okay", 
            "cool", "nice", "good", "got it", "understood", "perfect",
            "hi", "hello", "hey", "bye", "goodbye"
        ]
        query_lower = request.query.lower().strip()
        
        # If it's a short conversational message, respond naturally
        if (len(request.query.split()) <= 3 and 
            any(phrase in query_lower for phrase in conversational_phrases)):
            
            conversational_response = {
                "answer": "You're welcome! Feel free to ask me anything about your documents.",
                "citations": []
            }
            
            # Add AI response to memory
            conv_memory.add_ai_message(conversational_response["answer"])
            
            # Update session
            session_manager.update_session(
                request.session_id,
                {"last_activity": datetime.utcnow().isoformat()}
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return QueryResponse(
                success=True,
                query=request.query,
                answer=conversational_response["answer"],
                citations=[],
                session_id=request.session_id,
                used_web=False,
                used_table=False,
                processing_time_ms=processing_time
            )
        
        # Handle web synthesis if requested
        web_results = None
        if request.use_web:
            web_tool = WebSynthesisTool()
            web_results = web_tool.search_and_synthesize(request.query)
        
        # Run RAG chain
        rag_result = rag_chain.query(
            query=request.query,
            top_k=request.top_k,
            web_results=web_results,
            use_table_format=request.make_table
        )
        
        # Add AI response to memory
        conv_memory.add_ai_message(rag_result["answer"])
        
        # Update session
        session_manager.update_session(
            session_id=request.session_id,
            history=conv_memory.get_history(),
            increment_count=True
        )
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        return QueryResponse(
            success=True,
            query=request.query,
            answer=rag_result["answer"],
            citations=rag_result["citations"],
            session_id=request.session_id,
            used_web=request.use_web,
            used_table=request.make_table,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )
