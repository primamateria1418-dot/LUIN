#!/bin/bash
# LUIN — Import n8n Workflow Templates
# Usage: bash import-workflows.sh [N8N_BASE_URL]
# Default N8N_BASE_URL: http://localhost:5678

set -euo pipefail

N8N_BASE="${1:-http://localhost:5678}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== LUIN n8n Workflow Importer ==="
echo "Target: $N8N_BASE"
echo ""

# Check connectivity
if ! curl -sf "$N8N_BASE/health" > /dev/null 2>&1; then
    echo "[WARN] Cannot reach $N8N_BASE/health — will try import anyway"
fi

IMPORTED=0
FAILED=0

for workflow_file in "$SCRIPT_DIR"/*.json; do
    filename="$(basename "$workflow_file")"
    echo "Importing: $filename ..."

    # Import via n8n API
    response=$(curl -sf \
        -X POST "$N8N_BASE/api/v1/workflows" \
        -H "Content-Type: application/json" \
        -d @"$workflow_file" 2>&1) || {
        echo "  [FAIL] Could not import $filename"
        FAILED=$((FAILED + 1))
        continue
    }

    # Extract workflow ID from response
    workflow_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'unknown'))" 2>/dev/null || echo "unknown")
    workflow_name=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('name', 'unknown'))" 2>/dev/null || echo "unknown")

    echo "  [OK] Imported: $workflow_name (ID: $workflow_id)"
    IMPORTED=$((IMPORTED + 1))
done

echo ""
echo "=== Import Complete ==="
echo "  Imported: $IMPORTED workflows"
echo "  Failed:   $FAILED workflows"
echo ""
echo "Next steps:"
echo "  1. Open n8n at $N8N_BASE"
echo "  2. Enable each workflow (toggle switch)"
echo "  3. For PostEverywhere workflow, set environment variable:"
echo "     POSTEVERYWHERE_API_KEY in n8n Settings > Credentials"
echo ""
echo "Webhook endpoints:"
for workflow_file in "$SCRIPT_DIR"/*.json; do
    name=$(python3 -c "import json; print(json.load(open('$workflow_file')).get('name', 'unknown'))" 2>/dev/null || echo "unknown")
    path=$(python3 -c "
import json
with open('$workflow_file') as f:
    data = json.load(f)
for node in data.get('nodes', []):
    if node.get('type') == 'n8n-nodes-base.webhook':
        print(node.get('parameters', {}).get('path', ''))
" 2>/dev/null || echo "unknown")
    echo "  $name → $N8N_BASE/webhook/$path"
done
