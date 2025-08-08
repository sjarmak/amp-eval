#!/usr/bin/env python3
"""
Streamlit dashboard for Amp Model-Efficacy Evaluation Suite
Converts the Jupyter notebook analysis into a production web interface.
"""

import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional
import os
import time

# Configure page
st.set_page_config(
    page_title="Amp Model Evaluation Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_eval_results(results_dir: str = "../results") -> List[Dict]:
    """Load all evaluation result files with caching."""
    results_path = Path(results_dir)
    if not results_path.exists():
        return []
    
    all_results = []
    for result_file in results_path.glob("*.json"):
        try:
            with open(result_file) as f:
                data = json.load(f)
                data['eval_name'] = result_file.stem
                data['timestamp'] = result_file.stat().st_mtime
                all_results.append(data)
        except Exception as e:
            st.error(f"Error loading {result_file}: {e}")
    
    return sorted(all_results, key=lambda x: x.get('timestamp', 0), reverse=True)

def aggregate_by_model(results: List[Dict]) -> pd.DataFrame:
    """Group results by model and calculate aggregate metrics."""
    if not results:
        return pd.DataFrame()
    
    # Convert the actual data format to expected format
    processed_results = []
    for result in results:
        if 'test_results' in result:
            # This is a baseline evaluation format
            for test in result['test_results']:
                processed_results.append({
                    'model': test.get('selected_model', 'unknown'),
                    'success_rate': 1.0 if test.get('success', False) else 0.0,
                    'latency_s': 0.5,  # Default latency for test data
                    'tokens': 100,     # Default token count for test data
                    'eval_name': result.get('eval_name', 'baseline'),
                    'timestamp': result.get('timestamp', 0)
                })
        else:
            # This is expected format already
            processed_results.append(result)
    
    if not processed_results:
        return pd.DataFrame()
    
    df = pd.DataFrame(processed_results)
    
    # Ensure required columns exist
    required_cols = ['model', 'success_rate', 'latency_s', 'tokens']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.warning(f"Missing columns in data: {missing_cols}")
        return pd.DataFrame()
    
    model_stats = df.groupby('model').agg({
        'success_rate': ['mean', 'std', 'count'],
        'latency_s': ['mean', 'std'],
        'tokens': ['mean', 'std'],
        'eval_name': 'count'
    }).round(3)
    
    model_stats.columns = [
        'success_rate_mean', 'success_rate_std', 'success_count',
        'latency_mean', 'latency_std', 
        'tokens_mean', 'tokens_std', 
        'total_runs'
    ]
    
    return model_stats

def check_alert_conditions(current_stats: pd.DataFrame, baseline_stats: pd.DataFrame) -> List[Dict]:
    """Check for alert conditions based on performance thresholds."""
    alerts = []
    
    if baseline_stats.empty:
        return alerts
    
    for model in current_stats.index:
        if model not in baseline_stats.index:
            continue
            
        current = current_stats.loc[model]
        baseline = baseline_stats.loc[model]
        
        # Alert 1: KPI drops below threshold (>5% accuracy loss)
        success_diff = (current['success_rate_mean'] - baseline['success_rate_mean']) * 100
        if success_diff < -5:
            alerts.append({
                'type': 'accuracy_drop',
                'model': model,
                'message': f"Success rate dropped by {abs(success_diff):.1f}% for {model}",
                'severity': 'high',
                'current_value': current['success_rate_mean'],
                'baseline_value': baseline['success_rate_mean']
            })
        
        # Alert 2: Token budget overruns
        token_increase = (current['tokens_mean'] - baseline['tokens_mean']) / baseline['tokens_mean'] * 100
        if token_increase > 25:  # 25% increase in token usage
            alerts.append({
                'type': 'token_overrun',
                'model': model,
                'message': f"Token usage increased by {token_increase:.1f}% for {model}",
                'severity': 'medium',
                'current_value': current['tokens_mean'],
                'baseline_value': baseline['tokens_mean']
            })
    
    return alerts

def send_webhook_alert(webhook_url: str, alert: Dict) -> bool:
    """Send alert to webhook (Slack/Teams)."""
    try:
        payload = {
            "text": f"🚨 Amp Evaluation Alert: {alert['message']}",
            "attachments": [{
                "color": "danger" if alert['severity'] == 'high' else "warning",
                "fields": [
                    {"title": "Model", "value": alert['model'], "short": True},
                    {"title": "Type", "value": alert['type'], "short": True},
                    {"title": "Current", "value": f"{alert['current_value']:.3f}", "short": True},
                    {"title": "Baseline", "value": f"{alert['baseline_value']:.3f}", "short": True}
                ]
            }]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Failed to send webhook: {e}")
        return False

def main():
    st.title("🚀 Amp Model Evaluation Dashboard")
    st.markdown("Real-time monitoring of model performance, token efficiency, and accuracy trends")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Webhook configuration
    webhook_url = st.sidebar.text_input(
        "Slack/Teams Webhook URL", 
        value=os.getenv("ALERT_WEBHOOK_URL", ""),
        type="password",
        help="Optional: Set webhook URL for alerts"
    )
    
    # Alert thresholds
    st.sidebar.subheader("Alert Thresholds")
    accuracy_threshold = st.sidebar.slider("Accuracy drop threshold (%)", 1, 20, 5)
    token_threshold = st.sidebar.slider("Token increase threshold (%)", 10, 50, 25)
    
    # Test webhook button
    st.sidebar.subheader("Test Webhook")
    if webhook_url and st.sidebar.button("🧪 Send Test Alert"):
        test_alert = {
            'type': 'test_alert',
            'severity': 'medium',
            'model': 'test-model',
            'message': 'This is a test alert from the dashboard',
            'current_value': 0.75,
            'baseline_value': 0.95
        }
        if send_webhook_alert(webhook_url, test_alert):
            st.sidebar.success("✅ Test alert sent!")
        else:
            st.sidebar.error("❌ Test alert failed!")
    
    # Load data
    with st.spinner("Loading evaluation results..."):
        results = load_eval_results()
    
    if not results:
        st.warning("No evaluation results found. Run evaluations first.")
        st.code("openai tools evaluate amp-eval/evals/tool_calling_micro.yaml --registry amp-eval/adapters")
        return
    
    # Recent vs baseline comparison
    recent_results = [r for r in results if r.get('timestamp', 0) > time.time() - 86400]  # Last 24h
    baseline_results = results[-10:] if len(results) > 10 else results  # Last 10 runs as baseline
    
    current_stats = aggregate_by_model(recent_results) if recent_results else pd.DataFrame()
    baseline_stats = aggregate_by_model(baseline_results)
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    if not current_stats.empty:
        with col1:
            avg_success = current_stats['success_rate_mean'].mean()
            st.metric("Average Success Rate", f"{avg_success:.1%}", 
                     delta=f"{(avg_success - baseline_stats['success_rate_mean'].mean()):.1%}" if not baseline_stats.empty else None)
        
        with col2:
            avg_latency = current_stats['latency_mean'].mean()
            st.metric("Average Latency", f"{avg_latency:.2f}s",
                     delta=f"{(avg_latency - baseline_stats['latency_mean'].mean()):.2f}s" if not baseline_stats.empty else None)
        
        with col3:
            avg_tokens = current_stats['tokens_mean'].mean()
            st.metric("Average Tokens", f"{avg_tokens:.0f}",
                     delta=f"{(avg_tokens - baseline_stats['tokens_mean'].mean()):.0f}" if not baseline_stats.empty else None)
        
        with col4:
            total_runs = current_stats['total_runs'].sum()
            st.metric("Total Runs (24h)", f"{total_runs}")
    
    # Alert checking
    if not current_stats.empty and not baseline_stats.empty:
        alerts = check_alert_conditions(current_stats, baseline_stats)
        
        if alerts:
            st.error(f"🚨 {len(alerts)} Alert(s) Detected!")
            for alert in alerts:
                with st.expander(f"{alert['severity'].upper()}: {alert['message']}", expanded=True):
                    st.json(alert)
                    
                    if webhook_url and st.button(f"Send Alert: {alert['type']}", key=alert['type']):
                        if send_webhook_alert(webhook_url, alert):
                            st.success("Alert sent successfully!")
                        else:
                            st.error("Failed to send alert")
        else:
            st.info("✅ No alerts detected - all models performing within thresholds")
    else:
        st.warning("⚠️ Insufficient data for alert detection (need current + baseline metrics)")
    
    # Model performance comparison
    if not baseline_stats.empty:
        st.header("Model Performance Comparison")
        
        tab1, tab2, tab3 = st.tabs(["Success Rate", "Latency", "Token Usage"])
        
        with tab1:
            fig = px.bar(
                x=baseline_stats.index, 
                y=baseline_stats['success_rate_mean'],
                error_y=baseline_stats['success_rate_std'],
                title="Success Rate by Model",
                labels={'x': 'Model', 'y': 'Success Rate'}
            )
            fig.update_layout(yaxis_tickformat='.1%')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.bar(
                x=baseline_stats.index,
                y=baseline_stats['latency_mean'],
                error_y=baseline_stats['latency_std'],
                title="Average Latency by Model",
                labels={'x': 'Model', 'y': 'Latency (seconds)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            fig = px.bar(
                x=baseline_stats.index,
                y=baseline_stats['tokens_mean'],
                error_y=baseline_stats['tokens_std'],
                title="Average Token Usage by Model",
                labels={'x': 'Model', 'y': 'Tokens'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Time series trends
    if len(results) > 1:
        st.header("Performance Trends")
        
        df_trends = pd.DataFrame(results)
        df_trends['datetime'] = pd.to_datetime(df_trends['timestamp'], unit='s')
        
        fig = px.line(
            df_trends, 
            x='datetime', 
            y='success_rate', 
            color='model',
            title="Success Rate Trends Over Time"
        )
        fig.update_layout(yaxis_tickformat='.1%')
        st.plotly_chart(fig, use_container_width=True)
    
    # Raw data table
    with st.expander("Raw Evaluation Data"):
        if results:
            df_display = pd.DataFrame(results)
            df_display['datetime'] = pd.to_datetime(df_display['timestamp'], unit='s')
            st.dataframe(df_display.drop('timestamp', axis=1), use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total evaluations: {len(results)}")

if __name__ == "__main__":
    main()
