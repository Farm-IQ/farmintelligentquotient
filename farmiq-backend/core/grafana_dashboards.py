"""
FarmIQ Integrated Grafana Dashboard Configuration (Phase 5 - Modern Implementation)
Unified observability dashboards for FarmGrow RAG, FarmScore ML, and FarmSuite Intelligence
Integrates with Prometheus, Loki, and Grafana for comprehensive monitoring

Dashboards:
1. FarmGrow RAG: Document ingestion, embeddings, Ollama retrieval, query performance
2. FarmScore ML: Yield prediction, expense forecasting, disease classification, market prediction
3. FarmSuite Intelligence: Worker & farm intelligence, API performance, caching metrics
4. System Overview: Overall health, request volume, latency trends
5. Security: Authentication, rate limiting, security events, audit logs
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class PanelType(str, Enum):
    """Grafana panel types"""
    GRAPH = "graph"
    STAT = "stat"
    GAUGE = "gauge"
    TABLE = "table"
    HEATMAP = "heatmap"
    PIE = "piechart"
    BAR_GAUGE = "bargauge"
    ALERT_LIST = "alertlist"


class DashboardRefresh(str, Enum):
    """Dashboard refresh intervals"""
    THIRTY_SECONDS = "30s"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    TEN_MINUTES = "10m"


class ThresholdMode(str, Enum):
    """Threshold mode for panels"""
    ABSOLUTE = "absolute"
    PERCENTAGE = "percentage"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PrometheusTarget:
    """Prometheus data source target"""
    expr: str
    refId: str = "A"
    legendFormat: str = ""
    interval: str = "1m"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Threshold:
    """Panel threshold configuration"""
    color: str
    value: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"color": self.color, "value": self.value}


@dataclass
class GrafanaPanel:
    """Individual dashboard panel"""
    id: int
    title: str
    type: PanelType
    targets: List[Dict[str, Any]]
    gridPos: Dict[str, int]  # {h, w, x, y}
    options: Dict[str, Any] = field(default_factory=dict)
    fieldConfig: Dict[str, Any] = field(default_factory=dict)
    datasource: str = "Prometheus"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Grafana panel JSON"""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "targets": self.targets,
            "gridPos": self.gridPos,
            "options": self.options,
            "fieldConfig": self.fieldConfig,
            "datasource": self.datasource,
        }


