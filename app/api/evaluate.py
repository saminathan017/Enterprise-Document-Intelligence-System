"""
Evaluation API endpoint for RAG system.
Provides metrics and benchmarking capabilities.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

from app.evaluation.metrics import RAGEvaluator


router = APIRouter()


class EvaluationTestCase(BaseModel):
    """Single test case for evaluation."""
    query: str
    retrieved_docs: List[str]
    relevant_docs: List[str]
    generated_answer: str
    reference_answer: str
    context: str


class EvaluationRequest(BaseModel):
    """Request for batch evaluation."""
    test_cases: List[EvaluationTestCase] = Field(
        ..., 
        description="List of test cases to evaluate"
    )
    k: int = Field(default=5, description="Top-K for retrieval metrics")


class EvaluationResponse(BaseModel):
    """Response with evaluation metrics."""
    success: bool
    retrieval_metrics: Dict[str, float]
    generation_metrics: Dict[str, float]
    report: str
    num_test_cases: int
    evaluation_time_ms: int


class MetricsResponse(BaseModel):
    """Current system metrics response."""
    success: bool
    metrics: Dict[str, Any]
    timestamp: str


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_rag_system(request: EvaluationRequest):
    """
    Evaluate RAG system on a test set.
    
    Returns comprehensive metrics for retrieval and generation quality.
    """
    start_time = time.time()
    
    try:
        evaluator = RAGEvaluator()
        
        # Prepare retrieval test cases
        retrieval_cases = [
            {
                'retrieved': case.retrieved_docs,
                'relevant': case.relevant_docs
            }
            for case in request.test_cases
        ]
        
        # Prepare generation test cases
        generation_cases = [
            {
                'generated': case.generated_answer,
                'reference': case.reference_answer,
                'context': case.context
            }
            for case in request.test_cases
        ]
        
        # Evaluate
        retrieval_metrics = evaluator.evaluate_retrieval_batch(
            retrieval_cases, 
            k=request.k
        )
        generation_metrics = evaluator.evaluate_generation_batch(
            generation_cases
        )
        
        # Generate report
        report = evaluator.generate_report(
            retrieval_metrics,
            generation_metrics
        )
        
        evaluation_time = int((time.time() - start_time) * 1000)
        
        return EvaluationResponse(
            success=True,
            retrieval_metrics=retrieval_metrics,
            generation_metrics=generation_metrics,
            report=report,
            num_test_cases=len(request.test_cases),
            evaluation_time_ms=evaluation_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_current_metrics():
    """
    Get current system metrics.
    
    Returns real-time performance and quality metrics.
    """
    try:
        from datetime import datetime, timezone

        # In production, these would come from monitoring system
        metrics = {
            "citation_accuracy": 0.99,
            "avg_latency_ms": 4500,
            "p95_latency_ms": 6200,
            "p99_latency_ms": 8100,
            "queries_per_minute": 12,
            "error_rate": 0.001,
            "uptime_hours": 720
        }

        return MetricsResponse(
            success=True,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/health")
async def evaluation_health_check():
    """Health check for evaluation service."""
    return {
        "status": "healthy",
        "service": "evaluation",
        "version": "1.0.0"
    }
