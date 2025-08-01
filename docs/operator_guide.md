# Nova Agent Operator Guide

This guide explains how to operate Nova Agent v7 as an administrator. It covers daily workflows, system controls and manual overrides, so you can maintain optimal RPM (revenue per mille) and retention while ensuring compliance with platform policies.

## 1. Logging in

Nova Agent exposes a REST API secured with JWT authentication. To obtain a token:

1. Send a `POST` request to `/api/auth/login` with your username and password:

   ```json
   {
     "username": "admin",
     "password": "admin"
   }
   ```

2. The response contains a `token` and your `role`. Include this token as a `Bearer` token in the `Authorization` header for subsequent requests. Only users with the `admin` role can access governance reports, automation flags, approvals and overrides.

## 2. Dashboard endpoints

Nova’s backend provides endpoints consumed by the frontend dashboard. Key ones include:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/channels` | GET | Returns the latest channel performance data (scores, flags) from the most recent governance report. |
| `/api/tasks` | GET | Lists all tasks currently tracked by the task manager (generation, posting, governance runs). Admin‑only. |
| `/api/governance/report` | GET | Retrieves the latest or a specific dated governance report. Admin‑only. |
| `/api/governance/history` | GET | Lists available governance report filenames. Admin‑only. |
| `/api/logs` | GET | Returns recent audit log entries; pass `level=error` to filter. Admin‑only. |
| `/api/automation/flags` | GET/POST | View or update global automation flags: `posting_enabled`, `generation_enabled`, `require_approval`. Admin‑only. |
| `/api/channels/{id}/override` | GET/POST/DELETE | View, set or clear a manual override for a channel’s retire/promote flag. Admin‑only. |
| `/api/approvals` | GET | Lists content awaiting approval when `require_approval` is enabled. Admin‑only. |
| `/api/approvals/{id}/approve` | POST | Approves a pending draft and schedules it for publishing. Admin‑only. |
| `/api/approvals/{id}/reject` | POST | Rejects a pending draft. Admin‑only. |

## 3. Automation flags

Global flags control high‑level behaviour:

* **posting_enabled** – When `false`, all automated publishing is paused. Content generation can still proceed, but posts will not be sent to platforms. Use this during investigations or when your accounts are under review.
* **generation_enabled** – When `false`, the agent will not create new content ideas or drafts. Use this if you wish to freeze ideation without affecting existing scheduled posts.
* **require_approval** – When `true`, any attempt to publish via Publer, YouTube, Instagram or Facebook will be deferred. The content is stored in a pending approvals queue and must be manually approved before publishing.

To view current flags:

```bash
GET /api/automation/flags
```

To update one or more flags:

```bash
POST /api/automation/flags

{
  "posting_enabled": false,
  "require_approval": true
}
```

## 4. Channel flag overrides

Governance cycles may flag channels as **promote**, **watch** or **retire** based on performance. To override an automated decision (e.g. keep publishing to a retired channel), use the override endpoints.

* **View current override:**
  ```bash
  GET /api/channels/{channel_id}/override
  ```
* **Set override:**
  ```bash
  POST /api/channels/{channel_id}/override
  {
    "action": "ignore_retire"  // or force_retire, force_promote, ignore_promote
  }
  ```
* **Clear override:**
  ```bash
  DELETE /api/channels/{channel_id}/override
  ```

Overrides take effect on the next governance cycle and are recorded in the audit log for traceability.

## 5. Content approval workflow

When `require_approval` is enabled, posting functions in the integrations layer (Publer, YouTube, Instagram, Facebook) will create a **draft** instead of publishing. Each draft contains the provider, function name and arguments needed for publishing.

1. **List drafts** using `GET /api/approvals`. Each entry has an `id`, `provider`, `function`, argument details and metadata.
2. **Review the content** via the dashboard (front‑end should display a preview or text). Decide to approve or reject.
3. **Approve** with `POST /api/approvals/{id}/approve`. The system will enqueue a publish task and remove the draft from the pending list. If publishing fails, an alert is sent via Slack/email.
4. **Reject** with `POST /api/approvals/{id}/reject`. The draft is discarded and will not be posted.

## 6. Notifications

Nova sends alerts through Slack and/or email when:

* A governance report finishes, summarising flagged channels and tool health.
* A scheduled task fails (e.g. a content upload error). You will see a message like “Task 12345 (publish_post) failed: RuntimeError…” in Slack or email.

Configure notifications via environment variables:

* **Slack** – Set `SLACK_WEBHOOK_URL`. The webhook must be associated with a channel where you want alerts.
* **Email** – Set `SMTP_SERVER`, `SMTP_USER`, `SMTP_PASSWORD` and `ALERT_EMAIL`. Optional `SMTP_PORT` defaults to `587`.

## 7. Audit log access

Nova writes audit events (channel flag decisions, overrides, operator actions) to `logs/audit.log`. Use `GET /api/logs` to retrieve recent entries. You can filter by severity:

```bash
GET /api/logs?level=error
```

Consider tailing this file directly in production for real‑time visibility. Ensure sensitive information (API keys, tokens) is not logged.

## 8. Maintenance

Periodic tasks for operators:

* **Refresh API tokens:** Some services (Instagram) require periodic token refresh. Update the respective environment variables and restart the API.
* **Update configuration:** Adjust thresholds, trend sources or tool lists in `config/settings.yaml` and restart the governance cycle if necessary.
* **Monitor tool health:** Use the governance report’s tools section to identify degraded services. Investigate and adjust usage to avoid downtime.
* **Review prompts and monetization funnels:** Based on performance metrics and RPM, refine prompt templates and funnel strategies in the Notion control hub or your content repository.

## 9. Contact and support

For questions about Nova Agent operations, refer to the chat history or contact Jonathan Stuart. All system changes should be documented in Notion and approved by the governance team.