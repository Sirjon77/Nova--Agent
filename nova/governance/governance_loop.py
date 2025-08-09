
import json, pathlib, asyncio
from datetime import datetime
from nova.governance.niche_manager import NicheManager
from nova.governance.trend_scanner import TrendScanner
from nova.governance.tool_checker import ToolChecker
from nova.governance.changelog_watcher import ChangelogWatcher
from nova.policy import PolicyEnforcer
from nova.metrics import (
    governance_runs_total,
    channels_scored,
    actions_flagged,
    governance_loop_duration,
)
from nova.audit_logger import audit

async def run(cfg, channel_metrics, trend_seeds, tools_cfg):
    """Run a full governance cycle.

    This function orchestrates the nightly evaluation of channel performance,
    trending topics and tool health. It enforces policy limits, scores each
    channel, collects trend data, checks tool latency/cost and scans for
    new tool versions. Any flagged channels (retire/promote) are logged
    and annotated with an action for downstream automation.

    Args:
        cfg: Governance configuration dictionary.
        channel_metrics: Iterable of ChannelMetrics instances to score.
        trend_seeds: List of keywords or phrases to feed the trend scanner.
        tools_cfg: Iterable of ToolConfig objects describing external tools.

    Returns:
        The governance report dictionary written to disk.
    """
    # record metrics for observability and log start of cycle
    governance_runs_total.inc()
    audit('governance_cycle_start')

    # enforce global memory limit before doing any heavy work
    enforcer = PolicyEnforcer()
    if not enforcer.check_memory():
        raise MemoryError("Policy memory limit exceeded before governance cycle")

    # initialise core helpers
    nm = NicheManager(cfg['niche'])
    ts = TrendScanner(cfg['trends'])
    tc = ToolChecker(cfg['tools'])
    cw = ChangelogWatcher(cfg.get('changelog', {}))

    # score channels and determine flags
    scored_channels = nm.score_channels(channel_metrics)
    try:
        channels_scored.inc(len(channel_metrics) if channel_metrics else 0)
    except Exception:
        pass

    # Apply channel overrides. Overrides allow operators to force
    # retirement or promotion of specific channels, or to ignore
    # automated retire/promote flags. Load overrides from disk and
    # adjust the flag for each scored channel accordingly.
    try:
        from nova.overrides import load_overrides, VALID_OVERRIDES
        overrides = load_overrides()
    except Exception:
        overrides = {}
    for ch in scored_channels:
        override = overrides.get(ch.channel_id)
        # Add an attribute on the channel object so the report can
        # include the override directive later. This does not affect
        # scoring but makes the override visible to downstream
        # consumers (e.g. UI).
        setattr(ch, 'override', override)
        if override == 'force_retire':
            ch.flag = 'retire'
        elif override == 'force_promote':
            ch.flag = 'promote'
        elif override == 'ignore_retire' and ch.flag == 'retire':
            ch.flag = None
        elif override == 'ignore_promote' and ch.flag == 'promote':
            ch.flag = None

    # collect trend data
    trends = await ts.scan(trend_seeds)
    # Build tool configs from the governance configuration if none provided. If
    # tools_cfg is empty, look for a ``list`` of tools in cfg['tools'] and
    # construct ToolConfig instances. This allows operators to specify
    # monitored tools in ``settings.yaml`` without passing them explicitly.
    tool_cfgs = tools_cfg or []
    if not tool_cfgs:
        for item in cfg.get('tools', {}).get('list', []) or []:
            try:
                # Import here to avoid circular import at module load time
                from nova.governance.tool_checker import ToolConfig as _ToolConfig
                tool_cfgs.append(_ToolConfig(
                    name=item.get('name'),
                    ping_url=item.get('ping_url'),
                    expected_ms=item.get('expected_ms'),
                    cost_per_call=item.get('cost_per_call'),
                ))
            except Exception:
                pass
    # collect tool health metrics
    tool_health = [await tc.check(t) for t in tool_cfgs]

    # scan for new tool versions
    changelog_watch = cfg.get('changelog', {}).get('watch', [])
    changelogs  = await cw.scan(changelog_watch)

    # build report structure and annotate flagged channels
    channels_report = []
    for ch in scored_channels:
        entry = ch.__dict__.copy()
        # assign actions based on flags; log audit for transparency
        if ch.flag == 'retire':
            entry['action'] = 'reduce_content_output'
            audit('channel_flagged_retire', meta={'channel_id': ch.channel_id, 'score': ch.score})
        elif ch.flag == 'promote':
            entry['action'] = 'increase_content_output'
            audit('channel_flagged_promote', meta={'channel_id': ch.channel_id, 'score': ch.score})
        elif ch.flag == 'watch':
            entry['action'] = 'monitor'
            audit('channel_flagged_watch', meta={'channel_id': ch.channel_id, 'score': ch.score})
        else:
            entry['action'] = None
        channels_report.append(entry)

    # derive high-level insight summaries
    promote_list = [c['channel_id'] for c in channels_report if c.get('flag') == 'promote']
    retire_list = [c['channel_id'] for c in channels_report if c.get('flag') == 'retire']
    insights = []
    if promote_list:
        insights.append(f"Channels poised for growth: {', '.join(promote_list)} – recommend doubling down.")
    if retire_list:
        insights.append(f"Underperforming channels: {', '.join(retire_list)} – consider pausing or pivoting.")
    if not insights:
        insights.append("Most channels are stable; continue monitoring.")

    # basic new niche suggestions from trends
    new_niche_suggestions = []
    try:
        for t in trends or []:
            # include a lightweight suggestion payload
            new_niche_suggestions.append({
                'niche': t.get('keyword') or t.get('term') or 'unknown',
                'source': t.get('source', 'unknown'),
                'rationale': f"Projected RPM {t.get('projected_rpm', 'n/a')} with interest {t.get('interest', t.get('interest_score', 'n/a'))}"
            })
    except Exception:
        pass

    report = {
        'timestamp': datetime.utcnow().isoformat(timespec='seconds'),
        'channels': channels_report,
        'trends': trends,
        'tools': tool_health,
        'changelogs': changelogs,
        'insight_summaries': insights,
        'new_niche_suggestions': new_niche_suggestions,
    }

    # -------------------------------------------------------------------------
    # Update Prometheus metrics for flagged channels and tool health
    # For each channel flagged (retire/watch/promote) increment the counter with
    # a label matching the flag. For tools, set gauges for status and latency.
    try:
        from nova.metrics import flagged_channels_total, tool_health_status, tool_latency_ms
        for ch in scored_channels:
            if ch.flag:
                flagged_channels_total.labels(ch.flag).inc()
        for th in tool_health:
            tool = th.get('tool')
            status = th.get('status')
            latency = th.get('latency_ms')
            if tool:
                # Set status gauge: 1 for ok, 0 for error
                if status:
                    tool_health_status.labels(tool).set(1.0 if status == 'ok' else 0.0)
                # Set latency gauge if available
                if latency is not None:
                    try:
                        tool_latency_ms.labels(tool).set(float(latency))
                    except Exception:
                        pass
    except Exception:
        # Do not fail governance if metrics update fails
        pass

    # Count actions flagged for observability
    try:
        actions_flagged.inc(len([c for c in channels_report if c.get('action')]))
    except Exception:
        pass

    # Conditionally queue safe actions if auto_actions enabled; destructive actions require approval
    auto_actions = bool(cfg.get('auto_actions') or cfg.get('governance', {}).get('auto_actions')) if cfg else False
    if auto_actions:
        try:
            from nova.task_manager import task_manager, TaskType, dummy_task
            for ch in scored_channels:
                if ch.flag == 'promote':
                    await task_manager.enqueue(TaskType.GENERATE_CONTENT, dummy_task, duration=0)
                # do not auto-enqueue retire tasks; require human-in-the-loop
        except Exception as exc:
            import logging
            logging.getLogger('governance').warning('Failed to enqueue follow-up tasks: %s', exc)

    # write report to configured output directory
    out_dir = pathlib.Path(cfg['output_dir'])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f'governance_report_{datetime.utcnow().date()}.json'
    # time writing/notifications with governance_loop_duration
    try:
        with governance_loop_duration.time():
            out_file.write_text(json.dumps(report, indent=2))
            # Send notifications to operators via Slack and email if configured
            await _dispatch_notifications(cfg, report)
    except Exception:
        # Fallback if prometheus Summary context manager fails
        out_file.write_text(json.dumps(report, indent=2))
        await _dispatch_notifications(cfg, report)

    return report


