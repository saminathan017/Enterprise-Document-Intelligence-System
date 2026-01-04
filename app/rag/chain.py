"""
RAG chain with citations and source tracking.
"""

from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.rag.prompts import (
    SYSTEM_PROMPT,
    RAG_PROMPT_TEMPLATE,
    WEB_AUGMENTED_PROMPT,
    TABLE_GENERATION_PROMPT
)
from app.vectorstore.retrieval import Retriever
from app.models.responses import Citation


class RAGChain:
    """RAG chain with citation tracking."""
    
    def __init__(self, retriever: Retriever):
        """
        Initialize RAG chain.
        
        Args:
            retriever: Retriever instance
        """
        self.retriever = retriever
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key
        )
    
    def query(
        self,
        query: str,
        top_k: int = None,
        web_results: Optional[str] = None,
        use_table_format: bool = False
    ) -> Dict[str, Any]:
        """
        Run RAG query with citation tracking.
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            web_results: Optional web search results for augmentation
            use_table_format: Whether to generate table format
            
        Returns:
            Dict with 'answer' and 'citations' keys
        """
        # Retrieve relevant documents
        top_k = top_k or settings.top_k_retrieval
        docs = self.retriever.retrieve_with_scores(query, top_k)
        
        if not docs:
            return {
                "answer": "I cannot find any relevant documents to answer this question.",
                "citations": []
            }
        
        # Format context
        context = self._format_context(docs)
        
        # Select prompt template
        if use_table_format:
            user_prompt = TABLE_GENERATION_PROMPT.format(context=context, query=query)
        elif web_results:
            user_prompt = WEB_AUGMENTED_PROMPT.format(
                context=context,
                web_results=web_results,
                query=query
            )
        else:
            user_prompt = RAG_PROMPT_TEMPLATE.format(context=context, query=query)
        
        # Create messages
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        
        # Run LLM
        response = self.llm.invoke(messages)
        
        # Extract citations
        citations = self._extract_citations(docs)
        
        return {
            "answer": response.content.strip(),
            "citations": citations,
            "retrieved_docs": docs  # For debugging/analysis
        }
    
    def _format_context(self, docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents as context string."""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            source = doc["metadata"].get("source", "Unknown")
            chunk_idx = doc["metadata"].get("chunk_index", "?")
            
            context_parts.append(
                f"--- Document {i} [Source: {source}, chunk {chunk_idx}] ---\n"
                f"{doc['text']}\n"
            )
        
        return "\n".join(context_parts)
    
    def _extract_citations(self, docs: List[Dict[str, Any]]) -> List[Citation]:
        """
        Extract citations from retrieved documents.
        
        Args:
            docs: Retrieved documents with scores
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        for doc in docs:
            metadata = doc["metadata"]
            
            # Extract excerpt (first 200 chars)
            excerpt = doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"]
            
            citation = Citation(
                source=metadata.get("source", "Unknown"),
                chunk_id=metadata.get("chunk_id"),
                score=doc["score"],
                excerpt=excerpt
            )
            citations.append(citation)
        
        return citations
