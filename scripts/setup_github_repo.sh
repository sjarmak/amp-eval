#!/bin/bash

# GitHub Repository Setup Script for Amp Evaluation Suite
# Run this script to create and configure a GitHub repository

set -e

echo "🚀 Setting up GitHub repository for Amp Evaluation Suite"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_NAME="amp-eval"
REPO_DESCRIPTION="Production-grade AI model evaluation platform for continuous monitoring, cost optimization, and data-driven model selection"
REPO_VISIBILITY="private"  # Change to "public" if desired

echo -e "${BLUE}Repository Configuration:${NC}"
echo "  Name: $REPO_NAME"
echo "  Description: $REPO_DESCRIPTION"
echo "  Visibility: $REPO_VISIBILITY"
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo "Please install it from: https://cli.github.com/"
    echo "Or run: brew install gh"
    exit 1
fi

# Check if user is logged in to GitHub CLI
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to GitHub CLI${NC}"
    echo "Please login first:"
    echo "  gh auth login"
    exit 1
fi

echo -e "${GREEN}✅ GitHub CLI is configured${NC}"

# Get GitHub username
GITHUB_USER=$(gh api user --jq .login)
echo -e "${BLUE}GitHub user: $GITHUB_USER${NC}"

# Confirm repository creation
echo ""
read -p "Create repository $GITHUB_USER/$REPO_NAME? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Repository creation cancelled"
    exit 0
fi

# Create GitHub repository
echo -e "${BLUE}📦 Creating GitHub repository...${NC}"
if [ "$REPO_VISIBILITY" = "public" ]; then
    gh repo create "$REPO_NAME" \
        --description "$REPO_DESCRIPTION" \
        --public \
        --clone=false \
        --source=.
else
    gh repo create "$REPO_NAME" \
        --description "$REPO_DESCRIPTION" \
        --private \
        --clone=false \
        --source=.
fi

echo -e "${GREEN}✅ Repository created: https://github.com/$GITHUB_USER/$REPO_NAME${NC}"

# Add remote if it doesn't exist
if ! git remote get-url origin &> /dev/null; then
    echo -e "${BLUE}🔗 Adding remote origin...${NC}"
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    echo -e "${GREEN}✅ Remote origin added${NC}"
else
    echo -e "${YELLOW}⚠️  Remote origin already exists${NC}"
fi

# Push to GitHub
echo -e "${BLUE}📤 Pushing to GitHub...${NC}"
git push -u origin master

echo -e "${GREEN}✅ Code pushed to GitHub${NC}"

# Set up repository settings
echo -e "${BLUE}⚙️  Configuring repository settings...${NC}"

# Enable issues and projects
gh repo edit --enable-issues --enable-projects

# Add topics/tags
gh repo edit --add-topic "ai-evaluation"
gh repo edit --add-topic "model-benchmarking"  
gh repo edit --add-topic "cost-optimization"
gh repo edit --add-topic "openai-evals"
gh repo edit --add-topic "python"
gh repo edit --add-topic "streamlit"

echo -e "${GREEN}✅ Repository settings configured${NC}"

# Create initial labels for issues
echo -e "${BLUE}🏷️  Creating issue labels...${NC}"

# Delete default labels that we don't need
gh label delete "good first issue" --yes || true
gh label delete "help wanted" --yes || true

# Create custom labels
gh label create "priority-critical" --color "800080" --description "Critical priority issues" || true
gh label create "priority-high" --color "ff0000" --description "High priority issues" || true
gh label create "priority-medium" --color "ffaa00" --description "Medium priority issues" || true
gh label create "priority-low" --color "36a64f" --description "Low priority issues" || true

gh label create "cost-impact-high" --color "ff6b6b" --description "High cost impact (>$100/month)" || true
gh label create "cost-impact-medium" --color "feca57" --description "Medium cost impact ($20-100/month)" || true
gh label create "cost-impact-low" --color "48dbfb" --description "Low cost impact (<$20/month)" || true

gh label create "feedback" --color "7f8c8d" --description "User feedback and suggestions" || true
gh label create "evaluation-suite" --color "9b59b6" --description "Related to evaluation suites" || true
gh label create "model-integration" --color "3498db" --description "Model integration and support" || true
gh label create "dashboard" --color "e67e22" --description "Dashboard and UI related" || true
gh label create "security" --color "e74c3c" --description "Security related issues" || true

echo -e "${GREEN}✅ Issue labels created${NC}"

# Create branch protection rules (optional)
read -p "Set up branch protection rules? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🛡️  Setting up branch protection...${NC}"
    
    # Note: This requires admin permissions and might fail for personal repos
    gh api repos/:owner/:repo/branches/master/protection \
        --method PUT \
        --field required_status_checks='{"strict":true,"contexts":["ci"]}' \
        --field enforce_admins=true \
        --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
        --field restrictions=null \
        --silent || echo -e "${YELLOW}⚠️  Could not set up branch protection (requires admin access)${NC}"
fi

# Create initial project for tracking
echo -e "${BLUE}📋 Creating project for issue tracking...${NC}"
gh project create --title "Amp Evaluation Development" --body "Track development progress and feature requests" || true

# Create GitHub repository secrets (if in organization)
echo ""
echo -e "${YELLOW}📝 Manual setup required:${NC}"
echo ""
echo "1. Repository Secrets (Settings > Secrets and variables > Actions):"
echo "   - OPENAI_API_KEY: Your OpenAI API key"
echo "   - ANTHROPIC_API_KEY: Your Anthropic API key"
echo "   - SLACK_WEBHOOK_URL: Webhook for Slack notifications"
echo ""
echo "2. Environment Variables for Production:"
echo "   - Set up production deployment environment"
echo "   - Configure cost monitoring alerts"
echo "   - Set up Slack integration"
echo ""
echo "3. Enable GitHub Actions:"
echo "   - GitHub Actions should auto-enable with CI workflows"
echo "   - Review .github/workflows/ files"
echo ""
echo "4. Set up team access (if organization):"
echo "   - Add team members with appropriate permissions"
echo "   - Configure code review requirements"
echo ""

# Final summary
echo ""
echo -e "${GREEN}🎉 GitHub repository setup complete!${NC}"
echo ""
echo -e "${BLUE}Repository URL:${NC} https://github.com/$GITHUB_USER/$REPO_NAME"
echo -e "${BLUE}Clone URL:${NC} git clone https://github.com/$GITHUB_USER/$REPO_NAME.git"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Share repository with team members"
echo "2. Set up production deployment"
echo "3. Configure monitoring and alerts"
echo "4. Start evaluating your AI models!"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "- Quick Start: docs/QUICK_START.md"
echo "- Contributing: docs/CONTRIBUTING.md"
echo "- Dashboard Guide: docs/DASHBOARD_GUIDE.md"
echo ""
echo "Happy evaluating! 🚀"
