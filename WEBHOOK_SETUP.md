# 🔔 Webhook Setup Guide for Amp Evaluation Dashboard

## Overview
The dashboard supports webhook notifications for performance alerts via Slack, Microsoft Teams, Discord, or custom endpoints.

## 🔧 Setup Methods

### 1. Slack Webhooks (Recommended)

**Step 1: Create Slack App**
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Amp Evaluation Bot"
4. Choose your workspace

**Step 2: Enable Incoming Webhooks**
1. Go to "Incoming Webhooks" in your app settings
2. Toggle "Activate Incoming Webhooks" to On
3. Click "Add New Webhook to Workspace"
4. Choose channel (e.g., #alerts, #engineering)
5. Copy the webhook URL (starts with `https://hooks.slack.com/services/`)

**Step 3: Configure Dashboard**
```bash
export ALERT_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
# OR set in dashboard sidebar
```

### 2. Microsoft Teams

**Step 1: Add Incoming Webhook Connector**
1. In your Teams channel, click "..." → "Connectors"
2. Find "Incoming Webhook" → "Configure"
3. Name: "Amp Evaluation Alerts"
4. Upload icon (optional)
5. Copy the webhook URL

**Step 2: Use Teams Format**
```python
# The dashboard auto-detects Teams webhooks and uses appropriate format
export ALERT_WEBHOOK_URL="https://your-tenant.webhook.office.com/webhookb2/..."
```

### 3. Discord

**Step 1: Create Discord Webhook**
1. Go to your Discord server settings
2. Integrations → Webhooks → "New Webhook"
3. Choose channel and copy URL

**Step 2: Configure**
```bash
export ALERT_WEBHOOK_URL="https://discord.com/api/webhooks/your-webhook-id/your-token"
```

### 4. Custom Endpoints

For custom integrations, webhook receives:
```json
{
  "text": "🚨 Alert message",
  "attachments": [{
    "color": "danger",
    "fields": [
      {"title": "Model", "value": "gpt-5", "short": true},
      {"title": "Current Value", "value": "0.847", "short": true}
    ]
  }]
}
```

## 🧪 Testing Webhooks

### Quick Test with webhook.site
1. Go to https://webhook.site
2. Copy your unique URL
3. Test with our utility:

```bash
cd dashboard
python3 webhook_test.py --url "https://webhook.site/your-unique-id" --test all
```

### Local Testing Server
```bash
# Start local test server
python3 webhook_test.py --local-server

# In another terminal, test against localhost
python3 webhook_test.py --url "http://localhost:8888" --test all
```

### Production Testing
```bash
# Test your actual webhook
python3 webhook_test.py --url "$ALERT_WEBHOOK_URL" --test basic

# Test alert format
python3 webhook_test.py --url "$ALERT_WEBHOOK_URL" --test alert

# Simulate alert sequence
python3 webhook_test.py --url "$ALERT_WEBHOOK_URL" --test sequence
```

## 🚨 Alert Types & Conditions

| Alert Type | Trigger Condition | Default Threshold |
|------------|------------------|-------------------|
| **Accuracy Drop** | Success rate decreases | > 5% drop |
| **Token Overrun** | Token usage increases | > 25% increase |
| **Latency Spike** | Response time increases | > 50% increase |
| **Oracle Overuse** | Unexpected o3 usage | > 10% of total calls |

### Customizing Thresholds
```python
# In dashboard sidebar or environment
ACCURACY_THRESHOLD=3.0    # 3% accuracy drop
TOKEN_THRESHOLD=20.0      # 20% token increase
LATENCY_THRESHOLD=75.0    # 75% latency increase
```

## 🔄 Alert Deduplication

- **Cooldown Period**: 1 hour (3600 seconds) by default
- **Same alert won't fire** until cooldown expires
- **Prevents spam** during ongoing issues

Configure cooldown:
```bash
export ALERT_COOLDOWN=1800  # 30 minutes
```

## 📊 Dashboard Integration

### Manual Alert Testing
1. Open dashboard: http://localhost:8501
2. Enter webhook URL in sidebar
3. Set alert thresholds
4. Generate test alerts from interface

### Automated Monitoring
```bash
# Run alert checker every 15 minutes
*/15 * * * * cd /path/to/amp-eval/dashboard && python3 alerting.py

# Or use the alerting service
python3 alerting.py --webhook-url "$ALERT_WEBHOOK_URL"
```

## 🛡️ Security Best Practices

### 1. Webhook URL Protection
```bash
# Store in environment, not code
export ALERT_WEBHOOK_URL="https://..."

# Or use secret management
kubectl create secret generic webhook-secret --from-literal=url="https://..."
```

### 2. Rate Limiting
- Built-in cooldown prevents spam
- Dashboard implements exponential backoff
- Monitor webhook service quotas

### 3. Validation
```python
# Webhooks validate payload before sending
# Failed sends are logged but don't crash dashboard
# Retry logic for temporary failures
```

## 🔍 Troubleshooting

### Common Issues

**"No webhook URL configured"**
```bash
# Set environment variable
export ALERT_WEBHOOK_URL="https://your-webhook-url"
```

**"Failed to send alert: HTTP 400"**
- Check webhook URL format
- Verify service-specific payload requirements
- Test with webhook_test.py

**"Alert sent successfully but not received"**
- Check channel permissions
- Verify workspace/server access
- Test with basic message first

**"Webhook timeout"**
- Check network connectivity
- Increase timeout in alerting.py
- Use local test server to debug

### Debug Mode
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
python3 alerting.py --webhook-url "$ALERT_WEBHOOK_URL"
```

### Testing Checklist

✅ **Basic connectivity**: `webhook_test.py --test basic`  
✅ **Alert format**: `webhook_test.py --test alert`  
✅ **Dashboard integration**: Manual test in UI  
✅ **Alert sequence**: `webhook_test.py --test sequence`  
✅ **Cooldown behavior**: Generate duplicate alerts  

## 📱 Mobile Notifications

For mobile alerts, consider:
- **Slack mobile app** (push notifications)
- **Teams mobile app** 
- **PagerDuty integration** via webhook forwarding
- **Custom mobile app** using webhook → push service

## 🔄 Next Steps

1. **Set up primary webhook** (Slack/Teams)
2. **Test with webhook_test.py**
3. **Configure alert thresholds**
4. **Set up cron job** for continuous monitoring
5. **Add secondary channels** for critical alerts

Your webhook system is now ready for production monitoring! 🚀
