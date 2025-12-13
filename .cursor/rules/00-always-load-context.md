# ALWAYS LOAD CONTEXT FIRST

## 🚨 CRITICAL: Load Flattened Codebase

Before ANY code analysis or implementation:

1. **ALWAYS load**: `docs/flattened-codebase.xml`
2. **This file contains**: The latest snapshot of the entire Nova Agent codebase
3. **Auto-updated**: On every commit (old version deleted, new one created)
4. **Optimized**: Only includes core implementation files to reduce size

## If Context Seems Outdated

Run: `npm run update-context`

## Why This Matters

- Ensures you have the latest code structure
- Prevents conflicts with recent changes
- Provides full context for better implementations
- Automatically maintained by Git hooks

## File Location
```
docs/flattened-codebase.xml
```

This is the FIRST thing to load before any Nova Agent work!
