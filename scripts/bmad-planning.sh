#!/bin/bash
# Nova Agent BMAD Planning Automation Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[BMAD]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to run BMAD planning
run_bmad_planning() {
    local feature_name=$1
    local planning_type=$2
    
    print_status "Starting BMAD planning for feature: $feature_name"
    
    # Create planning directory
    mkdir -p docs/planning/$feature_name
    
    # Copy Nova Agent context
    print_status "Loading Nova Agent context..."
    cp docs/flattened-codebase.xml docs/planning/$feature_name/context.xml
    
    # Create feature brief
    cat > docs/planning/$feature_name/brief.md << EOF
# Feature Brief: $feature_name

## Nova Agent Context
- Codebase: docs/flattened-codebase.xml loaded
- Architecture: Multi-tenant, async, JWT/RBAC enabled
- Standards: 95% test coverage, type hints, black/ruff formatting

## Feature Request
[Describe the feature here]

## Constraints
- Must integrate with existing MemoryManager
- Must follow Nova Agent API patterns
- Must maintain backward compatibility
- Must include comprehensive tests

## Success Criteria
- [ ] PRD created and approved
- [ ] Architecture design reviewed
- [ ] Test strategy defined
- [ ] Implementation plan ready
EOF
    
    print_success "Feature brief created at docs/planning/$feature_name/brief.md"
    
    # Run BMAD planning based on type
    if [ "$planning_type" == "full" ]; then
        print_status "Running full BMAD planning workflow..."
        
        # Create workflow file
        cat > docs/planning/$feature_name/workflow.yaml << EOF
name: "$feature_name Planning"
type: "brownfield-fullstack"
context:
  - docs/flattened-codebase.xml
  - .cursor/rules/00-nova-agent.md
  - .cursor/rules/01-nova-agent-bmad-planning.md
agents:
  - analyst
  - pm
  - architect
  - qa
  - dev
outputs:
  - docs/planning/$feature_name/prd.md
  - docs/planning/$feature_name/architecture.md
  - docs/planning/$feature_name/test-strategy.md
  - docs/planning/$feature_name/implementation-plan.md
EOF
        
        # Run BMAD orchestrator
        print_status "Launching BMAD orchestrator..."
        npx bmad-method orchestrator --workflow docs/planning/$feature_name/workflow.yaml || {
            print_warning "BMAD orchestrator not available, creating templates instead..."
            create_planning_templates $feature_name
        }
    else
        print_status "Running quick planning..."
        create_planning_templates $feature_name
    fi
    
    print_success "Planning complete for $feature_name"
    print_status "Next steps:"
    echo "  1. Review planning docs in docs/planning/$feature_name/"
    echo "  2. Update PRD and architecture as needed"
    echo "  3. Run 'npm run bmad:implement -- --feature $feature_name' to start development"
}

