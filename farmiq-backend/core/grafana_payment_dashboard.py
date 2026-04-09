"""
Grafana Payment Provider Dashboard Configuration
Tracks: M-Pesa, Afrika Talking, Hedera metrics
For real-time monitoring of all payment channels

Author: FarmIQ Backend Team
Date: March 2026
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any
from enum import Enum
import json


class MetricType(str, Enum):
    """Grafana metric types"""
    GRAPH = "graph"
    GAUGE = "gauge"
    STAT = "stat"
    TABLE = "table"
    HEATMAP = "heatmap"
    LOGS = "logs"


class UnitType(str, Enum):
    """Metric unit types"""
    COUNT = "short"
    PERCENT = "percent"
    SECONDS = "s"
    MILLISECONDS = "ms"
    BYTES = "bytes"
    REQUESTS_PER_SECOND = "reqps"
    CURRENCY = "currencyUSD"


@dataclass
class DashboardPanel:
    """Grafana dashboard panel"""
    title: str
    type: MetricType
    targets: List[Dict[str, Any]]
    unit: str = "short"
    thresholds: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Grafana panel JSON"""
        return {
            "title": self.title,
            "type": self.type.value,
            "targets": self.targets,
            "options": {
                "unit": self.unit,
                "thresholds": self.thresholds or {}
            }
        }


