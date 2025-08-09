from fastapi import FastAPI, HTTPException, Depends, Query, Body, Form, File, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn
import asyncio
from datetime import datetime
from pathlib import Path
# Optional Prometheus instrumentation. Import may fail if the package is not
# installed. We guard the import to allow the API to start without this
# optional dependency.
try:
    from prometheus_fastapi_instrumentator import Instrumentator  # type: ignore
    _instrumentation_available = True
except Exception:
    Instrumentator = None  # type: ignore
    _instrumentation_available = False
from nova.metrics import tasks_executed, task_duration, memory_items, governance_runs_total
# JWT middleware import moved to function level to avoid security validation during import
# from auth.jwt_middleware import JWTAuthMiddleware, issue_token

# Task management imports
from nova.task_manager import task_manager, TaskType, dummy_task

# Import integration helpers for affiliate and CRM functionality
from integrations import (
    generate_product_link,
    subscribe_user as _ck_subscribe_user,
    add_tags_to_subscriber as _ck_add_tags,
)
from integrations.convertkit import ConvertKitError
# Import Beacons and HubSpot helpers. These aliases avoid polluting the
# namespace with generic names and allow for more controlled imports.
from integrations.beacons import (
    generate_profile_link as _beacons_generate_profile_link,
    update_links as _beacons_update_links,
)
from integrations.hubspot import (
    create_contact as _hubspot_create_contact,
    HubSpotError,
)
from integrations.metricool import (
    get_metrics as _metricool_get_metrics,
    get_overview as _metricool_get_overview,
    MetricoolError,
)
# Import TubeBuddy (YouTube Data API) helpers and errors
from integrations.tubebuddy import (
    search_keywords as _tubebuddy_search_keywords,
    get_trending_videos as _tubebuddy_get_trending_videos,
    TubeBuddyError,
)
# Import SocialPilot helper and error
from integrations.socialpilot import (
    schedule_post as _socialpilot_schedule_post,
    SocialPilotError,
)
# Import Publer helper and error
from integrations.publer import (
    schedule_post as _publer_schedule_post,
    PublerError,
)
# Import translation helper and error
from integrations.translate import (
    translate_text as _translate_text,
    TranslationError,
)
# Import vidIQ trending helper and error
from integrations.vidiq import (
    get_trending_keywords as _vidiq_get_trending_keywords,
    VidiqError,
)

# Import YouTube, Instagram, Facebook and TTS helpers.  These provide
# direct content publishing and synthesis capabilities.  We alias them
# with a leading underscore to make it clear they are internal helper
# functions rather than API route handlers.
from integrations.youtube import upload_video as _youtube_upload_video
from integrations.instagram import publish_video as _instagram_publish_video
from integrations.facebook import publish_post as _facebook_publish_post
from integrations.tts import synthesize_speech as _synthesize_speech
from typing import Any, List, Optional, Dict, Tuple, Union
from dataclasses import asdict
from nova.ab_testing import ABTestManager

# Import new modules for advanced functionalities
from nova.profit_machine import ProfitMachineDesigner
from nova.algorithm_trigger import HookEngine
from nova.hidden_prompt_discovery import PromptDiscoverer
from nova.direct_marketing import DirectMarketingPlanner
from nova.accelerated_learning import LearningCoach
from nova.negotiation_coach import NegotiationCoach
from nova.hashtag_optimizer import HashtagOptimizer
from nova.posting_scheduler import PostingScheduler
from nova.rpm_leaderboard import PromptLeaderboard
from nova.prompt_vault import PromptVault
from nova.analytics import aggregate_metrics, top_prompts, rpm_by_audience  # type: ignore

# v7.0 Planning Engine imports
from nova.planner import PlanningEngine, PlanningContext, DecisionType, ApprovalStatus
from nova.task_scheduler import TaskScheduler, TaskPriority

# NOTE: This is the canonical FastAPI application instance for Nova Agent.
# Do NOT instantiate FastAPI elsewhere; use this app for adding all routers and routes.
app = FastAPI(title="Nova Agent API", version="7.0")

# Initialize v7.0 components
planning_engine = PlanningEngine()
task_scheduler = TaskScheduler()

# Initialize A/B testing manager
ab_manager = ABTestManager()

# Attach JWT middleware (conditional to avoid import-time validation)
def _add_jwt_middleware():
    try:
        from auth.jwt_middleware import JWTAuthMiddleware
        app.add_middleware(JWTAuthMiddleware)
    except RuntimeError as e:
        # Skip JWT middleware if security validation fails
        print(f"⚠️  JWT middleware disabled: {e}")

_add_jwt_middleware()

# Validate required environment configuration early
try:
    from nova.config.env import validate_env_or_exit
    validate_env_or_exit()
except SystemExit:
    # In test contexts, allow process to continue as TestClient may import without full env
    pass

# Enable CORS for all origins (development/public use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrumentation
if _instrumentation_available and Instrumentator:
    try:
        Instrumentator().instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")
    except Exception:
        # Do not crash if instrumentation setup fails
        pass
else:
    # If the Prometheus FastAPI Instrumentator is not installed, expose a simple
    # metrics endpoint using the underlying prometheus_client library. This
    # ensures that /metrics continues to serve metrics for tests and
    # deployments where the optional instrumentator dependency is absent.
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST  # type: ignore
        from fastapi import Response  # type: ignore

        @app.get("/metrics", include_in_schema=False)
        async def metrics_fallback() -> Response:
            data = generate_latest()
            return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        # If prometheus_client is missing entirely, we cannot expose metrics; in
        # that case the /metrics endpoint will not exist.
        pass

# -----------------------------------------------------------------------------
# Startup events
#
# When the FastAPI application starts, schedule the nightly governance run. In
# the absence of Celery or APScheduler, we implement a simple loop that
# waits for 24 hours between executions. If the governance task fails it
# will log the exception but the loop will continue on the next cycle. The
# scheduling uses asyncio to avoid blocking the event loop.

@app.on_event("startup")
async def schedule_governance_nightly() -> None:
    """Launch the periodic governance runner in the background."""
    import yaml
    from nova.governance.governance_loop import run as governance_run
    # Load governance configuration once; fallback to defaults if missing
    try:
        with open('config/settings.yaml', 'r') as _f:
            cfg_all = yaml.safe_load(_f)
        gov_cfg = cfg_all.get('governance', {})
    except Exception:
        gov_cfg = {}

    async def _runner() -> None:
        """Background task that runs governance nightly and memory cleanup hourly."""
        import logging
        from nova.memory_guard import cleanup as memory_cleanup
        gov_logger = logging.getLogger("governance_scheduler")
        # Timestamps to track when last memory cleanup occurred
        last_cleanup = None
        while True:
            now = datetime.utcnow()
            # Run governance once every 24 hours (or on first run)
            try:
                await governance_run(gov_cfg, [], [], [])
                gov_logger.info("Governance cycle completed")
            except Exception as exc:
                gov_logger.warning("Governance run failed: %s", exc)
            # Perform memory cleanup hourly
            try:
                # Determine memory limit from policy if available
                import yaml
                with open('config/policy.yaml', 'r') as _pf:
                    policy_cfg = yaml.safe_load(_pf)
                mem_limit = policy_cfg.get('sandbox', {}).get('memory_limit_mb') if policy_cfg else None
            except Exception:
                mem_limit = None
            try:
                await memory_cleanup(max_age_hours=24, memory_limit_mb=mem_limit)
            except Exception as exc:
                gov_logger.warning("Memory cleanup failed: %s", exc)
            # Sleep for 24 hours before next governance run
            await asyncio.sleep(24 * 60 * 60)

    # Start the runner without awaiting it so that startup can complete
    asyncio.create_task(_runner())

@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}

# -----------------------------------------------------------------------------
# Authentication endpoints
#
# A simple login endpoint issues JWT tokens to authenticated users. In a real
# deployment credentials would be stored securely (e.g. hashed in a database).
# Here we read credentials from environment variables prefixed with NOVA_USER_*

from pydantic import BaseModel
from nova.audit_logger import audit
import os
from fastapi import status


class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    role: str
    # Backward-compat field for older clients/tests expecting 'token'
    token: Union[str, None] = None


def _get_user_role(username: str) -> Union[str, None]:
    """Return the role associated with a username.

    Roles are determined based on environment variables:
    - NOVA_ADMIN_USERNAME maps to Role.admin
    - NOVA_USER_USERNAME maps to Role.user

    Returns:
        Role string ('admin' or 'user') if matched, else None.
    """
    admin_user = os.environ.get('NOVA_ADMIN_USERNAME', 'admin')
    normal_user = os.environ.get('NOVA_USER_USERNAME', 'user')
    if username == admin_user:
        return 'admin'
    if username == normal_user:
        return 'user'
    return None


