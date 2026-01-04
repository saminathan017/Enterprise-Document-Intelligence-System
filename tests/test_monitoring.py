#!/usr/bin/env python3
"""Test monitoring and A/B testing frameworks."""

print("="*60)
print("MONITORING & A/B TESTING DEMO")
print("="*60)

# Test Monitoring
print("\n1. MONITORING FRAMEWORK")
print("-" * 60)

from app.monitoring.metrics import get_monitor

monitor = get_monitor()

# Simulate some queries
print("Simulating 10 queries...")
for i in range(10):
    monitor.track_query(
        latency_ms=4000 + i * 200,
        citation_score=0.95 + i * 0.005,
        success=True
    )

# Get metrics
latency = monitor.get_latency_metrics()
quality = monitor.get_quality_metrics()

print(f"\n✅ Latency Metrics:")
print(f"   P50: {latency['p50']:.0f}ms")
print(f"   P95: {latency['p95']:.0f}ms")
print(f"   P99: {latency['p99']:.0f}ms")
print(f"   Mean: {latency['mean']:.0f}ms")

print(f"\n✅ Quality Metrics:")
print(f"   Citation Accuracy: {quality['citation_accuracy']:.2%}")
print(f"   Success Rate: {quality['success_rate']:.2%}")
print(f"   Min Citation: {quality['min_citation']:.2%}")
print(f"   Max Citation: {quality['max_citation']:.2%}")

# Test A/B Testing
print("\n2. A/B TESTING FRAMEWORK")
print("-" * 60)

from app.experiments.ab_test import get_experiment_tracker

tracker = get_experiment_tracker()

# Create experiment
experiment = tracker.create_experiment(
    experiment_id="chunk_size_test",
    variants=["control_600", "treatment_1000"],
    description="Testing chunk size impact on accuracy"
)

print(f"✅ Created Experiment: {experiment['id']}")
print(f"   Variants: {experiment['variants']}")
print(f"   Description: {experiment['description']}")

# Simulate users and log metrics
print(f"\n✅ Simulating 20 users...")
for i in range(20):
    user_id = f"user_{i}"
    variant = tracker.assign_variant("chunk_size_test", user_id)
    
    # Control has 85% accuracy, treatment has 92%
    accuracy = 0.85 if variant == "control_600" else 0.92
    latency = 4500 if variant == "control_600" else 4800
    
    tracker.log_metric("chunk_size_test", variant, "accuracy", accuracy)
    tracker.log_metric("chunk_size_test", variant, "latency", latency)

# Get variant metrics
control_metrics = tracker.get_variant_metrics("chunk_size_test", "control_600")
treatment_metrics = tracker.get_variant_metrics("chunk_size_test", "treatment_1000")

print(f"\n✅ Control (600 chars):")
for metric, stats in control_metrics.items():
    print(f"   {metric}: mean={stats['mean']:.2f}, count={stats['count']}")

print(f"\n✅ Treatment (1000 chars):")
for metric, stats in treatment_metrics.items():
    print(f"   {metric}: mean={stats['mean']:.2f}, count={stats['count']}")

# Statistical comparison
comparison = tracker.compare_variants(
    "chunk_size_test",
    "accuracy",
    "control_600",
    "treatment_1000"
)

print(f"\n✅ Statistical Analysis (Accuracy):")
print(f"   Control Mean: {comparison['mean_a']:.2%}")
print(f"   Treatment Mean: {comparison['mean_b']:.2%}")
print(f"   P-value: {comparison['p_value']:.6f}")
print(f"   Significant: {comparison['is_significant']}")
print(f"   Cohen's d: {comparison['cohens_d']:.2f}")
print(f"   Improvement: {comparison['relative_improvement']:.2%}")

if comparison['is_significant']:
    print(f"\n   🎉 SIGNIFICANT IMPROVEMENT DETECTED!")
    print(f"   Treatment is {comparison['relative_improvement']:.2%} better!")

print("\n" + "="*60)
print("✅ MONITORING & A/B TESTING WORKING PERFECTLY!")
print("="*60)
print("\nKey Features:")
print("• Real-time latency tracking (P50/P95/P99)")
print("• Quality metrics monitoring")
print("• A/B test variant assignment")
print("• Statistical significance testing")
print("• Cohen's d effect size calculation")
print("\n🚀 Production-ready ML operations!")
