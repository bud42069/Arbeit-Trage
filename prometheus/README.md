# Prometheus & Alerting Setup Guide

## Overview

This directory contains Prometheus configuration files for monitoring and alerting on the CEX/DEX Arbitrage Platform.

## Files

- `prometheus.yml` - Prometheus server configuration
- `alerts.yml` - Alerting rules for critical events
- `alertmanager.yml` - Alertmanager configuration (routing and receivers)

## Quick Start

### 1. Install Prometheus

```bash
# Linux (Ubuntu/Debian)
wget https://github.com/prometheus/prometheus/releases/download/v2.48.0/prometheus-2.48.0.linux-amd64.tar.gz
tar xvfz prometheus-2.48.0.linux-amd64.tar.gz
cd prometheus-2.48.0.linux-amd64/

# Copy config files
cp /app/prometheus/prometheus.yml .
cp /app/prometheus/alerts.yml .

# Start Prometheus
./prometheus --config.file=prometheus.yml
```

### 2. Install Alertmanager

```bash
# Linux (Ubuntu/Debian)
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-0.26.0.linux-amd64.tar.gz
cd alertmanager-0.26.0.linux-amd64/

# Copy config
cp /app/prometheus/alertmanager.yml .

# Update Slack webhook URL
sed -i 's/YOUR_SLACK_WEBHOOK_URL_HERE/https:\/\/hooks.slack.com\/services\/YOUR\/WEBHOOK\/URL/' alertmanager.yml

# Start Alertmanager
./alertmanager --config.file=alertmanager.yml
```

### 3. Configure Slack Integration

1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to workspace
5. Select channel (#arbitrage-alerts)
6. Copy webhook URL
7. Update in `alertmanager.yml`:
   ```yaml
   slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
   ```

### 4. Verify Setup

```bash
# Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Check alerts are loaded
curl http://localhost:9090/api/v1/rules

# Test alertmanager
curl http://localhost:9093/-/healthy
```

## Alert Rules Reference

### Critical Alerts (Immediate Action)

| Alert | Threshold | Action |
|-------|-----------|--------|
| ConnectorDisconnected | venue offline > 30s | Check logs, verify API keys |
| StaleDataDetected | no data > 10s | Verify network, restart connector |
| DailyLossLimitExceeded | PnL < -$500 | Review trades, investigate |
| ServiceDown | Prometheus can't scrape | Check service status |
| MaxPositionSizeViolation | Position > $1000 | Immediate investigation |

### Warning Alerts (Monitor)

| Alert | Threshold | Action |
|-------|-----------|--------|
| DailyLossLimitApproaching | PnL < -$400 | Monitor closely |
| TradingSystemPaused | paused > 1min | Check pause reason |
| HighAPIErrorRate | 5xx rate > 5% | Check logs |
| HighDetectionLatency | p95 > 2s | Optimize signal engine |
| HighExecutionLatency | p95 > 1.5s | Check API response times |
| HighExecutionFailureRate | failures > 10% | Review execution logs |

### Info Alerts (FYI)

| Alert | Threshold | Action |
|-------|-----------|--------|
| NoOpportunitiesDetected | 0 opps for 1hr | Normal during low volatility |

## Testing Alerts

### Manually Trigger Alerts

```bash
# Test connection alert - pause Gemini connector
supervisorctl stop backend
sleep 40
# Alert should fire after 30 seconds

# Test staleness alert - block network (requires root)
iptables -A OUTPUT -d api.gemini.com -j DROP
sleep 15
# Alert should fire after 10 seconds
iptables -D OUTPUT -d api.gemini.com -j DROP

# Test loss limit - inject losing trades
for i in {1..10}; do
  curl -X POST "http://localhost:8001/api/v1/test/inject-opportunity?spread_pct=-2.0"
  sleep 1
done
# Check if daily PnL drops below -$400
```

### Check Alert Status

```bash
# View active alerts
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {alertname: .labels.alertname, state: .state}'

# Check alertmanager
curl -s http://localhost:9093/api/v2/alerts | jq '.[] | {status: .status.state, alertname: .labels.alertname}'
```

## Slack Channel Setup

Recommended channel structure:

- **#arbitrage-critical** - Critical alerts requiring immediate action
- **#arbitrage-warnings** - Warnings to monitor
- **#arbitrage-info** - Informational alerts and daily digest
- **#arbitrage-resolved** - Resolved alerts (optional)

## PagerDuty Integration (Optional)

1. Create PagerDuty integration
2. Get integration key
3. Update `alertmanager.yml`:
   ```yaml
   pagerduty_configs:
     - routing_key: 'YOUR_KEY_HERE'
   ```
4. Restart alertmanager

## Grafana Dashboards

For visualization, import pre-built dashboard (create separately):

- Connection status panels
- Opportunity rate charts
- PnL tracking
- Latency heatmaps
- Error rate graphs

## Maintenance

### Daily
- Review alert notifications in Slack
- Check for any critical alerts
- Verify no alerts are stuck in "pending" state

### Weekly
- Review alert thresholds for false positives
- Adjust sensitivity as needed
- Check Prometheus storage usage

### Monthly
- Update alert rules based on operational learnings
- Review and tune thresholds
- Test alert delivery (email, Slack, PagerDuty)

## Troubleshooting

### Alerts Not Firing

```bash
# Check if Prometheus is evaluating rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {alert: .name, state: .state}'

# Check if metrics are being scraped
curl -s http://localhost:9090/api/v1/query?query=arb_connection_status | jq .

# Verify alertmanager is configured
curl http://localhost:9090/api/v1/alertmanagers
```

### Alerts Not Reaching Slack

```bash
# Test alertmanager
curl -s http://localhost:9093/-/healthy

# Check alertmanager logs
journalctl -u alertmanager -n 100

# Test Slack webhook manually
curl -X POST YOUR_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test alert from Arbitrage system"}'
```

### Too Many Alerts

- Increase `for:` duration in alert rules
- Adjust thresholds to be less sensitive
- Use inhibit_rules to suppress redundant alerts
- Configure repeat_interval to reduce spam

## Resources

- **Prometheus Docs:** https://prometheus.io/docs/
- **Alertmanager Docs:** https://prometheus.io/docs/alerting/latest/alertmanager/
- **Slack Integration:** https://api.slack.com/messaging/webhooks
- **PagerDuty Integration:** https://www.pagerduty.com/docs/guides/prometheus-integration-guide/
