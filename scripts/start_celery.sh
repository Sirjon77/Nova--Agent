#!/bin/bash

# Nova Agent Celery Startup Script
# 
# This script starts Celery workers and beat scheduler for Nova Agent v7.0
# It replaces the legacy manual scheduling with robust background task processing.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 Nova Agent Celery Startup${NC}"
echo "Project root: $PROJECT_ROOT"
echo

# Change to project directory
cd "$PROJECT_ROOT"

# Check if Redis is running
check_redis() {
    echo -e "${YELLOW}📡 Checking Redis connectivity...${NC}"
    
    REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli -u "$REDIS_URL" ping &> /dev/null; then
            echo -e "${GREEN}✅ Redis is running and accessible${NC}"
        else
            echo -e "${RED}❌ Redis is not accessible at $REDIS_URL${NC}"
            echo "Please ensure Redis is running and accessible."
            echo "Start Redis with: redis-server"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  redis-cli not found, skipping connectivity check${NC}"
        echo "Assuming Redis is available at $REDIS_URL"
    fi
}

# Check Python dependencies
check_dependencies() {
    echo -e "${YELLOW}📦 Checking Python dependencies...${NC}"
    
    python3 -c "import celery, redis" 2>/dev/null || {
        echo -e "${RED}❌ Missing required dependencies: celery or redis${NC}"
        echo "Install with: pip install -r requirements.txt"
        exit 1
    }
    
    echo -e "${GREEN}✅ Dependencies are installed${NC}"
}

# Function to start Celery worker
start_worker() {
    local queue_name="${1:-celery}"
    local concurrency="${2:-4}"
    
    echo -e "${BLUE}🔧 Starting Celery worker for queue: $queue_name${NC}"
    echo "Concurrency: $concurrency"
    echo "Log level: ${CELERY_LOG_LEVEL:-info}"
    
    celery -A nova.celery_app worker \
        --loglevel="${CELERY_LOG_LEVEL:-info}" \
        --concurrency="$concurrency" \
        --queues="$queue_name" \
        --hostname="worker-$queue_name@%h" \
        --pidfile="/tmp/celery-worker-$queue_name.pid" \
        --logfile="logs/celery-worker-$queue_name.log" \
        --detach
}

# Function to start Celery beat scheduler
start_beat() {
    echo -e "${BLUE}⏰ Starting Celery beat scheduler${NC}"
    echo "Schedule file: celerybeat-schedule"
    
    celery -A nova.celery_app beat \
        --loglevel="${CELERY_LOG_LEVEL:-info}" \
        --schedule="celerybeat-schedule" \
        --pidfile="/tmp/celery-beat.pid" \
        --logfile="logs/celery-beat.log" \
        --detach
}

# Function to start monitoring (flower)
start_monitoring() {
    if command -v flower &> /dev/null; then
        echo -e "${BLUE}🌸 Starting Flower monitoring (optional)${NC}"
        echo "Web interface will be available at: http://localhost:5555"
        
        flower -A nova.celery_app \
            --port=5555 \
            --logging=info \
            --pidfile="/tmp/flower.pid" \
            --logfile="logs/flower.log" \
            --detach
    else
        echo -e "${YELLOW}⚠️  Flower not installed, skipping monitoring setup${NC}"
        echo "Install with: pip install flower"
    fi
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Celery Status${NC}"
    echo
    
    # Check if processes are running
    if [ -f "/tmp/celery-beat.pid" ] && kill -0 "$(cat /tmp/celery-beat.pid)" 2>/dev/null; then
        echo -e "${GREEN}✅ Celery Beat: Running (PID: $(cat /tmp/celery-beat.pid))${NC}"
    else
        echo -e "${RED}❌ Celery Beat: Not running${NC}"
    fi
    
    for queue in celery governance maintenance metrics trends analysis; do
        pid_file="/tmp/celery-worker-$queue.pid"
        if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
            echo -e "${GREEN}✅ Worker ($queue): Running (PID: $(cat "$pid_file"))${NC}"
        else
            echo -e "${RED}❌ Worker ($queue): Not running${NC}"
        fi
    done
    
    if [ -f "/tmp/flower.pid" ] && kill -0 "$(cat /tmp/flower.pid)" 2>/dev/null; then
        echo -e "${GREEN}✅ Flower Monitoring: Running (PID: $(cat /tmp/flower.pid))${NC}"
        echo "   Web interface: http://localhost:5555"
    fi
}

