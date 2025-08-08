#!/usr/bin/env python3
"""
Webhook testing utilities for Amp Evaluation Dashboard
Test Slack/Teams webhook integrations and alert functionality.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional

class WebhookTester:
    """Test webhook integrations with various payload formats."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def test_basic_slack_message(self) -> bool:
        """Test basic Slack message posting."""
        payload = {
            "text": "🧪 Test message from Amp Evaluation Dashboard",
            "username": "amp-eval-bot",
            "icon_emoji": ":robot_face:"
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            print(f"Basic message test: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"Basic message test failed: {e}")
            return False
    
    def test_alert_format(self) -> bool:
        """Test the actual alert format used by the dashboard."""
        payload = {
            "text": "🚨 TEST ALERT: Success rate dropped by 15.2% for gpt-5",
            "attachments": [{
                "color": "danger",
                "fields": [
                    {"title": "Model", "value": "gpt-5", "short": True},
                    {"title": "Type", "value": "Accuracy Drop", "short": True},
                    {"title": "Severity", "value": "HIGH", "short": True},
                    {"title": "Threshold", "value": "5.0%", "short": True},
                    {"title": "Current Value", "value": "0.847", "short": True},
                    {"title": "Baseline Value", "value": "0.999", "short": True}
                ],
                "footer": "Amp Evaluation Suite",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            print(f"Alert format test: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"Alert format test failed: {e}")
            return False
    
    def test_teams_format(self) -> bool:
        """Test Microsoft Teams webhook format."""
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF6B6B",
            "summary": "Amp Evaluation Alert",
            "sections": [{
                "activityTitle": "🚨 Model Performance Alert",
                "activitySubtitle": "Amp Evaluation Dashboard",
                "activityImage": "https://example.com/amp-logo.png",
                "facts": [
                    {"name": "Model", "value": "gpt-5"},
                    {"name": "Alert Type", "value": "Token Overrun"},
                    {"name": "Current Usage", "value": "1,250 tokens"},
                    {"name": "Baseline", "value": "800 tokens"},
                    {"name": "Increase", "value": "+56.3%"}
                ],
                "markdown": True
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name": "View Dashboard",
                "targets": [{
                    "os": "default",
                    "uri": "http://localhost:8501"
                }]
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            print(f"Teams format test: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"Teams format test failed: {e}")
            return False
    
    def simulate_alert_sequence(self) -> bool:
        """Simulate a sequence of alerts over time."""
        alerts = [
            {"severity": "medium", "message": "Token usage increased by 28% for sonnet-4"},
            {"severity": "high", "message": "Success rate dropped by 8% for gpt-5"},
            {"severity": "critical", "message": "Oracle usage spiked by 45% unexpectedly"}
        ]
        
        colors = {"medium": "warning", "high": "danger", "critical": "#ff0000"}
        
        for i, alert in enumerate(alerts):
            payload = {
                "text": f"🚨 SIMULATION ALERT {i+1}/3: {alert['message']}",
                "attachments": [{
                    "color": colors[alert['severity']],
                    "fields": [
                        {"title": "Severity", "value": alert['severity'].upper(), "short": True},
                        {"title": "Test Sequence", "value": f"{i+1} of 3", "short": True}
                    ],
                    "footer": "Amp Evaluation Suite - Test Mode",
                    "ts": int(datetime.now().timestamp())
                }]
            }
            
            try:
                response = requests.post(self.webhook_url, json=payload, timeout=10)
                print(f"Alert {i+1} sent: {response.status_code}")
                if i < len(alerts) - 1:
                    time.sleep(2)  # Space out alerts
            except Exception as e:
                print(f"Alert {i+1} failed: {e}")
                return False
        
        return True
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all webhook tests and return results."""
        print(f"🧪 Testing webhook: {self.webhook_url}")
        print("-" * 50)
        
        results = {
            "basic_message": self.test_basic_slack_message(),
            "alert_format": self.test_alert_format(),
            "teams_format": self.test_teams_format(),
            "alert_sequence": self.simulate_alert_sequence()
        }
        
        print("\n📊 Test Results:")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test}: {status}")
        
        success_rate = sum(results.values()) / len(results)
        print(f"\nOverall success rate: {success_rate:.1%}")
        
        return results

def get_test_webhook_urls():
    """Get common test webhook URLs and services."""
    return {
        "webhook.site": "https://webhook.site/#!/unique-id",
        "requestbin": "https://requestbin.com/",
        "ngrok_local": "https://your-ngrok-id.ngrok.io/webhook",
        "discord": "https://discord.com/api/webhooks/your-webhook-id/your-token",
        "slack": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    }

def create_local_test_server():
    """Create a simple local webhook test server."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    class WebhookHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            print(f"\n🔔 Received webhook:")
            print(f"Headers: {dict(self.headers)}")
            print(f"Body: {post_data.decode('utf-8')}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "received"}')
        
        def log_message(self, format, *args):
            pass  # Suppress default logging
    
    server = HTTPServer(('localhost', 8888), WebhookHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    print("🌐 Local test server running at http://localhost:8888")
    return server

def main():
    """CLI for webhook testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test webhook integrations")
    parser.add_argument("--url", required=True, help="Webhook URL to test")
    parser.add_argument("--test", choices=["basic", "alert", "teams", "sequence", "all"],
                       default="all", help="Specific test to run")
    parser.add_argument("--local-server", action="store_true",
                       help="Start local test server")
    
    args = parser.parse_args()
    
    if args.local_server:
        server = create_local_test_server()
        print("Press Ctrl+C to stop server")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.shutdown()
            print("\nServer stopped")
        return
    
    tester = WebhookTester(args.url)
    
    if args.test == "all":
        tester.run_all_tests()
    elif args.test == "basic":
        tester.test_basic_slack_message()
    elif args.test == "alert":
        tester.test_alert_format()
    elif args.test == "teams":
        tester.test_teams_format()
    elif args.test == "sequence":
        tester.simulate_alert_sequence()

if __name__ == "__main__":
    print("Webhook Test Utilities")
    print("Available test services:")
    for name, url in get_test_webhook_urls().items():
        print(f"  {name}: {url}")
    print()
    main()
