# BMAD Automation Guide for Nova Agent

## 🤖 Automated Planning Workflow

The Nova Agent project now has fully automated BMAD planning integration. This guide explains how to use it.

## Quick Start

### Plan a New Feature
```bash
# Quick planning (creates templates)
npm run plan -- --feature <feature-name>

# Full BMAD workflow
npm run new-feature -- --feature <feature-name>
```

### Example
```bash
# Create API rate limiting feature
npm run plan -- --feature api-rate-limiting

# This creates:
# - docs/planning/api-rate-limiting/brief.md
# - docs/planning/api-rate-limiting/prd.md
# - docs/planning/api-rate-limiting/architecture.md
# - docs/planning/api-rate-limiting/test-strategy.md
# - docs/planning/api-rate-limiting/implementation-plan.md
```

## 🔧 Automation Features

### 1. Cursor Integration
- **Custom Rules**: `.cursor/rules/01-nova-agent-bmad-planning.md`
- **Context Loading**: Automatically loads `docs/flattened-codebase.xml`
- **Agent Directives**: Specific instructions for each BMAD agent

### 2. VS Code Tasks (Cursor Compatible)
Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux) and type "Tasks: Run Task":
- **BMAD: Plan New Feature** - Interactive feature planning
- **BMAD: Full Planning Workflow** - Complete BMAD process
- **BMAD: Architecture Review** - Review existing architecture
- **BMAD: Update Context** - Refresh flattened codebase

### 3. Git Hooks
When you commit on a feature branch (`feature/*` or `feat/*`):
- Automatically creates planning docs if they don't exist
- Adds planning docs to your commit
- Updates commit message with planning references

### 4. NPM Scripts
```json
{
  "scripts": {
    "plan": "./scripts/bmad-planning.sh",
    "new-feature": "npm run bmad:full-plan",
    "bmad:plan-feature": "./scripts/bmad-planning.sh",
    "bmad:quick-plan": "./scripts/bmad-planning.sh",
    "bmad:full-plan": "./scripts/bmad-planning.sh --full",
    "bmad:arch-review": "cat docs/flattened-codebase.xml | npx bmad-method orchestrator --task architecture-review",
    "bmad:implement": "npx bmad-method orchestrator --task implement"
  }
}
```

## 📋 Planning Templates

### PRD Template
- Functional requirements with Nova Agent integration
- Non-functional requirements (95% coverage, JWT/RBAC)
- API design following FastAPI patterns
- Success metrics

### Architecture Template
- System overview with mermaid diagrams
- Component design aligned with Nova Agent
- Integration points (MemoryManager, Auth, Tasks)
- Security and scalability considerations

### Test Strategy Template
- 95% coverage target
- Unit, integration, and performance tests
- Mock strategy for external services
- CI/CD integration

### Implementation Plan Template
- 10-day phased approach
- Daily tasks and deliverables
- Success criteria checklist

## 🎯 Workflow Steps

### 1. Start Feature
```bash
git checkout -b feature/my-new-feature
```

### 2. Run Planning
```bash
npm run new-feature -- --feature my-new-feature
```

### 3. Review & Update Docs
- Edit `docs/planning/my-new-feature/*.md`
- Align with Nova Agent patterns
- Get approval from team

### 4. Implement
```bash
npm run bmad:implement -- --feature my-new-feature
```

### 5. Test & Deploy
- Ensure 95% coverage
- All CI checks pass
- Deploy following Nova Agent procedures

## 🛡️ Nova Agent Specific Rules

### Memory Integration
All features MUST integrate with `MemoryManager`:
```python
from utils.memory_manager import get_global_memory_manager

memory = get_global_memory_manager()
await memory.add_memory("category", data)
```

### API Patterns
Follow existing FastAPI patterns:
```python
@app.post("/api/v1/feature", dependencies=[role_required(Role.user)])
async def create_feature(
    request: FeatureRequest,
    current_user: User = Depends(get_current_user)
):
    pass
```

### Testing Requirements
Maintain 95% coverage:
```python
def test_feature():
    # Unit test
    pass

def test_feature_api(client, auth_headers):
    # Integration test
    pass
```

## 🚀 Best Practices

1. **Always run planning** before implementing features
2. **Update planning docs** as requirements change
3. **Follow the templates** but customize for your feature
4. **Get approval** on PRD/Architecture before coding
5. **Maintain test coverage** at 95% or higher

## 📁 Directory Structure
```
docs/planning/
├── <feature-name>/
│   ├── brief.md              # Feature overview
│   ├── prd.md               # Product requirements
│   ├── architecture.md      # Technical design
│   ├── test-strategy.md     # Testing approach
│   ├── implementation-plan.md # Development plan
│   └── context.xml          # Codebase snapshot
```

## 🔄 Continuous Improvement

The automation will evolve based on usage. Key areas for enhancement:
1. Integration with actual BMAD orchestrator when available
2. AI-powered PRD generation from brief
3. Automatic test generation from requirements
4. Architecture validation against existing patterns

## 💡 Tips

- Use descriptive feature names (e.g., `user-analytics`, not `ua`)
- Keep planning docs updated throughout development
- Reference planning docs in PR descriptions
- Use BMAD agents in Cursor for assistance

This automation ensures consistent, high-quality feature development following Nova Agent standards and BMAD methodology.