class PaymentProviderDashboard:
    """Generate Grafana dashboard for payment providers"""
    
    # ===================== M-PESA PANELS =====================
    
    @staticmethod
    def mpesa_transactions_per_minute() -> DashboardPanel:
        """M-Pesa: Transactions per minute"""
        return DashboardPanel(
            title="M-Pesa: Transactions/Minute",
            type=MetricType.GRAPH,
            unit=UnitType.REQUESTS_PER_SECOND,
            targets=[
                {
                    "expr": 'rate(mpesa_transactions_total[1m])',
                    "legendFormat": "{{method}}",
                    "refId": "A",
                }
            ],
            thresholds={
                "mode": "absolute",
                "value": [
                    {"color": "green", "value": 0},
                    {"color": "yellow", "value": 50},
                    {"color": "red", "value": 100}
                ]
            }
        )
    
    @staticmethod
    def mpesa_success_rate() -> DashboardPanel:
        """M-Pesa: Success rate percentage"""
        return DashboardPanel(
            title="M-Pesa: Success Rate %",
            type=MetricType.GAUGE,
            unit=UnitType.PERCENT,
            targets=[
                {
                    "expr": '(mpesa_transactions_success_total / mpesa_transactions_total) * 100',
                    "legendFormat": "Success Rate",
                    "refId": "A",
                }
            ],
            thresholds={
                "mode": "absolute",
                "value": [
                    {"color": "red", "value": 60},
                    {"color": "yellow", "value": 90},
                    {"color": "green", "value": 99.5}
                ]
            }
        )
    
    @staticmethod
    def mpesa_failed_transactions() -> DashboardPanel:
        """M-Pesa: Failed transactions"""
        return DashboardPanel(
            title="M-Pesa: Failed Transactions",
            type=MetricType.STAT,
            unit=UnitType.COUNT,
            targets=[
                {
                    "expr": 'mpesa_transactions_failed_total',
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def mpesa_callback_latency() -> DashboardPanel:
        """M-Pesa: Callback latency (milliseconds)"""
        return DashboardPanel(
            title="M-Pesa: Callback Latency (ms)",
            type=MetricType.GRAPH,
            unit=UnitType.MILLISECONDS,
            targets=[
                {
                    "expr": 'histogram_quantile(0.95, mpesa_callback_latency_milliseconds)',
                    "legendFormat": "p95",
                    "refId": "A",
                },
                {
                    "expr": 'histogram_quantile(0.99, mpesa_callback_latency_milliseconds)',
                    "legendFormat": "p99",
                    "refId": "B",
                }
            ]
        )
    
    @staticmethod
    def mpesa_stk_timeout_rate() -> DashboardPanel:
        """M-Pesa: STK Push timeout rate"""
        return DashboardPanel(
            title="M-Pesa: STK Timeout Rate %",
            type=MetricType.GAUGE,
            unit=UnitType.PERCENT,
            targets=[
                {
                    "expr": '(mpesa_stk_timeout_total / mpesa_stk_initiated_total) * 100',
                    "legendFormat": "Timeout Rate",
                    "refId": "A",
                }
            ],
            thresholds={
                "mode": "absolute",
                "value": [
                    {"color": "green", "value": 0},
                    {"color": "yellow", "value": 5},
                    {"color": "red", "value": 10}
                ]
            }
        )
    
    @staticmethod
    def mpesa_revenue_per_hour() -> DashboardPanel:
        """M-Pesa: Revenue per hour (KES)"""
        return DashboardPanel(
            title="M-Pesa: Revenue/Hour (KES)",
            type=MetricType.GRAPH,
            unit=UnitType.CURRENCY,
            targets=[
                {
                    "expr": 'rate(mpesa_revenue_total[1h])',
                    "legendFormat": "{{currency}}",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def mpesa_errors_breakdown() -> DashboardPanel:
        """M-Pesa: Error codes breakdown"""
        return DashboardPanel(
            title="M-Pesa: Error Codes Breakdown",
            type=MetricType.TABLE,
            targets=[
                {
                    "expr": 'mpesa_error_total',
                    "format": "table",
                    "refId": "A",
                }
            ]
        )
    
    # ===================== AFRIKA TALKING PANELS =====================
    
    @staticmethod
    def afritalk_sms_per_minute() -> DashboardPanel:
        """Afrika Talking: SMS sent per minute"""
        return DashboardPanel(
            title="Afrika Talking: SMS/Minute",
            type=MetricType.GRAPH,
            unit=UnitType.REQUESTS_PER_SECOND,
            targets=[
                {
                    "expr": 'rate(afritalk_sms_sent_total[1m])',
                    "legendFormat": "SMS/min",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def afritalk_sms_delivery_rate() -> DashboardPanel:
        """Afrika Talking: SMS delivery rate %"""
        return DashboardPanel(
            title="Afrika Talking: SMS Delivery Rate %",
            type=MetricType.GAUGE,
            unit=UnitType.PERCENT,
            targets=[
                {
                    "expr": '(afritalk_sms_delivered_total / afritalk_sms_sent_total) * 100',
                    "legendFormat": "Delivery Rate",
                    "refId": "A",
                }
            ],
            thresholds={
                "mode": "absolute",
                "value": [
                    {"color": "red", "value": 80},
                    {"color": "yellow", "value": 92},
                    {"color": "green", "value": 95}
                ]
            }
        )
    
    @staticmethod
    def afritalk_sms_bounce_rate() -> DashboardPanel:
        """Afrika Talking: SMS bounce rate %"""
        return DashboardPanel(
            title="Afrika Talking: SMS Bounce Rate %",
            type=MetricType.GAUGE,
            unit=UnitType.PERCENT,
            targets=[
                {
                    "expr": '(afritalk_sms_bounced_total / afritalk_sms_sent_total) * 100',
                    "legendFormat": "Bounce Rate",
                    "refId": "A",
                }
            ],
            thresholds={
                "mode": "absolute",
                "value": [
                    {"color": "green", "value": 0},
                    {"color": "yellow", "value": 3},
                    {"color": "red", "value": 5}
                ]
            }
        )
    
    @staticmethod
    def afritalk_ussd_active_sessions() -> DashboardPanel:
        """Afrika Talking: Active USSD sessions"""
        return DashboardPanel(
            title="Afrika Talking: Active USSD Sessions",
            type=MetricType.GAUGE,
            unit=UnitType.COUNT,
            targets=[
                {
                    "expr": 'afritalk_ussd_sessions_active',
                    "legendFormat": "Active Sessions",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def afritalk_ussd_response_time() -> DashboardPanel:
        """Afrika Talking: USSD response time (ms)"""
        return DashboardPanel(
            title="Afrika Talking: USSD Response Time (ms)",
            type=MetricType.GRAPH,
            unit=UnitType.MILLISECONDS,
            targets=[
                {
                    "expr": 'histogram_quantile(0.95, afritalk_ussd_response_time_ms)',
                    "legendFormat": "p95",
                    "refId": "A",
                },
                {
                    "expr": 'histogram_quantile(0.99, afritalk_ussd_response_time_ms)',
                    "legendFormat": "p99",
                    "refId": "B",
                }
            ]
        )
    
    @staticmethod
    def afritalk_bulk_sms_campaigns() -> DashboardPanel:
        """Afrika Talking: Bulk SMS campaigns status"""
        return DashboardPanel(
            title="Afrika Talking: Bulk SMS Campaigns",
            type=MetricType.TABLE,
            targets=[
                {
                    "expr": 'afritalk_bulk_sms_campaign_total',
                    "format": "table",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def afritalk_credit_balance() -> DashboardPanel:
        """Afrika Talking: SMS credit balance"""
        return DashboardPanel(
            title="Afrika Talking: SMS Credit Balance",
            type=MetricType.GAUGE,
            unit=UnitType.CURRENCY,
            targets=[
                {
                    "expr": 'afritalk_sms_credit_balance',
                    "legendFormat": "Balance (KES)",
                    "refId": "A",
                }
            ],
            thresholds={
                "mode": "absolute",
                "value": [
                    {"color": "red", "value": 5000},
                    {"color": "yellow", "value": 20000},
                    {"color": "green", "value": 100000}
                ]
            }
        )
    
    # ===================== HEDERA PANELS =====================
    
    @staticmethod
    def hedera_token_mints_per_minute() -> DashboardPanel:
        """Hedera: Token mints per minute"""
        return DashboardPanel(
            title="Hedera: Token Mints/Minute",
            type=MetricType.GRAPH,
            unit=UnitType.REQUESTS_PER_SECOND,
            targets=[
                {
                    "expr": 'rate(hedera_tokens_minted_total[1m])',
                    "legendFormat": "mints/min",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def hedera_hcs_log_writes() -> DashboardPanel:
        """Hedera: HCS log writes per minute"""
        return DashboardPanel(
            title="Hedera: HCS Log Writes/Minute",
            type=MetricType.GRAPH,
            unit=UnitType.REQUESTS_PER_SECOND,
            targets=[
                {
                    "expr": 'rate(hedera_hcs_messages_total[1m])',
                    "legendFormat": "writes/min",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def hedera_transaction_cost() -> DashboardPanel:
        """Hedera: Transaction cost (USD)"""
        return DashboardPanel(
            title="Hedera: Transaction Cost (USD/hour)",
            type=MetricType.GRAPH,
            unit=UnitType.CURRENCY,
            targets=[
                {
                    "expr": 'rate(hedera_transaction_cost_usd_total[1h])',
                    "legendFormat": "Cost/hour",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def hedera_network_latency() -> DashboardPanel:
        """Hedera: Network latency (ms)"""
        return DashboardPanel(
            title="Hedera: Network Latency (ms)",
            type=MetricType.GRAPH,
            unit=UnitType.MILLISECONDS,
            targets=[
                {
                    "expr": 'histogram_quantile(0.95, hedera_network_latency_ms)',
                    "legendFormat": "p95",
                    "refId": "A",
                },
                {
                    "expr": 'histogram_quantile(0.99, hedera_network_latency_ms)',
                    "legendFormat": "p99",
                    "refId": "B",
                }
            ]
        )
    
    @staticmethod
    def hedera_consensus_node_latency() -> DashboardPanel:
        """Hedera: Consensus node response latency"""
        return DashboardPanel(
            title="Hedera: Consensus Node Latency (ms)",
            type=MetricType.HEATMAP,
            unit=UnitType.MILLISECONDS,
            targets=[
                {
                    "expr": 'hedera_consensus_latency_ms',
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def hedera_mirror_node_queries() -> DashboardPanel:
        """Hedera: Mirror node queries per minute"""
        return DashboardPanel(
            title="Hedera: Mirror Node Queries/Minute",
            type=MetricType.GRAPH,
            unit=UnitType.REQUESTS_PER_SECOND,
            targets=[
                {
                    "expr": 'rate(hedera_mirror_queries_total[1m])',
                    "legendFormat": "queries/min",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def hedera_account_balance() -> DashboardPanel:
        """Hedera: Vault account HBAR balance"""
        return DashboardPanel(
            title="Hedera: Vault Account Balance (HBAR)",
            type=MetricType.GAUGE,
            unit=UnitType.COUNT,
            targets=[
                {
                    "expr": 'hedera_vault_account_balance_hbar',
                    "legendFormat": "{{account_id}}",
                    "refId": "A",
                }
            ],
            thresholds={
                "mode": "absolute",
                "value": [
                    {"color": "red", "value": 10},
                    {"color": "yellow", "value": 50},
                    {"color": "green", "value": 1000}
                ]
            }
        )
    
    @staticmethod
    def hedera_token_supply() -> DashboardPanel:
        """Hedera: FIQ token total supply"""
        return DashboardPanel(
            title="Hedera: FIQ Token Supply",
            type=MetricType.STAT,
            unit=UnitType.COUNT,
            targets=[
                {
                    "expr": 'hedera_token_supply{token_name="FIQ"}',
                    "legendFormat": "FIQ Supply",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def hedera_errors() -> DashboardPanel:
        """Hedera: Error rate"""
        return DashboardPanel(
            title="Hedera: Error Rate %",
            type=MetricType.GAUGE,
            unit=UnitType.PERCENT,
            targets=[
                {
                    "expr": '(hedera_errors_total / hedera_requests_total) * 100',
                    "legendFormat": "Error Rate",
                    "refId": "A",
                }
            ],
            thresholds={
                "mode": "absolute",
                "value": [
                    {"color": "green", "value": 0},
                    {"color": "yellow", "value": 1},
                    {"color": "red", "value": 5}
                ]
            }
        )
    
    # ===================== CROSS-PROVIDER PANELS =====================
    
    @staticmethod
    def payment_gateway_uptime() -> DashboardPanel:
        """Payment Gateway: Uptime % for all providers"""
        return DashboardPanel(
            title="Payment Gateway: Uptime by Provider %",
            type=MetricType.GRAPH,
            unit=UnitType.PERCENT,
            targets=[
                {
                    "expr": '(payment_uptime_seconds / 3600) * 100',
                    "legendFormat": "{{provider}}",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def payment_gateway_transactions_total() -> DashboardPanel:
        """Payment Gateway: Total transactions"""
        return DashboardPanel(
            title="Payment Gateway: Transactions by Provider",
            type=MetricType.GRAPH,
            unit=UnitType.REQUESTS_PER_SECOND,
            targets=[
                {
                    "expr": 'rate(payment_gateway_transactions_total[5m])',
                    "legendFormat": "{{provider}}",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def payment_gateway_success_rate() -> DashboardPanel:
        """Payment Gateway: Success rate by provider"""
        return DashboardPanel(
            title="Payment Gateway: Success Rate by Provider %",
            type=MetricType.GRAPH,
            unit=UnitType.PERCENT,
            targets=[
                {
                    "expr": '(payment_gateway_success_total / payment_gateway_transactions_total) * 100',
                    "legendFormat": "{{provider}}",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def payment_gateway_latency() -> DashboardPanel:
        """Payment Gateway: P95/P99 latency"""
        return DashboardPanel(
            title="Payment Gateway: P95/P99 Latency (ms)",
            type=MetricType.GRAPH,
            unit=UnitType.MILLISECONDS,
            targets=[
                {
                    "expr": 'histogram_quantile(0.95, payment_gateway_latency_ms)',
                    "legendFormat": "p95 {{provider}}",
                    "refId": "A",
                },
                {
                    "expr": 'histogram_quantile(0.99, payment_gateway_latency_ms)',
                    "legendFormat": "p99 {{provider}}",
                    "refId": "B",
                }
            ]
        )
    
    @staticmethod
    def payment_gateway_alerts() -> DashboardPanel:
        """Payment Gateway: Active alerts"""
        return DashboardPanel(
            title="Payment Gateway: Active Alerts",
            type=MetricType.TABLE,
            targets=[
                {
                    "expr": 'ALERTS{severity=~"critical|warning"}',
                    "format": "table",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def payment_revenue_by_provider() -> DashboardPanel:
        """Payment Gateway: Revenue by provider"""
        return DashboardPanel(
            title="Payment Gateway: Revenue by Provider (KES)",
            type=MetricType.GRAPH,
            unit=UnitType.CURRENCY,
            targets=[
                {
                    "expr": 'rate(payment_gateway_revenue_total[1h])',
                    "legendFormat": "{{provider}}",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def user_distribution_by_provider() -> DashboardPanel:
        """Payment Gateway: Active users by provider"""
        return DashboardPanel(
            title="Payment Gateway: Active Users by Provider",
            type=MetricType.GRAPH,
            unit=UnitType.COUNT,
            targets=[
                {
                    "expr": 'payment_gateway_active_users',
                    "legendFormat": "{{provider}}",
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def transaction_failure_reasons() -> DashboardPanel:
        """Payment Gateway: Transaction failure breakdown"""
        return DashboardPanel(
            title="Payment Gateway: Transaction Failures",
            type=MetricType.TABLE,
            targets=[
                {
                    "expr": 'payment_gateway_failed_transactions_total',
                    "format": "table",
                    "instant": True,
                    "refId": "A",
                }
            ]
        )
    
    @staticmethod
    def sla_compliance_dashboard() -> Dict[str, Any]:
        """Complete SLA compliance dashboard"""
        return {
            "sla_targets": {
                "mpesa": {
                    "uptime": "99.5%",
                    "success_rate": "99%",
                    "latency_p95": "2000ms",
                    "latency_p99": "5000ms",
                },
                "afritalk": {
                    "uptime": "99%",
                    "success_rate": "95%",
                    "delivery_rate": "95%",
                    "latency_p95": "500ms",
                },
                "hedera": {
                    "uptime": "99.9%",
                    "success_rate": "99.9%",
                    "latency_p95": "3000ms",
                    "latency_p99": "6000ms",
                },
            },
            "critical_alerts": [
                "M-Pesa downtime >30 minutes",
                "Afrika Talking SMS delivery <90%",
                "Hedera consensus latency >10 seconds",
                "Payment gateway success rate <95%",
            ],
            "warning_alerts": [
                "M-Pesa success rate <99%",
                "Afrika Talking balance <10,000 KES",
                "Hedera HBAR balance <50",
                "Any provider latency >5 seconds",
            ]
        }
    
    @staticmethod
    def get_all_panels() -> List[DashboardPanel]:
        """Get all dashboard panels"""
        return [
            # M-Pesa panels
            PaymentProviderDashboard.mpesa_transactions_per_minute(),
            PaymentProviderDashboard.mpesa_success_rate(),
            PaymentProviderDashboard.mpesa_failed_transactions(),
            PaymentProviderDashboard.mpesa_callback_latency(),
            PaymentProviderDashboard.mpesa_stk_timeout_rate(),
            PaymentProviderDashboard.mpesa_revenue_per_hour(),
            PaymentProviderDashboard.mpesa_errors_breakdown(),
            # Afrika Talking panels
            PaymentProviderDashboard.afritalk_sms_per_minute(),
            PaymentProviderDashboard.afritalk_sms_delivery_rate(),
            PaymentProviderDashboard.afritalk_sms_bounce_rate(),
            PaymentProviderDashboard.afritalk_ussd_active_sessions(),
            PaymentProviderDashboard.afritalk_ussd_response_time(),
            PaymentProviderDashboard.afritalk_bulk_sms_campaigns(),
            PaymentProviderDashboard.afritalk_credit_balance(),
            # Hedera panels
            PaymentProviderDashboard.hedera_token_mints_per_minute(),
            PaymentProviderDashboard.hedera_hcs_log_writes(),
            PaymentProviderDashboard.hedera_transaction_cost(),
            PaymentProviderDashboard.hedera_network_latency(),
            PaymentProviderDashboard.hedera_consensus_node_latency(),
            PaymentProviderDashboard.hedera_mirror_node_queries(),
            PaymentProviderDashboard.hedera_account_balance(),
            PaymentProviderDashboard.hedera_token_supply(),
            PaymentProviderDashboard.hedera_errors(),
            # Cross-provider panels
            PaymentProviderDashboard.payment_gateway_uptime(),
            PaymentProviderDashboard.payment_gateway_transactions_total(),
            PaymentProviderDashboard.payment_gateway_success_rate(),
            PaymentProviderDashboard.payment_gateway_latency(),
            PaymentProviderDashboard.payment_gateway_alerts(),
            PaymentProviderDashboard.payment_revenue_by_provider(),
            PaymentProviderDashboard.user_distribution_by_provider(),
            PaymentProviderDashboard.transaction_failure_reasons(),
        ]
    
    @staticmethod
    def export_as_json() -> str:
        """Export dashboard as Grafana JSON"""
        panels = PaymentProviderDashboard.get_all_panels()
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "FarmIQ Payment Provider Monitoring",
                "tags": ["payments", "monitoring", "M-Pesa", "Afrika-Talking", "Hedera"],
                "timezone": "Africa/Nairobi",
                "schemaVersion": 38,
                "version": 1,
                "refresh": "30s",
                "panels": [panel.to_dict() for panel in panels],
            }
        }
        return json.dumps(dashboard, indent=2)


# ===================== PROMETHEUS METRICS SETUP =====================

PROMETHEUS_METRICS_CONFIG = """
# M-Pesa Metrics
mpesa_transactions_total{method="stk_push",app_instance="farmiq"} Counter
mpesa_transactions_success_total{method="stk_push"} Counter
mpesa_transactions_failed_total{method="stk_push",error_code=""} Counter
mpesa_callback_latency_milliseconds{endpoint="/callback"} Histogram
mpesa_stk_initiated_total Counter
mpesa_stk_timeout_total Counter
mpesa_revenue_total{currency="KES"} Counter
mpesa_error_total{error_code=""} Counter

# Afrika Talking Metrics
afritalk_sms_sent_total{priority="normal"} Counter
afritalk_sms_delivered_total Counter
afritalk_sms_bounced_total Counter
afritalk_ussd_sessions_active Gauge
afritalk_ussd_response_time_ms Histogram
afritalk_bulk_sms_campaign_total{status="succeeded"} Counter
afritalk_sms_credit_balance Gauge

# Hedera Metrics
hedera_tokens_minted_total{token_name="FIQ"} Counter
hedera_hcs_messages_total{topic_id=""} Counter
hedera_transaction_cost_usd_total Counter
hedera_network_latency_ms Histogram
hedera_consensus_latency_ms Histogram
hedera_mirror_queries_total Counter
hedera_vault_account_balance_hbar Gauge
hedera_token_supply{token_name="FIQ"} Gauge
hedera_errors_total{error_type=""} Counter
hedera_requests_total Counter

# Payment Gateway Metrics
payment_uptime_seconds{provider=""} Counter
payment_gateway_transactions_total{provider=""} Counter
payment_gateway_success_total{provider=""} Counter
payment_gateway_latency_ms{provider=""} Histogram
payment_gateway_revenue_total{provider=""} Counter
payment_gateway_active_users{provider=""} Gauge
payment_gateway_failed_transactions_total{provider="",reason=""} Counter
"""

GRAFANA_ALERTS_CONFIG = """
# Critical Alerts

- alert: MPesaHighErrorRate
  expr: (rate(mpesa_transactions_failed_total[5m]) / rate(mpesa_transactions_total[5m])) > 0.01
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "M-Pesa error rate >1%"
    
- alert: MPesaStalled
  expr: rate(mpesa_transactions_total[5m]) < 1
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "M-Pesa transactions <1/min"

- alert: AfrikaTalkingDowntime
  expr: afritalk_sms_sent_total == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Afrika Talking unreachable"

- alert: HederaHighLatency
  expr: histogram_quantile(0.95, hedera_network_latency_ms) > 10000
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Hedera latency >10 seconds"

- alert: PaymentGatewayHighFailure
  expr: (rate(payment_gateway_failed_transactions_total[5m]) / rate(payment_gateway_transactions_total[5m])) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Payment gateway failure rate >5%"

# Warning Alerts

- alert: MPesaHighLatency
  expr: histogram_quantile(0.95, mpesa_callback_latency_milliseconds) > 5000
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "M-Pesa p95 latency >5 seconds"

- alert: AfrikaTalkingLowBalance
  expr: afritalk_sms_credit_balance < 10000
  for: 30m
  labels:
    severity: warning
  annotations:
    summary: "Afrika Talking SMS balance <10,000 KES"

- alert: HederaLowBalance
  expr: hedera_vault_account_balance_hbar < 50
  for: 30m
  labels:
    severity: warning
  annotations:
    summary: "Hedera vault HBAR balance <50"
"""
