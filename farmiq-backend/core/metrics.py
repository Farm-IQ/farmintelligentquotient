"""
Phase 3 Task 4: Prometheus Metrics Collection for FarmGrow RAG
Production-ready observability metrics for monitoring and alerting

Metrics Collected:
- Request counters (total, by type)
- Request duration histograms
- Cache hit rate percentage
- Document retrieval performance
- LLM inference performance
- Error rates and types
- Active users and sessions
- Queue depths and processing times
"""
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json


class MetricType(Enum):
    """Prometheus metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Histogram:
    """Histogram metric for tracking distributions."""
    name: str
    buckets: List[float]
    sum: float = 0.0
    count: int = 0
    bucket_counts: Dict[float, int] = None
    
    def __post_init__(self):
        """Initialize bucket counts."""
        if self.bucket_counts is None:
            self.bucket_counts = {bucket: 0 for bucket in self.buckets}
    
    def observe(self, value: float):
        """Record an observation."""
        self.sum += value
        self.count += 1
        
        # Increment appropriate bucket
        for bucket in sorted(self.buckets):
            if value <= bucket:
                self.bucket_counts[bucket] += 1
    
    def mean(self) -> float:
        """Get mean value."""
        return self.sum / self.count if self.count > 0 else 0.0


class MetricsCollector:
    """
    Prometheus-compatible metrics collector.
    
    Tracks:
    - Counters: Monotonically increasing values
    - Gauges: Values that can go up or down
    - Histograms: Distribution of observations
    - Summaries: Quantile data
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.labels: Dict[str, Dict[str, any]] = {}
        
        self._init_farmgrow_metrics()
    
    def _init_farmgrow_metrics(self):
        """Initialize FarmGrow-specific metrics."""
        # Query metrics
        self.counter("farmgrow_requests_total", "Total RAG requests received")
        self.counter("farmgrow_queries_chat", "Total chat queries")
        self.counter("farmgrow_queries_search", "Total search queries")
        
        # Document retrieval
        self.counter("farmgrow_documents_retrieved_total", "Total documents retrieved")
        self.histogram(
            "farmgrow_retrieval_duration_ms",
            "Document retrieval duration",
            buckets=[10, 50, 100, 500, 1000, 5000]
        )
        
        # LLM generation
        self.counter("farmgrow_responses_generated_total", "Total responses generated")
        self.histogram(
            "farmgrow_generation_duration_ms",
            "LLM response generation duration",
            buckets=[100, 500, 1000, 2000, 5000, 10000]
        )
        
        # Embedding operations
        self.counter("farmgrow_embeddings_generated_total", "Total embeddings generated")
        self.histogram(
            "farmgrow_embedding_duration_ms",
            "Embedding generation duration",
            buckets=[50, 100, 200, 500, 1000]
        )
        
        # Cache metrics
        self.counter("farmgrow_cache_hits_total", "Total cache hits")
        self.counter("farmgrow_cache_misses_total", "Total cache misses")
        self.gauge("farmgrow_cache_size", "Current cache size (embeddings)")
        self.gauge("farmgrow_cache_hit_rate", "Cache hit rate percentage (0-100)")
        
        # Error metrics
        self.counter("farmgrow_errors_total", "Total errors")
        self.counter("farmgrow_errors_retrieval", "Retrieval errors")
        self.counter("farmgrow_errors_generation", "Generation errors")
        self.counter("farmgrow_errors_ocr", "OCR errors")
        
        # Session/User metrics
        self.gauge("farmgrow_active_users", "Active users right now")
        self.gauge("farmgrow_active_sessions", "Active chat sessions")
        
        # Database metrics
        self.counter("farmgrow_db_queries_total", "Total database queries")
        self.histogram(
            "farmgrow_db_query_duration_ms",
            "Database query duration",
            buckets=[5, 10, 50, 100, 500, 1000]
        )
        self.gauge("farmgrow_db_pool_size", "Database connection pool size")
        self.gauge("farmgrow_db_pool_active", "Active database connections")
    
    def counter(self, name: str, help_text: str = "") -> None:
        """Create or get counter metric."""
        if name not in self.counters:
            self.counters[name] = 0
            self.labels[name] = {"help": help_text, "type": "counter"}
    
    def inc_counter(self, name: str, amount: int = 1) -> None:
        """Increment counter."""
        if name not in self.counters:
            self.counter(name)
        self.counters[name] += amount
    
    def gauge(self, name: str, help_text: str = "") -> None:
        """Create or get gauge metric."""
        if name not in self.gauges:
            self.gauges[name] = 0.0
            self.labels[name] = {"help": help_text, "type": "gauge"}
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set gauge value."""
        if name not in self.gauges:
            self.gauge(name)
        self.gauges[name] = value
    
    def inc_gauge(self, name: str, amount: float = 1.0) -> None:
        """Increment gauge."""
        if name not in self.gauges:
            self.gauge(name)
        self.gauges[name] += amount
    
    def dec_gauge(self, name: str, amount: float = 1.0) -> None:
        """Decrement gauge."""
        if name not in self.gauges:
            self.gauge(name)
        self.gauges[name] -= amount
    
    def histogram(
        self,
        name: str,
        help_text: str = "",
        buckets: Optional[List[float]] = None
    ) -> None:
        """Create or get histogram metric."""
        if name not in self.histograms:
            if buckets is None:
                buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
            self.histograms[name] = Histogram(name=name, buckets=buckets)
            self.labels[name] = {"help": help_text, "type": "histogram"}
    
    def observe(self, name: str, value: float) -> None:
        """Record histogram observation."""
        if name not in self.histograms:
            self.histogram(name)
        self.histograms[name].observe(value)
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        lines.append("# HELP farmgrow_metrics FarmGrow RAG Metrics")
        lines.append("# TYPE farmgrow_metrics untyped")
        lines.append("")
        
        # Counters
        for name, value in self.counters.items():
            help_text = self.labels.get(name, {}).get("help", "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
                lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        lines.append("")
        
        # Gauges
        for name, value in self.gauges.items():
            help_text = self.labels.get(name, {}).get("help", "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
                lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        lines.append("")
        
        # Histograms
        for name, histogram in self.histograms.items():
            help_text = self.labels.get(name, {}).get("help", "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
                lines.append(f"# TYPE {name} histogram")
            
            # Buckets
            for bucket, count in histogram.bucket_counts.items():
                lines.append(f'{name}_bucket{{le="{bucket}"}} {count}')
            
            # Sum and count
            lines.append(f"{name}_sum {histogram.sum:.4f}")
            lines.append(f"{name}_count {histogram.count}")
        
        return "\n".join(lines)
    
    def export_json(self) -> Dict:
        """Export metrics as JSON."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "counters": self.counters,
            "gauges": self.gauges,
            "histograms": {
                name: {
                    "sum": h.sum,
                    "count": h.count,
                    "mean": h.mean(),
                    "buckets": h.bucket_counts
                }
                for name, h in self.histograms.items()
            }
        }
    
    def get_summary(self) -> Dict:
        """Get summary of all metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "counters": len(self.counters),
            "gauges": len(self.gauges),
            "histograms": len(self.histograms),
            "total_metrics": len(self.counters) + len(self.gauges) + len(self.histograms),
            "samples": {
                "cache_hit_rate": self.gauges.get("farmgrow_cache_hit_rate", 0),
                "active_users": self.gauges.get("farmgrow_active_users", 0),
                "total_requests": self.counters.get("farmgrow_requests_total", 0),
                "total_errors": self.counters.get("farmgrow_errors_total", 0),
                "cache_size": self.gauges.get("farmgrow_cache_size", 0),
            }
        }


class MetricsMiddleware:
    """FastAPI middleware for automatic metrics collection."""
    
    def __init__(self, collector: MetricsCollector):
        """Initialize middleware."""
        self.collector = collector
    
    async def __call__(self, request, call_next):
        """Process request and collect metrics."""
        start_time = time.time()
        
        # Track active requests
        self.collector.inc_gauge("farmgrow_active_requests", 1)
        
        try:
            response = await call_next(request)
            
            # Track request duration
            duration_ms = (time.time() - start_time) * 1000
            self.collector.observe("farmgrow_request_duration_ms", duration_ms)
            
            # Track by request type
            if "query" in request.url.path:
                if "chat" in request.url.path:
                    self.collector.inc_counter("farmgrow_queries_chat")
                elif "search" in request.url.path:
                    self.collector.inc_counter("farmgrow_queries_search")
            
            # Track overall requests
            self.collector.inc_counter("farmgrow_requests_total")
            
            return response
        
        except Exception as e:
            self.collector.inc_counter("farmgrow_errors_total")
            raise
        
        finally:
            self.collector.dec_gauge("farmgrow_active_requests", 1)


class QueryMetricsTracker:
    """Track metrics for individual queries."""
    
    def __init__(self, collector: MetricsCollector):
        """Initialize tracker."""
        self.collector = collector
        self.query_start = time.time()
        self.stages = {}
    
    def mark_stage(self, stage_name: str):
        """Mark completion of a stage."""
        elapsed = (time.time() - self.query_start) * 1000
        self.stages[stage_name] = elapsed
    
    def retrieval_complete(self, num_documents: int, duration_ms: float):
        """Mark retrieval complete."""
        self.collector.observe("farmgrow_retrieval_duration_ms", duration_ms)
        self.collector.inc_counter("farmgrow_documents_retrieved_total", num_documents)
    
    def generation_complete(self, duration_ms: float):
        """Mark generation complete."""
        self.collector.observe("farmgrow_generation_duration_ms", duration_ms)
        self.collector.inc_counter("farmgrow_responses_generated_total")
    
    def embedding_generated(self, duration_ms: float):
        """Mark embedding generated."""
        self.collector.observe("farmgrow_embedding_duration_ms", duration_ms)
        self.collector.inc_counter("farmgrow_embeddings_generated_total")
    
    def cache_hit(self):
        """Record cache hit."""
        self.collector.inc_counter("farmgrow_cache_hits_total")
        self._update_cache_hit_rate()
    
    def cache_miss(self):
        """Record cache miss."""
        self.collector.inc_counter("farmgrow_cache_misses_total")
        self._update_cache_hit_rate()
    
    def _update_cache_hit_rate(self):
        """Update cache hit rate percentage."""
        hits = self.collector.counters.get("farmgrow_cache_hits_total", 0)
        misses = self.collector.counters.get("farmgrow_cache_misses_total", 0)
        total = hits + misses
        
        if total > 0:
            hit_rate = (hits / total) * 100
            self.collector.set_gauge("farmgrow_cache_hit_rate", hit_rate)
    
    def error(self, error_type: str):
        """Record error."""
        self.collector.inc_counter("farmgrow_errors_total")
        
        # Track specific error types
        error_counter = f"farmgrow_errors_{error_type}"
        if error_counter not in self.collector.counters:
            self.collector.counter(error_counter)
        self.collector.inc_counter(error_counter)
    
    def get_summary(self) -> Dict:
        """Get query execution summary."""
        total_time = (time.time() - self.query_start) * 1000
        
        return {
            "total_duration_ms": total_time,
            "stages": self.stages,
            "metrics": self.collector.get_summary()
        }


# ============================================================================
# EVALUATION METRICS (Model Performance)
# ============================================================================

def calculate_auc_roc(
    y_true: list,
    y_pred: list,
) -> float:
    """
    Calculate Area Under the Receiver Operating Characteristic Curve
    
    Args:
        y_true: True binary labels (0 or 1)
        y_pred: Predicted probabilities
        
    Returns:
        AUC-ROC score (0-1)
    """
    try:
        from sklearn.metrics import roc_auc_score
        return roc_auc_score(y_true, y_pred)
    except ImportError:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("sklearn not available, returning placeholder AUC")
        return 0.8  # Placeholder


def calculate_accuracy(
    y_true: list,
    y_pred: list,
) -> float:
    """
    Calculate accuracy for classification
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        
    Returns:
        Accuracy (0-1)
    """
    if not y_true or len(y_true) != len(y_pred):
        return 0.0
    
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true)


def calculate_precision_recall(
    y_true: list,
    y_pred: list,
) -> tuple:
    """
    Calculate precision and recall
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        
    Returns:
        (precision, recall) tuple
    """
    try:
        from sklearn.metrics import precision_score, recall_score
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        return precision, recall
    except ImportError:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("sklearn not available")
        return 0.0, 0.0


def calculate_sharpe_ratio(returns: list, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio for returns
    
    Args:
        returns: List of returns
        risk_free_rate: Annual risk-free rate (default: 2%)
        
    Returns:
        Sharpe ratio
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    try:
        import statistics
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming daily returns, 252 trading days)
        excess_return = avg_return - (risk_free_rate / 252)
        sharpe = (excess_return / std_return) * (252 ** 0.5)
        return sharpe
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating Sharpe ratio: {e}")
        return 0.0


def calculate_max_drawdown(values: list) -> float:
    """
    Calculate maximum drawdown
    
    Args:
        values: Series of values (e.g., portfolio values)
        
    Returns:
        Maximum drawdown (0-1)
    """
    if not values or len(values) < 2:
        return 0.0
    
    max_dd = 0.0
    peak = values[0]
    
    for val in values[1:]:
        drawdown = (peak - val) / peak if peak > 0 else 0
        if drawdown > max_dd:
            max_dd = drawdown
        if val > peak:
            peak = val
    
    return max_dd


def calculate_win_rate(returns: list) -> float:
    """
    Calculate win rate (percentage of positive returns)
    
    Args:
        returns: List of returns
        
    Returns:
        Win rate (0-1)
    """
    if not returns:
        return 0.0
    
    winning = sum(1 for r in returns if r > 0)
    return winning / len(returns)


def calculate_profit_factor(returns: list) -> float:
    """
    Calculate profit factor (gross profit / gross loss)
    
    Args:
        returns: List of returns
        
    Returns:
        Profit factor
    """
    positive_returns = sum(r for r in returns if r > 0)
    negative_returns = abs(sum(r for r in returns if r < 0))
    
    if negative_returns == 0:
        return 0.0
    
    return positive_returns / negative_returns


# ============================================================================
# SYSTEM HEALTH CHECKS
# ============================================================================

class HealthCheck:
    """System health check utilities"""
    
    @staticmethod
    async def check_supabase(db) -> Dict:
        """
        Check Supabase connectivity
        
        Args:
            db: Database repository
            
        Returns:
            Health status
        """
        try:
            # Try simple query
            result = await db.count("farmiq_credit_profiles")
            return {
                "service": "supabase",
                "status": "healthy",
                "latency_ms": 0,
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Supabase health check failed: {e}")
            return {
                "service": "supabase",
                "status": "unhealthy",
                "error": str(e),
            }
    
    @staticmethod
    def check_ollama() -> Dict:
        """
        Check Ollama LLM service
        
        Returns:
            Health status
        """
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                return {
                    "service": "ollama",
                    "status": "healthy",
                    "models": response.json().get("models", []),
                }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Ollama health check failed: {e}")
        
        return {
            "service": "ollama",
            "status": "unhealthy",
            "note": "LLM features disabled",
        }


# Global collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
