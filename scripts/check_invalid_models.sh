#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Checking for hardcoded invalid model aliases..."

# Search for invalid model aliases in source code
# Exclude the model registry itself and test files
grep -R --line-number -E 'gpt-4o-(mini|vision)' src/ nova/ utils/ backend/ agents/ \
    | grep -v 'model_registry.py' \
    | grep -v 'test_' \
    | grep -v 'tests/' \
    | grep -v 'docs/' \
    | grep -v '.git/' \
    | grep -v 'README' \
    | grep -v 'CHANGELOG' \
    | grep -v 'CODE_QUALITY' \
    | grep -v 'ENHANCEMENTS' \
    | grep -v 'GPT3_PRO' \
    && { 
        echo "❌  Found hard‑coded alias outside registry"
        echo "   Please use the model registry or update to official model names"
        exit 1
    } \
    || echo "✅  No invalid aliases detected in source code"

echo "✅ Model alias check completed successfully" 