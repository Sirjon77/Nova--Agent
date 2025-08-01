# NovaAgent v4.2 – Tier A⁺/S Upgrade

**Generated:** 2025-06-30T00:41:48.628800 UTC

This patch implements the 10‑step ladder upgrades:

| # | Feature | File / Service |
|---|---------|----------------|
| 1 | Memory ranking & pruning | `utils/memory_ranker.py` (uses LangChain ContextualCompressionRetriever - swap in later) |
| 2 | Tool outcome feedback | `utils/tool_wrapper.py` |
| 3 | Multi‑step planner | `agents/multi_step_planner.py` |
| 4 | Cost‑aware model switch | Patched into `utils/model_router.py` |
| 5 | Hierarchical parent agent | `agents/parent_agent.py` |
| 6 | Lightweight self‑repair | `utils/self_repair.py` |
| 7 | Action confidence scoring | `utils/confidence.py` |
| 8 | Persistent vector KB | `utils/knowledge_publisher.py` |
| 9 | Governance & telemetry | `utils/telemetry.py` (LangSmith / Grafana) |
| 10| Vision plug‑in | `agents/vision_agent.py` (GPT‑4o vision stub) |

## Library / Service Recommendations

| Need | Lightweight | Enterprise |
|------|-------------|------------|
| Memory ranking | `langchain.retrievers.ContextualCompressionRetriever` | LlamaIndex + PGVector |
| Hierarchical agents | CrewAI, Autogen | Jina AI AgentCloud |
| Telemetry | OpenAI Traces, LangSmith | Datadog APM, Honeycomb |
| Self‑repair | Guidance “fix-it” pattern | Devin‑style patch loops |
| Vision endpoint | GPT‑4o vision (OpenAI) | LLaVA‑Next self‑host |

**Quick diff test:**

```bash
pytest tests      # includes new tests for memory prune soon
```
