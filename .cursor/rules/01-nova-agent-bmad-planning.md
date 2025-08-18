# Nova Agent BMAD Planning Integration

## Automated Planning Workflow

### When Starting New Features
1. **Automatically trigger BMAD planning** for any feature request
2. **Use Nova Agent context** from `docs/flattened-codebase.xml`
3. **Follow BMAD workflow**: Analyst → PM → Architect → QA → Dev

### Planning Phase Automation

#### 1. Feature Request Analysis
When user requests a new feature:
- **Analyst Agent**: Analyze existing Nova Agent architecture
- Consider: Memory management, API patterns, authentication flow
- Output: Project brief aligned with Nova Agent standards

#### 2. PRD Generation
- **PM Agent**: Create PRD with Nova Agent specifications
- Include: JWT/RBAC requirements, API design, memory integration
- Reference: Existing patterns in codebase

#### 3. Architecture Design
- **Architect Agent**: Design following Nova Agent patterns
- Use: Existing module structure, async patterns, error handling
- Output: Architecture doc compatible with current system

#### 4. Test Strategy
- **QA Agent**: Create test plan maintaining 95% coverage
- Include: Unit tests, integration tests, performance tests
- Follow: Nova Agent testing patterns

### Automated Triggers

#### Git Hook Integration
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Auto-run BMAD planning for new features
if git diff --cached --name-only | grep -E "(feat|feature)/" > /dev/null; then
  echo "New feature detected, running BMAD planning..."
  npm run bmad:plan-feature
fi
```

#### VS Code Task Runner
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "BMAD Plan Feature",
      "type": "shell",
      "command": "npm run bmad:plan-feature",
      "group": "build",
      "presentation": {
        "reveal": "always"
      },
      "problemMatcher": []
    }
  ]
}
```

### Nova Agent Specific Context

#### Memory Management
- All features must integrate with `MemoryManager`
- Use existing memory patterns from `utils/memory_manager.py`
- Maintain backward compatibility with legacy memory system

#### API Design
- Follow FastAPI patterns in `nova/api/app.py`
- Include JWT authentication via `auth/jwt_middleware.py`
- Add RBAC checks using `auth/rbac.py`

#### Async Patterns
- Use async/await for all I/O operations
- Follow patterns from existing async modules
- Integrate with task manager for background jobs

#### Testing Standards
- Maintain 95% coverage requirement
- Use pytest fixtures from `tests/conftest.py`
- Mock external services appropriately

### Workflow Commands

#### Quick Planning
```bash
# For small features
npm run bmad:quick-plan -- --feature "feature-name"
```

#### Full Planning
```bash
# For major features
npm run bmad:full-plan -- --feature "feature-name"
```

#### Architecture Review
```bash
# Review existing architecture before changes
npm run bmad:arch-review
```

### Integration Points

1. **Pre-commit**: Validate planning docs exist
2. **PR Template**: Include planning doc references
3. **CI Pipeline**: Check planning compliance
4. **Code Review**: Verify implementation matches plan

### BMAD Agent Directives for Nova Agent

#### @analyst
- Load `docs/flattened-codebase.xml` first
- Analyze existing patterns before suggesting new ones
- Consider multi-tenant architecture constraints

#### @pm
- Reference Nova Agent's existing features
- Maintain backward compatibility requirements
- Include performance and scalability considerations

#### @architect
- Use established Nova Agent design patterns
- Integrate with existing services (Redis, Celery, etc.)
- Design for horizontal scalability

#### @qa
- Ensure 95% test coverage
- Include chaos testing considerations
- Test multi-tenant isolation

#### @dev
- Follow Nova Agent coding standards
- Use type hints and proper documentation
- Implement with existing utility functions
