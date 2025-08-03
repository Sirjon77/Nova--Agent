#!/usr/bin/env bash
# Fails CI if legacy memory helpers are still referenced outside the shim/tests.

set -euo pipefail

echo "🔍 Checking for legacy memory helper usage..."

# Check for direct save_to_memory and query_memory calls
LEGACY_CALLS=$(grep -R --line-number -E 'save_to_memory\(|query_memory\(|fetch_from_memory\(' . \
  | grep -v 'memory/legacy_adapter.py' \
  | grep -v 'tests/' \
  | grep -v 'memory.py' \
  | grep -v '.git/' \
  | grep -v 'node_modules/' \
  | grep -v '__pycache__/' \
  | grep -v '.pytest_cache/' \
  | grep -v '*.md' \
  | grep -v '*.txt' \
  | grep -v '*.json' \
  | grep -v '*.yaml' \
  | grep -v '*.yml' \
  | grep -v 'CODE_QUALITY_IMPROVEMENTS.md' \
  | grep -v 'FINAL_ENHANCEMENT_SUMMARY.md' \
  | grep -v '_execute_query_memory' || true)

if [ -n "$LEGACY_CALLS" ]; then
    echo "❌ Legacy memory helpers detected:"
    echo "$LEGACY_CALLS"
    echo ""
    echo "❌ Legacy memory helpers detected – migrate to MemoryManager."
    echo "Files using legacy memory functions:"
    echo "$LEGACY_CALLS" | cut -d: -f1 | sort | uniq
    exit 1
fi

# Check for legacy imports
LEGACY_IMPORTS=$(grep -R --line-number -E '^[[:space:]]*from memory import|^[[:space:]]*import memory' . \
  | grep -v 'memory/legacy_adapter.py' \
  | grep -v 'tests/' \
  | grep -v 'memory.py' \
  | grep -v '.git/' \
  | grep -v 'node_modules/' \
  | grep -v '__pycache__/' \
  | grep -v '.pytest_cache/' \
  | grep -v '*.md' \
  | grep -v '*.txt' \
  | grep -v '*.json' \
  | grep -v '*.yaml' \
  | grep -v '*.yml' \
  | grep -v 'CODE_QUALITY_IMPROVEMENTS.md' \
  | grep -v 'FINAL_ENHANCEMENT_SUMMARY.md' \
  | grep -v 'ENHANCEMENTS_IMPLEMENTED.md' \
  | grep -v 'scripts/check_legacy_memory_calls.sh' || true)

if [ -n "$LEGACY_IMPORTS" ]; then
    echo "❌ Legacy memory imports detected:"
    echo "$LEGACY_IMPORTS"
    echo ""
    echo "❌ Legacy memory imports detected – migrate to MemoryManager."
    echo "Files importing legacy memory module:"
    echo "$LEGACY_IMPORTS" | cut -d: -f1 | sort | uniq
    exit 1
fi

echo "✅ No legacy memory helpers found."
echo "✅ Memory integration is clean and unified!" 