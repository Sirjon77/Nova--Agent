# 📈 Nova Agent Monitoring & Alerting Plan

This document outlines a basic monitoring and alerting strategy for Nova Agent in production. The goal is to detect anomalies early (such as missed governance cycles, rapid growth in task failures, or memory bloat) and notify operators so they can intervene before issues impact RPM or reach.

## Key Metrics to Track

| Metric | Source | Why it matters |
| --- | --- | --- |
| **Governance cycles per day** | Prometheus counter `nova_governance_runs_total` | Ensures that the nightly governance loop is running as scheduled. A drop could indicate a scheduler failure or crash. |
| **Flagged channels by type** | Prometheus counter `flagged_channels_total{flag="…"}` | Tracks how many channels were retired, watched or promoted. Sudden spikes may suggest changes in scoring or unusual performance shifts. |
| **Task execution count & duration** | Prometheus counter `nova_tasks_executed` and histogram `nova_task_duration_seconds` | Provides visibility into task throughput and latency. Increases in duration might indicate external API slowness. |
| **Tool health status** | Prometheus gauge `nova_tool_health_status{tool="…"}` and `nova_tool_latency_ms{tool="…"}` | Monitors the availability and latency of external services (e.g. vidIQ, Metricool). Non‑OK statuses should trigger investigation. |
| **Process memory usage** | System metric from `nova.memory_guard` | Detects memory leaks or runaway processes. Compare against limits set in `policy.yaml`. |
| **Pending approvals queue length** | Count of drafts in `data/pending_approvals.json` | A growing queue could indicate bottlenecks in manual review or misconfigured approval flags. |
| **Audit errors and warnings** | Log entries via `/api/logs?level=error` | Surface critical issues not captured by metrics, such as unexpected exceptions or failed API calls. |

## Alerting Guidelines

1. **Missed Governance Run**: If no new governance report is produced within 24 hours, send a Slack/email alert. Use a Prometheus alert rule on the derivative of `nova_governance_runs_total`.
2. **High Failure Rate**: Trigger an alert if more than 10 % of tasks fail within a one‑hour window. This can be calculated by comparing task status counts in the task manager logs or a derived Prometheus metric.
3. **Tool Outage**: Alert when `nova_tool_health_status{tool}` becomes `0` or when latency exceeds the expected threshold (configured in `settings.yaml`).
4. **Memory Threshold**: Alert if process RSS exceeds the `memory_limit_mb` specified in `policy.yaml` for more than 10 minutes. Tune thresholds based on baseline usage.
5. **Large Approval Backlog**: Alert if the number of pending approvals exceeds a configured limit (e.g. 20 drafts) or if a single draft has been pending for over 12 hours.

## Implementation Notes

* **Prometheus & Grafana**: Expose metrics via the `/metrics` endpoint (either using `prometheus_fastapi_instrumentator` or the fallback implemented in `nova.api.app`). Scrape these metrics into Prometheus and build dashboards in Grafana. Configure alert rules as described above.
* **Log Aggregation**: Ship `logs/audit.log` and other application logs to a central log management system (e.g. Loki, ELK). Use alerts on error patterns or high log volume.
* **Slack & Email Notifications**: Use the existing `nova.notify.send_alert` helper to send immediate alerts for task failures, governance completion summaries, and other critical events. Ensure environment variables (`SLACK_WEBHOOK_URL`, `SMTP_SERVER`, etc.) are set.
* **Periodic Reviews**: Schedule monthly reviews of metrics trends and adjust thresholds, weights, or scoring logic based on observed performance. Continually refine what constitutes “normal” behaviour as the system scales.

By following this monitoring plan, operators can maintain high confidence that Nova Agent is operating within expected parameters and intervene quickly when anomalies arise. Continuous monitoring is essential to protect RPM and ensure long‑term scalability of the platform.