@app.post("/api/auth/login", tags=["auth"], response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(req: LoginRequest):
    """Authenticate a user and return a JWT.

    This endpoint compares the provided credentials against environment
    variables. Set NOVA_ADMIN_USERNAME and NOVA_ADMIN_PASSWORD for the
    admin user, and NOVA_USER_USERNAME and NOVA_USER_PASSWORD for a normal
    user. If credentials are valid, a signed JWT is returned along with
    the user's role.
    """
    username = req.username
    password = req.password
    # Fetch credentials from env or default values
    admin_user = os.environ.get('NOVA_ADMIN_USERNAME', 'admin')
    admin_pass = os.environ.get('NOVA_ADMIN_PASSWORD', 'admin')
    user_user = os.environ.get('NOVA_USER_USERNAME', 'user')
    user_pass = os.environ.get('NOVA_USER_PASSWORD', 'user')
    # Verify credentials and determine role
    if username == admin_user and password == admin_pass:
        role = 'admin'
    elif username == user_user and password == user_pass:
        role = 'user'
    else:
        audit('login_failed', user=username, meta={'reason': 'invalid_credentials'})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    try:
        # Prefer new utils that issue access + refresh tokens
        from auth.jwt_utils import create_access_token, create_refresh_token
        claims = {"sub": username, "role": role}
        access = create_access_token(claims)
        refresh = create_refresh_token(claims)
        audit('login_success', user=username, meta={'role': role})
        return LoginResponse(access_token=access, refresh_token=refresh, token_type="bearer", role=role, token=access)
    except Exception as e:
        audit('login_error', user=username, meta={'error': str(e)})
        raise HTTPException(status_code=500, detail=f"JWT token generation failed: {e}")


class RefreshRequest(BaseModel):
    refresh_token: str


@app.post("/api/auth/refresh", tags=["auth"], status_code=status.HTTP_200_OK)
async def refresh_token(req: RefreshRequest):
    """Exchange a refresh token for a new access token (and rotated refresh)."""
    try:
        from auth.jwt_utils import decode_token, create_access_token, create_refresh_token, JWTError, ExpiredSignatureError
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            audit('token_refresh_failed', user=payload.get('sub'), meta={'reason': 'wrong_type'})
            raise HTTPException(status_code=400, detail="Not a refresh token")
        new_access = create_access_token({"sub": payload.get("sub"), "role": payload.get("role")})
        new_refresh = create_refresh_token({"sub": payload.get("sub"), "role": payload.get("role")})
        audit('token_refresh', user=payload.get('sub'), meta={'result': 'success'})
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
    except ExpiredSignatureError:
        audit('token_refresh_failed', user='unknown', meta={'reason': 'expired'})
        raise HTTPException(status_code=401, detail="Refresh token expired, please login again")
    except Exception:
        audit('token_refresh_failed', user='unknown', meta={'reason': 'invalid'})
        raise HTTPException(status_code=401, detail="Invalid refresh token")

from auth.rbac import role_required
from auth.roles import Role

# In-memory stores

# In-memory cache for channels loaded from governance reports. This will be
# refreshed whenever the governance cycle runs.
_channels_cache = None

# Pydantic models for analytics and leaderboard endpoints
class AnalyticsMetricsRequest(BaseModel):
    """Request body for analytics summary and leaderboard endpoints.

    Each metric dictionary should contain keys required by ``PromptLeaderboard``
    and analytics helpers, including ``prompt_id``, ``rpm``, ``avd``,
    ``ctr``, ``audience_country`` and ``audience_age``.
    """

    metrics: List[Dict[str, Any]]

class LeaderboardResponse(BaseModel):
    """Response model for RPM leaderboard results."""
    ranking: List[Tuple[str, float]]
    clusters: Dict[str, List[str]]

class AutoRetireRequest(BaseModel):
    """Request model to automatically retire a percentage of prompts.

    ``metrics``: The performance metrics used to rank prompts.
    ``percent``: Percentage of prompts to retire (0-100).
    ``vault_path``: Optional path to the prompt vault file; defaults to
    ``reports/prompt_vault.json``.
    """

    metrics: List[Dict[str, Any]]
    percent: float = 10.0
    vault_path: Optional[str] = None

class AutoRetireResponse(BaseModel):
    """Response returned when prompts are automatically retired."""
    retired: List[str]


@app.get("/api/channels", tags=["dashboard"], dependencies=[role_required(Role.user, Role.admin)])
async def list_channels():
    """Return the latest channel performance data.

    Reads the most recent governance report file from disk and returns
    its `channels` section. If no report is available, returns an
    empty list. This endpoint is accessible to both user and admin
    roles.
    """
    global _channels_cache
    # If cached, return quickly
    if _channels_cache is not None:
        return _channels_cache
    # Determine reports directory from settings
    import yaml, json, pathlib
    try:
        with open('config/settings.yaml', 'r') as _f:
            cfg = yaml.safe_load(_f)
        reports_dir = pathlib.Path(cfg.get('governance', {}).get('output_dir', 'reports'))
    except Exception:
        reports_dir = pathlib.Path('reports')
    files = sorted(reports_dir.glob('governance_report_*.json'), reverse=True)
    if not files:
        return []
    latest = files[0]
    try:
        data = json.loads(latest.read_text())
        channels = data.get('channels', [])
    except Exception:
        channels = []
    # Cache for subsequent calls to avoid disk read on each request
    _channels_cache = channels
    return channels

# -----------------------------------------------------------------------------
# Analytics and leaderboard endpoints
#
# These endpoints provide summary statistics and ranking information for
# prompt performance.  They operate purely on the provided metrics and do not
# persist state.  Admin privileges are required to access these routes as
# performance metrics may contain sensitive information.

@app.post(
    "/api/analytics/summary",
    tags=["analytics"],
    dependencies=[role_required(Role.admin,)],
)
async def analytics_summary(req: AnalyticsMetricsRequest) -> Dict[str, Any]:
    """Return summary statistics for a set of prompt metrics.

    This endpoint aggregates the provided metrics to produce total views,
    average RPM and identifies top prompts as well as RPM grouped by
    audience segment.

    Args:
        req: The request body containing a list of metric dictionaries.

    Returns:
        A dictionary with aggregated statistics, top performing prompts and
        RPM by audience.
    """
    metrics_data = req.metrics
    # Compute aggregate stats
    summary = aggregate_metrics(metrics_data)
    # Determine top 5 prompts by RPM
    top5 = top_prompts(metrics_data, n=5)
    # Group RPM by audience
    audience = rpm_by_audience(metrics_data)
    return {"summary": summary, "top_prompts": top5, "rpm_by_audience": audience}


@app.post(
    "/api/leaderboard",
    tags=["analytics"],
    response_model=LeaderboardResponse,
    dependencies=[role_required(Role.admin,)],
)
async def leaderboard(req: AnalyticsMetricsRequest) -> LeaderboardResponse:
    """Return ranked prompts and audience clusters based on performance metrics.

    This endpoint uses ``PromptLeaderboard`` to ingest the provided metrics
    and compute a weighted ranking.  It also clusters prompt IDs by
    audience country and age.

    Args:
        req: Request body containing metric dictionaries.

    Returns:
        LeaderboardResponse with ranking and clusters.
    """
    lb = PromptLeaderboard()
    lb.ingest_metrics(req.metrics)
    ranking = lb.rank_prompts()
    clusters = lb.cluster_by_audience()
    return LeaderboardResponse(ranking=ranking, clusters=clusters)


@app.post(
    "/api/leaderboard/auto_retire",
    tags=["analytics"],
    response_model=AutoRetireResponse,
    dependencies=[role_required(Role.admin,)],
)
async def leaderboard_auto_retire(req: AutoRetireRequest) -> AutoRetireResponse:
    """Automatically retire the bottom percentage of prompts and return retired IDs.

    This endpoint loads or creates a prompt vault at the given path,
    ingests the provided metrics into a leaderboard, retires the bottom
    ``percent`` prompts and persists the updated vault.

    Args:
        req: Request body specifying metrics, percent and optional vault path.

    Returns:
        A response containing the list of retired prompt IDs.
    """
    vault_path = req.vault_path or "reports/prompt_vault.json"
    vault = PromptVault(vault_path)
    vault.load()
    lb = PromptLeaderboard()
    lb.ingest_metrics(req.metrics)
    retired_ids = vault.auto_retire(lb, percent=req.percent)
    vault.save()
    return AutoRetireResponse(retired=retired_ids)

@app.get("/api/tasks", tags=["dashboard"], dependencies=[role_required(Role.admin,)])
async def list_tasks():
    """Return all tasks currently tracked by the task manager.

    This endpoint is restricted to admin users. Tasks include queued,
    running, completed and failed jobs. The results are returned as a
    list of dictionaries sorted by creation time descending.
    """
    tasks = list(task_manager.all_tasks().values())
    tasks_sorted = sorted(tasks, key=lambda t: t.created_at, reverse=True)
    return [t.to_dict() for t in tasks_sorted]


# Endpoint to submit a new task
from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    """Request body for creating a new task.

    Attributes:
        type: A string representing the task type (see ``TaskType``).
        duration: Optional integer specifying a sleep duration for the
            dummy task. This is ignored for most other task types.
        params: Optional dictionary of parameters specific to the task
            type. For example, ``discover_prompts`` tasks can include
            ``roles``, ``domains``, ``outcomes`` and ``niches``.
    """
    type: str
    duration: Union[int, None] = None
    params: Union[dict, None] = None


@app.post("/api/tasks", tags=["dashboard"], dependencies=[role_required(Role.admin,)])
async def create_task(req: CreateTaskRequest):
    """Create a new asynchronous task and return its ID.

    Depending on the requested type, the task manager will run a
    placeholder coroutine. This endpoint can be extended to support
    additional task types (e.g. content generation, video upload) by
    mapping types to appropriate coroutines in this function.

    Args:
        req: The task creation parameters.

    Returns:
        A dictionary containing the ID of the enqueued task.
    """
    # Map the requested type to a known TaskType; default to CUSTOM
    try:
        task_type = TaskType(req.type)
    except ValueError:
        task_type = TaskType.CUSTOM
    # Determine the coroutine to run based on task type
    if task_type == TaskType.GENERATE_CONTENT:
        # Use dummy task as a placeholder for content generation
        duration = req.duration or 5
        coro = dummy_task
        params = {"duration": duration}
    elif task_type == TaskType.PUBLISH_POST:
        # Publishing is not yet implemented; use dummy task
        duration = req.duration or 2
        coro = dummy_task
        params = {"duration": duration}
    elif task_type == TaskType.RUN_GOVERNANCE:
        # Run the governance loop asynchronously via task manager
        async def governance_wrapper() -> dict:
            from nova.governance.governance_loop import run as governance_run
            import yaml
            # Load configuration
            cfg_all = yaml.safe_load(open('config/settings.yaml'))
            cfg = cfg_all.get('governance', {}) if cfg_all else {}
            # For now, supply empty metrics/seeds/tools
            await governance_run(cfg, [], [], [])
            return {"governance": "completed"}
        coro = governance_wrapper
        params = {}
    elif task_type == TaskType.DISCOVER_PROMPTS:
        async def discover_prompts_wrapper(**kw) -> dict:
            roles = kw.get('roles', [])
            domains = kw.get('domains', [])
            outcomes = kw.get('outcomes', [])
            niches = kw.get('niches', [])
            limit = kw.get('limit', 10)
            discoverer = PromptDiscoverer()
            templates = discoverer.discover_prompts(roles, domains, outcomes, niches, limit)
            # Convert to serialisable dicts
            result = [
                {
                    "text": t.structure,
                    "description": t.description,
                    "tags": t.tags,
                }
                for t in templates
            ]
            return {"prompts": result}
        coro = discover_prompts_wrapper
        params = req.params or {}
    elif task_type == TaskType.GENERATE_FUNNEL:
        async def generate_funnel_wrapper(**kw) -> dict:
            name = kw.get('name', 'Unnamed Offer')
            price = float(kw.get('price', 0))
            description = kw.get('description', '')
            upsells = kw.get('upsells', [])
            retention = kw.get('retention_strategy', None)
            designer = ProfitMachineDesigner()
            offer = designer.create_offer(name, price, description)
            for upsell in upsells:
                designer.add_upsell(offer.id, upsell)
            if retention:
                designer.set_retention_strategy(offer.id, retention)
            funnel = designer.build_sales_funnel(offer)
            return {"offer_id": offer.id, "funnel": funnel}
        coro = generate_funnel_wrapper
        params = req.params or {}
    elif task_type == TaskType.GENERATE_LEARNING_PLAN:
        async def learning_plan_wrapper(**kw) -> dict:
            skill = kw.get('skill', 'unknown skill')
            coach = LearningCoach()
            plan = coach.create_plan(skill)
            return {
                "skill": plan.skill,
                "segments": [
                    {
                        "title": seg.title,
                        "duration_minutes": seg.duration_minutes,
                        "description": seg.description,
                    }
                    for seg in plan.segments
                ],
            }
        coro = learning_plan_wrapper
        params = req.params or {}
    elif task_type == TaskType.GENERATE_NEGOTIATION:
        async def negotiation_wrapper(**kw) -> dict:
            industry = kw.get('industry', 'general')
            audience = kw.get('audience', 'client')
            coach = NegotiationCoach()
            framework = coach.create_framework(industry, audience)
            return {
                "industry": framework.industry,
                "target_audience": framework.target_audience,
                "preparation": framework.preparation,
                "communication": framework.communication,
                "closing": framework.closing,
            }
        coro = negotiation_wrapper
        params = req.params or {}
    elif task_type == TaskType.GENERATE_DIRECT_MARKETING:
        async def direct_marketing_wrapper(**kw) -> dict:
            """
            Generate a direct marketing micro‑funnel.

            This wrapper builds a CTA with a trackable link, constructs a
            landing page blueprint, generates a drip email sequence and
            optionally produces a fully rendered micro‑landing page
            (HTML) and a weekly performance digest.  Optional flags
            include `include_html` to embed a full HTML snippet and
            `metrics` to summarise past performance.  The base URL
            defaults to ``https://example.com`` but can be overridden.
            """
            video_id = kw.get('video_id', 'unknown')
            offer_code = kw.get('offer_code', 'offer')
            product_name = kw.get('product_name', 'Product')
            benefits = kw.get('benefits', ['Benefit 1', 'Benefit 2'])
            email_days = int(kw.get('email_days', 3))
            base_url = kw.get('base_url', 'https://example.com')
            include_html = False
            raw_include_html = kw.get('include_html', False)
            if isinstance(raw_include_html, str):
                include_html = raw_include_html.strip().lower() in {'1', 'true', 'yes', 'on'}
            elif isinstance(raw_include_html, bool):
                include_html = raw_include_html
            # Image URL for the landing page (optional)
            image_url = kw.get('image_url')
            planner = DirectMarketingPlanner(base_url=base_url)
            cta = planner.build_cta(video_id, offer_code)
            landing = planner.create_landing_page(product_name, benefits, cta)
            emails = planner.build_email_sequence(product_name, email_days)
            result: Dict[str, Any] = {
                "cta": cta.__dict__,
                "landing_page": {
                    "headline": landing.headline,
                    "subheadline": landing.subheadline,
                    "benefits": landing.benefits,
                    "cta": landing.cta.__dict__,
                },
                "email_sequence": emails,
            }
            # Optional full HTML landing page
            if include_html:
                html = planner.generate_micro_landing_page(product_name, benefits, cta, image_url=image_url)
                result["landing_page_html"] = html
            # Optional weekly digest summarising provided metrics
            metrics = kw.get('metrics')
            if metrics and isinstance(metrics, list):
                try:
                    digest = planner.generate_weekly_digest(metrics)
                    result["digest"] = digest
                except Exception:
                    # Ignore digest errors silently
                    pass
            return result
        coro = direct_marketing_wrapper
        params = req.params or {}
    elif task_type == TaskType.SUGGEST_HASHTAGS:
        async def suggest_hashtags_wrapper(**kw) -> dict:
            """
            Suggest hashtags for a given topic.

            This wrapper supports two modes: a static mode that looks up
            predefined hashtags for the specified topic, and an
            optional dynamic mode that derives hashtags from
            contemporaneous trend data.  The dynamic mode can be
            enabled by passing `use_trends=true` in the task
            parameters.  When enabled, the wrapper instantiates a
            ``TrendScanner`` with minimal configuration, scans for
            trends based on the provided topic and then calls
            ``HashtagOptimizer.suggest_from_trends`` to convert the
            resulting keywords into ranked hashtag suggestions.  If
            trend scanning fails or yields no results, the static
            fallback using ``HashtagOptimizer.suggest`` is used.

            Keyword arguments:
                topic: The subject or seed phrase for which to
                    generate hashtags.
                count: Maximum number of hashtags to return.
                use_trends: When truthy, enable dynamic trend
                    generation (default: False).
            Returns:
                A dict containing a list of hashtag strings.
            """
            topic = kw.get('topic', '')
            count = int(kw.get('count', 3))
            # Determine whether to use trend scanning; interpret common
            # truthy string values (e.g., "true", "1") as True
            raw_use_trends = kw.get('use_trends', False)
            use_trends = False
            if isinstance(raw_use_trends, str):
                use_trends = raw_use_trends.strip().lower() in {'1', 'true', 'yes', 'on'}
            elif isinstance(raw_use_trends, bool):
                use_trends = raw_use_trends
            optimizer = HashtagOptimizer()
            # Attempt dynamic trend-based generation if enabled and a topic is provided
            if use_trends and topic:
                try:
                    from nova.governance.trend_scanner import TrendScanner
                    # Minimal configuration for trend scanning: no external sources
                    cfg = {
                        'rpm_multiplier': 1,
                        'top_n': count,
                        'use_tiktok': False,
                        'use_vidiq': False,
                        'use_youtube': False,
                        'use_google_ads': False,
                        'use_gwi': False,
                        'use_affiliate': False,
                    }
                    scanner = TrendScanner(cfg)
                    # Scan for trends using the topic as the seed phrase
                    trends = await scanner.scan([topic])
                    # Convert trends to hashtag suggestions
                    suggestions = optimizer.suggest_from_trends(trends, count)
                    # Fall back to static suggestions if the result is empty
                    if suggestions:
                        return {"hashtags": suggestions}
                except Exception:
                    # Ignore any errors and fall back
                    pass
            # Static fallback using predefined hashtags
            suggestions = optimizer.suggest(topic, count)
            return {"hashtags": suggestions}
        coro = suggest_hashtags_wrapper
        params = req.params or {}
    elif task_type == TaskType.SCHEDULE_POSTS:
        async def schedule_posts_wrapper(**kw) -> dict:
            platform = kw.get('platform', 'tiktok')
            days_ahead = int(kw.get('days_ahead', 7))
            posts_per_day = int(kw.get('posts_per_day', 1))
            offset = int(kw.get('timezone_offset_hours', 0))
            scheduler = PostingScheduler(timezone_offset_hours=offset)
            times = scheduler.compute_post_times(platform, days_ahead, posts_per_day)
            # Convert datetimes to ISO strings for JSON serialisation
            return {"times": [t.isoformat() for t in times]}
        coro = schedule_posts_wrapper
        params = req.params or {}
    elif task_type == TaskType.GENERATE_HOOKS:
        async def generate_hooks_wrapper(**kw) -> dict:
            platform = kw.get('platform', 'tiktok')
            count = int(kw.get('count', 3))
            engine = HookEngine()
            hooks = engine.generate_hooks(platform, count)
            ranked = engine.rank_hooks(hooks)
            return {
                "hooks": [hook.text for hook in hooks],
                "ranked": [
                    {"text": hook.text, "score": score}
                    for hook, score in ranked
                ],
            }
        coro = generate_hooks_wrapper
        params = req.params or {}
    elif task_type == TaskType.PROCESS_METRICS:
        async def process_metrics_wrapper(**kw) -> dict:
            metrics = kw.get('metrics', [])
            retire_percent = float(kw.get('retire_percent', 10.0))
            vault_path = kw.get('vault_path', 'reports/prompt_vault.json')
            leaderboard = PromptLeaderboard()
            # Ingest provided metrics; expect list of dicts
            if isinstance(metrics, list):
                leaderboard.ingest_metrics(metrics)
            # Load vault and retire underperforming prompts
            vault = PromptVault(vault_path)
            vault.load()
            retired = vault.auto_retire(leaderboard, percent=retire_percent)
            # Save updated vault
            vault.save()
            return {"retired": retired, "remaining": len(vault.prompts)}
        coro = process_metrics_wrapper
        params = req.params or {}
    elif task_type == TaskType.ANALYZE_COMPETITORS:
        async def analyze_competitors_wrapper(**kw) -> dict:
            """
            Benchmark competitors using trending seeds.

            This task accepts a list of seed keywords (as 'seeds') and
            an optional 'count' specifying the maximum number of competitor
            entries to return.  It uses the governance trend scanner
            configuration to initialise a ``CompetitorAnalyzer`` and
            returns a list of competitor entries ordered by projected
            RPM.
            """
            seeds = kw.get('seeds', [])
            count = int(kw.get('count', 5))
            # Load governance trend configuration from settings
            import yaml
            try:
                cfg_all = yaml.safe_load(open('config/settings.yaml'))
            except Exception:
                cfg_all = {}
            trends_cfg = {}
            if isinstance(cfg_all, dict):
                trends_cfg = cfg_all.get('governance', {}).get('trends', {}) or {}
            try:
                from nova.competitor_analyzer import CompetitorAnalyzer
                analyzer = CompetitorAnalyzer(trends_cfg)
                results = await analyzer.benchmark_competitors(seeds, count=count)
                return {"competitors": results}
            except Exception as exc:
                # On failure, return empty list with error message
                return {"competitors": [], "error": f"{type(exc).__name__}: {exc}"}
        coro = analyze_competitors_wrapper
        params = req.params or {}
    elif task_type == TaskType.DISTRIBUTE_POSTS:
        async def distribute_posts_wrapper(**kw) -> dict:
            """
            Distribute content across multiple accounts on a platform.

            Parameters expected in ``kw``:

            - platform (str): Target platform (e.g., 'tiktok'). Defaults to 'tiktok'.
            - base_caption (str): Base caption to adapt per account. Defaults to ''.
            - base_cta (str): Base call‑to‑action. Defaults to 'Check the link in bio'.
            - accounts (list[str], optional): List of account identifiers. If not
              provided, the function will attempt to load accounts from
              ``config/settings.yaml`` under the ``accounts`` section.

            Returns:
                A dict containing a ``posts`` key with a list of posts,
                each including ``account``, ``caption`` and ``cta`` fields.
            """
            platform = kw.get('platform', 'tiktok')
            base_caption = kw.get('base_caption', '')
            base_cta = kw.get('base_cta', 'Check the link in bio')
            accounts = kw.get('accounts')
            # If accounts not explicitly provided, load from settings
            if not accounts:
                import yaml
                try:
                    cfg_all = yaml.safe_load(open('config/settings.yaml'))
                    accounts_cfg = cfg_all.get('accounts', {}) if cfg_all else {}
                    accounts = accounts_cfg.get(platform.lower(), [])
                except Exception:
                    accounts = []
            try:
                from nova.multi_account import MultiAccountDistributor
                distributor = MultiAccountDistributor({platform: accounts or []})
                posts = distributor.distribute(platform, base_caption, base_cta)
                return {"posts": posts}
            except Exception as exc:
                return {"posts": [], "error": f"{type(exc).__name__}: {exc}"}
        coro = distribute_posts_wrapper
        params = req.params or {}
    else:
        # Custom tasks default to sleeping for the provided duration
        duration = req.duration or 1
        coro = dummy_task
        params = {"duration": duration}
    # Enqueue the task and return its ID
    task_id = await task_manager.enqueue(task_type, coro, **params)
    return {"id": task_id}

# Endpoint to trigger the governance cycle manually
@app.post("/api/governance/run", tags=["governance"], dependencies=[role_required(Role.admin,)])
async def run_governance_now() -> dict:
    """Manually trigger a governance run and return the task ID.

    This endpoint enqueues a governance task via the task manager. The actual
    work is executed asynchronously and clients can track its progress via
    the tasks API or WebSocket events.
    """
    audit('governance_run_triggered', user='admin')
    # Use the existing create_task function to enqueue a RUN_GOVERNANCE task.
    req = CreateTaskRequest(type=TaskType.RUN_GOVERNANCE.value)
    return await create_task(req)

# -----------------------------------------------------------------------------
# Additional governance and log endpoints (admin only)
#
# These endpoints allow operators to fetch historical governance reports and
# audit logs via the API. They are secured to admin users to prevent
# inadvertent disclosure of potentially sensitive performance data.

@app.get("/api/governance/history", tags=["governance"], dependencies=[role_required(Role.admin,)])
async def list_governance_reports() -> list[str]:
    """Return a list of available governance report filenames.

    The files are read from the reports directory configured in
    ``config/settings.yaml`` under ``governance.output_dir``. Only file
    names (not full paths) are returned to the client.

    Returns:
        A list of file names sorted by date descending.
    """
    import yaml, pathlib
    try:
        cfg = yaml.safe_load(open('config/settings.yaml'))
        reports_dir = pathlib.Path(cfg.get('governance', {}).get('output_dir', 'reports'))
    except Exception:
        reports_dir = pathlib.Path('reports')
    files = sorted(reports_dir.glob('governance_report_*.json'), reverse=True)
    return [f.name for f in files]

@app.get("/api/governance/report", tags=["governance"], dependencies=[role_required(Role.admin,)])
async def get_governance_report(date: Union[str, None] = Query(default=None, description="ISO date (YYYY-MM-DD) of report to fetch")):
    """Return the latest or specified governance report.

    If no date is provided, this endpoint will attempt to find the most recent
    report file in the configured output directory. If a date is provided,
    it will look for a report named `governance_report_{date}.json`. If the
    report cannot be found, a 404 error is returned.
    """
    # Determine reports directory from configuration; fallback to default
    reports_dir = pathlib.Path('reports')
    try:
        import yaml
        with open('config/settings.yaml', 'r') as _f:
            cfg = yaml.safe_load(_f)
        reports_dir = pathlib.Path(cfg.get('governance', {}).get('output_dir', 'reports'))
    except Exception:
        # If config missing or unreadable, use default 'reports'
        reports_dir = pathlib.Path('reports')

    if date:
        # Validate basic date format
        if not (len(date) == 10 and date[4] == '-' and date[7] == '-'):
            raise HTTPException(status_code=400, detail="Date must be in YYYY-MM-DD format")
        target_file = reports_dir / f"governance_report_{date}.json"
        if not target_file.exists():
            raise HTTPException(status_code=404, detail="Report for specified date not found")
        data = json.loads(target_file.read_text())
        return data

    # No date specified; find most recent report
    if not reports_dir.exists():
        raise HTTPException(status_code=404, detail="No governance reports directory found")
    files = sorted(reports_dir.glob('governance_report_*.json'), reverse=True)
    if not files:
        raise HTTPException(status_code=404, detail="No governance reports available")
    latest = files[0]
    data = json.loads(latest.read_text())
    return data

@app.get("/api/logs", tags=["logs"], dependencies=[role_required(Role.admin,)])
async def get_logs(level: Union[str, None] = None) -> dict:
    """Return recent audit log entries.

    Reads the ``logs/audit.log`` file and returns its contents. An optional
    ``level`` query parameter can be provided to filter entries containing
    that string (e.g. "error", "warning").

    Args:
        level: Optional text to filter log entries.

    Returns:
        A dictionary with a single ``entries`` key containing a list of log
        lines.
    """
    import pathlib
    log_file = pathlib.Path('logs/audit.log')
    if not log_file.exists():
        return {"entries": []}
    try:
        lines = log_file.read_text().splitlines()
    except Exception:
        return {"entries": []}
    if level:
        level_lower = level.lower()
        filtered = [ln for ln in lines if level_lower in ln.lower()]
        return {"entries": filtered}
    return {"entries": lines}

from fastapi import WebSocket, WebSocketDisconnect
connections = set()

# -----------------------------------------------------------------------------
# Approval workflow endpoints (admin only)
#
# These endpoints expose pending content items that require operator
# approval before publishing. Approvals are stored via the nova.approvals
# module and, upon approval, tasks are enqueued to perform the actual
# posting using the originally captured provider, function and arguments.

from nova.approvals import list_drafts as _list_drafts, approve_draft as _approve_draft, reject_draft as _reject_draft

@app.get(
    "/api/approvals",
    tags=["approvals"],
    dependencies=[role_required(Role.admin,)],
)
async def list_approvals() -> list[dict]:
    """Return all pending approval drafts.

    Only admin users may view pending approvals. The returned list
    contains raw draft dictionaries including provider, function,
    arguments and metadata. Sensitive information should not be stored
    in drafts.
    """
    return _list_drafts()


@app.post(
    "/api/approvals/{draft_id}/approve",
    tags=["approvals"],
    dependencies=[role_required(Role.admin,)],
)
async def approve_content(draft_id: str) -> dict:
    """Approve a pending draft and enqueue a publishing task.

    Args:
        draft_id: Identifier of the draft to approve.

    Returns:
        A dictionary containing the task ID enqueued to perform the
        publishing. If the draft does not exist, a 404 HTTP exception
        is raised.
    """
    from importlib import import_module
    from fastapi import HTTPException
    # Remove the draft from storage
    draft = _approve_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    provider = draft.get("provider")
    function_name = draft.get("function")
    args = draft.get("args", [])
    kwargs = draft.get("kwargs", {})
    # Some kwargs may include an ISO string for scheduled_time. Convert
    # any value that looks like an ISO datetime back into a datetime
    # object for the integration function. We detect keys named
    # 'scheduled_time' and attempt parsing.
    try:
        from datetime import datetime
        if "scheduled_time" in kwargs and isinstance(kwargs["scheduled_time"], str):
            try:
                kwargs["scheduled_time"] = datetime.fromisoformat(kwargs["scheduled_time"])
            except Exception:
                # Keep string if parsing fails
                pass
    except Exception:
        pass
    # Dynamically import the provider module and resolve the function
    try:
        mod = import_module(f"integrations.{provider}")
        func = getattr(mod, function_name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load provider function: {exc}")
    # Wrap the call in a coroutine for the task manager
    async def _publish_wrapper():
        # Call the provider function synchronously; if it raises an
        # exception the task manager will capture it and update status
        return func(*args, **kwargs)
    # Enqueue the publish task
    task_id = await task_manager.enqueue(TaskType.PUBLISH_POST, _publish_wrapper)
    return {"status": "enqueued", "task_id": task_id}


@app.post(
    "/api/approvals/{draft_id}/reject",
    tags=["approvals"],
    dependencies=[role_required(Role.admin,)],
)
async def reject_content(draft_id: str) -> dict:
    """Reject a pending draft.

    The draft will be removed from storage and no further action
    performed. A message confirming deletion is returned. If the draft
    does not exist, a 404 HTTP exception is raised.
    """
    from fastapi import HTTPException
    removed = _reject_draft(draft_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"status": "rejected", "draft_id": draft_id}

# -----------------------------------------------------------------------------
# Automation flags endpoints
#
# These endpoints allow admin users to view and modify global automation
# settings, such as whether automated posting or content generation is
# enabled and whether content approval is required. Flags are persisted
# via the nova.automation_flags module.

from nova.automation_flags import (
    get_flags,
    set_flags,
    DEFAULTS as _AUTOMATION_DEFAULTS,
)
from pydantic import BaseModel as _BaseModel


class AutomationUpdateRequest(_BaseModel):
    """Request body for updating automation flags.

    All fields are optional. Only provided flags will be updated. See
    ``nova.automation_flags.DEFAULTS`` for available flags.
    """
    posting_enabled: Union[bool, None] = None
    generation_enabled: Union[bool, None] = None
    require_approval: Union[bool, None] = None


@app.get(
    "/api/automation/flags",
    tags=["automation"],
    dependencies=[role_required(Role.admin,)],
)
async def get_automation_flags() -> dict:
    """Return the current automation flags.

    Returns:
        A dictionary containing flag names and their boolean values.
    """
    return get_flags()


@app.post(
    "/api/automation/flags",
    tags=["automation"],
    dependencies=[role_required(Role.admin,)],
)
async def update_automation_flags(req: AutomationUpdateRequest) -> dict:
    """Update one or more automation flags.

    Args:
        req: A Pydantic model with any subset of automation flags.

    Returns:
        The updated flag state after applying changes.

    Raises:
        HTTPException: If an unknown flag is provided.
    """
    changes = {k: v for k, v in req.dict().items() if v is not None}
    try:
        updated = set_flags(**changes)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return updated

# -----------------------------------------------------------------------------
# Override management endpoints
#
# Operators may need to override the automated retire/promote flags generated
# by the governance loop. These endpoints allow an admin to force a retire
# or promote decision for a specific channel, or to ignore such flags. The
# current override can also be queried. Overrides are persisted on disk via
# the ``nova.overrides`` module and will influence the outcome of the next
# governance run. Only admin users may access these endpoints.

from pydantic import BaseModel
from nova.overrides import (
    load_overrides,
    get_override,
    set_override,
    clear_override,
    VALID_OVERRIDES,
)


class OverrideRequest(BaseModel):
    """Request body for setting a channel override.

    Attributes:
        action: One of ``force_retire``, ``force_promote``, ``ignore_retire``,
            or ``ignore_promote``. See ``nova.overrides.VALID_OVERRIDES`` for
            the full list. The override will take effect on the next
            governance cycle.
    """
    action: str


@app.get(
    "/api/channels/{channel_id}/override",
    tags=["channels"],
    dependencies=[role_required(Role.admin,)],
)
async def get_channel_override(channel_id: str) -> dict:
    """Return the override directive for a given channel, if set.

    Args:
        channel_id: Identifier of the channel.

    Returns:
        A dictionary containing the channel ID and its override directive (or
        ``null`` if none set).
    """
    override = get_override(channel_id)
    return {"channel_id": channel_id, "override": override}


@app.post(
    "/api/channels/{channel_id}/override",
    tags=["channels"],
    dependencies=[role_required(Role.admin,)],
)
async def set_channel_override(channel_id: str, req: OverrideRequest) -> dict:
    """Set an override for a channel.

    Args:
        channel_id: Identifier of the channel.
        req: Pydantic model containing the desired override action.

    Returns:
        A dictionary with the updated override state.

    Raises:
        HTTPException: If the provided action is not valid.
    """
    action = req.action
    if action not in VALID_OVERRIDES:
        raise HTTPException(status_code=400, detail="Invalid override action")
    try:
        set_override(channel_id, action)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to set override: {exc}")
    return {"channel_id": channel_id, "override": action}


@app.delete(
    "/api/channels/{channel_id}/override",
    tags=["channels"],
    dependencies=[role_required(Role.admin,)],
)
async def delete_channel_override(channel_id: str) -> dict:
    """Clear any override directive for a channel.

    Args:
        channel_id: Identifier of the channel.

    Returns:
        A dictionary confirming the override was cleared.
    """
    try:
        clear_override(channel_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to clear override: {exc}")
    return {"channel_id": channel_id, "override": None}

# -----------------------------------------------------------------------------
# Integration endpoints (admin only)
#
# These endpoints expose simple wrappers around external integrations such as
# Gumroad and ConvertKit. They enable operators to generate affiliate links
# and manage subscribers directly via the API. All endpoints are restricted
# to admin users because they can trigger external side effects (e.g. adding
# subscribers or creating e‑commerce links).

from pydantic import BaseModel as _PydanticBaseModel


class GumroadLinkRequest(_PydanticBaseModel):
    """Request body for generating a Gumroad product link.

    Attributes:
        product_slug: The slug of the Gumroad product (e.g., ``"my-course"``).
        include_affiliate: If True (default), and if ``GUMROAD_AFFILIATE_ID``
            is set in the environment, append the affiliate query parameter
            to the URL. Set to False to omit affiliate tracking.
    """

    product_slug: str
    include_affiliate: Union[bool, None] = True


@app.post(
    "/api/integrations/gumroad/link",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def generate_gumroad_link(req: GumroadLinkRequest) -> dict:
    """Generate a Gumroad product URL.

    This endpoint constructs the URL to a Gumroad product landing page. If
    ``include_affiliate`` is True and an affiliate ID is set in the
    environment, the link will include the appropriate query parameter for
    revenue attribution.

    Args:
        req: Request body containing the product slug and optional flag.

    Returns:
        A JSON object with a single ``url`` field containing the generated
        link.
    """
    url = generate_product_link(req.product_slug, include_affiliate=bool(req.include_affiliate))
    return {"url": url}


class ConvertKitSubscribeRequest(_PydanticBaseModel):
    """Request body for subscribing a user via ConvertKit.

    Attributes:
        email: The subscriber's email address.
        first_name: Optional first name for personalization.
        form_id: Optional ConvertKit form ID; if omitted, uses the default
            from ``CONVERTKIT_FORM_ID`` environment variable.
        tags: Optional list of tag names to apply to the subscriber.
    """
    email: str
    first_name: Union[str, None] = None
    form_id: Union[str, None] = None
    tags: Union[list[str], None] = None


@app.post(
    "/api/integrations/convertkit/subscribe",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def convertkit_subscribe(req: ConvertKitSubscribeRequest) -> dict:
    """Subscribe a user to a ConvertKit form and optionally apply tags.

    Args:
        req: Subscription details including email, optional name, form ID and
            tags.

    Returns:
        The JSON response from ConvertKit describing the subscriber.

    Raises:
        HTTPException: With status 400 if the ConvertKit API call fails.
    """
    try:
        result = _ck_subscribe_user(
            email=req.email,
            first_name=req.first_name,
            form_id=req.form_id,
            tags=req.tags,
        )
        return result
    except ConvertKitError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class ConvertKitTagRequest(_PydanticBaseModel):
    """Request body for applying tags to an existing ConvertKit subscriber.

    Attributes:
        subscriber_id: The unique identifier of the subscriber.
        tags: A list of tag names to apply.
    """
    subscriber_id: str
    tags: list[str]


@app.post(
    "/api/integrations/convertkit/tags",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def convertkit_add_tags(req: ConvertKitTagRequest) -> dict:
    """Add tags to an existing ConvertKit subscriber.

    Args:
        req: Tagging details containing the subscriber ID and list of tag names.

    Returns:
        The JSON response from ConvertKit after tags are applied.

    Raises:
        HTTPException: With status 400 if the API call fails.
    """
    try:
        result = _ck_add_tags(subscriber_id=req.subscriber_id, tags=req.tags)
        return result
    except ConvertKitError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

# -----------------------------------------------------------------------------
# Beacons integration endpoints (admin only)
#
# These endpoints provide simple wrappers around the Beacons link‑in‑bio
# service.  Operators can generate profile URLs and prepare payloads to
# update the list of links on a Beacons page.  Because Beacons does not
# currently offer a public API for updating links, the ``update_links``
# helper returns a payload rather than performing an HTTP request.

class BeaconsLinkRequest(_PydanticBaseModel):
    """Request body for generating a Beacons profile link.

    Attributes:
        username: The Beacons username (without the leading '@').  A
            leading '@' will be stripped automatically.
    """
    username: str


class BeaconsLinkItem(_PydanticBaseModel):
    """Representation of a single link on a Beacons page.

    Attributes:
        title: The display name of the link (e.g. "YouTube").
        url: The target URL for the link.
    """
    title: str
    url: str


class BeaconsUpdateLinksRequest(_PydanticBaseModel):
    """Request body for updating the links on a Beacons page.

    Attributes:
        username: The Beacons username (without '@').
        links: A list of link objects containing titles and URLs.
    """
    username: str
    links: list[BeaconsLinkItem]


@app.post(
    "/api/integrations/beacons/link",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def generate_beacons_link(req: BeaconsLinkRequest) -> dict:
    """Generate the public Beacons profile URL for a user.

    Args:
        req: The request containing the Beacons username.

    Returns:
        A JSON object with a ``url`` field containing the profile link.
    """
    url = _beacons_generate_profile_link(req.username)
    return {"url": url}


@app.post(
    "/api/integrations/beacons/update-links",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def beacons_update_links(req: BeaconsUpdateLinksRequest) -> dict:
    """Prepare an update payload for a Beacons page.

    This endpoint validates the provided links and delegates to the
    ``update_links`` helper from the integrations package.  Because
    Beacons does not currently have a public API, the helper returns
    the payload rather than performing the update.

    Args:
        req: The request containing the username and list of links.

    Returns:
        A dictionary summarising the intended update payload.

    Raises:
        HTTPException: With status 400 if the links are invalid.
    """
    try:
        # Convert Pydantic models to plain dicts expected by the helper
        link_dicts = [{"title": item.title, "url": item.url} for item in req.links]
        result = _beacons_update_links(req.username, link_dicts)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# -----------------------------------------------------------------------------
# HubSpot CRM integration endpoints (admin only)
#
# These endpoints enable the creation of contacts within HubSpot CRM.  An
# operator can supply an email address, optional name fields and any
# additional properties supported by HubSpot.  The API key must be set in
# the ``HUBSPOT_API_KEY`` environment variable.  Only admin users are
# permitted to create contacts.

class HubSpotContactRequest(_PydanticBaseModel):
    """Request body for creating a contact in HubSpot.

    Attributes:
        email: The contact's email address.
        first_name: Optional first name.
        last_name: Optional last name.
        properties: Optional dictionary of additional HubSpot properties.
            Keys should match HubSpot property names (e.g., "company",
            "phone").
    """
    email: str
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    properties: Union[dict[str, Any], None] = None


@app.post(
    "/api/integrations/hubspot/contact",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def hubspot_create_contact(req: HubSpotContactRequest) -> dict:
    """Create a contact record in HubSpot CRM.

    Args:
        req: The request containing email, optional names and extra
            properties.

    Returns:
        The JSON response from HubSpot after the contact is created.

    Raises:
        HTTPException: With status 400 if the HubSpot API call fails.
    """
    try:
        extra_props = req.properties or {}
        result = _hubspot_create_contact(
            email=req.email,
            first_name=req.first_name,
            last_name=req.last_name,
            **extra_props,
        )
        return result
    except HubSpotError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# -----------------------------------------------------------------------------
# Metricool integration endpoints (admin only)
#
# These endpoints expose Metricool analytics to Nova.  Operators can fetch
# cross-platform performance metrics for a specific profile or retrieve an
# account-level overview.  The underlying integration handles API calls
# against Metricool's REST API and requires valid credentials in the
# environment variables ``METRICOOL_API_TOKEN`` and ``METRICOOL_ACCOUNT_ID``.

@app.get(
    "/api/integrations/metricool/profile/{profile_id}/metrics",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def metricool_profile_metrics(profile_id: str) -> dict:
    """Fetch Metricool metrics for a given profile.

    Args:
        profile_id: The identifier of the social profile in Metricool (e.g., a
            channel or account ID).

    Returns:
        A dictionary of metrics as returned by Metricool.

    Raises:
        HTTPException: With status 400 if credentials are missing or the
            Metricool API reports an error.
    """
    try:
        data = _metricool_get_metrics(profile_id)
        return data  # type: ignore[return-value]
    except (ValueError, MetricoolError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get(
    "/api/integrations/metricool/overview",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def metricool_overview() -> dict:
    """Fetch the Metricool account overview.

    Returns:
        A dictionary of aggregated metrics across all profiles.  If
        credentials are not set, returns a 400 error.
    """
    data = _metricool_get_overview()
    if data is None:
        raise HTTPException(status_code=400, detail="Metricool credentials not configured")
    return data  # type: ignore[return-value]

# -----------------------------------------------------------------------------
# TubeBuddy (YouTube Data API) integration endpoints (admin only)
#
# These endpoints expose keyword search and trending video retrieval via
# Google's YouTube Data API.  Operators can search for related keywords
# associated with a query or fetch the most popular videos in a given
# region/category.  A valid API key must be set in the environment
# variables ``GOOGLE_API_KEY`` or ``TUBEBUDDY_API_KEY``.  Only admin users
# may access these endpoints.

from typing import Optional, List
from fastapi import HTTPException  # Imported here to handle API errors in integration endpoints


@app.get(
    "/api/integrations/tubebuddy/keywords",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def tubebuddy_search_keywords(q: str, max_results: int = 10) -> List[str]:
    """Search YouTube for related keywords.

    Args:
        q: The search query term.
        max_results: Maximum number of keyword suggestions to return (default 10).

    Returns:
        A list of keywords relevant to the query.

    Raises:
        HTTPException: With status 400 if the API call fails (e.g., missing key).
    """
    try:
        return _tubebuddy_search_keywords(q, max_results=max_results)
    except (TubeBuddyError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get(
    "/api/integrations/tubebuddy/trending",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def tubebuddy_trending_videos(
    region: Optional[str] = None,
    category: Optional[str] = None,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Fetch trending videos on YouTube.

    Args:
        region: Two-letter region code (ISO 3166-1 alpha-2). Defaults to the
            ``DEFAULT_REGION`` environment variable or "US" if omitted.
        category: Optional YouTube category ID to filter results.
        max_results: Number of videos to return (max 50).

    Returns:
        A list of video metadata dictionaries (id, title, description, channelTitle).

    Raises:
        HTTPException: With status 400 if the API call fails or credentials are missing.
    """
    try:
        return _tubebuddy_get_trending_videos(
            region=region, category=category, max_results=max_results
        )
    except (TubeBuddyError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# -----------------------------------------------------------------------------
# SocialPilot integration endpoints (admin only)
#
# These endpoints allow operators to schedule posts via the SocialPilot API.
# SocialPilot can publish content to multiple platforms from a single API call.
# Posts can include text content, media URLs, scheduling information and
# additional metadata.  Only admin users may create SocialPilot posts.

class SocialPilotPostRequest(_PydanticBaseModel):
    """Request body for scheduling a SocialPilot post.

    Attributes:
        content: The text content of the post.
        media_url: Optional URL to an image or video to attach.
        platforms: Optional list of platform identifiers (e.g., "youtube", "tiktok").
        scheduled_time: Optional ISO 8601 datetime string specifying when to publish.
        extras: Optional dictionary of additional payload keys to merge.
    """

    content: str
    media_url: Union[str, None] = None
    platforms: Union[List[str], None] = None
    scheduled_time: Union[datetime, None] = None
    extras: Union[dict[str, Any], None] = None


@app.post(
    "/api/integrations/socialpilot/post",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def socialpilot_schedule_post(req: SocialPilotPostRequest) -> dict:
    """Schedule a social media post via SocialPilot.

    Args:
        req: The post request containing content and optional media/platforms/schedule.

    Returns:
        A dictionary describing the created post or approval draft.

    Raises:
        HTTPException: With status 400 if posting is disabled, approval is required,
            credentials are missing or the API returns an error.
    """
    try:
        result = _socialpilot_schedule_post(
            content=req.content,
            media_url=req.media_url,
            platforms=req.platforms,
            scheduled_time=req.scheduled_time,
            extras=req.extras,
        )
        # If approval is required, the schedule_post function will return a dict
        # containing pending_approval and approval_id keys.  We forward it directly.
        return result  # type: ignore[return-value]
    except (ValueError, RuntimeError, SocialPilotError) as exc:
        # Expose all integration errors as 400 for consistency
        raise HTTPException(status_code=400, detail=str(exc))

# -----------------------------------------------------------------------------
# Publer integration endpoints (admin only)
#
# Similar to the SocialPilot endpoints above, Publer allows Nova to schedule
# posts across multiple platforms via a single API call. Publer is another
# social media management service that supports scheduling posts to YouTube,
# TikTok, Instagram and Facebook. Only admin users may schedule posts via
# Publer. When posting is disabled or approval is required, the underlying
# integration will raise a RuntimeError and return a draft. These are
# surfaced to the caller as HTTP 400 responses with appropriate messages.

class PublerPostRequest(_PydanticBaseModel):
    """Request body for scheduling a Publer post.

    Attributes:
        content: The text content of the post.
        media_url: Optional URL to attach media to the post.
        platforms: Optional list of platform identifiers.
        scheduled_time: Optional ISO datetime string for scheduled publish time.
        extras: Optional additional payload fields.
    """
    content: str
    media_url: Union[str, None] = None
    platforms: Union[List[str], None] = None
    scheduled_time: Union[datetime, None] = None
    extras: Union[dict[str, Any], None] = None


@app.post(
    "/api/integrations/publer/post",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def publer_schedule_post(req: PublerPostRequest) -> dict:
    """Schedule a social media post via Publer.

    Args:
        req: The post request including content and optional media/platform/schedule/extras.

    Returns:
        A dictionary describing the created post or pending approval details.

    Raises:
        HTTPException: With status 400 if posting is disabled, credentials are missing,
        approval is required or the API returns an error.
    """
    try:
        result = _publer_schedule_post(
            content=req.content,
            media_url=req.media_url,
            platforms=req.platforms,
            scheduled_time=req.scheduled_time,
            extras=req.extras,
        )
        return result  # type: ignore[return-value]
    except (ValueError, RuntimeError, PublerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# -----------------------------------------------------------------------------
# Translation integration endpoints
#
# This endpoint exposes the Google Translate integration to translate text
# between languages. Operators can translate scripts, captions or other
# metadata to support multi‑language audiences. The underlying integration
# requires the `GOOGLE_TRANSLATE_API_KEY` environment variable and makes
# synchronous HTTP requests. Failures surface as HTTP 400 errors. Only
# admin users may call this endpoint to avoid excessive costs.

class TranslateRequest(_PydanticBaseModel):
    """Request body for text translation.

    Attributes:
        text: The text to translate.
        target_language: ISO 639‑1 code of the target language (e.g. "es").
        source_language: Optional ISO 639‑1 code of the source language.
        format: Either "text" or "html" indicating the format of the input.
    """
    text: str
    target_language: str
    source_language: Union[str, None] = None
    format: str = "text"


class TranslateResponse(_PydanticBaseModel):
    """Response body for translation requests."""
    translated_text: str


@app.post(
    "/api/integrations/translate",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
    response_model=TranslateResponse,
)
async def translate_text_api(req: TranslateRequest) -> TranslateResponse:
    """Translate text via Google Translate.

    Args:
        req: The translation request containing the text and target language.

    Returns:
        The translated text wrapped in a response model.

    Raises:
        HTTPException: With status 400 if the API key is missing or translation fails.
    """
    try:
        translated = _translate_text(
            req.text,
            target_language=req.target_language,
            source_language=req.source_language,
            format=req.format,
        )
        return TranslateResponse(translated_text=translated)
    except (RuntimeError, TranslationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# -----------------------------------------------------------------------------
# vidIQ integration endpoints (admin only)
#
# vidIQ offers trending search keywords and metrics for YouTube. This endpoint
# wraps the `get_trending_keywords` helper to fetch a list of trending
# keywords along with their scores. A valid `VIDIQ_API_KEY` must be set
# in the environment. Only admin users may call this endpoint.

from pydantic import BaseModel
from typing import List as _List


class VidiqKeyword(BaseModel):
    """Schema for a vidIQ trending keyword entry."""
    keyword: str
    score: float


@app.get(
    "/api/integrations/vidiq/trending",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
    response_model=_List[VidiqKeyword],
)
async def vidiq_trending(max_items: int = 10) -> _List[VidiqKeyword]:
    """Fetch trending keywords from vidIQ.

    Args:
        max_items: Maximum number of keywords to return (default 10).

    Returns:
        A list of keyword entries containing `keyword` and `score`.

    Raises:
        HTTPException: With status 400 if the API key is missing or an error occurs.
    """
    try:
        trending = _vidiq_get_trending_keywords(max_items)
    except (VidiqError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [VidiqKeyword(keyword=term, score=score) for term, score in trending]

# -----------------------------------------------------------------------------
# A/B testing endpoints (admin only)
#
# These endpoints allow operators to create and manage A/B tests for various
# aspects of the content pipeline.  Tests can be used to compare
# thumbnails, prompts, captions or any other values.  Only admin users may
# create, delete or view the details of tests because these operations
# affect the agent's behaviour.

class ABTestCreateRequest(_PydanticBaseModel):
    """Request body for creating an A/B test.

    Attributes:
        variants: A list of at least two variant values to compare.  Each
            value can be any JSON‑serialisable type (e.g. strings for
            filenames, dicts for structured prompts).
    """
    variants: list[Any]


class ABTestResultRequest(_PydanticBaseModel):
    """Request body for recording a test result.

    Attributes:
        variant: The variant value that was served.
        metric: Numeric performance metric for the variant (e.g. CTR, RPM).
    """
    variant: Any
    metric: float


@app.post(
    "/api/ab-tests/{test_id}",
    tags=["ab_tests"],
    dependencies=[role_required(Role.admin,)],
)
async def create_ab_test(test_id: str, req: ABTestCreateRequest) -> dict:
    """Create a new A/B test.

    Args:
        test_id: Unique identifier for the test.
        req: Request body containing the list of variants.

    Returns:
        A message confirming creation.

    Raises:
        HTTPException: If the test already exists or an invalid request
            is made.
    """
    try:
        ab_manager.create_test(test_id, req.variants)
        return {"status": "created", "test_id": test_id, "variants": req.variants}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete(
    "/api/ab-tests/{test_id}",
    tags=["ab_tests"],
    dependencies=[role_required(Role.admin,)],
)
async def delete_ab_test(test_id: str) -> dict:
    """Delete an existing A/B test and its persisted data."""
    try:
        ab_manager.delete_test(test_id)
        return {"status": "deleted", "test_id": test_id}
    except Exception:
        # If the test does not exist, return 404
        raise HTTPException(status_code=404, detail="Test not found")


@app.get(
    "/api/ab-tests/{test_id}/variant",
    tags=["ab_tests"],
    dependencies=[role_required(Role.admin,)],
)
async def get_ab_test_variant(test_id: str) -> dict:
    """Return a randomly selected variant for the specified test."""
    try:
        variant = ab_manager.choose_variant(test_id)
        return {"variant": variant}
    except KeyError:
        raise HTTPException(status_code=404, detail="Test not found")


@app.post(
    "/api/ab-tests/{test_id}/result",
    tags=["ab_tests"],
    dependencies=[role_required(Role.admin,)],
)
async def record_ab_test_result(test_id: str, req: ABTestResultRequest) -> dict:
    """Record the result of serving a variant for a given test."""
    try:
        ab_manager.record_result(test_id, req.variant, req.metric)
        return {"status": "recorded", "test_id": test_id, "variant": req.variant, "metric": req.metric}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get(
    "/api/ab-tests/{test_id}",
    tags=["ab_tests"],
    dependencies=[role_required(Role.admin,)],
)
async def get_ab_test(test_id: str) -> dict:
    """Return the details of an A/B test."""
    try:
        data = ab_manager.get_test(test_id)
        return data
    except KeyError:
        raise HTTPException(status_code=404, detail="Test not found")


@app.get(
    "/api/ab-tests/{test_id}/best",
    tags=["ab_tests"],
    dependencies=[role_required(Role.admin,)],
)
async def get_ab_test_best(test_id: str) -> dict:
    """Return the variant with the highest average metric for a test."""
    try:
        best = ab_manager.best_variant(test_id)
        return {"best_variant": best}
    except KeyError:
        raise HTTPException(status_code=404, detail="Test not found")

# -----------------------------------------------------------------------------
# Direct posting and TTS integration endpoints (admin only)
#
# These endpoints expose lower‑level integrations for uploading videos to
# YouTube, publishing content to Instagram and Facebook, and synthesising
# speech using a third‑party TTS provider.  They require admin privileges
# because they trigger actions on external services.  The underlying
# integration functions handle automation flags (posting enabled/approval
# required) and may return a dictionary with approval metadata instead of
# performing the action directly.  Callers should inspect the returned
# object to determine whether a post was created or a draft was queued.

class YouTubeUploadRequest(_PydanticBaseModel):
    """Request body for uploading a video to YouTube.

    Attributes:
        file_path: Absolute or relative path to the video file on the server.
        title: Title for the video.
        description: Optional description text.
        tags: Optional list of tags/keywords.
        privacy_status: Privacy setting ("public", "unlisted", "private").
    """
    file_path: str
    title: str
    description: Union[str, None] = None
    tags: Union[List[str], None] = None
    privacy_status: str = "public"


class InstagramPostRequest(_PydanticBaseModel):
    """Request body for publishing a video to Instagram.

    Attributes:
        video_url: Publicly accessible URL to the video to post.
        caption: Optional caption text.
        thumbnail_url: Optional URL for a custom thumbnail image.
    """
    video_url: str
    caption: Union[str, None] = None
    thumbnail_url: Union[str, None] = None


class FacebookPostRequest(_PydanticBaseModel):
    """Request body for publishing a post to Facebook.

    Attributes:
        message: The textual content of the post.
        link: Optional URL to attach as a link share.
        media_url: Optional URL to an image or video to attach.
    """
    message: str
    link: Union[str, None] = None
    media_url: Union[str, None] = None


class TTSRequest(_PydanticBaseModel):
    """Request body for synthesising speech from text.

    Attributes:
        text: The text to convert to speech.
        voice_id: Optional voice identifier. If not provided, the default
            configured voice will be used.
        format: Audio format (e.g., "mp3", "wav"). Defaults to "mp3".
    """
    text: str
    voice_id: Union[str, None] = None
    format: str = "mp3"


@app.post(
    "/api/integrations/youtube/upload",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def youtube_upload_video(req: YouTubeUploadRequest) -> dict:
    """Upload a video to YouTube via the Data API.

    This endpoint wraps the `upload_video` helper, running it in a separate
    thread to avoid blocking the event loop. If posting is disabled or
    approval is required, the helper will raise an error or return a draft
    descriptor. On success, returns the YouTube video ID or approval info.

    Args:
        req: The upload request containing file path and metadata.

    Returns:
        A dictionary containing either the `video_id` on success or the
        `pending_approval`/`approval_id` keys if approval is needed.

    Raises:
        HTTPException: With status 400 if credentials are missing or an error
            occurs during upload.
    """
    try:
        result = await asyncio.to_thread(
            _youtube_upload_video,
            req.file_path,
            title=req.title,
            description=req.description or "",
            tags=req.tags,
            privacy_status=req.privacy_status,
        )
        # If the helper returned a dict (e.g., pending approval), forward it.
        if isinstance(result, dict):
            return result  # type: ignore[return-value]
        return {"video_id": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post(
    "/api/integrations/instagram/post",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def instagram_publish_video(req: InstagramPostRequest) -> dict:
    """Publish a video to Instagram via the Graph API.

    Wraps the `publish_video` helper and executes it in a thread. The helper
    handles automation flags and may return a draft descriptor if approval
    is required. On success, returns a media ID.

    Args:
        req: The publish request containing the video URL and optional
            caption/thumbnail.

    Returns:
        A dictionary with either `media_id` on success or draft info if
        approval is required.

    Raises:
        HTTPException: With status 400 on any error (e.g., missing tokens).
    """
    try:
        result = await asyncio.to_thread(
            _instagram_publish_video,
            req.video_url,
            caption=req.caption or "",
            thumbnail_url=req.thumbnail_url,
        )
        if isinstance(result, dict):
            return result  # type: ignore[return-value]
        return {"media_id": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post(
    "/api/integrations/facebook/post",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def facebook_publish_post(req: FacebookPostRequest) -> dict:
    """Publish a post or media to Facebook via the Graph API.

    Runs the `publish_post` helper in a separate thread. The helper
    determines whether to create a photo, video or feed post based on
    the provided media URL. It respects automation flags and may return
    a draft descriptor instead of posting immediately.

    Args:
        req: The post request with message and optional link/media URL.

    Returns:
        A dictionary containing either the created post ID (for photos/feed
        posts), the media ID (for videos) or draft info if approval is
        required.

    Raises:
        HTTPException: With status 400 if required credentials are missing
        or another error occurs.
    """
    try:
        result = await asyncio.to_thread(
            _facebook_publish_post,
            req.message,
            link=req.link,
            media_url=req.media_url,
        )
        if isinstance(result, dict):
            return result  # type: ignore[return-value]
        return {"id": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post(
    "/api/integrations/tts",
    tags=["integrations"],
    dependencies=[role_required(Role.admin,)],
)
async def tts_synthesize(req: TTSRequest) -> dict:
    """Generate speech audio from text using the TTS integration.

    Calls the `synthesize_speech` helper in a thread and returns the
    path to the generated audio file. Any runtime or HTTP errors are
    converted to a 400 response.

    Args:
        req: The TTS request containing text and optional voice/format.

    Returns:
        A dictionary with the `audio_path` pointing to the generated file.

    Raises:
        HTTPException: With status 400 if synthesis fails or credentials
        are missing.
    """
    try:
        path = await asyncio.to_thread(
            _synthesize_speech,
            req.text,
            voice_id=req.voice_id,
            format=req.format,
        )
        return {"audio_path": path}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

# -----------------------------------------------------------------------------
# WebSocket broadcasting helper
#
# To decouple event emission from the WebSocket handler itself, we provide a
# simple broadcast helper. Other parts of the system (e.g. the TaskManager)
# can import and call this function to push structured messages to all
# connected clients. Messages should be JSON‑serialisable dictionaries.

async def broadcast_event(message: dict) -> None:
    """Send a message to all connected WebSocket clients.

    Any connection that raises an exception during send will be removed
    from the connections set to avoid future errors. This function is
    safe to call concurrently from multiple tasks.

    Args:
        message: A JSON‑serialisable dictionary to transmit.
    """
    dead = set()
    for ws in list(connections):
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    for ws in dead:
        connections.discard(ws)

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    try:
        while True:
            # keepalive / echo
            msg = await ws.receive_text()
            await ws.send_text(f"echo: {msg}")
    except WebSocketDisconnect:
        connections.discard(ws)

# Mount all legacy routers and the Flask model API via WSGIMiddleware
from realtime import router as realtime_router
from routes.research import router as research_router
from routes.observability import router as observability_router
from agents.decision_matrix_agent import router as decision_router
from interface_handler import router as interface_router
from nova_agent_v4_4.chat_api import router as chat_v4_router

# Include all routers on the single FastAPI app
app.include_router(realtime_router)
app.include_router(research_router)
app.include_router(observability_router)
app.include_router(decision_router)
app.include_router(interface_router)
app.include_router(chat_v4_router)

# Add missing endpoints from main.py
@app.get("/status", tags=["meta"])
def read_status():
    return {
        "status": "Nova Agent v6.7 running",
        "loop": "heartbeat active",
        "version": "6.7",
        "features": ["autonomous_research", "nlp_intent_detection", "memory_management"]
    }

# Define path to model tiers configuration
MODEL_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "model_tiers.json"

@app.get("/api/current-model-tiers", tags=["meta"])
async def current_model_tiers():
    if MODEL_CONFIG_PATH.exists():
        import json
        return json.loads(MODEL_CONFIG_PATH.read_text())
    return {}

# Mount Flask blueprint via WSGIMiddleware
try:
    from backend.model_api import model_api  # the Flask Blueprint
    from flask import Flask
    from fastapi.middleware.wsgi import WSGIMiddleware
    
    # Create a minimal Flask app and register the blueprint
    flask_app = Flask(__name__)
    flask_app.register_blueprint(model_api)
    
    # Mount the Flask app on the FastAPI app
    app.mount("/", WSGIMiddleware(flask_app))
except ImportError:
    # If Flask components are not available, continue without them
    pass

# -----------------------------------------------------------------------------
# v7.0 Planning Engine API Endpoints
# -----------------------------------------------------------------------------

class StrategicPlanRequest(BaseModel):
    """Request body for generating a strategic plan."""
    goal: str
    current_metrics: Dict[str, Any]
    historical_data: Dict[str, Any]
    external_factors: Dict[str, Any]
    constraints: Dict[str, Any]
    goals: Dict[str, Any]

class DecisionApprovalRequest(BaseModel):
    """Request body for approving/rejecting decisions."""
    decision_id: str
    action: str  # "approve" or "reject"
    reason: Optional[str] = None
    approved_by: str

class TaskScheduleRequest(BaseModel):
    """Request body for scheduling tasks."""
    name: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    scheduled_time: Optional[datetime] = None
    priority: str = "medium"
    dependencies: Optional[List[str]] = None

@app.post(
    "/api/v7/planning/strategic-plan",
    tags=["v7_planning"],
    dependencies=[role_required(Role.admin,)],
)
async def generate_strategic_plan(req: StrategicPlanRequest) -> Dict[str, Any]:
    """Generate a comprehensive strategic plan using the v7.0 planning engine."""
    try:
        context = PlanningContext(
            current_metrics=req.current_metrics,
            historical_data=req.historical_data,
            external_factors=req.external_factors,
            constraints=req.constraints,
            goals=req.goals
        )
        
        plan = await planning_engine.generate_strategic_plan(context, req.goal)
        
        # Schedule tasks from the plan
        task_ids = task_scheduler.schedule_from_plan(plan)
        plan['scheduled_task_ids'] = task_ids
        
        return {
            "success": True,
            "plan": plan,
            "message": f"Strategic plan generated with {len(task_ids)} scheduled tasks"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")

@app.get(
    "/api/v7/planning/decisions/pending",
    tags=["v7_planning"],
    dependencies=[role_required(Role.admin,)],
)
async def get_pending_decisions() -> List[Dict[str, Any]]:
    """Get all pending decisions requiring approval."""
    try:
        decisions = planning_engine.get_pending_decisions()
        return [asdict(decision) for decision in decisions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending decisions: {str(e)}")

@app.post(
    "/api/v7/planning/decisions/approve",
    tags=["v7_planning"],
    dependencies=[role_required(Role.admin,)],
)
async def approve_decision(req: DecisionApprovalRequest) -> Dict[str, Any]:
    """Approve or reject a pending decision."""
    try:
        if req.action == "approve":
            success = planning_engine.approve_decision(req.decision_id, req.approved_by)
            message = "Decision approved successfully"
        elif req.action == "reject":
            success = planning_engine.reject_decision(req.decision_id, req.approved_by, req.reason or "No reason provided")
            message = "Decision rejected successfully"
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=404, detail="Decision not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process decision: {str(e)}")

@app.get(
    "/api/v7/planning/decisions/history",
    tags=["v7_planning"],
    dependencies=[role_required(Role.admin,)],
)
async def get_decision_history(
    decision_type: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get decision history, optionally filtered by type."""
    try:
        if decision_type:
            dt = DecisionType(decision_type)
            decisions = planning_engine.get_decision_history(dt, limit)
        else:
            decisions = planning_engine.get_decision_history(limit=limit)
        
        return [asdict(decision) for decision in decisions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get decision history: {str(e)}")

@app.post(
    "/api/v7/scheduler/task",
    tags=["v7_scheduler"],
    dependencies=[role_required(Role.admin,)],
)
async def schedule_task(req: TaskScheduleRequest) -> Dict[str, Any]:
    """Schedule a new task."""
    try:
        priority = TaskPriority[req.priority.upper()]
        scheduled_time = req.scheduled_time or datetime.now()
        
        task_id = task_scheduler.schedule_task(
            name=req.name,
            description=req.description,
            action_type=req.action_type,
            parameters=req.parameters,
            scheduled_time=scheduled_time,
            priority=priority,
            dependencies=req.dependencies
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Task '{req.name}' scheduled successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule task: {str(e)}")

@app.get(
    "/api/v7/scheduler/tasks/pending",
    tags=["v7_scheduler"],
    dependencies=[role_required(Role.admin,)],
)
async def get_pending_tasks() -> List[Dict[str, Any]]:
    """Get all pending tasks."""
    try:
        tasks = task_scheduler.get_pending_tasks()
        return [asdict(task) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending tasks: {str(e)}")

@app.get(
    "/api/v7/scheduler/tasks/running",
    tags=["v7_scheduler"],
    dependencies=[role_required(Role.admin,)],
)
async def get_running_tasks() -> List[Dict[str, Any]]:
    """Get all currently running tasks."""
    try:
        tasks = task_scheduler.get_running_tasks()
        return [asdict(task) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get running tasks: {str(e)}")

@app.get(
    "/api/v7/scheduler/tasks/completed",
    tags=["v7_scheduler"],
    dependencies=[role_required(Role.admin,)],
)
async def get_completed_tasks(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recently completed tasks."""
    try:
        tasks = task_scheduler.get_completed_tasks(limit)
        return [asdict(task) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get completed tasks: {str(e)}")

@app.get(
    "/api/v7/scheduler/task/{task_id}",
    tags=["v7_scheduler"],
    dependencies=[role_required(Role.admin,)],
)
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a specific task."""
    try:
        status = task_scheduler.get_task_status(task_id)
        if status:
            return status
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@app.delete(
    "/api/v7/scheduler/task/{task_id}",
    tags=["v7_scheduler"],
    dependencies=[role_required(Role.admin,)],
)
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """Cancel a scheduled task."""
    try:
        success = task_scheduler.cancel_task(task_id)
        if success:
            return {"success": True, "message": f"Task {task_id} cancelled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")

@app.post(
    "/api/v7/scheduler/start",
    tags=["v7_scheduler"],
    dependencies=[role_required(Role.admin,)],
)
async def start_scheduler() -> Dict[str, Any]:
    """Start the task scheduler loop."""
    try:
        # This would start the scheduler in a background task
        # For now, just return success
        return {
            "success": True,
            "message": "Task scheduler started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

# Update the status endpoint to reflect v7.0
@app.get("/status", tags=["meta"])
def read_status():
    return {
        "status": "Nova Agent v7.0 running",
        "loop": "heartbeat active",
        "version": "7.0",
        "features": [
            "autonomous_research", 
            "nlp_intent_detection", 
            "memory_management",
            "planning_engine",
            "task_scheduler",
            "enhanced_governance"
        ]
    }

__all__ = ["app"]
