#!/bin/bash
# Coverage Report Generator
# Generates coverage reports and optionally opens the HTML report in browser

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Coverage Report Generator${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Run tests with coverage
echo -e "${YELLOW}Running tests with coverage...${NC}"
python -m pytest tests/ \
    --cov=dataclass_config \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    --cov-fail-under=90

echo ""
echo -e "${GREEN}✓ Coverage reports generated:${NC}"
echo "  • Terminal: Shown above"
echo "  • HTML:     htmlcov/index.html"
echo "  • XML:      coverage.xml"
echo ""

# Check if we should open the browser
if [ "$1" = "--open" ] || [ "$1" = "-o" ]; then
    echo -e "${BLUE}Opening HTML report in browser...${NC}"

    # Try different browser commands
    if command -v xdg-open &> /dev/null; then
        xdg-open htmlcov/index.html
    elif command -v open &> /dev/null; then
        open htmlcov/index.html
    elif command -v firefox &> /dev/null; then
        firefox htmlcov/index.html &
    elif command -v google-chrome &> /dev/null; then
        google-chrome htmlcov/index.html &
    else
        echo -e "${YELLOW}Could not find a browser to open the report.${NC}"
        echo "Please open htmlcov/index.html manually."
    fi
else
    echo "Tip: Run with --open or -o to open HTML report in browser"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
