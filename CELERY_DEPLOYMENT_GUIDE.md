# Nova Agent Celery Beat Deployment Guide

## 🎯 Overview

Nova Agent v7.0 has migrated from manual asyncio loops to Celery Beat for robust, scalable background job processing. This guide covers deployment and operation of the new system.

## 🏗️ Architecture Changes

### Before (Legacy)
```python
# Manual loop in FastAPI startup
@app.on_event("startup")
async def schedule_governance_nightly():
    async def _runner():
        while True:
            await governance_run(cfg, [], [], [])
            await asyncio.sleep(24 * 60 * 60)
    asyncio.create_task(_runner())
```

### After (Celery Beat)
```python
# Robust scheduling with retry logic
celery_app.conf.beat_schedule = {
    'nightly-governance-loop': {
        'task': 'nova.governance.run_governance_task',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'governance'}
    }
}
```

## 📦 Prerequisites

### Required Services
- **Redis**: Celery broker and result backend
- **Python 3.9+**: With celery>=5.3.0 and redis>=4.5.0

### Environment Variables
```bash
# Required
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your_secure_jwt_key_here

# Optional  
CELERY_LOG_LEVEL=info
COMPETITOR_SEEDS=competitor1,competitor2,competitor3
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
# Includes: celery>=5.3.0, redis>=4.5.0
```

### 2. Start Redis
```bash
# Ubuntu/Debian
sudo systemctl start redis-server

# macOS with Homebrew
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

### 3. Start Celery Services
```bash
# Use the provided startup script
./scripts/start_celery.sh start

# Or manually:
celery -A nova.celery_app worker --loglevel=info --detach
celery -A nova.celery_app beat --loglevel=info --detach
```

### 4. Verify Operation
```bash
# Check status
./scripts/start_celery.sh status

# Test connectivity
./scripts/start_celery.sh test

# View logs
./scripts/start_celery.sh logs
```

## 📋 Scheduled Tasks

| Task | Schedule | Purpose | Queue |
|------|----------|---------|-------|
| **Governance Loop** | Daily 2:00 AM UTC | Channel scoring, policy enforcement | governance |
| **Memory Cleanup** | Hourly | Cache cleanup, memory management | maintenance |
| **Analytics Processing** | Daily 3:00 AM UTC | Metrics aggregation, leaderboards | analytics |
| **Competitor Analysis** | Weekly (Sunday 4:00 AM UTC) | Market intelligence | analysis |
| **Trend Scanning** | Daily 6:00 AM UTC | Content opportunities | trends |

## 🛠️ Management API

### Task Status
```bash
# Get Celery cluster status
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/api/celery/status

# Check specific task
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/api/celery/task/$TASK_ID
```

### Manual Triggers
```bash
# Trigger governance manually
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"auto_actions": false}' \
     http://localhost:8000/api/celery/governance/run

# Trigger memory cleanup
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/api/celery/maintenance/cleanup?max_age_hours=24
```

## 🔧 Production Configuration

### Worker Scaling
```bash
# Multiple workers for different queues
celery -A nova.celery_app worker --queues=governance --concurrency=1 --hostname=gov@%h
celery -A nova.celery_app worker --queues=maintenance --concurrency=2 --hostname=maint@%h  
celery -A nova.celery_app worker --queues=analytics,trends --concurrency=3 --hostname=data@%h

# Or use the startup script
./scripts/start_celery.sh start
```

### Monitoring with Flower
```bash
# Install flower
pip install flower

# Start monitoring interface
flower -A nova.celery_app --port=5555

# Access web interface
open http://localhost:5555
```

### Process Management
```bash
# Using systemd (recommended for production)
sudo cp deployment/celery-worker.service /etc/systemd/system/
sudo cp deployment/celery-beat.service /etc/systemd/system/
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
```

## 📊 Monitoring & Alerting

### Health Checks
```python
# Built-in health check task
from nova.celery_app import health_check
result = health_check.delay()
print(result.get())  # {'status': 'healthy', 'worker': True}
```

### Metrics Integration
- All tasks include Prometheus metrics
- Task execution counters and timers
- Queue depth and worker status
- Integration with existing `/metrics` endpoint

### Log Files
```bash
# Default log locations
logs/celery-beat.log          # Scheduler logs
logs/celery-worker-*.log      # Worker logs per queue
logs/flower.log               # Monitoring interface
```

## 🔄 Migration from Legacy System

### Phase 1: Parallel Operation
1. Deploy new Celery system alongside existing loops
2. Monitor both systems for 24-48 hours
3. Verify task execution and results

### Phase 2: Gradual Migration
1. Disable legacy scheduling in production config
2. Enable Celery Beat scheduling
3. Monitor for missed executions or failures

### Phase 3: Cleanup
1. Remove legacy scheduling code
2. Update monitoring and alerting
3. Archive old log files

### Rollback Plan
If issues arise, quickly revert by:
1. Stopping Celery services: `./scripts/start_celery.sh stop`
2. Re-enabling legacy scheduling in FastAPI startup
3. Restarting the application

## 🐛 Troubleshooting

### Common Issues

#### Redis Connection Failed
```bash
# Check Redis status
redis-cli ping

# Check connection from Python
python3 -c "import redis; r=redis.from_url('redis://localhost:6379/0'); print(r.ping())"
```

#### No Active Workers
```bash
# Check worker processes
ps aux | grep celery

# Restart workers
./scripts/start_celery.sh restart
```

#### Tasks Not Executing
```bash
# Check beat scheduler
celery -A nova.celery_app inspect scheduled

# Check worker queues
celery -A nova.celery_app inspect active
```

#### High Memory Usage
```bash
# Monitor worker memory
celery -A nova.celery_app inspect stats

# Restart workers periodically (already configured)
# workers restart after 100 tasks
```

### Performance Tuning

#### Concurrency Settings
```python
# Adjust in nova/celery_app.py
worker_max_tasks_per_child = 100  # Restart after N tasks
task_acks_late = True             # Reliability over speed
```

#### Queue Optimization
```python
# Route heavy tasks to dedicated queues
task_routes = {
    'nova.trends.*': {'queue': 'trends'},
    'nova.analysis.*': {'queue': 'analysis'},
}
```

## 📈 Benefits Achieved

### Reliability
- ✅ Automatic retries with exponential backoff
- ✅ Task isolation prevents cascade failures  
- ✅ Persistent task queue survives restarts

### Scalability
- ✅ Horizontal worker scaling across instances
- ✅ Queue-based load balancing
- ✅ Independent task lifecycle management

### Observability  
- ✅ Real-time task monitoring via API
- ✅ Comprehensive logging and metrics
- ✅ Web-based management interface

### Maintainability
- ✅ Centralized task scheduling configuration
- ✅ Modular task organization by domain
- ✅ Version-controlled schedule changes

## 🔗 Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Monitoring](https://flower.readthedocs.io/)
- [Nova Agent API Documentation](http://localhost:8000/docs)

---

**Deployment Status**: ✅ Ready for Production  
**Migration Complexity**: 🟡 Medium (requires Redis setup)  
**Rollback Risk**: 🟢 Low (legacy system can be re-enabled quickly)
