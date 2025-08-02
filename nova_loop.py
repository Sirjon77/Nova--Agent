from launch_ready import launch_setup
launch_setup()

import time
import smtplib
import asyncio
from email.message import EmailMessage

from nova_bootloader import load_nova_directive
from nova_selftest import run_nova_selftest

from agents.promptgen import generate_prompt_variants
from agents.rpmwatcher import check_rpm_drops
from agents.avatarops import adjust_avatars

from monetization_router import route_monetization
from rpm_heatmap import generate_rpm_heatmap
from funnel_tracker import track_funnel
from tag_score_engine import tag_and_score
from retargeting_optimizer import optimize_cta

# Autonomous Research System
from nova.autonomous_research import run_autonomous_research
from nova.research_dashboard import get_research_summary

from notion_sync import sync_to_notion
from sheets_export import export_to_google_sheet
from metricool_post import schedule_post_metricool
from convertkit_push import push_to_convertkit
from gumroad_sync import log_sale_to_gumroad

EMAIL_SENDER = "jonathanstuart2177@gmail.com"
EMAIL_PASSWORD = "your_app_password_here"  # Use a Gmail App Password
EMAIL_RECEIVER = "jonathanstuart2177@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email_log(subject, body):
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

def run_nova_loop():
    report = []

    report.append("🔁 [Nova] Booting...")
    report.append(load_nova_directive())
    report.append(run_nova_selftest())

    report.append("\n🧠 Running Intelligence Agents...")
    generate_prompt_variants()
    check_rpm_drops()
    adjust_avatars()

    report.append("\n💰 Running Monetization Modules...")
    generate_rpm_heatmap()
    optimize_cta()

    report.append("\n🔬 Running Autonomous Research...")
    try:
        # Run autonomous research cycle
        research_result = asyncio.run(run_autonomous_research())
        if research_result and "error" not in research_result:
            report.append(f"✅ Research cycle completed: {research_result.get('experiments_completed', 0)} experiments")
            
            # Get research summary
            research_summary = get_research_summary()
            if research_summary and "error" not in research_summary:
                success_rate = research_summary.get("success_rate", 0)
                avg_improvement = research_summary.get("average_improvement", 0)
                report.append(f"📊 Research stats: {success_rate:.1f}% success rate, {avg_improvement:.1f}% avg improvement")
        else:
            report.append(f"❌ Research cycle failed: {research_result.get('error', 'Unknown error')}")
    except Exception as e:
        report.append(f"❌ Research error: {str(e)}")

    report.append("\n🔗 Syncing with External Platforms...")
    try:
        sync_to_notion("notion-db-id", {"Name": {"title": [{"text": {"content": "Nova Sync"}}]}}, "notion-token")
        export_to_google_sheet("Nova Sheet", [["PromptID", "RPM", "Retention"]])
        schedule_post_metricool("metricool-api-key", "account-id", "Scheduled Content", "2025-07-01T10:00:00Z")
        push_to_convertkit("convertkit-api-key", "form-id", "user@example.com")
        log_sale_to_gumroad("gumroad-token", "product-id")
    except Exception as e:
        report.append(f"❌ Integration error: {str(e)}")

    report.append("\n✅ Nova Cycle Complete — Sleeping for 4 hours...")

    send_email_log("✅ Nova Agent Cycle Complete", "\n".join(report))
    time.sleep(4 * 60 * 60)

if __name__ == "__main__":
    while True:
        run_nova_loop()

# === Auto-run Weaviate Memory Sync ===
try:
    from weaviate_memory_sync import embed_memory_to_weaviate
    embed_memory_to_weaviate("nova_memory_log_test.json")
except Exception as e:
    print("⚠️ Memory sync failed:", e)
# === End Auto-sync ===


import os
from agent_spawner import AgentSpawner

def simulate_agent_spawn_if_enabled():
    if os.getenv("ENABLE_SIMULATION", "false").lower() == "true":
        from datetime import datetime
        current_hour = datetime.utcnow().hour
        if current_hour % 12 == 0:
            spawner = AgentSpawner()
            spawner.spawn_agent(
                role_description="RPM Diagnostic Simulator",
                tools=[],
                goal="Analyze engagement drops in simulated avatar"
            )
