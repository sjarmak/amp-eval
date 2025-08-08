#!/usr/bin/env python3
"""
Context window usage monitoring and performance degradation assessment.

Tracks how context window utilization affects model performance and provides
recommendations for optimization.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

from .cost_tracking import MODEL_COSTS

logger = logging.getLogger(__name__)


class PerformanceTier(Enum):
    """Performance quality tiers based on context usage."""
    OPTIMAL = "optimal"        # 0-60% context usage
    GOOD = "good"             # 60-75% context usage  
    DEGRADED = "degraded"     # 75-90% context usage
    POOR = "poor"             # 90-95% context usage
    CRITICAL = "critical"     # 95%+ context usage


@dataclass
class ContextUsageMetrics:
    """Metrics for a single evaluation's context usage."""
    model: str
    evaluation_id: str
    task_id: str
    timestamp: float
    
    # Context window metrics
    total_context_tokens: int
    context_limit: int
    context_utilization: float
    
    # Input composition
    system_prompt_tokens: int
    user_prompt_tokens: int
    history_tokens: int
    tool_context_tokens: int
    
    # Performance metrics
    response_tokens: int
    latency_ms: float
    accuracy_score: float
    quality_score: float
    
    # Degradation indicators
    performance_tier: PerformanceTier
    truncation_detected: bool
    repetition_detected: bool
    coherence_score: float
    
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ContextOptimizationSuggestion:
    """Suggestion for optimizing context usage."""
    suggestion_type: str
    priority: str  # high, medium, low
    description: str
    expected_savings: int  # tokens
    implementation_effort: str  # low, medium, high
    

@dataclass
class DegradationReport:
    """Report on performance degradation patterns."""
    model: str
    time_period: str
    total_evaluations: int
    degraded_evaluations: int
    degradation_rate: float
    
    # Performance by context tier
    performance_by_tier: Dict[str, Dict[str, float]]
    
    # Optimization suggestions
    suggestions: List[ContextOptimizationSuggestion]
    
    # Cost impact
    total_wasted_tokens: int
    estimated_wasted_cost: float


