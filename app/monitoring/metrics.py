"""
Model Monitoring Framework
Tracks latency, quality metrics, and embedding drift.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
import numpy as np
import time


class ModelMonitor:
    """Production monitoring for RAG system."""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize monitor with sliding window.
        
        Args:
            window_size: Number of recent queries to track
        """
        self.window_size = window_size
        
        # Latency tracking
        self.latencies = deque(maxlen=window_size)
        
        # Quality metrics
        self.citation_scores = deque(maxlen=window_size)
        self.query_success = deque(maxlen=window_size)
        
        # Embedding drift
        self.embedding_samples = deque(maxlen=100)
        self.baseline_embedding = None
        
        # Error tracking
        self.errors = deque(maxlen=100)
        
        # Timestamps
        self.query_timestamps = deque(maxlen=window_size)
    
    def track_query(
        self,
        latency_ms: float,
        citation_score: float,
        success: bool,
        embedding: Optional[np.ndarray] = None
    ):
        """
        Track a single query execution.
        
        Args:
            latency_ms: Query latency in milliseconds
            citation_score: Average citation score (0-1)
            success: Whether query succeeded
            embedding: Optional query embedding for drift detection
        """
        self.latencies.append(latency_ms)
        self.citation_scores.append(citation_score)
        self.query_success.append(1 if success else 0)
        self.query_timestamps.append(datetime.utcnow())
        
        if embedding is not None:
            self.embedding_samples.append(embedding)
            
            if self.baseline_embedding is None and len(self.embedding_samples) >= 10:
                # Set baseline from first 10 samples
                self.baseline_embedding = np.mean(
                    list(self.embedding_samples)[:10], 
                    axis=0
                )
    
    def track_error(self, error_type: str, error_message: str):
        """Track an error occurrence."""
        self.errors.append({
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.utcnow()
        })
    
    def get_latency_metrics(self) -> Dict[str, float]:
        """
        Get latency percentiles.
        
        Returns:
            Dict with P50, P95, P99 latencies in ms
        """
        if not self.latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0}
        
        latencies = sorted(self.latencies)
        n = len(latencies)
        
        return {
            "p50": latencies[int(n * 0.50)],
            "p95": latencies[int(n * 0.95)],
            "p99": latencies[int(n * 0.99)],
            "mean": np.mean(latencies)
        }
    
    def get_quality_metrics(self) -> Dict[str, float]:
        """
        Get quality metrics.
        
        Returns:
            Dict with citation accuracy and success rate
        """
        if not self.citation_scores:
            return {"citation_accuracy": 0.0, "success_rate": 0.0}
        
        return {
            "citation_accuracy": np.mean(self.citation_scores),
            "success_rate": np.mean(self.query_success),
            "min_citation": min(self.citation_scores),
            "max_citation": max(self.citation_scores)
        }
    
    def get_throughput_metrics(self) -> Dict[str, float]:
        """
        Get throughput metrics.
        
        Returns:
            Dict with queries per minute
        """
        if len(self.query_timestamps) < 2:
            return {"queries_per_minute": 0.0}
        
        # Calculate time span
        time_span = (
            self.query_timestamps[-1] - self.query_timestamps[0]
        ).total_seconds() / 60.0  # Convert to minutes
        
        if time_span == 0:
            return {"queries_per_minute": 0.0}
        
        qpm = len(self.query_timestamps) / time_span
        
        return {
            "queries_per_minute": qpm,
            "total_queries": len(self.query_timestamps)
        }
    
    def detect_embedding_drift(self) -> Dict[str, Any]:
        """
        Detect embedding drift from baseline.
        
        Returns:
            Dict with drift metrics and alert status
        """
        if self.baseline_embedding is None or len(self.embedding_samples) < 10:
            return {
                "drift_detected": False,
                "drift_score": 0.0,
                "message": "Insufficient data for drift detection"
            }
        
        # Calculate recent mean embedding
        recent_embeddings = list(self.embedding_samples)[-10:]
        recent_mean = np.mean(recent_embeddings, axis=0)
        
        # Calculate cosine similarity
        dot_product = np.dot(self.baseline_embedding, recent_mean)
        norm_baseline = np.linalg.norm(self.baseline_embedding)
        norm_recent = np.linalg.norm(recent_mean)
        
        similarity = dot_product / (norm_baseline * norm_recent)
        drift_score = 1.0 - similarity
        
        # Alert if drift > 10%
        drift_detected = drift_score > 0.10
        
        return {
            "drift_detected": drift_detected,
            "drift_score": float(drift_score),
            "similarity": float(similarity),
            "message": "Significant drift detected!" if drift_detected else "Normal"
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get error summary.
        
        Returns:
            Dict with error counts and recent errors
        """
        if not self.errors:
            return {
                "total_errors": 0,
                "error_rate": 0.0,
                "recent_errors": []
            }
        
        # Count errors by type
        error_counts = defaultdict(int)
        for error in self.errors:
            error_counts[error["type"]] += 1
        
        # Calculate error rate
        total_queries = len(self.query_timestamps)
        error_rate = len(self.errors) / total_queries if total_queries > 0 else 0.0
        
        return {
            "total_errors": len(self.errors),
            "error_rate": error_rate,
            "error_counts": dict(error_counts),
            "recent_errors": list(self.errors)[-5:]  # Last 5 errors
        }
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring report.
        
        Returns:
            Dict with all metrics
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "latency": self.get_latency_metrics(),
            "quality": self.get_quality_metrics(),
            "throughput": self.get_throughput_metrics(),
            "drift": self.detect_embedding_drift(),
            "errors": self.get_error_summary()
        }
    
    def check_alerts(self) -> List[Dict[str, str]]:
        """
        Check for alert conditions.
        
        Returns:
            List of active alerts
        """
        alerts = []
        
        # Check latency
        latency = self.get_latency_metrics()
        if latency["p95"] > 10000:  # 10 seconds
            alerts.append({
                "severity": "high",
                "type": "latency",
                "message": f"P95 latency is {latency['p95']:.0f}ms (threshold: 10000ms)"
            })
        
        # Check quality
        quality = self.get_quality_metrics()
        if quality["citation_accuracy"] < 0.80:  # 80%
            alerts.append({
                "severity": "medium",
                "type": "quality",
                "message": f"Citation accuracy is {quality['citation_accuracy']:.2%} (threshold: 80%)"
            })
        
        # Check drift
        drift = self.detect_embedding_drift()
        if drift["drift_detected"]:
            alerts.append({
                "severity": "medium",
                "type": "drift",
                "message": f"Embedding drift detected: {drift['drift_score']:.2%}"
            })
        
        # Check error rate
        errors = self.get_error_summary()
        if errors["error_rate"] > 0.05:  # 5%
            alerts.append({
                "severity": "high",
                "type": "errors",
                "message": f"Error rate is {errors['error_rate']:.2%} (threshold: 5%)"
            })
        
        return alerts


# Global monitor instance
_monitor = None


def get_monitor() -> ModelMonitor:
    """Get global monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = ModelMonitor()
    return _monitor
