# GitHub Setup Guide

Complete guide for pushing the CEX/DEX Arbitrage Platform to GitHub and setting up version control.

---

## Prerequisites

- Git installed locally
- GitHub account created
- SSH key configured (recommended) or personal access token

---

## Step 1: Create GitHub Repository

### Option A: Via GitHub Web Interface

1. Go to https://github.com/new
2. Enter repository details:
   - **Name:** `cex-dex-arbitrage` (or your preferred name)
   - **Description:** `Production-grade spot arbitrage system for CEX/DEX price discrepancies`
   - **Visibility:** Private (recommended for trading systems)
   - **Initialize:** Do NOT initialize with README, .gitignore, or license (we already have these)
3. Click "Create repository"

### Option B: Via GitHub CLI

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Linux: See https://github.com/cli/cli#installation

# Authenticate
gh auth login

# Create repository
gh repo create cex-dex-arbitrage --private --description "Production-grade spot arbitrage system"
```

---

## Step 2: Initialize Local Git Repository

From the `/app` directory:

```bash
# Navigate to project root
cd /app

# Initialize git repository (if not already done)
git init

# Verify .gitignore exists and is configured properly
cat .gitignore

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Complete CEX/DEX arbitrage platform

- FastAPI backend with Gemini, Coinbase, Solana connectors
- React frontend with professional operator console
- Real-time WebSocket data streaming
- Signal detection and execution engines
- MongoDB persistence with async repositories
- Risk management with kill-switches
- Prometheus metrics and observability
- OBSERVE_ONLY mode for safe testing
- Comprehensive documentation and runbook
"
```

---

## Step 3: Configure Remote and Push

### If Using HTTPS:

```bash
# Add remote (replace USERNAME and REPO_NAME)
git remote add origin https://github.com/USERNAME/cex-dex-arbitrage.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

**Note:** You'll be prompted for your GitHub username and personal access token (not password).

### If Using SSH:

```bash
# Add remote (replace USERNAME)
git remote add origin git@github.com:USERNAME/cex-dex-arbitrage.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 4: Verify Files on GitHub

Check that these key files are present:

- ✅ `/README.md` - Project overview and quick start
- ✅ `/RUNBOOK.md` - Operational procedures
- ✅ `/backend/.env.template` - Environment configuration template
- ✅ `/frontend/.env.template` - Frontend configuration template
- ✅ `/docs/API.md` - API documentation
- ✅ `/docs/GITHUB_SETUP.md` - This guide
- ✅ `/backend/` - Python backend code
- ✅ `/frontend/` - React frontend code
- ✅ `/tests/` - Test files

**Verify Exclusions:**
- ❌ `/backend/.env` - Should NOT be present (contains secrets)
- ❌ `/frontend/.env` - Should NOT be present
- ❌ `/node_modules/` - Should NOT be present
- ❌ `/__pycache__/` - Should NOT be present

---

## Step 5: Protect Sensitive Information

### Verify .env Files Are Ignored

```bash
# Check git status - .env files should NOT appear
git status

# If .env files are listed, they're not properly ignored
# Add them to .gitignore:
echo "backend/.env" >> .gitignore
echo "frontend/.env" >> .gitignore
echo "*.env" >> .gitignore

# Remove from git if accidentally committed:
git rm --cached backend/.env
git rm --cached frontend/.env
git commit -m "Remove .env files from version control"
git push
```

### Rotate API Keys (If Exposed)

If you accidentally pushed API keys:

1. **Immediately rotate all keys:**
   - Gemini: https://exchange.gemini.com/settings/api
   - Helius: https://dashboard.helius.dev
   - Coinbase: https://portal.cdp.coinbase.com/access/api

2. **Remove from Git history:**
   ```bash
   # Use BFG Repo-Cleaner or git-filter-branch
   # This is advanced - see GitHub's guide:
   # https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
   ```

3. **Update local .env with new keys**

---

## Step 6: Set Up Branch Protection (Recommended)

### Via GitHub Web Interface:

1. Go to repository **Settings** → **Branches**
2. Click **Add rule** under "Branch protection rules"
3. Configure:
   - **Branch name pattern:** `main`
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass (if CI/CD configured)
   - ✅ Require branches to be up to date
   - ✅ Include administrators (recommended)
4. Save changes

---

## Step 7: Add Collaborators (Optional)

### Via GitHub Web Interface:

1. Go to repository **Settings** → **Collaborators**
2. Click **Add people**
3. Enter GitHub username or email
4. Select permission level:
   - **Read:** View code only
   - **Write:** Push to non-protected branches
   - **Admin:** Full access
5. Send invitation

---

## Step 8: Configure GitHub Secrets (For CI/CD)

If setting up GitHub Actions:

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add secrets:
   - `GEMINI_API_KEY`
   - `GEMINI_API_SECRET`
   - `HELIUS_API_KEY`
   - `MONGO_URL`
   - (Add others as needed)

**Note:** These secrets will be available to GitHub Actions workflows but never exposed in logs.

---

## Step 9: Set Up GitHub Actions (Optional)

Create `.github/workflows/ci.yml`:

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      mongodb:
        image: mongo:7
        ports:
          - 27017:27017
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run linter
        run: |
          cd backend
          ruff check .
      
      - name: Run tests
        run: |
          cd tests
          python -m pytest backend_test.py
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          yarn install
      
      - name: Run linter
        run: |
          cd frontend
          yarn lint
      
      - name: Build
        run: |
          cd frontend
          yarn build
```

