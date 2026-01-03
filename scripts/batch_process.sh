#!/bin/bash
# Batch processing example for KYC PoV pipeline

set -e

# Configuration
INPUT_DIR="${1:-data/uploads}"
OUTPUT_DIR="${2:-outputs}"

# Colors for output
GREEN='\033[0.32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting batch KYC processing...${NC}"
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Ensure virtualenv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not detected. Attempting to activate...${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo "Error: .venv not found. Run 'uv venv .venv && source .venv/bin/activate && uv pip install -e .' first."
        exit 1
    fi
fi

# Check if API key is set
if [ -z "$FIREWORKS_API_KEY" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    else
        echo "Error: FIREWORKS_API_KEY not set and .env not found."
        exit 1
    fi
fi

# Run batch processing
echo -e "${GREEN}Processing all images in $INPUT_DIR...${NC}"
kyc-pov --batch "$INPUT_DIR" --output "$OUTPUT_DIR"

# Display summary
if [ -f "$OUTPUT_DIR/summary.json" ]; then
    echo ""
    echo -e "${GREEN}Batch processing complete!${NC}"
    echo "Summary:"
    python3 << EOF
import json
with open("$OUTPUT_DIR/summary.json") as f:
    data = json.load(f)
    print(f"  Total: {data['total']}")
    print(f"  Success: {data['success']}")
    print(f"  Manual Review: {data['manual_review']}")
    print(f"  Retry Upload: {data['retry']}")
    print(f"  Errors: {data['error']}")
EOF
else
    echo -e "${YELLOW}Warning: summary.json not found${NC}"
fi