class ContextMonitor:
    """Monitor context window usage and performance degradation."""
    
    def __init__(self, db_path: str = "context_monitoring.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for context monitoring."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    evaluation_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    
                    total_context_tokens INTEGER NOT NULL,
                    context_limit INTEGER NOT NULL,
                    context_utilization REAL NOT NULL,
                    
                    system_prompt_tokens INTEGER NOT NULL,
                    user_prompt_tokens INTEGER NOT NULL,
                    history_tokens INTEGER NOT NULL,
                    tool_context_tokens INTEGER NOT NULL,
                    
                    response_tokens INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    accuracy_score REAL NOT NULL,
                    quality_score REAL NOT NULL,
                    
                    performance_tier TEXT NOT NULL,
                    truncation_detected BOOLEAN NOT NULL,
                    repetition_detected BOOLEAN NOT NULL,
                    coherence_score REAL NOT NULL,
                    
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_timestamp ON context_metrics(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_model ON context_metrics(model)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_utilization ON context_metrics(context_utilization)
            """)
    
    def assess_performance_tier(self, context_utilization: float) -> PerformanceTier:
        """Determine performance tier based on context utilization."""
        if context_utilization >= 0.95:
            return PerformanceTier.CRITICAL
        elif context_utilization >= 0.90:
            return PerformanceTier.POOR
        elif context_utilization >= 0.75:
            return PerformanceTier.DEGRADED
        elif context_utilization >= 0.60:
            return PerformanceTier.GOOD
        else:
            return PerformanceTier.OPTIMAL
    
    def detect_response_issues(self, response_text: str, expected_length: int = None) -> Tuple[bool, bool, float]:
        """Detect truncation, repetition, and coherence issues in responses."""
        if not response_text:
            return True, False, 0.0  # Likely truncated if empty
        
        # Detect truncation
        truncation_detected = False
        if response_text.endswith(('...', '[truncated]', 'I apologize, but I')):
            truncation_detected = True
        elif expected_length and len(response_text) < expected_length * 0.5:
            truncation_detected = True
        
        # Detect repetition
        repetition_detected = False
        words = response_text.split()
        if len(words) > 10:
            # Check for repeated phrases
            for i in range(len(words) - 5):
                phrase = ' '.join(words[i:i+3])
                remaining_text = ' '.join(words[i+3:])
                if phrase in remaining_text:
                    repetition_detected = True
                    break
        
        # Simple coherence score based on sentence structure and flow
        coherence_score = 1.0
        sentences = response_text.split('.')
        
        # Penalty for very short or very long sentences
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if avg_sentence_length < 3 or avg_sentence_length > 50:
            coherence_score -= 0.2
        
        # Penalty for repetitive patterns
        if repetition_detected:
            coherence_score -= 0.3
        
        # Penalty for truncation
        if truncation_detected:
            coherence_score -= 0.4
        
        coherence_score = max(0.0, coherence_score)
        
        return truncation_detected, repetition_detected, coherence_score
    
    def record_context_usage(self, metrics: ContextUsageMetrics):
        """Record context usage metrics for analysis."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO context_metrics (
                    model, evaluation_id, task_id, timestamp,
                    total_context_tokens, context_limit, context_utilization,
                    system_prompt_tokens, user_prompt_tokens, history_tokens, tool_context_tokens,
                    response_tokens, latency_ms, accuracy_score, quality_score,
                    performance_tier, truncation_detected, repetition_detected, coherence_score,
                    metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.model, metrics.evaluation_id, metrics.task_id, metrics.timestamp,
                metrics.total_context_tokens, metrics.context_limit, metrics.context_utilization,
                metrics.system_prompt_tokens, metrics.user_prompt_tokens, 
                metrics.history_tokens, metrics.tool_context_tokens,
                metrics.response_tokens, metrics.latency_ms, 
                metrics.accuracy_score, metrics.quality_score,
                metrics.performance_tier.value, metrics.truncation_detected,
                metrics.repetition_detected, metrics.coherence_score,
                json.dumps(metrics.metadata or {})
            ))
    
    def analyze_degradation_patterns(self, model: str, days: int = 30) -> DegradationReport:
        """Analyze performance degradation patterns for a model."""
        since_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            # Overall statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_evaluations,
                    SUM(CASE WHEN performance_tier IN ('degraded', 'poor', 'critical') THEN 1 ELSE 0 END) as degraded_evaluations,
                    AVG(accuracy_score) as avg_accuracy,
                    AVG(quality_score) as avg_quality,
                    AVG(coherence_score) as avg_coherence
                FROM context_metrics
                WHERE model = ? AND timestamp > ?
            """, (model, since_timestamp))
            
            row = cursor.fetchone()
            total_evaluations = row[0] or 0
            degraded_evaluations = row[1] or 0
            degradation_rate = degraded_evaluations / total_evaluations if total_evaluations > 0 else 0
            
            # Performance by tier
            cursor = conn.execute("""
                SELECT 
                    performance_tier,
                    COUNT(*) as count,
                    AVG(accuracy_score) as avg_accuracy,
                    AVG(quality_score) as avg_quality,
                    AVG(coherence_score) as avg_coherence,
                    AVG(latency_ms) as avg_latency
                FROM context_metrics
                WHERE model = ? AND timestamp > ?
                GROUP BY performance_tier
            """, (model, since_timestamp))
            
            performance_by_tier = {}
            for row in cursor.fetchall():
                tier, count, accuracy, quality, coherence, latency = row
                performance_by_tier[tier] = {
                    'count': count,
                    'avg_accuracy': accuracy or 0,
                    'avg_quality': quality or 0,
                    'avg_coherence': coherence or 0,
                    'avg_latency': latency or 0
                }
            
            # Calculate wasted tokens (high context usage with poor performance)
            cursor = conn.execute("""
                SELECT SUM(total_context_tokens)
                FROM context_metrics
                WHERE model = ? AND timestamp > ? 
                AND context_utilization > 0.8 
                AND (accuracy_score < 0.7 OR quality_score < 0.7)
            """, (model, since_timestamp))
            
            wasted_tokens = cursor.fetchone()[0] or 0
        
        # Generate optimization suggestions
        suggestions = self._generate_optimization_suggestions(
            model, performance_by_tier, degradation_rate
        )
        
        # Calculate cost impact
        model_costs = MODEL_COSTS.get(model, {})
        input_cost_per_1k = model_costs.get("input_cost_per_1k", 0.01)
        estimated_wasted_cost = (wasted_tokens / 1000) * input_cost_per_1k
        
        return DegradationReport(
            model=model,
            time_period=f"{days} days",
            total_evaluations=total_evaluations,
            degraded_evaluations=degraded_evaluations,
            degradation_rate=degradation_rate,
            performance_by_tier=performance_by_tier,
            suggestions=suggestions,
            total_wasted_tokens=wasted_tokens,
            estimated_wasted_cost=estimated_wasted_cost
        )
    
    def _generate_optimization_suggestions(self, model: str, performance_by_tier: Dict,
                                         degradation_rate: float) -> List[ContextOptimizationSuggestion]:
        """Generate context optimization suggestions based on analysis."""
        suggestions = []
        
        # High degradation rate suggestions
        if degradation_rate > 0.3:
            suggestions.append(ContextOptimizationSuggestion(
                suggestion_type="prompt_optimization",
                priority="high",
                description="High degradation rate detected. Consider shortening system prompts and using more concise instructions.",
                expected_savings=500,
                implementation_effort="medium"
            ))
        
        # Critical tier usage
        critical_count = performance_by_tier.get('critical', {}).get('count', 0)
        if critical_count > 0:
            suggestions.append(ContextOptimizationSuggestion(
                suggestion_type="context_splitting",
                priority="high",
                description=f"{critical_count} evaluations hit critical context usage. Split long prompts or use chunking strategy.",
                expected_savings=10000,
                implementation_effort="high"
            ))
        
        # Poor tier with low accuracy
        poor_stats = performance_by_tier.get('poor', {})
        if poor_stats.get('avg_accuracy', 1.0) < 0.6:
            suggestions.append(ContextOptimizationSuggestion(
                suggestion_type="history_pruning",
                priority="medium",
                description="Poor accuracy at high context usage. Implement conversation history pruning.",
                expected_savings=2000,
                implementation_effort="medium"
            ))
        
        # General optimization for any degraded performance
        degraded_count = performance_by_tier.get('degraded', {}).get('count', 0)
        if degraded_count > 5:
            suggestions.append(ContextOptimizationSuggestion(
                suggestion_type="template_optimization",
                priority="low",
                description="Multiple degraded evaluations. Review prompt templates for redundancy.",
                expected_savings=1000,
                implementation_effort="low"
            ))
        
        return suggestions
    
    def get_context_efficiency_report(self, model: str = None, days: int = 7) -> Dict[str, Any]:
        """Get efficiency report showing context usage vs performance."""
        since_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        
        with sqlite3.connect(self.db_path) as conn:
            where_clause = "WHERE timestamp > ?"
            params = [since_timestamp]
            
            if model:
                where_clause += " AND model = ?"
                params.append(model)
            
            # Context utilization bins
            cursor = conn.execute(f"""
                SELECT 
                    CASE 
                        WHEN context_utilization < 0.5 THEN 'low'
                        WHEN context_utilization < 0.75 THEN 'medium'
                        WHEN context_utilization < 0.9 THEN 'high'
                        ELSE 'critical'
                    END as utilization_tier,
                    COUNT(*) as count,
                    AVG(accuracy_score) as avg_accuracy,
                    AVG(quality_score) as avg_quality,
                    AVG(latency_ms) as avg_latency,
                    AVG(total_context_tokens) as avg_context_tokens,
                    SUM(CASE WHEN truncation_detected THEN 1 ELSE 0 END) as truncation_count
                FROM context_metrics
                {where_clause}
                GROUP BY utilization_tier
            """, params)
            
            efficiency_data = {}
            for row in cursor.fetchall():
                tier, count, accuracy, quality, latency, tokens, truncations = row
                efficiency_data[tier] = {
                    'count': count,
                    'avg_accuracy': accuracy or 0,
                    'avg_quality': quality or 0,
                    'avg_latency': latency or 0,
                    'avg_context_tokens': tokens or 0,
                    'truncation_rate': (truncations or 0) / count if count > 0 else 0
                }
        
        return {
            'time_period': f"Last {days} days",
            'model': model or "all models",
            'efficiency_by_tier': efficiency_data,
            'recommendation': self._get_efficiency_recommendation(efficiency_data)
        }
    
    def _get_efficiency_recommendation(self, efficiency_data: Dict) -> str:
        """Generate efficiency recommendation based on usage patterns."""
        critical_count = efficiency_data.get('critical', {}).get('count', 0)
        high_count = efficiency_data.get('high', {}).get('count', 0)
        
        if critical_count > 0:
            return "Critical: Immediate context optimization needed to prevent performance degradation"
        elif high_count > efficiency_data.get('medium', {}).get('count', 0):
            return "Warning: High context usage patterns detected, consider optimization"
        else:
            return "Good: Context usage appears efficient with minimal degradation"


def create_context_metrics_from_evaluation(evaluation_id: str, task_id: str, model: str,
                                         prompt_data: Dict[str, Any], response_data: Dict[str, Any],
                                         performance_scores: Dict[str, float]) -> ContextUsageMetrics:
    """Helper function to create context metrics from evaluation data."""
    
    # Extract token counts from prompt data
    system_tokens = prompt_data.get('system_prompt_tokens', 0)
    user_tokens = prompt_data.get('user_prompt_tokens', 0)
    history_tokens = prompt_data.get('history_tokens', 0)
    tool_tokens = prompt_data.get('tool_context_tokens', 0)
    
    total_context = system_tokens + user_tokens + history_tokens + tool_tokens
    context_limit = MODEL_COSTS.get(model, {}).get('context_window', 128000)
    
    # Extract response data
    response_text = response_data.get('text', '')
    response_tokens = response_data.get('tokens', 0)
    latency_ms = response_data.get('latency_ms', 0)
    
    # Create monitor instance to assess issues
    monitor = ContextMonitor()
    truncation, repetition, coherence = monitor.detect_response_issues(response_text)
    
    context_utilization = total_context / context_limit if context_limit > 0 else 0
    performance_tier = monitor.assess_performance_tier(context_utilization)
    
    return ContextUsageMetrics(
        model=model,
        evaluation_id=evaluation_id,
        task_id=task_id,
        timestamp=time.time(),
        total_context_tokens=total_context,
        context_limit=context_limit,
        context_utilization=context_utilization,
        system_prompt_tokens=system_tokens,
        user_prompt_tokens=user_tokens,
        history_tokens=history_tokens,
        tool_context_tokens=tool_tokens,
        response_tokens=response_tokens,
        latency_ms=latency_ms,
        accuracy_score=performance_scores.get('accuracy', 0.0),
        quality_score=performance_scores.get('quality', 0.0),
        performance_tier=performance_tier,
        truncation_detected=truncation,
        repetition_detected=repetition,
        coherence_score=coherence
    )


if __name__ == "__main__":
    # Example usage
    monitor = ContextMonitor()
    
    # Example context metrics
    metrics = ContextUsageMetrics(
        model="gpt-5",
        evaluation_id="test_eval_001",
        task_id="task_001",
        timestamp=time.time(),
        total_context_tokens=80000,
        context_limit=128000,
        context_utilization=0.625,
        system_prompt_tokens=1000,
        user_prompt_tokens=2000,
        history_tokens=70000,
        tool_context_tokens=7000,
        response_tokens=500,
        latency_ms=1500,
        accuracy_score=0.85,
        quality_score=0.8,
        performance_tier=PerformanceTier.GOOD,
        truncation_detected=False,
        repetition_detected=False,
        coherence_score=0.9
    )
    
    monitor.record_context_usage(metrics)
    
    # Generate degradation report
    report = monitor.analyze_degradation_patterns("gpt-5", days=7)
    print(f"Degradation rate: {report.degradation_rate:.1%}")
    print(f"Wasted tokens: {report.total_wasted_tokens}")
    print(f"Estimated wasted cost: ${report.estimated_wasted_cost:.2f}")
    print(f"Suggestions: {len(report.suggestions)}")
    
    for suggestion in report.suggestions:
        print(f"- {suggestion.description} (Priority: {suggestion.priority})")
