"""
Slack integration for the Amp Evaluation Suite.
Handles notifications, alerts, and interactive commands.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuration for different types of alerts."""
    name: str
    channel: str
    threshold: float
    message_template: str
    severity: str = "warning"  # info, warning, error, critical
    cooldown_minutes: int = 60


class SlackNotifier:
    """Handles Slack notifications for the Amp Evaluation Suite."""
    
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.client = None
        
        if self.bot_token:
            self.client = WebClient(token=self.bot_token)
        
        # Alert configurations
        self.alert_configs = {
            "performance_regression": AlertConfig(
                name="Performance Regression",
                channel="#amp-eval-alerts",
                threshold=5.0,  # 5% drop
                message_template="⚠️ Performance regression detected: {model} {metric} dropped {change}%",
                severity="warning",
                cooldown_minutes=30
            ),
            "cost_spike": AlertConfig(
                name="Cost Spike",
                channel="#amp-eval-alerts", 
                threshold=50.0,  # $50 above daily average
                message_template="💰 Cost spike alert: Daily spend ${amount} is ${over} above average",
                severity="error",
                cooldown_minutes=60
            ),
            "oracle_overuse": AlertConfig(
                name="Oracle Overuse",
                channel="#amp-eval-alerts",
                threshold=10.0,  # 10% of total runs
                message_template="🔮 Oracle usage is {percentage}% of total runs (threshold: {threshold}%)",
                severity="warning",
                cooldown_minutes=120
            ),
            "evaluation_failure": AlertConfig(
                name="Evaluation Failure",
                channel="#amp-eval-alerts",
                threshold=3.0,  # 3 consecutive failures
                message_template="❌ Evaluation suite '{suite}' failed {count} times consecutively",
                severity="error",
                cooldown_minutes=15
            ),
            "system_health": AlertConfig(
                name="System Health",
                channel="#amp-eval-alerts",
                threshold=99.0,  # Below 99% uptime
                message_template="🚨 System health degraded: {metric} at {value}% (threshold: {threshold}%)",
                severity="critical",
                cooldown_minutes=5
            )
        }
        
        # Tracking last alert times for cooldown
        self._last_alerts = {}
    
    def send_alert(self, alert_type: str, data: Dict[str, Any]) -> bool:
        """Send an alert if conditions are met and cooldown has passed."""
        if alert_type not in self.alert_configs:
            logger.error(f"Unknown alert type: {alert_type}")
            return False
        
        config = self.alert_configs[alert_type]
        
        # Check cooldown
        last_alert_time = self._last_alerts.get(alert_type)
        if last_alert_time:
            cooldown_delta = timedelta(minutes=config.cooldown_minutes)
            if datetime.now() - last_alert_time < cooldown_delta:
                logger.debug(f"Alert {alert_type} still in cooldown")
                return False
        
        # Format message
        message = config.message_template.format(**data)
        
        # Send to Slack
        success = self._send_message(
            channel=config.channel,
            text=message,
            severity=config.severity,
            alert_type=alert_type,
            data=data
        )
        
        if success:
            self._last_alerts[alert_type] = datetime.now()
        
        return success
    
    def send_daily_summary(self, channel: str = "#amp-eval") -> bool:
        """Send daily summary of evaluation activity."""
        # This would typically fetch data from the evaluation results
        summary_data = self._get_daily_summary()
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Daily Amp Evaluation Summary"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Evaluations Run:* {summary_data.get('total_evaluations', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Success Rate:* {summary_data.get('success_rate', 0):.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Cost:* ${summary_data.get('total_cost', 0):.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Avg Response Time:* {summary_data.get('avg_response_time', 0):.1f}s"
                    }
                ]
            }
        ]
        
        # Add top performing models
        if summary_data.get('top_models'):
            model_text = []
            for model, score in summary_data['top_models'].items():
                model_text.append(f"• {model}: {score:.1f}%")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Performing Models:*\n" + "\n".join(model_text)
                }
            })
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Dashboard"
                    },
                    "url": os.getenv("DASHBOARD_URL", "http://localhost:8501"),
                    "action_id": "view_dashboard"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text", 
                        "text": "Run Evaluation"
                    },
                    "action_id": "run_evaluation"
                }
            ]
        })
        
        return self._send_blocks(channel=channel, blocks=blocks)
    
    def send_new_evaluation_notification(self, suite_name: str, description: str, 
                                       estimated_cost: float, channel: str = "#amp-eval") -> bool:
        """Notify team about new evaluation suite."""
        message = {
            "text": f"🆕 New evaluation suite: {suite_name}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🆕 New Evaluation Suite Added"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Suite:* {suite_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Estimated Monthly Cost:* ${estimated_cost:.2f}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{description}"
                    }
                }
            ]
        }
        
        return self._send_message_dict(channel=channel, message=message)
    
    def send_weekly_report(self, channel: str = "#amp-eval") -> bool:
        """Send weekly performance and cost report."""
        report_data = self._get_weekly_report()
        
        # Create performance trend visualization
        trend_emoji = "📈" if report_data.get('performance_trend', 0) > 0 else "📉"
        cost_emoji = "💰" if report_data.get('cost_trend', 0) > 0 else "💚"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📈 Weekly Amp Evaluation Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Performance Summary*\n{trend_emoji} Overall accuracy: {report_data.get('avg_accuracy', 0):.1f}% ({report_data.get('performance_trend', 0):+.1f}% vs last week)"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Cost Summary*\n{cost_emoji} Total cost: ${report_data.get('total_cost', 0):.2f} ({report_data.get('cost_trend', 0):+.1f}% vs last week)"
                }
            }
        ]
        
        # Add top issues if any
        if report_data.get('issues'):
            issue_text = []
            for issue in report_data['issues'][:3]:  # Top 3 issues
                issue_text.append(f"• {issue}")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Issues to Address:*\n" + "\n".join(issue_text)
                }
            })
        
        return self._send_blocks(channel=channel, blocks=blocks)
    
    def handle_slash_command(self, command: str, args: List[str], user_id: str, channel_id: str) -> Dict:
        """Handle slash commands like /amp-eval status."""
        if command == "status":
            return self._handle_status_command(user_id, channel_id)
        elif command == "run":
            return self._handle_run_command(args, user_id, channel_id)
        elif command == "cost":
            return self._handle_cost_command(user_id, channel_id)
        elif command == "help":
            return self._handle_help_command(user_id, channel_id)
        else:
            return {
                "response_type": "ephemeral",
                "text": f"Unknown command: {command}. Use `/amp-eval help` for available commands."
            }
    
    def _send_message(self, channel: str, text: str, severity: str = "info", 
                     alert_type: str = None, data: Dict = None) -> bool:
        """Send a basic message to Slack."""
        # Choose color based on severity
        color_map = {
            "info": "#36a64f",      # Green
            "warning": "#ffaa00",   # Orange 
            "error": "#ff0000",     # Red
            "critical": "#800080"   # Purple
        }
        
        color = color_map.get(severity, "#36a64f")
        
        if self.client:
            try:
                self.client.chat_postMessage(
                    channel=channel,
                    text=text,
                    attachments=[{
                        "color": color,
                        "text": text
                    }]
                )
                return True
            except SlackApiError as e:
                logger.error(f"Failed to send Slack message: {e}")
                return False
        
        elif self.webhook_url:
            payload = {
                "channel": channel,
                "text": text,
                "attachments": [{
                    "color": color,
                    "text": text
                }]
            }
            
            try:
                response = requests.post(self.webhook_url, json=payload, timeout=10)
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send webhook message: {e}")
                return False
        
        logger.warning("No Slack configuration available")
        return False
    
    def _send_blocks(self, channel: str, blocks: List[Dict]) -> bool:
        """Send a message with rich formatting blocks."""
        if self.client:
            try:
                self.client.chat_postMessage(channel=channel, blocks=blocks)
                return True
            except SlackApiError as e:
                logger.error(f"Failed to send Slack blocks: {e}")
                return False
        
        elif self.webhook_url:
            payload = {"channel": channel, "blocks": blocks}
            try:
                response = requests.post(self.webhook_url, json=payload, timeout=10)
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send webhook blocks: {e}")
                return False
        
        return False
    
    def _send_message_dict(self, channel: str, message: Dict) -> bool:
        """Send a pre-formatted message dictionary."""
        if self.client:
            try:
                self.client.chat_postMessage(channel=channel, **message)
                return True
            except SlackApiError as e:
                logger.error(f"Failed to send Slack message: {e}")
                return False
        
        elif self.webhook_url:
            payload = {"channel": channel, **message}
            try:
                response = requests.post(self.webhook_url, json=payload, timeout=10)
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send webhook message: {e}")
                return False
        
        return False
    
    def _get_daily_summary(self) -> Dict[str, Any]:
        """Get daily summary data. In practice, this would query the database."""
        # Placeholder - would integrate with actual evaluation results
        return {
            "total_evaluations": 47,
            "success_rate": 87.2,
            "total_cost": 23.45,
            "avg_response_time": 2.3,
            "top_models": {
                "gpt-5": 92.1,
                "sonnet-4": 85.7,
                "o3": 94.3
            }
        }
    
    def _get_weekly_report(self) -> Dict[str, Any]:
        """Get weekly report data. In practice, this would query the database."""
        # Placeholder - would integrate with actual evaluation results
        return {
            "avg_accuracy": 86.5,
            "performance_trend": -2.1,
            "total_cost": 164.30,
            "cost_trend": 12.5,
            "issues": [
                "single_file_fix suite showing degraded performance",
                "Oracle usage increased to 8.2% (approaching 10% threshold)",
                "Token efficiency down 15% for gpt-5 tasks"
            ]
        }
    
    def _handle_status_command(self, user_id: str, channel_id: str) -> Dict:
        """Handle /amp-eval status command."""
        # Would query actual system status
        status_data = {
            "system_health": "healthy",
            "active_evaluations": 3,
            "queue_depth": 2,
            "last_run": "2 minutes ago"
        }
        
        return {
            "response_type": "ephemeral",
            "text": f"*Amp Evaluation Status*\n"
                   f"System: {status_data['system_health']}\n"
                   f"Active: {status_data['active_evaluations']} evaluations\n"
                   f"Queue: {status_data['queue_depth']} pending\n"
                   f"Last run: {status_data['last_run']}"
        }
    
    def _handle_run_command(self, args: List[str], user_id: str, channel_id: str) -> Dict:
        """Handle /amp-eval run [suite] command."""
        if not args:
            return {
                "response_type": "ephemeral",
                "text": "Usage: `/amp-eval run <suite-name>`\nAvailable suites: tool_calling_micro, single_file_fix, oracle_knowledge"
            }
        
        suite_name = args[0]
        # Would trigger actual evaluation run
        return {
            "response_type": "in_channel",
            "text": f"🚀 {user_id} started evaluation suite: `{suite_name}`\nResults will be posted when complete."
        }
    
    def _handle_cost_command(self, user_id: str, channel_id: str) -> Dict:
        """Handle /amp-eval cost command."""
        # Would query actual cost data
        cost_data = {
            "today": 12.34,
            "week": 78.90,
            "month": 234.56,
            "budget": 500.00
        }
        
        budget_pct = (cost_data["month"] / cost_data["budget"]) * 100
        
        return {
            "response_type": "ephemeral",
            "text": f"*Cost Summary*\n"
                   f"Today: ${cost_data['today']:.2f}\n"
                   f"This week: ${cost_data['week']:.2f}\n"
                   f"This month: ${cost_data['month']:.2f} ({budget_pct:.1f}% of budget)\n"
                   f"Monthly budget: ${cost_data['budget']:.2f}"
        }
    
    def _handle_help_command(self, user_id: str, channel_id: str) -> Dict:
        """Handle /amp-eval help command."""
        return {
            "response_type": "ephemeral",
            "text": "*Amp Evaluation Commands*\n"
                   "`/amp-eval status` - Show system status\n"
                   "`/amp-eval run <suite>` - Run evaluation suite\n"
                   "`/amp-eval cost` - Show cost summary\n"
                   "`/amp-eval help` - Show this help\n\n"
                   "For more info, visit the dashboard or check #amp-eval"
        }


