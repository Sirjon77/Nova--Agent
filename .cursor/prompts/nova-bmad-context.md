# Nova Agent BMAD Context

## Automatic Context Loading
When working on Nova Agent, always load:
1. `docs/flattened-codebase.xml` - Full codebase context
2. `.cursor/rules/00-nova-agent.md` - Core development rules
3. `.cursor/rules/01-nova-agent-bmad-planning.md` - BMAD planning integration

## BMAD Agents Available
- **@analyst** - Market research, competitive analysis, project briefs
- **@pm** - Product requirements, user stories, feature prioritization
- **@architect** - System design, API architecture, integration planning
- **@qa** - Test strategies, quality gates, performance criteria
- **@dev** - Implementation, code review, optimization
- **@ux-expert** - UI/UX design, user flows, accessibility
- **@sm** - Sprint planning, story breakdown, team coordination
- **@po** - Product ownership, stakeholder alignment, roadmap

## Quick Commands
```bash
# Plan a new feature
npm run new-feature -- --feature <name>

# Quick planning for small changes
npm run plan -- --feature <name>

# Review architecture before changes
npm run bmad:arch-review

# Update codebase context
npm run bmad:flatten
```

## Nova Agent Patterns to Follow
1. **Memory Integration**: All features must use MemoryManager
2. **API Design**: Follow FastAPI patterns with JWT/RBAC
3. **Async First**: Use async/await for all I/O operations
4. **Testing**: Maintain 95% coverage with comprehensive tests
5. **Documentation**: Update docs for all user-facing changes

## Planning Workflow
1. Create feature branch: `git checkout -b feature/<name>`
2. Run planning: `npm run new-feature -- --feature <name>`
3. Review generated docs in `docs/planning/<name>/`
4. Update PRD and architecture as needed
5. Get approval before implementation
6. Implement following the plan
7. Ensure all tests pass before merge

## Integration Checkpoints
- [ ] Planning docs created and reviewed
- [ ] Architecture aligns with Nova Agent patterns
- [ ] Test strategy maintains 95% coverage
- [ ] Implementation follows the approved plan
- [ ] All CI/CD checks pass
- [ ] Documentation updated