# Function to stop all Celery processes
stop_celery() {
    echo -e "${YELLOW}🛑 Stopping all Celery processes...${NC}"
    
    # Stop beat scheduler
    if [ -f "/tmp/celery-beat.pid" ]; then
        kill "$(cat /tmp/celery-beat.pid)" 2>/dev/null || true
        rm -f "/tmp/celery-beat.pid"
    fi
    
    # Stop workers
    for queue in celery governance maintenance metrics trends analysis; do
        pid_file="/tmp/celery-worker-$queue.pid"
        if [ -f "$pid_file" ]; then
            kill "$(cat "$pid_file")" 2>/dev/null || true
            rm -f "$pid_file"
        fi
    done
    
    # Stop flower
    if [ -f "/tmp/flower.pid" ]; then
        kill "$(cat /tmp/flower.pid)" 2>/dev/null || true
        rm -f "/tmp/flower.pid"
    fi
    
    echo -e "${GREEN}✅ All Celery processes stopped${NC}"
}

# Create logs directory
mkdir -p logs

# Parse command line arguments
case "${1:-start}" in
    "start")
        check_redis
        check_dependencies
        
        echo -e "${BLUE}🚀 Starting Nova Agent Celery cluster...${NC}"
        echo
        
        # Start beat scheduler
        start_beat
        
        # Start workers for different queues
        start_worker "celery" 2      # General tasks
        start_worker "governance" 1  # Governance tasks (single worker)
        start_worker "maintenance" 1 # Maintenance tasks
        start_worker "metrics" 1     # Metrics processing
        start_worker "trends" 1      # Trend analysis
        start_worker "analysis" 1    # Deep analysis tasks
        
        # Start monitoring (optional)
        start_monitoring
        
        echo
        echo -e "${GREEN}🎉 Celery cluster started successfully!${NC}"
        echo
        
        # Show status
        sleep 2
        show_status
        
        echo
        echo -e "${BLUE}📋 Quick Commands:${NC}"
        echo "  View status:    $0 status"
        echo "  Stop cluster:   $0 stop"
        echo "  View logs:      tail -f logs/celery-*.log"
        echo "  Monitor tasks:  http://localhost:5555 (if Flower is running)"
        ;;
        
    "stop")
        stop_celery
        ;;
        
    "restart")
        stop_celery
        sleep 2
        exec "$0" start
        ;;
        
    "status")
        show_status
        ;;
        
    "logs")
        echo -e "${BLUE}📋 Recent Celery logs:${NC}"
        echo
        
        if [ -f "logs/celery-beat.log" ]; then
            echo -e "${YELLOW}=== Beat Scheduler ===${NC}"
            tail -n 10 "logs/celery-beat.log"
            echo
        fi
        
        for queue in celery governance maintenance; do
            log_file="logs/celery-worker-$queue.log"
            if [ -f "$log_file" ]; then
                echo -e "${YELLOW}=== Worker: $queue ===${NC}"
                tail -n 5 "$log_file"
                echo
            fi
        done
        ;;
        
    "test")
        echo -e "${BLUE}🧪 Testing Celery connectivity...${NC}"
        
        python3 -c "
from nova.celery_app import celery_app, health_check
print('✅ Celery app imported successfully')

try:
    # Test basic connectivity
    inspect = celery_app.control.inspect()
    workers = inspect.active()
    if workers:
        print(f'✅ Found {len(workers)} active workers')
        for worker in workers:
            print(f'   - {worker}')
    else:
        print('⚠️  No active workers found')
    
    # Test task queuing
    task = health_check.delay()
    print(f'✅ Health check task queued: {task.id}')
    
except Exception as e:
    print(f'❌ Celery test failed: {e}')
"
        ;;
        
    *)
        echo -e "${BLUE}Nova Agent Celery Management${NC}"
        echo
        echo "Usage: $0 {start|stop|restart|status|logs|test}"
        echo
        echo "Commands:"
        echo "  start    - Start Celery workers and beat scheduler"
        echo "  stop     - Stop all Celery processes"
        echo "  restart  - Restart the entire cluster"
        echo "  status   - Show current status of all processes"
        echo "  logs     - Show recent log entries"
        echo "  test     - Test Celery connectivity and task queuing"
        echo
        echo "Environment variables:"
        echo "  REDIS_URL          - Redis broker URL (default: redis://localhost:6379/0)"
        echo "  CELERY_LOG_LEVEL   - Log level (default: info)"
        ;;
esac
