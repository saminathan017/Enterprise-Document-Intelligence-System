"""
A/B Testing Framework for RAG System
Enables controlled experiments to compare model variants.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import hashlib
import numpy as np
from scipy import stats


class ExperimentTracker:
    """Track A/B test experiments and analyze results."""
    
    def __init__(self):
        """Initialize experiment tracker."""
        self.experiments = {}  # experiment_id -> experiment data
        self.variant_assignments = {}  # user_id -> variant
        self.metrics = defaultdict(lambda: defaultdict(list))  # experiment -> variant -> metrics
    
    def create_experiment(
        self,
        experiment_id: str,
        variants: List[str],
        description: str,
        allocation: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Create a new A/B test experiment.
        
        Args:
            experiment_id: Unique experiment identifier
            variants: List of variant names (e.g., ['control', 'treatment'])
            description: Experiment description
            allocation: Optional variant allocation percentages
            
        Returns:
            Experiment configuration
        """
        if allocation is None:
            # Equal allocation by default
            allocation = {v: 1.0 / len(variants) for v in variants}
        
        self.experiments[experiment_id] = {
            "id": experiment_id,
            "variants": variants,
            "description": description,
            "allocation": allocation,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        return self.experiments[experiment_id]
    
    def assign_variant(
        self,
        experiment_id: str,
        user_id: str
    ) -> str:
        """
        Assign user to a variant using consistent hashing.
        
        Args:
            experiment_id: Experiment ID
            user_id: User ID
            
        Returns:
            Assigned variant name
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Check if already assigned
        key = f"{experiment_id}:{user_id}"
        if key in self.variant_assignments:
            return self.variant_assignments[key]
        
        # Consistent hashing for assignment
        experiment = self.experiments[experiment_id]
        variants = experiment["variants"]
        allocation = experiment["allocation"]
        
        # Hash user ID to get deterministic random value
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        random_value = (hash_value % 10000) / 10000.0  # 0.0 to 1.0
        
        # Assign based on allocation
        cumulative = 0.0
        for variant in variants:
            cumulative += allocation[variant]
            if random_value < cumulative:
                self.variant_assignments[key] = variant
                return variant
        
        # Fallback to first variant
        self.variant_assignments[key] = variants[0]
        return variants[0]
    
    def log_metric(
        self,
        experiment_id: str,
        variant: str,
        metric_name: str,
        value: float
    ):
        """
        Log a metric for a variant.
        
        Args:
            experiment_id: Experiment ID
            variant: Variant name
            metric_name: Metric name (e.g., 'latency', 'accuracy')
            value: Metric value
        """
        self.metrics[experiment_id][f"{variant}:{metric_name}"].append(value)
    
    def get_variant_metrics(
        self,
        experiment_id: str,
        variant: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Get aggregated metrics for a variant.
        
        Args:
            experiment_id: Experiment ID
            variant: Variant name
            
        Returns:
            Dict of metric statistics
        """
        results = {}
        
        for key, values in self.metrics[experiment_id].items():
            if key.startswith(f"{variant}:"):
                metric_name = key.split(":", 1)[1]
                
                if values:
                    results[metric_name] = {
                        "mean": np.mean(values),
                        "std": np.std(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }
        
        return results
    
    def compare_variants(
        self,
        experiment_id: str,
        metric_name: str,
        variant_a: str,
        variant_b: str,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Compare two variants using t-test.
        
        Args:
            experiment_id: Experiment ID
            metric_name: Metric to compare
            variant_a: First variant
            variant_b: Second variant
            alpha: Significance level (default: 0.05)
            
        Returns:
            Statistical comparison results
        """
        key_a = f"{variant_a}:{metric_name}"
        key_b = f"{variant_b}:{metric_name}"
        
        values_a = self.metrics[experiment_id].get(key_a, [])
        values_b = self.metrics[experiment_id].get(key_b, [])
        
        if not values_a or not values_b:
            return {
                "error": "Insufficient data for comparison",
                "variant_a_count": len(values_a),
                "variant_b_count": len(values_b)
            }
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(values_a, values_b)
        
        # Calculate effect size (Cohen's d)
        mean_a = np.mean(values_a)
        mean_b = np.mean(values_b)
        pooled_std = np.sqrt(
            (np.std(values_a)**2 + np.std(values_b)**2) / 2
        )
        cohens_d = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0.0
        
        # Determine significance
        is_significant = p_value < alpha
        
        # Calculate relative improvement
        relative_improvement = (mean_b - mean_a) / mean_a if mean_a != 0 else 0.0
        
        return {
            "metric": metric_name,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "mean_a": mean_a,
            "mean_b": mean_b,
            "t_statistic": t_stat,
            "p_value": p_value,
            "is_significant": is_significant,
            "cohens_d": cohens_d,
            "relative_improvement": relative_improvement,
            "sample_size_a": len(values_a),
            "sample_size_b": len(values_b),
            "confidence_level": 1 - alpha
        }
    
    def generate_experiment_report(
        self,
        experiment_id: str
    ) -> str:
        """
        Generate a comprehensive experiment report.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Formatted report string
        """
        if experiment_id not in self.experiments:
            return f"Experiment {experiment_id} not found"
        
        experiment = self.experiments[experiment_id]
        report = []
        
        report.append("=" * 70)
        report.append(f"A/B TEST EXPERIMENT REPORT: {experiment_id}")
        report.append("=" * 70)
        report.append(f"Description: {experiment['description']}")
        report.append(f"Created: {experiment['created_at']}")
        report.append(f"Status: {experiment['status']}")
        report.append("")
        
        report.append("VARIANTS:")
        report.append("-" * 70)
        for variant in experiment["variants"]:
            allocation = experiment["allocation"][variant]
            metrics = self.get_variant_metrics(experiment_id, variant)
            
            report.append(f"\n{variant.upper()} (Allocation: {allocation:.1%})")
            
            if metrics:
                for metric_name, stats_dict in metrics.items():
                    report.append(
                        f"  {metric_name:20s}: "
                        f"mean={stats_dict['mean']:.2f}, "
                        f"std={stats_dict['std']:.2f}, "
                        f"n={stats_dict['count']}"
                    )
            else:
                report.append("  No data collected yet")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def stop_experiment(self, experiment_id: str):
        """Stop an experiment."""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]["status"] = "stopped"
            self.experiments[experiment_id]["stopped_at"] = datetime.utcnow().isoformat()


# Global experiment tracker
_tracker = None


def get_experiment_tracker() -> ExperimentTracker:
    """Get global experiment tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ExperimentTracker()
    return _tracker
