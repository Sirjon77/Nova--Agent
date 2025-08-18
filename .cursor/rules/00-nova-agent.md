# Nova Agent – Build Rules

## Core Development Principles
- Always read **docs/flattened-codebase.xml** for cross‑file context before editing.
- Follow project guardrails: no hard‑coded secrets; use env/config; add logs + Prometheus metrics on key paths; retries w/ backoff.
- Prefer small PR‑sized changes; include unit tests; keep ≥95% coverage threshold.
- Respect multi‑tenant boundaries (JWT + RBAC) when adding APIs.
- For heavy changes: propose a short plan, then implement one slice at a time.

## Security & Best Practices
- **No hardcoded credentials** - Use environment variables or secret management
- **JWT authentication** required for all API endpoints
- **RBAC enforcement** - Check user permissions before operations
- **Input validation** - Sanitize all user inputs
- **Error handling** - Never expose internal errors to users

## Code Quality Standards
- **Type hints** required for all functions
- **Docstrings** for all public functions and classes
- **Black formatting** - Run before committing
- **Ruff linting** - Fix all issues before PR
- **Test coverage** - Maintain ≥95% coverage

## Architecture Guidelines
- **Modular design** - Keep components loosely coupled
- **Use existing patterns** - Check similar modules before creating new ones
- **Memory management** - Use MemoryManager for all storage operations
- **Async first** - Use async/await for I/O operations
- **Logging** - Use structured logging with appropriate levels

## Testing Requirements
- **Unit tests** for all new functions
- **Integration tests** for API endpoints
- **Mock external services** in tests
- **Test edge cases** and error conditions
- **Performance tests** for critical paths

## Documentation
- **Update README** when adding new features
- **API documentation** for new endpoints
- **Code comments** for complex logic
- **Changelog entries** for user-facing changes
- **Architecture decisions** documented in docs/

## Deployment & Operations
- **Environment-specific configs** - Never commit production secrets
- **Health checks** required for new services
- **Prometheus metrics** for monitoring
- **Graceful shutdown** handling
- **Rate limiting** on public endpoints