# -----------------------------------------------------------------------------
# Notification helpers
#
# These helpers send summary alerts to a Slack channel and email address
# specified in the governance configuration. They are implemented outside of
# the run() function to keep the core governance logic clean. If the
# environment variables required for sending notifications are not present
# (e.g. SLACK_WEBHOOK_URL), the functions will log a warning and
# gracefully return without raising an exception.

import os
import logging
import httpx
import smtplib
from email.message import EmailMessage

log = logging.getLogger("governance_notifications")

async def _dispatch_notifications(cfg: dict, report: dict) -> None:
    """Dispatch Slack and email notifications summarising governance results.

    Args:
        cfg: The governance configuration dict.
        report: The full governance report generated by `run()`.
    """
    notify_cfg = cfg.get('notify', {}) if cfg else {}
    slack_channel = notify_cfg.get('slack_channel')
    email_addr = notify_cfg.get('email')
    # Prepare summary lines for flagged channels and tool statuses. Include
    # problematic tools in the summary to alert operators when a service is
    # down or underperforming.
    flagged = [c for c in report.get('channels', []) if c.get('flag')]
    if not flagged:
        channels_summary = "No channels flagged for retire or promote."
    else:
        parts = []
        for ch in flagged:
            parts.append(f"{ch['channel_id']} ({ch['flag']} score {ch['score']})")
        channels_summary = ", ".join(parts)
    # Identify tools with a non‑ok status or low score
    tools_info = report.get('tools', []) or []
    failing_tools = []
    for t in tools_info:
        # t may be a dict with keys: tool, status, latency_ms, score
        try:
            tool_name = t.get('tool')
            status = t.get('status')
            score = t.get('score')
            if status and status != 'ok':
                failing_tools.append(f"{tool_name} ({status})")
            # treat low score as potential issue (<50)
            elif score is not None and score < 50:
                failing_tools.append(f"{tool_name} (score {score})")
        except Exception:
            continue
    if failing_tools:
        tools_summary = ", ".join(failing_tools)
    else:
        tools_summary = None

    # Slack notification
    if slack_channel:
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if webhook_url:
            # Build message lines
            lines = [f"Nova Agent Governance Report {report['timestamp']}"]
            lines.append(f"Channels: {channels_summary}")
            if tools_summary:
                lines.append(f"Tools: {tools_summary}")
            payload = {
                'channel': slack_channel,
                'text': "\n".join(lines),
            }
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    await client.post(webhook_url, json=payload)
            except Exception as e:
                log.warning("Failed to send Slack notification: %s", e)
        else:
            log.warning("SLACK_WEBHOOK_URL environment variable not set; skipping Slack notification")

    # Email notification
    if email_addr:
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        if smtp_server and smtp_user and smtp_password:
            msg = EmailMessage()
            msg['Subject'] = f"Nova Agent Governance Report {report['timestamp']}"
            msg['From'] = smtp_user
            msg['To'] = email_addr
            body_lines = ["Governance report summary:"]
            body_lines.append(f"Channels: {channels_summary}")
            if tools_summary:
                body_lines.append(f"Tools: {tools_summary}")
            body_lines.append("\nFull report attached as JSON.")
            msg.set_content("\n".join(body_lines))
            # attach JSON report as text file
            msg.add_attachment(json.dumps(report, indent=2), filename='governance_report.json', subtype='json')
            try:
                with smtplib.SMTP(smtp_server) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            except Exception as e:
                log.warning("Failed to send email notification: %s", e)
        else:
            log.warning("SMTP environment variables missing; skipping email notification")