simulate_agent_spawn_if_enabled()


# In your nova_loop.py
from prompt_web_hook import process_prompt_for_crawl

def handle_loop():
    test_prompts = ["Check this: https://en.wikipedia.org/wiki/Artificial_intelligence"]
    for prompt in test_prompts:
        crawl_data = process_prompt_for_crawl(prompt)
        if crawl_data:
            print("[Loop] Deep web results found.")


# Autonomous Crawler Trigger Logic (Nova Activated)
import re
from prompt_web_hook import process_prompt_for_crawl

AUTO_CRAWL_ENABLED = True  # Can be overridden by .env in real deployment

def detect_urls(text):
    return re.findall(r'https?://\S+', text)

def autonomous_web_crawl(memory_prompts):
    if not AUTO_CRAWL_ENABLED:
        print("[Nova] Autonomous crawling is disabled.")
        return []
    for prompt in memory_prompts:
        urls = detect_urls(prompt)
        for url in urls:
            print(f"[Nova] Auto-crawling detected URL: {url}")
            result = process_prompt_for_crawl(url)
            if result:
                print(f"[Nova] Crawled and processed {len(result)} pages.")

# Run Crawl Test Suite on Startup
from crawl_test_runner import run_crawl_test_suite

if AUTO_CRAWL_ENABLED:
    print("[Nova] Running web crawl test suite...")
    logs = run_crawl_test_suite()
    with open("startup_crawl_log.json", "w") as log_file:
        import json
        json.dump(logs, log_file)

# After autonomous crawl logic
from summarizer_and_memory import summarize_text, store_summary_to_memory
if AUTO_CRAWL_ENABLED and 'result' in locals():
    for entry in result:
        summary = summarize_text(entry['text'])
        store_summary_to_memory(entry['url'], summary)

# Optional: Auto-reflection trigger
from reflection_loop import reflect_on_memory

try:
    reflect_on_memory()
except Exception as e:
    print(f"[Reflect] Skipped due to error: {e}")

# Simulate A/B test prompt use and monetization funnel trigger
from prompt_ab_test import PromptABTest
from funnel_log import log_monetization_event

ab = PromptABTest()
ab.create_test("welcome_prompt", ["Welcome to Nova!", "Start your AI journey now."])
selected = ab.run_test("welcome_prompt")
print(f"[A/B Test] Served prompt: {selected}")

log_monetization_event(source="welcome_prompt", revenue=0.12, event_type="click")

# Tag current prompt version to log
prompt_version = 'v2'
print(f"[Nova Loop] Operating under prompt version: {prompt_version}")

# Log active prompt version
prompt_version = "v2"
print(f"[Nova Loop] Operating under prompt version: {prompt_version}")
with open("loop_meta_log.json", "a") as meta_log:
    import json
    meta_log.write(json.dumps({"timestamp": __import__('datetime').datetime.utcnow().isoformat(), "prompt_version": prompt_version}) + "\n")


# Injected: Scheduled Trend Parsing + RPM Matching
import datetime
from backend.research.trend_merger import match_trends_to_prompts

def run_daily_trend_merge():
    today = datetime.date.today().isoformat()
    try:
        matches = match_trends_to_prompts(
            trend_data_path=f"research_insights/fitfuel/gwi_fitness_latam_{today}.json",
            rpm_log_path="ab_test_log.json"
        )
        with open("matched_trends_to_rpm.json", "w") as f_out:
            json.dump(matches, f_out, indent=2)
    except Exception as e:
        print("Trend merge failed:", e)

# Trigger daily at 5AM in heartbeat loop
if datetime.datetime.now().hour == 5:
    run_daily_trend_merge()


# --- Injected: Recurring Health Check on Boot + Post Loop ---
from backend.diagnostics.loop_health_checker import run_loop_health_check

# Run once on boot
run_loop_health_check(stage='boot')

# Run again at end of each loop cycle
def end_of_loop_hook():
    run_loop_health_check(stage='post-loop')