@dataclass
class GrafanaDashboard:
    """Complete Grafana dashboard configuration"""
    title: str
    uid: str
    description: str
    tags: List[str]
    timezone: str = "browser"
    refresh: DashboardRefresh = DashboardRefresh.ONE_MINUTE
    panels: List[GrafanaPanel] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Grafana dashboard JSON"""
        return {
            "dashboard": {
                "title": self.title,
                "uid": self.uid,
                "description": self.description,
                "tags": self.tags,
                "timezone": self.timezone,
                "refresh": self.refresh.value,
                "panels": [p.to_dict() for p in self.panels],
                "schemaVersion": 38,
                "version": 0,
            }
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# DASHBOARD BUILDER HELPER CLASS
# ============================================================================

class DashboardPanelFactory:
    """Factory for creating common panel types"""
    
    @staticmethod
    def create_stat_panel(
        title: str,
        query: str,
        panel_id: int = 1,
        x: int = 0,
        y: int = 0,
        width: int = 4,
        height: int = 3,
        unit: str = "short",
    ) -> GrafanaPanel:
        """Create a stat panel (big number)"""
        return GrafanaPanel(
            id=panel_id,
            title=title,
            type=PanelType.STAT,
            targets=[{"expr": query, "refId": "A", "legendFormat": title}],
            gridPos={"h": height, "w": width, "x": x, "y": y},
            fieldConfig={
                "defaults": {
                    "unit": unit,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 70},
                            {"color": "red", "value": 90},
                        ]
                    }
                }
            }
        )
    
    @staticmethod
    def create_graph_panel(
        title: str,
        queries: Dict[str, str],
        panel_id: int = 1,
        x: int = 0,
        y: int = 0,
        width: int = 12,
        height: int = 8,
        y_axis_label: str = "",
    ) -> GrafanaPanel:
        """Create a time-series graph panel"""
        targets = [
            {"expr": expr, "refId": refId, "legendFormat": refId}
            for refId, expr in queries.items()
        ]
        
        return GrafanaPanel(
            id=panel_id,
            title=title,
            type=PanelType.GRAPH,
            targets=targets,
            gridPos={"h": height, "w": width, "x": x, "y": y},
            options={
                "legend": {"calcs": ["mean", "max", "min"], "showLegend": True}
            }
        )
    
    @staticmethod
    def create_gauge_panel(
        title: str,
        query: str,
        panel_id: int = 1,
        x: int = 0,
        y: int = 0,
        width: int = 4,
        height: int = 4,
        min_value: int = 0,
        max_value: int = 100,
    ) -> GrafanaPanel:
        """Create a gauge panel (circular meter)"""
        return GrafanaPanel(
            id=panel_id,
            title=title,
            type=PanelType.GAUGE,
            targets=[{"expr": query, "refId": "A", "legendFormat": title}],
            gridPos={"h": height, "w": width, "x": x, "y": y},
            options={
                "orientation": "auto",
                "showThresholdLabels": False,
                "showThresholdMarkers": True,
            },
            fieldConfig={
                "defaults": {
                    "unit": "short",
                    "min": min_value,
                    "max": max_value,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 70},
                            {"color": "red", "value": 90},
                        ]
                    }
                }
            }
        )


# ============================================================================
# DASHBOARD 1: FARMGROW RAG SYSTEM DASHBOARD
# ============================================================================

def create_farmgrow_dashboard() -> GrafanaDashboard:
    """FarmGrow RAG System Dashboard
    
    Monitors:
    - Document ingestion pipeline
    - Embeddings generation and cache
    - Ollama LLM query performance
    - Query success/failure rates
    - Token usage and API metrics
    """
    panels = []
    panel_id = 1
    
    # Row: Document Processing
    panels.append(DashboardPanelFactory.create_stat_panel(
        title="Documents Ingested (24h)",
        query='increase(farmiq_documents_ingested_total[24h])',
        panel_id=panel_id, x=0, y=0, width=4, height=3
    ))
    panel_id += 1
    
    panels.append(DashboardPanelFactory.create_stat_panel(
        title="Active Embeddings Cache",
        query='farmiq_embeddings_cache_size',
        panel_id=panel_id, x=4, y=0, width=4, height=3, unit="short"
    ))
    panel_id += 1
    
    panels.append(DashboardPanelFactory.create_gauge_panel(
        title="Cache Hit Rate %",
        query='farmiq_embeddings_cache_hit_rate * 100',
        panel_id=panel_id, x=8, y=0, width=4, height=4, max_value=100
    ))
    panel_id += 1
    
    # Row: Query Performance
    panels.append(DashboardPanelFactory.create_graph_panel(
        title="Ollama Query Latency (ms)",
        queries={
            "p50": 'histogram_quantile(0.5, farmiq_ollama_query_latency_ms_bucket)',
            "p95": 'histogram_quantile(0.95, farmiq_ollama_query_latency_ms_bucket)',
            "p99": 'histogram_quantile(0.99, farmiq_ollama_query_latency_ms_bucket)',
        },
        panel_id=panel_id, x=0, y=4, width=12, height=6
    ))
    panel_id += 1
    
    return GrafanaDashboard(
        title="FarmGrow RAG System",
        uid="farmgrow-rag-v1",
        description="Real-time monitoring of FarmGrow RAG document processing and LLM queries",
        tags=["farmgrow", "rag", "embeddings", "ollama"],
        refresh=DashboardRefresh.ONE_MINUTE,
        panels=panels
    )


# ============================================================================
# DASHBOARD 2: FARMSCORE ML MODELS DASHBOARD
# ============================================================================

def create_farmscore_dashboard() -> GrafanaDashboard:
    """FarmScore ML Models Dashboard
    
    Monitors:
    - YieldPredictor performance (R², RMSE)
    - ExpenseForecaster accuracy (MAPE)
    - DiseaseClassifier confidence
    - MarketPredictor accuracy
    - ROIOptimizer profitability
    """
    panels = []
    panel_id = 1
    
    # ML Model Performance Gauges
    models = [
        ("YieldPredictor", "farmiq_model_yield_r2_score"),
        ("ExpenseForecaster", "1.0 - farmiq_model_expense_mape_percent / 100"),
        ("DiseaseClassifier", "avg(farmiq_model_disease_confidence_score)"),
        ("MarketPredictor", "farmiq_model_market_accuracy"),
    ]
    
    x_pos = 0
    for model_name, query in models:
        panels.append(DashboardPanelFactory.create_gauge_panel(
            title=f"{model_name} Performance",
            query=query,
            panel_id=panel_id, x=x_pos, y=0, width=4, height=4, max_value=1
        ))
        panel_id += 1
        x_pos = (x_pos + 4) % 16
    
    # Prediction Volume
    panels.append(DashboardPanelFactory.create_graph_panel(
        title="Predictions per Hour",
        queries={
            "Yield": 'rate(farmiq_yield_predictions_total[1h])',
            "Expense": 'rate(farmiq_expense_predictions_total[1h])',
            "Disease": 'rate(farmiq_disease_predictions_total[1h])',
            "Market": 'rate(farmiq_market_predictions_total[1h])',
        },
        panel_id=panel_id, x=0, y=4, width=12, height=6
    ))
    
    return GrafanaDashboard(
        title="FarmScore ML Models",
        uid="farmscore-ml-v1",
        description="ML model performance and prediction metrics for FarmScore intelligence",
        tags=["farmscore", "ml", "predictions", "models"],
        refresh=DashboardRefresh.FIVE_MINUTES,
        panels=panels
    )


# ============================================================================
# DASHBOARD 3: FARMSUITE INTELLIGENCE DASHBOARD
# ============================================================================

def create_farmsuite_dashboard() -> GrafanaDashboard:
    """FarmSuite Intelligence Dashboard
    
    Monitors:
    - Worker and farm intelligence metrics
    - System caching performance
    - API response times and errors
    - Security and authorization
    """
    panels = []
    panel_id = 1
    
    # Performance KPIs
    panels.append(DashboardPanelFactory.create_stat_panel(
        title="Avg Response Time (ms)",
        query='avg(rate(farmiq_api_request_duration_seconds * 1000[5m]))',
        panel_id=panel_id, x=0, y=0, width=4, height=3, unit="ms"
    ))
    panel_id += 1
    
    panels.append(DashboardPanelFactory.create_stat_panel(
        title="Error Rate %",
        query='rate(farmiq_api_errors_total[5m]) * 100',
        panel_id=panel_id, x=4, y=0, width=4, height=3, unit="percent"
    ))
    panel_id += 1
    
    panels.append(DashboardPanelFactory.create_gauge_panel(
        title="System Cache Hit Rate %",
        query='farmiq_cache_hit_rate * 100',
        panel_id=panel_id, x=8, y=0, width=4, height=4, max_value=100
    ))
    panel_id += 1
    
    # Request Volume
    panels.append(DashboardPanelFactory.create_graph_panel(
        title="API Requests per Minute",
        queries={
            "Success": 'rate(farmiq_api_requests_total{status=~"2..|3.."}[1m]) * 60',
            "Errors": 'rate(farmiq_api_requests_total{status=~"4..|5.."}[1m]) * 60',
        },
        panel_id=panel_id, x=0, y=4, width=12, height=6
    ))
    
    return GrafanaDashboard(
        title="FarmSuite Intelligence",
        uid="farmsuite-intelligence-v1",
        description="System performance, caching, and intelligence metrics for FarmSuite",
        tags=["farmsuite", "performance", "intelligence", "caching"],
        refresh=DashboardRefresh.ONE_MINUTE,
        panels=panels
    )


# ============================================================================
# DASHBOARD 4: SYSTEM OVERVIEW DASHBOARD
# ============================================================================

def create_system_overview_dashboard() -> GrafanaDashboard:
    """System Overview Dashboard
    
    Monitors:
    - Overall API request volume and latency
    - System resource usage (CPU, memory)
    - Database connection pool status
    - Error rates across all systems
    """
    panels = []
    panel_id = 1
    
    # Top Level Metrics
    panels.append(DashboardPanelFactory.create_stat_panel(
        title="Total Requests (24h)",
        query='increase(farmiq_api_requests_total[24h])',
        panel_id=panel_id, x=0, y=0, width=4, height=3
    ))
    panel_id += 1
    
    panels.append(DashboardPanelFactory.create_gauge_panel(
        title="System Uptime %",
        query='up * 100',
        panel_id=panel_id, x=4, y=0, width=4, height=4, max_value=100
    ))
    panel_id += 1
    
    panels.append(DashboardPanelFactory.create_stat_panel(
        title="Avg Latency (ms)",
        query='avg(farmiq_api_request_duration_seconds * 1000)',
        panel_id=panel_id, x=8, y=0, width=4, height=3, unit="ms"
    ))
    panel_id += 1
    
    # Overall Trends
    panels.append(DashboardPanelFactory.create_graph_panel(
        title="Request Volume Trend",
        queries={
            "Requests/min": 'rate(farmiq_api_requests_total[1m]) * 60',
        },
        panel_id=panel_id, x=0, y=4, width=12, height=6
    ))
    
    return GrafanaDashboard(
        title="System Overview",
        uid="system-overview-v1",
        description="High-level system health and performance overview",
        tags=["system", "overview", "health"],
        refresh=DashboardRefresh.THIRTY_SECONDS,
        panels=panels
    )


# ============================================================================
# DASHBOARD 5: SECURITY & AUDIT DASHBOARD
# ============================================================================

def create_security_dashboard() -> GrafanaDashboard:
    """Security & Audit Dashboard
    
    Monitors:
    - Authentication failures
    - Authorization denials
    - Rate limit violations
    - SQL injection attempts blocked
    - XSS attempts blocked
    - Audit log events
    """
    panels = []
    panel_id = 1
    
    panels.append(DashboardPanelFactory.create_stat_panel(
        title="Auth Failures (24h)",
        query='increase(farmiq_auth_failures_total[24h])',
        panel_id=panel_id, x=0, y=0, width=4, height=3
    ))
    panel_id += 1
    
    panels.append(DashboardPanelFactory.create_stat_panel(
        title="Rate Limits Exceeded",
        query='increase(farmiq_rate_limit_exceeded_total[24h])',
        panel_id=panel_id, x=4, y=0, width=4, height=3
    ))
    panel_id += 1
    
    panels.append(DashboardPanelFactory.create_stat_panel(
        title="Security Events Blocked",
        query='increase(farmiq_security_event_blocked_total[24h])',
        panel_id=panel_id, x=8, y=0, width=4, height=3
    ))
    panel_id += 1
    
    # Security Events Timeline
    panels.append(DashboardPanelFactory.create_graph_panel(
        title="Security Events Over Time",
        queries={
            "Auth Failures": 'rate(farmiq_auth_failures_total[1h]) * 60',
            "Rate Limit": 'rate(farmiq_rate_limit_exceeded_total[1h]) * 60',
            "Blocked": 'rate(farmiq_security_event_blocked_total[1h]) * 60',
        },
        panel_id=panel_id, x=0, y=4, width=12, height=6
    ))
    
    return GrafanaDashboard(
        title="Security & Audit",
        uid="security-audit-v1",
        description="Security events, authentications, and audit logs",
        tags=["security", "audit", "compliance"],
        refresh=DashboardRefresh.ONE_MINUTE,
        panels=panels
    )


# ============================================================================
# DASHBOARD REGISTRY
# ============================================================================

DASHBOARDS = {
    "farmgrow": create_farmgrow_dashboard,
    "farmscore": create_farmscore_dashboard,
    "farmsuite": create_farmsuite_dashboard,
    "system-overview": create_system_overview_dashboard,
    "security": create_security_dashboard,
}


def get_dashboard(dashboard_id: str) -> Optional[GrafanaDashboard]:
    """Get dashboard by ID"""
    builder = DASHBOARDS.get(dashboard_id)
    if builder:
        return builder()
    else:
        logger.warning(f"Dashboard not found: {dashboard_id}")
        return None


def list_dashboards() -> List[str]:
    """List all available dashboards"""
    return list(DASHBOARDS.keys())


def export_all_dashboards() -> Dict[str, Dict[str, Any]]:
    """Export all dashboards as JSON-serializable dicts"""
    return {
        dashboard_id: get_dashboard(dashboard_id).to_dict()
        for dashboard_id in DASHBOARDS.keys()
    }