# Function to create planning templates
create_planning_templates() {
    local feature_name=$1
    
    # PRD Template
    cat > docs/planning/$feature_name/prd.md << 'EOF'
# Product Requirements Document: [Feature Name]

## Overview
[Brief description of the feature]

## Background
- **Context**: How this fits into Nova Agent
- **Problem**: What problem does this solve
- **Users**: Who will use this feature

## Functional Requirements
1. **FR1**: [Requirement]
   - Integration with MemoryManager
   - API endpoint design
   - Authentication/authorization

2. **FR2**: [Requirement]
   - Data models
   - Business logic
   - Error handling

## Non-Functional Requirements
1. **Performance**: Response time < 200ms
2. **Scalability**: Support 10k concurrent users
3. **Security**: JWT/RBAC, input validation
4. **Reliability**: 99.9% uptime
5. **Testing**: 95% code coverage

## API Design
```python
@app.post("/api/v1/[feature]", dependencies=[role_required(Role.user)])
async def create_[feature](
    request: [Feature]Request,
    current_user: User = Depends(get_current_user),
    memory: MemoryManager = Depends(get_memory_manager)
):
    """[Feature] endpoint following Nova Agent patterns."""
    pass
```

## Data Models
```python
class [Feature]Model(BaseModel):
    """[Feature] data model."""
    id: str
    user_id: str
    # Add fields
```

## Success Metrics
- [ ] All functional requirements implemented
- [ ] 95% test coverage achieved
- [ ] Performance benchmarks met
- [ ] Security review passed
EOF

    # Architecture Template
    cat > docs/planning/$feature_name/architecture.md << 'EOF'
# Architecture Design: [Feature Name]

## System Overview
```mermaid
graph TD
    A[Client] -->|JWT| B[API Gateway]
    B --> C[Nova Agent API]
    C --> D[Feature Module]
    D --> E[MemoryManager]
    D --> F[Background Tasks]
    E --> G[Redis/Storage]
    F --> H[Celery]
```

## Component Design

### API Layer
- Endpoint: `/api/v1/[feature]`
- Authentication: JWT middleware
- Authorization: RBAC checks
- Validation: Pydantic models

### Business Logic
- Module: `nova/[feature].py`
- Async operations
- Error handling with custom exceptions
- Logging and metrics

### Data Layer
- Integration with MemoryManager
- Caching strategy
- Data persistence approach

### Background Processing
- Celery tasks for async operations
- Task scheduling
- Result storage

## Integration Points
1. **MemoryManager**: Store feature data
2. **Auth System**: JWT/RBAC integration
3. **Task Manager**: Background processing
4. **Monitoring**: Prometheus metrics

## Security Considerations
- Input validation
- Rate limiting
- Audit logging
- Data encryption

## Scalability Design
- Horizontal scaling support
- Caching layers
- Database optimization
- Load balancing ready
EOF

    # Test Strategy Template
    cat > docs/planning/$feature_name/test-strategy.md << 'EOF'
# Test Strategy: [Feature Name]

## Test Coverage Goals
- Target: 95% code coverage
- Unit tests: All functions
- Integration tests: All API endpoints
- Performance tests: Critical paths

## Test Categories

### Unit Tests
```python
# tests/test_[feature].py
def test_[feature]_creation():
    """Test [feature] creation logic."""
    pass

def test_[feature]_validation():
    """Test input validation."""
    pass
```

### Integration Tests
```python
# tests/test_[feature]_api.py
def test_create_[feature]_endpoint(client, auth_headers):
    """Test POST /api/v1/[feature]."""
    pass
```

### Performance Tests
- Load testing with 1000 concurrent requests
- Response time benchmarks
- Memory usage profiling

## Mock Strategy
- External services mocked
- Database fixtures
- Authentication mocks

## CI/CD Integration
- Tests run on every commit
- Coverage reports generated
- Performance regression checks
EOF

    # Implementation Plan Template
    cat > docs/planning/$feature_name/implementation-plan.md << 'EOF'
# Implementation Plan: [Feature Name]

## Phase 1: Setup (Day 1)
- [ ] Create feature branch
- [ ] Set up module structure
- [ ] Create initial tests

## Phase 2: Core Implementation (Days 2-3)
- [ ] Implement data models
- [ ] Create business logic
- [ ] Add MemoryManager integration

## Phase 3: API Development (Days 4-5)
- [ ] Create API endpoints
- [ ] Add authentication/authorization
- [ ] Implement validation

## Phase 4: Testing (Days 6-7)
- [ ] Write comprehensive unit tests
- [ ] Create integration tests
- [ ] Performance testing

## Phase 5: Documentation (Day 8)
- [ ] API documentation
- [ ] Update README
- [ ] Create user guide

## Phase 6: Review & Deploy (Days 9-10)
- [ ] Code review
- [ ] Security review
- [ ] Deploy to staging
- [ ] Production deployment

## Success Criteria
- [ ] All tests passing
- [ ] 95% coverage achieved
- [ ] Documentation complete
- [ ] Performance benchmarks met
EOF
}

# Main script logic
main() {
    local feature_name=""
    local planning_type="quick"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --feature)
                feature_name="$2"
                shift 2
                ;;
            --full)
                planning_type="full"
                shift
                ;;
            --help)
                echo "Usage: $0 --feature <feature-name> [--full]"
                echo "  --feature: Name of the feature to plan"
                echo "  --full: Run full BMAD planning workflow (default: quick)"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Validate feature name
    if [ -z "$feature_name" ]; then
        print_warning "Feature name required. Usage: $0 --feature <feature-name>"
        exit 1
    fi
    
    # Run planning
    run_bmad_planning "$feature_name" "$planning_type"
}

# Run main function
main "$@"