Commit and push:
```bash
mkdir -p .github/workflows
# Create ci.yml with content above
git add .github/workflows/ci.yml
git commit -m "Add CI/CD pipeline with GitHub Actions"
git push
```

---

## Step 10: Create Repository Documentation

### Add README Badges

Update `/README.md` with status badges:

```markdown
![Build Status](https://github.com/USERNAME/cex-dex-arbitrage/actions/workflows/ci.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.11-blue)
![Node Version](https://img.shields.io/badge/node-18-green)
![License](https://img.shields.io/badge/license-MIT-blue)
```

### Create CONTRIBUTING.md (Optional)

```markdown
# Contributing to CEX/DEX Arbitrage Platform

## Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test locally
4. Commit with descriptive messages
5. Push to your fork
6. Open a Pull Request

## Code Standards

- **Python:** Follow PEP 8, use type hints
- **JavaScript:** Follow ESLint configuration
- **Commits:** Use conventional commits (feat:, fix:, docs:, etc.)

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Update documentation as needed
```

---

## Common Git Workflows

### Making Changes

```bash
# Create feature branch
git checkout -b feature/add-new-venue

# Make changes
# ...

# Stage changes
git add backend/connectors/new_venue.py

# Commit with descriptive message
git commit -m "feat: Add Kraken exchange connector

- Implement WebSocket connection
- Add orderbook subscription
- Include authentication for private endpoints"

# Push to GitHub
git push origin feature/add-new-venue
```

### Creating Pull Request

1. Go to repository on GitHub
2. Click "Compare & pull request"
3. Fill in PR description:
   - What changes were made
   - Why they were necessary
   - How to test
   - Any breaking changes
4. Request reviewers
5. Wait for approval and merge

### Syncing with Main

```bash
# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main

# Switch back to feature branch
git checkout feature/your-feature

# Rebase on main (or merge)
git rebase main

# Push (may need --force if rebased)
git push origin feature/your-feature --force-with-lease
```

---

## Troubleshooting

### Authentication Failed (HTTPS)

**Error:** `Authentication failed for 'https://github.com/...'`

**Solution:**
1. Generate personal access token: https://github.com/settings/tokens
2. Select scopes: `repo`, `workflow`
3. Use token as password when prompted

### Permission Denied (SSH)

**Error:** `Permission denied (publickey)`

**Solution:**
1. Generate SSH key:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```
2. Add to SSH agent:
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```
3. Add public key to GitHub: https://github.com/settings/keys

### Large Files Rejected

**Error:** `remote: error: File X is 123.45 MB; this exceeds GitHub's file size limit`

**Solution:**
1. Ensure file is in `.gitignore`
2. Remove from git:
   ```bash
   git rm --cached path/to/large/file
   git commit -m "Remove large file"
   ```
3. Use Git LFS for large files if needed

### Accidentally Committed Secrets

**Immediate Actions:**
1. Rotate all exposed credentials immediately
2. Remove from git history (see Step 5)
3. Force push: `git push --force origin main`
4. Verify keys are no longer visible on GitHub

---

## Best Practices

✅ **DO:**
- Commit frequently with descriptive messages
- Use branches for all features and fixes
- Keep .env files out of version control
- Write meaningful commit messages
- Review your own PR before requesting review
- Keep commits atomic (one logical change per commit)

❌ **DON'T:**
- Commit directly to main (use PRs)
- Push broken code
- Include credentials or API keys
- Make massive commits with many changes
- Use generic commit messages ("fixes", "updates")
- Force push to main branch

---

## Additional Resources

- **GitHub Docs:** https://docs.github.com
- **Git Cheat Sheet:** https://education.github.com/git-cheat-sheet-education.pdf
- **Conventional Commits:** https://www.conventionalcommits.org
- **Keeping Secrets Safe:** https://docs.github.com/en/authentication/keeping-your-account-and-data-secure

---

## Repository Links

After setup, update these links in your README.md:

- **Repository:** https://github.com/USERNAME/cex-dex-arbitrage
- **Issues:** https://github.com/USERNAME/cex-dex-arbitrage/issues
- **Pull Requests:** https://github.com/USERNAME/cex-dex-arbitrage/pulls
- **Actions:** https://github.com/USERNAME/cex-dex-arbitrage/actions

---

**Setup Complete!** Your CEX/DEX Arbitrage Platform is now on GitHub with proper version control.