# Flask app for handling Slack webhooks and slash commands
def create_slack_app():
    """Create Flask app for Slack webhook handling."""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    notifier = SlackNotifier()
    
    @app.route("/slack/events", methods=["POST"])
    def handle_slack_events():
        """Handle Slack event subscriptions."""
        data = request.json
        
        # Handle URL verification
        if data.get("type") == "url_verification":
            return jsonify({"challenge": data["challenge"]})
        
        # Handle actual events
        event = data.get("event", {})
        if event.get("type") == "app_mention":
            # Handle @amp-eval mentions
            channel = event["channel"]
            text = event["text"]
            user = event["user"]
            
            # Simple command parsing
            if "status" in text.lower():
                response = notifier._handle_status_command(user, channel)
                notifier._send_message(channel, response["text"])
        
        return jsonify({"status": "ok"})
    
    @app.route("/slack/commands", methods=["POST"])
    def handle_slash_commands():
        """Handle Slack slash commands."""
        command_text = request.form.get("text", "")
        user_id = request.form.get("user_id")
        channel_id = request.form.get("channel_id")
        
        # Parse command and arguments
        parts = command_text.split()
        command = parts[0] if parts else "help"
        args = parts[1:] if len(parts) > 1 else []
        
        response = notifier.handle_slash_command(command, args, user_id, channel_id)
        return jsonify(response)
    
    @app.route("/slack/interactive", methods=["POST"])
    def handle_interactive_components():
        """Handle Slack button clicks and interactions."""
        payload = json.loads(request.form["payload"])
        action = payload.get("actions", [{}])[0]
        action_id = action.get("action_id")
        
        if action_id == "run_evaluation":
            # Handle "Run Evaluation" button click
            return jsonify({
                "text": "Which evaluation suite would you like to run?",
                "response_type": "ephemeral",
                "blocks": [
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Tool Calling"},
                                "action_id": "run_tool_calling"
                            },
                            {
                                "type": "button", 
                                "text": {"type": "plain_text", "text": "Bug Fixes"},
                                "action_id": "run_bug_fixes"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Oracle"},
                                "action_id": "run_oracle"
                            }
                        ]
                    }
                ]
            })
        
        return jsonify({"status": "ok"})
    
    return app


if __name__ == "__main__":
    # Example usage
    notifier = SlackNotifier()
    
    # Send test alert
    notifier.send_alert("performance_regression", {
        "model": "gpt-5",
        "metric": "accuracy",
        "change": 7.5
    })
    
    # Send daily summary
    notifier.send_daily_summary()
