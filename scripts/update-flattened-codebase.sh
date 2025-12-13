#!/bin/bash
# Update flattened codebase with optimization and cleanup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
MAX_FILE_SIZE_MB=5
TEMP_FILE="docs/flattened-codebase.xml.tmp"

# Function to clean up old file
cleanup_old() {
    if [ -f "docs/flattened-codebase.xml" ]; then
        OLD_SIZE=$(du -h docs/flattened-codebase.xml | cut -f1)
        echo -e "${YELLOW}🗑️  Removing old flattened codebase (${OLD_SIZE})...${NC}"
        rm -f docs/flattened-codebase.xml
    fi
}

# Function to update flattened codebase
update_flattened() {
    echo -e "${YELLOW}🔄 Updating flattened codebase...${NC}"
    
    # Always clean up old file first
    cleanup_old
    
    # Ensure docs directory exists
    mkdir -p docs
    
    # Try multiple methods to update
    
    # Method 1: Direct npx with version
    if npx bmad-method@4.39.0 flatten --input . --output "$TEMP_FILE" 2>/dev/null; then
        mv "$TEMP_FILE" docs/flattened-codebase.xml
        echo -e "${GREEN}✅ Updated using BMAD${NC}"
        return 0
    fi
    
    # Method 2: Fallback - create an optimized flattened version
    echo -e "${YELLOW}⚠️  BMAD flatten not working, creating optimized version...${NC}"
    
    # Create a simple XML with key files
    cat > docs/flattened-codebase.xml << EOF
<?xml version="1.0" encoding="UTF-8"?>
<files>
  <!-- Auto-generated optimized flattened codebase -->
  <metadata>
    <generated>$(date -u +"%Y-%m-%dT%H:%M:%SZ")</generated>
    <method>optimized-fallback</method>
    <description>Contains core implementation files only (excludes tests, docs, configs)</description>
  </metadata>
EOF
    
    # Add only core Python files (exclude tests, migrations, etc.)
    find . -name "*.py" \
        -not -path "./venv/*" \
        -not -path "./.venv/*" \
        -not -path "./__pycache__/*" \
        -not -path "./tests/*" \
        -not -path "./alembic/*" \
        -not -path "./.git/*" \
        -not -path "./docs/*" \
        -not -path "*test*.py" \
        -not -path "*migration*.py" \
        | sort | while read -r file; do
        # Skip very large files
        FILE_SIZE_KB=$(du -k "$file" | cut -f1)
        if [ "$FILE_SIZE_KB" -lt 100 ]; then  # Only include files < 100KB
            echo "  <file path=\"$file\"><![CDATA[" >> docs/flattened-codebase.xml
            cat "$file" >> docs/flattened-codebase.xml
            echo "]]></file>" >> docs/flattened-codebase.xml
        fi
    done
    
    # Add key configuration files
    for config in "package.json" ".cursorrules" "requirements.txt" "pyproject.toml"; do
        if [ -f "$config" ]; then
            echo "  <file path=\"$config\"><![CDATA[" >> docs/flattened-codebase.xml
            cat "$config" >> docs/flattened-codebase.xml
            echo "]]></file>" >> docs/flattened-codebase.xml
        fi
    done
    
    echo "</files>" >> docs/flattened-codebase.xml
    
    echo -e "${GREEN}✅ Created optimized flattened codebase${NC}"
    return 0
}

# Check if called with --watch flag
if [[ "$1" == "--watch" ]]; then
    echo -e "${GREEN}👀 Watching for changes...${NC}"
    
    # Use fswatch if available
    if command -v fswatch &> /dev/null; then
        fswatch -o . -e ".*" -i "\\.py$" -i "\\.js$" -i "\\.json$" | while read f; do
            update_flattened
        done
    else
        echo -e "${RED}❌ fswatch not installed. Install with: brew install fswatch${NC}"
        exit 1
    fi
else
    # One-time update
    update_flattened
fi
