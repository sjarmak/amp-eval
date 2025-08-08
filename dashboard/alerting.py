#!/usr/bin/env python3
"""
Alerting system for Amp Model-Efficacy Evaluation Suite
Monitors performance metrics and triggers notifications for regressions.
"""

import json
import requests
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    ACCURACY_DROP = "accuracy_drop"
    TOKEN_OVERRUN = "token_overrun"
    LATENCY_SPIKE = "latency_spike"
    ORACLE_OVERUSE = "oracle_overuse"
    EVALUATION_FAILURE = "evaluation_failure"

@dataclass
class Alert:
    alert_type: AlertType
    severity: AlertSeverity
    model: str
    message: str
    current_value: float
    baseline_value: float
    threshold: float
    timestamp: datetime
    metadata: Dict = None

class AlertManager:
    """Manages alert detection, deduplication, and notification."""
    
    def __init__(self, 
                 webhook_url: Optional[str] = None,
                 alert_cooldown: int = 3600,  # 1 hour cooldown
                 results_dir: str = "../results"):
        self.webhook_url = webhook_url or os.getenv("ALERT_WEBHOOK_URL")
        self.alert_cooldown = alert_cooldown
        self.results_dir = Path(results_dir)
        self.recent_alerts = {}  # Track recent alerts for deduplication
        
        # Alert thresholds (configurable)
        self.thresholds = {
            AlertType.ACCURACY_DROP: 5.0,      # 5% accuracy drop
            AlertType.TOKEN_OVERRUN: 25.0,     # 25% token increase
            AlertType.LATENCY_SPIKE: 50.0,     # 50% latency increase
            AlertType.ORACLE_OVERUSE: 10.0,    # 10% increase in o3 usage
        }
    
    def load_evaluation_results(self, hours_back: int = 24) -> List[Dict]:
        """Load recent evaluation results."""
        if not self.results_dir.exists():
            return []
        
        cutoff_time = time.time() - (hours_back * 3600)
        results = []
        
        for result_file in self.results_dir.glob("*.json"):
            if result_file.stat().st_mtime > cutoff_time:
                try:
                    with open(result_file) as f:
                        data = json.load(f)
                        data['eval_name'] = result_file.stem
                        data['timestamp'] = result_file.stat().st_mtime
                        results.append(data)
                except Exception as e:
                    logger.error(f"Error loading {result_file}: {e}")
        
        return sorted(results, key=lambda x: x.get('timestamp', 0), reverse=True)
    
    def calculate_baseline_metrics(self, results: List[Dict], 
                                 baseline_days: int = 7) -> pd.DataFrame:
        """Calculate baseline metrics from historical data."""
        cutoff_time = time.time() - (baseline_days * 24 * 3600)
        baseline_results = [r for r in results if r.get('timestamp', 0) > cutoff_time]
        
        if not baseline_results:
            return pd.DataFrame()
        
        df = pd.DataFrame(baseline_results)
        
        # Ensure required columns exist
        required_cols = ['model', 'success_rate', 'latency_s', 'tokens']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing columns in baseline data: {missing_cols}")
            return pd.DataFrame()
        
        return df.groupby('model').agg({
            'success_rate': 'mean',
            'latency_s': 'mean',
            'tokens': 'mean'
        }).round(4)
    
    def detect_accuracy_regression(self, current_stats: pd.DataFrame, 
                                 baseline_stats: pd.DataFrame) -> List[Alert]:
        """Detect accuracy drops exceeding threshold."""
        alerts = []
        threshold = self.thresholds[AlertType.ACCURACY_DROP]
        
        for model in current_stats.index:
            if model not in baseline_stats.index:
                continue
            
            current_rate = current_stats.loc[model, 'success_rate']
            baseline_rate = baseline_stats.loc[model, 'success_rate']
            drop_percent = (baseline_rate - current_rate) * 100
            
            if drop_percent > threshold:
                severity = AlertSeverity.CRITICAL if drop_percent > 15 else AlertSeverity.HIGH
                
                alert = Alert(
                    alert_type=AlertType.ACCURACY_DROP,
                    severity=severity,
                    model=model,
                    message=f"Success rate dropped by {drop_percent:.1f}% for {model}",
                    current_value=current_rate,
                    baseline_value=baseline_rate,
                    threshold=threshold,
                    timestamp=datetime.now(),
                    metadata={'drop_percent': drop_percent}
                )
                alerts.append(alert)
        
        return alerts
    
    def detect_token_overrun(self, current_stats: pd.DataFrame, 
                           baseline_stats: pd.DataFrame) -> List[Alert]:
        """Detect token usage increases exceeding threshold."""
        alerts = []
        threshold = self.thresholds[AlertType.TOKEN_OVERRUN]
        
        for model in current_stats.index:
            if model not in baseline_stats.index:
                continue
            
            current_tokens = current_stats.loc[model, 'tokens']
            baseline_tokens = baseline_stats.loc[model, 'tokens']
            
            if baseline_tokens > 0:
                increase_percent = ((current_tokens - baseline_tokens) / baseline_tokens) * 100
                
                if increase_percent > threshold:
                    severity = AlertSeverity.HIGH if increase_percent > 50 else AlertSeverity.MEDIUM
                    
                    alert = Alert(
                        alert_type=AlertType.TOKEN_OVERRUN,
                        severity=severity,
                        model=model,
                        message=f"Token usage increased by {increase_percent:.1f}% for {model}",
                        current_value=current_tokens,
                        baseline_value=baseline_tokens,
                        threshold=threshold,
                        timestamp=datetime.now(),
                        metadata={'increase_percent': increase_percent}
                    )
                    alerts.append(alert)
        
        return alerts
    
    def detect_latency_spike(self, current_stats: pd.DataFrame, 
                           baseline_stats: pd.DataFrame) -> List[Alert]:
        """Detect latency increases exceeding threshold."""
        alerts = []
        threshold = self.thresholds[AlertType.LATENCY_SPIKE]
        
        for model in current_stats.index:
            if model not in baseline_stats.index:
                continue
            
            current_latency = current_stats.loc[model, 'latency_s']
            baseline_latency = baseline_stats.loc[model, 'latency_s']
            
            if baseline_latency > 0:
                increase_percent = ((current_latency - baseline_latency) / baseline_latency) * 100
                
                if increase_percent > threshold:
                    severity = AlertSeverity.HIGH if increase_percent > 100 else AlertSeverity.MEDIUM
                    
                    alert = Alert(
                        alert_type=AlertType.LATENCY_SPIKE,
                        severity=severity,
                        model=model,
                        message=f"Latency increased by {increase_percent:.1f}% for {model}",
                        current_value=current_latency,
                        baseline_value=baseline_latency,
                        threshold=threshold,
                        timestamp=datetime.now(),
                        metadata={'increase_percent': increase_percent}
                    )
                    alerts.append(alert)
        
        return alerts
    
    def detect_oracle_overuse(self, results: List[Dict]) -> List[Alert]:
        """Detect unexpected increases in Oracle (o3) model usage."""
        recent_results = [r for r in results if r.get('timestamp', 0) > time.time() - 86400]
        baseline_results = results[-50:] if len(results) > 50 else results
        
        recent_o3_usage = len([r for r in recent_results if r.get('model') == 'o3'])
        baseline_o3_usage = len([r for r in baseline_results if r.get('model') == 'o3'])
        
        if baseline_o3_usage > 0:
            total_recent = len(recent_results)
            total_baseline = len(baseline_results)
            
            recent_rate = recent_o3_usage / total_recent if total_recent > 0 else 0
            baseline_rate = baseline_o3_usage / total_baseline
            
            increase_percent = ((recent_rate - baseline_rate) / baseline_rate) * 100
            threshold = self.thresholds[AlertType.ORACLE_OVERUSE]
            
            if increase_percent > threshold:
                alert = Alert(
                    alert_type=AlertType.ORACLE_OVERUSE,
                    severity=AlertSeverity.MEDIUM,
                    model="o3",
                    message=f"Oracle usage increased by {increase_percent:.1f}% (unexpected model upgrades)",
                    current_value=recent_rate,
                    baseline_value=baseline_rate,
                    threshold=threshold,
                    timestamp=datetime.now(),
                    metadata={'recent_count': recent_o3_usage, 'baseline_count': baseline_o3_usage}
                )
                return [alert]
        
        return []
    
    def is_duplicate_alert(self, alert: Alert) -> bool:
        """Check if this alert was recently sent to avoid spam."""
        alert_key = f"{alert.alert_type.value}_{alert.model}"
        
        if alert_key in self.recent_alerts:
            last_sent = self.recent_alerts[alert_key]
            if (datetime.now() - last_sent).seconds < self.alert_cooldown:
                return True
        
        return False
    
    def send_slack_notification(self, alert: Alert) -> bool:
        """Send alert to Slack webhook."""
        if not self.webhook_url:
            logger.warning("No webhook URL configured for alerts")
            return False
        
        # Color based on severity
        colors = {
            AlertSeverity.LOW: "good",
            AlertSeverity.MEDIUM: "warning", 
            AlertSeverity.HIGH: "danger",
            AlertSeverity.CRITICAL: "#ff0000"
        }
        
        payload = {
            "text": f"🚨 Amp Evaluation Alert: {alert.message}",
            "attachments": [{
                "color": colors.get(alert.severity, "warning"),
                "fields": [
                    {"title": "Model", "value": alert.model, "short": True},
                    {"title": "Type", "value": alert.alert_type.value.replace('_', ' ').title(), "short": True},
                    {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                    {"title": "Threshold", "value": f"{alert.threshold}%", "short": True},
                    {"title": "Current Value", "value": f"{alert.current_value:.3f}", "short": True},
                    {"title": "Baseline Value", "value": f"{alert.baseline_value:.3f}", "short": True}
                ],
                "footer": "Amp Evaluation Suite",
                "ts": int(alert.timestamp.timestamp())
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                # Mark as sent to avoid duplicates
                alert_key = f"{alert.alert_type.value}_{alert.model}"
                self.recent_alerts[alert_key] = alert.timestamp
                logger.info(f"Alert sent successfully: {alert.message}")
                return True
            else:
                logger.error(f"Failed to send alert: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def check_all_alerts(self) -> List[Alert]:
        """Run all alert checks and return detected alerts."""
        results = self.load_evaluation_results()
        if not results:
            logger.info("No recent evaluation results found")
            return []
        
        # Get current and baseline metrics
        current_results = results[:10]  # Most recent 10 runs
        baseline_stats = self.calculate_baseline_metrics(results)
        
        if baseline_stats.empty:
            logger.warning("No baseline data available for comparison")
            return []
        
        current_df = pd.DataFrame(current_results)
        current_stats = current_df.groupby('model').agg({
            'success_rate': 'mean',
            'latency_s': 'mean', 
            'tokens': 'mean'
        }).round(4)
        
        all_alerts = []
        
        # Run all detection methods
        all_alerts.extend(self.detect_accuracy_regression(current_stats, baseline_stats))
        all_alerts.extend(self.detect_token_overrun(current_stats, baseline_stats))
        all_alerts.extend(self.detect_latency_spike(current_stats, baseline_stats))
        all_alerts.extend(self.detect_oracle_overuse(results))
        
        # Filter out duplicate alerts
        filtered_alerts = [alert for alert in all_alerts if not self.is_duplicate_alert(alert)]
        
        logger.info(f"Detected {len(all_alerts)} alerts, {len(filtered_alerts)} after deduplication")
        return filtered_alerts
    
    def process_alerts(self) -> int:
        """Main method to check for alerts and send notifications."""
        alerts = self.check_all_alerts()
        sent_count = 0
        
        for alert in alerts:
            if self.send_slack_notification(alert):
                sent_count += 1
        
        logger.info(f"Processed {len(alerts)} alerts, sent {sent_count} notifications")
        return sent_count

def main():
    """CLI entry point for alert checking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check for evaluation alerts")
    parser.add_argument("--webhook-url", help="Slack webhook URL")
    parser.add_argument("--results-dir", default="../results", help="Results directory")
    parser.add_argument("--dry-run", action="store_true", help="Check alerts without sending")
    
    args = parser.parse_args()
    
    alert_manager = AlertManager(
        webhook_url=args.webhook_url,
        results_dir=args.results_dir
    )
    
    if args.dry_run:
        alerts = alert_manager.check_all_alerts()
        print(f"Found {len(alerts)} alerts:")
        for alert in alerts:
            print(f"  {alert.severity.value.upper()}: {alert.message}")
    else:
        sent_count = alert_manager.process_alerts()
        print(f"Sent {sent_count} alert notifications")

if __name__ == "__main__":
    main()