# === Cron Trigger: Daily Memory Export to S3 or GDrive ===
import datetime, os
from memory_export_to_s3 import export_logs_to_s3

def try_export_memory():
    current_hour = datetime.datetime.now().hour
    if current_hour == 18:  # 6PM export
        bucket = os.getenv("S3_BUCKET")
        key = os.getenv("S3_ACCESS_KEY")
        secret = os.getenv("S3_SECRET_KEY")
        if bucket and key and secret:
            export_logs_to_s3(bucket, key, secret)
        else:
            try:
                from memory_export_to_drive import export_logs_to_gdrive
                export_logs_to_gdrive()
            except:
                print("No valid cloud export target configured.")

try_export_memory()



# === Nova v2.5 Evolution Modules ===
from avatar_reasoner import reason_avatar_behavior
from api_guardian import monitor_api_response
from crew_coordinator import delegate_task
from revenue_dashboard import get_revenue_summary
from post_analytics_collector import collect_analytics

def run_evolution_modules():
    print("[Nova v2.5] Running avatar reasoning...")
    print(reason_avatar_behavior({'name': 'NovaBot'}))

    print("[Nova v2.5] Monitoring API response...")
    result = monitor_api_response(type('obj', (object,), {'status_code': 500})())
    print(f"API Guardian result: {result}")

    print("[Nova v2.5] Delegating task to sub-agent...")
    print(delegate_task('agent_001', 'Post to TikTok'))

    print("[Nova v2.5] Collecting revenue data...")
    print(get_revenue_summary())

    print("[Nova v2.5] Pulling post analytics...")
    print(collect_analytics('YouTube', 'abc123'))

# Inject into loop (you can call run_evolution_modules inside your actual loop logic)
if __name__ == "__main__":
    print("[Nova] Starting loop...")
    run_evolution_modules()


# === Nova Diagnostic Logger Hook ===
import json, os
from datetime import datetime

def log_diagnostic(message):
    log_entry = {"timestamp": datetime.now().isoformat(), "message": message}
    diag_file = os.path.join("diagnostics", "loop_health_report.json")
    os.makedirs(os.path.dirname(diag_file), exist_ok=True)
    try:
        if os.path.exists(diag_file):
            with open(diag_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"logs": []}
        data["logs"].append(log_entry)
        with open(diag_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error writing diagnostic log: {e}")

# Log start of loop for visibility
log_diagnostic("Heartbeat loop triggered")


# === Nova v2.6 Neural Crew Logic ===
from crew_brain import crew_brain_loop
from crew_agent import run_agent_role
from crew_voter import vote_on_strategy
from analytics_model import predict_engagement
from roi_mapper import map_post_to_roi
from time_slot_predictor import get_best_post_time
from loop_intelligence_core import analyze_last_loop
from crew_memory_reflector import record_crew_memory

def run_neural_crew():
    crew_brain_loop()
    print(run_agent_role('strategist', 'optimize RPM'))
    print(f"Strategy vote result: {vote_on_strategy(['Boost Morning', 'Evening Prime'])}")
    print(f"Engagement prediction: {predict_engagement('post_abc')}")
    print(f"ROI mapping: {map_post_to_roi('post_abc')}")
    print(f"Best time to post on TikTok: {get_best_post_time('TikTok')}")
    print(analyze_last_loop('Previous log sample'))
    record_crew_memory('Neural loop cycle completed')

# Call inside main loop
run_neural_crew()

# --- MODEL ROTATION START ---
from utils.model_router import (
    get_active_model_config,
    set_active_model,
    detect_model_switch_command,
    detect_task_based_model
)

def route_model_from_message(message):
    override = detect_model_switch_command(message)
    if override:
        set_active_model(override)
        print(f"[Nova Agent] Model manually set to: {override}")
    else:
        suggested = detect_task_based_model(message)
        if suggested:
            set_active_model(suggested)
            print(f"[Nova Agent] Model auto-selected: {suggested}")
    return get_active_model_config()
# --- MODEL ROTATION END ---
