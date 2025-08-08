#!/usr/bin/env python3
"""
Metrics storage backend for Amp Model-Efficacy Evaluation Suite
Provides structured storage and retrieval of evaluation metrics.
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import uuid
import logging

logger = logging.getLogger(__name__)

@dataclass
class EvaluationMetric:
    """Structured evaluation metric record."""
    id: str
    timestamp: datetime
    model: str
    evaluation_name: str
    success_rate: float
    latency_s: float
    tokens: int
    cost_usd: float = 0.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class MetricsStore:
    """SQLite-based metrics storage with time-series capabilities."""
    
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    evaluation_name TEXT NOT NULL,
                    success_rate REAL NOT NULL,
                    latency_s REAL NOT NULL,
                    tokens INTEGER NOT NULL,
                    cost_usd REAL DEFAULT 0.0,
                    metadata TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_timestamp ON evaluations(timestamp);
                CREATE INDEX IF NOT EXISTS idx_model ON evaluations(model);
                CREATE INDEX IF NOT EXISTS idx_eval_name ON evaluations(evaluation_name);
                
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    model TEXT NOT NULL,
                    message TEXT NOT NULL,
                    current_value REAL,
                    baseline_value REAL,
                    threshold_value REAL,
                    sent BOOLEAN DEFAULT FALSE,
                    metadata TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_alert_timestamp ON alerts(timestamp);
                CREATE INDEX IF NOT EXISTS idx_alert_type ON alerts(alert_type);
            """)
    
    def store_evaluation(self, metric: EvaluationMetric) -> str:
        """Store a single evaluation metric."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO evaluations 
                (id, timestamp, model, evaluation_name, success_rate, latency_s, tokens, cost_usd, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.id,
                int(metric.timestamp.timestamp()),
                metric.model,
                metric.evaluation_name,
                metric.success_rate,
                metric.latency_s,
                metric.tokens,
                metric.cost_usd,
                json.dumps(metric.metadata)
            ))
        
        logger.info(f"Stored evaluation: {metric.id} for {metric.model}")
        return metric.id
    
    def import_from_json_files(self, results_dir: str = "../results") -> int:
        """Import existing JSON result files into the database."""
        results_path = Path(results_dir)
        if not results_path.exists():
            logger.warning(f"Results directory not found: {results_path}")
            return 0
        
        imported_count = 0
        
        for result_file in results_path.glob("*.json"):
            try:
                with open(result_file) as f:
                    data = json.load(f)
                
                # Convert to EvaluationMetric
                metric = EvaluationMetric(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.fromtimestamp(result_file.stat().st_mtime),
                    model=data.get('model', 'unknown'),
                    evaluation_name=result_file.stem,
                    success_rate=data.get('success_rate', 0.0),
                    latency_s=data.get('latency_s', 0.0),
                    tokens=data.get('tokens', 0),
                    cost_usd=data.get('cost_usd', 0.0),
                    metadata={
                        'source_file': str(result_file),
                        'raw_data': data
                    }
                )
                
                self.store_evaluation(metric)
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing {result_file}: {e}")
        
        logger.info(f"Imported {imported_count} evaluation records")
        return imported_count
    
    def get_metrics(self, 
                   model: Optional[str] = None,
                   evaluation_name: Optional[str] = None,
                   hours_back: Optional[int] = None,
                   limit: Optional[int] = None) -> pd.DataFrame:
        """Retrieve evaluation metrics with optional filtering."""
        
        query = "SELECT * FROM evaluations WHERE 1=1"
        params = []
        
        if model:
            query += " AND model = ?"
            params.append(model)
        
        if evaluation_name:
            query += " AND evaluation_name = ?"
            params.append(evaluation_name)
        
        if hours_back:
            cutoff_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp())
            query += " AND timestamp >= ?"
            params.append(cutoff_time)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['metadata'] = df['metadata'].apply(
                lambda x: json.loads(x) if x else {}
            )
        
        return df
    
    def get_model_aggregates(self, hours_back: int = 24) -> pd.DataFrame:
        """Get aggregated metrics by model for the specified time period."""
        query = """
            SELECT 
                model,
                COUNT(*) as total_runs,
                AVG(success_rate) as avg_success_rate,
                STDEV(success_rate) as std_success_rate,
                AVG(latency_s) as avg_latency,
                STDEV(latency_s) as std_latency,
                AVG(tokens) as avg_tokens,
                STDEV(tokens) as std_tokens,
                SUM(cost_usd) as total_cost,
                MIN(timestamp) as first_run,
                MAX(timestamp) as last_run
            FROM evaluations 
            WHERE timestamp >= ?
            GROUP BY model
            ORDER BY avg_success_rate DESC
        """
        
        cutoff_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp())
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=[cutoff_time])
        
        if not df.empty:
            df['first_run'] = pd.to_datetime(df['first_run'], unit='s')
            df['last_run'] = pd.to_datetime(df['last_run'], unit='s')
        
        return df
    
    def get_time_series(self, 
                       model: Optional[str] = None,
                       metric: str = 'success_rate',
                       hours_back: int = 168) -> pd.DataFrame:  # 7 days default
        """Get time series data for trend analysis."""
        
        query = f"""
            SELECT timestamp, model, {metric}
            FROM evaluations 
            WHERE timestamp >= ?
        """
        params = [int((datetime.now() - timedelta(hours=hours_back)).timestamp())]
        
        if model:
            query += " AND model = ?"
            params.append(model)
        
        query += " ORDER BY timestamp"
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        return df
    
    def store_alert(self, alert_type: str, severity: str, model: str, 
                   message: str, current_value: float, baseline_value: float,
                   threshold_value: float, metadata: Dict = None) -> str:
        """Store an alert record."""
        alert_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alerts 
                (id, timestamp, alert_type, severity, model, message, 
                 current_value, baseline_value, threshold_value, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_id,
                int(datetime.now().timestamp()),
                alert_type,
                severity,
                model,
                message,
                current_value,
                baseline_value,
                threshold_value,
                json.dumps(metadata or {})
            ))
        
        logger.info(f"Stored alert: {alert_id} - {message}")
        return alert_id
    
    def mark_alert_sent(self, alert_id: str) -> bool:
        """Mark an alert as sent to prevent duplicate notifications."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE alerts SET sent = TRUE WHERE id = ?", 
                [alert_id]
            )
            return cursor.rowcount > 0
    
    def get_recent_alerts(self, hours_back: int = 24) -> pd.DataFrame:
        """Get recent alerts for dashboard display."""
        query = """
            SELECT * FROM alerts 
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """
        
        cutoff_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp())
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=[cutoff_time])
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['metadata'] = df['metadata'].apply(
                lambda x: json.loads(x) if x else {}
            )
        
        return df
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Tuple[int, int]:
        """Clean up old evaluation and alert data."""
        cutoff_time = int((datetime.now() - timedelta(days=days_to_keep)).timestamp())
        
        with sqlite3.connect(self.db_path) as conn:
            eval_deleted = conn.execute(
                "DELETE FROM evaluations WHERE timestamp < ?", 
                [cutoff_time]
            ).rowcount
            
            alert_deleted = conn.execute(
                "DELETE FROM alerts WHERE timestamp < ?", 
                [cutoff_time]
            ).rowcount
        
        logger.info(f"Cleaned up {eval_deleted} evaluations and {alert_deleted} alerts")
        return eval_deleted, alert_deleted
    
    def export_to_csv(self, output_dir: str = "exports") -> List[str]:
        """Export all data to CSV files for external analysis."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        exported_files = []
        
        # Export evaluations
        eval_df = self.get_metrics()
        if not eval_df.empty:
            eval_file = output_path / f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            eval_df.to_csv(eval_file, index=False)
            exported_files.append(str(eval_file))
        
        # Export alerts
        alert_df = self.get_recent_alerts(hours_back=24*30)  # 30 days
        if not alert_df.empty:
            alert_file = output_path / f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            alert_df.to_csv(alert_file, index=False)
            exported_files.append(str(alert_file))
        
        logger.info(f"Exported {len(exported_files)} files to {output_path}")
        return exported_files

def main():
    """CLI for metrics store operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Metrics store operations")
    parser.add_argument("--import-json", action="store_true", 
                       help="Import JSON result files")
    parser.add_argument("--results-dir", default="../results",
                       help="Results directory for import")
    parser.add_argument("--export-csv", action="store_true",
                       help="Export data to CSV")
    parser.add_argument("--cleanup", type=int, metavar="DAYS",
                       help="Clean up data older than N days")
    parser.add_argument("--db-path", default="metrics.db",
                       help="SQLite database path")
    
    args = parser.parse_args()
    
    store = MetricsStore(args.db_path)
    
    if args.import_json:
        count = store.import_from_json_files(args.results_dir)
        print(f"Imported {count} evaluation records")
    
    if args.export_csv:
        files = store.export_to_csv()
        print(f"Exported {len(files)} files")
    
    if args.cleanup:
        eval_count, alert_count = store.cleanup_old_data(args.cleanup)
        print(f"Cleaned up {eval_count} evaluations and {alert_count} alerts")

if __name__ == "__main__":
    main()
