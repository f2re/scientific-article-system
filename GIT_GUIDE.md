# Git Usage Guide for Scientific Article System

## What Gets Tracked in Git

### ✅ Always Tracked

**Agent Definitions & Configuration:**
- `.claude/agents/*.md` - All agent definitions
- `input/research_config.md` - Research configuration
- `CLAUDE.md`, `MULTI_AGENT_PLAN.md` - System documentation

**Source Code:**
- `tools/article_search/*.py` - Search tool modules
- `tools/search_papers.py` - Main CLI tool
- `tools/README.md` - Tool documentation

**Article Content:**
- `sections/*.md` - Article sections (intro, methods, results, discussion)
- `FINAL_ARTICLE.md` - Final published article
- `CHANGES.md` - Editorial change log
- `abstract.md` - Article abstract

**Catalogs & Reports (Final versions):**
- `papers/papers_catalog.json` - Curated paper catalog
- `papers/SEARCH_REPORT.md` - Literature search report
- `papers/SEARCH_SUMMARY.md` - Quick summary
- `papers/search_plan.md` - Search strategy
- `papers/links_only/*.txt` - Paper link collections

**Analysis:**
- `analysis/papers_analyzed.json` - Literature analysis
- `review/feedback.json` - Peer review feedback

**Documentation:**
- `README.md` - Main documentation
- `REFACTORING_SUMMARY.md` - Development notes
- `GIT_GUIDE.md` - This file

### ❌ Never Tracked (In .gitignore)

**Downloaded PDFs:**
- `papers/downloaded/*.pdf` - Too large, can be re-downloaded
- `papers/temp/` - Temporary storage

**Python Artifacts:**
- `__pycache__/` - Compiled Python files
- `*.pyc`, `*.pyo` - Bytecode
- `venv/`, `.venv/` - Virtual environments

**Generated Scripts:**
- `papers/*.py` - Agent-generated temporary scripts
- `papers/*.log` - Search logs

**Temporary Files:**
- `*.tmp`, `*.cache`, `*.bak` - Temporary files
- `*~`, `*.swp` - Editor backups
- `papers/*_temp.json` - Temporary catalogs

**IDE Files:**
- `.vscode/`, `.idea/` - Editor settings
- `*.code-workspace` - Workspace files

**OS Files:**
- `.DS_Store` - macOS metadata
- `Thumbs.db` - Windows thumbnails

**Credentials:**
- `.env`, `*.key` - API keys and secrets
- `credentials.json` - Authentication files

**Personal Notes:**
- `PRIVATE_NOTES.md` - Your private notes
- `notes/private/` - Private directory

## Initial Git Setup

### 1. Initialize Repository

```bash
cd /Users/meteo/Documents/WWW/scientific-article-system

# Initialize git
git init

# Check status
git status
```

### 2. First Commit

```bash
# Add all tracked files
git add .

# Check what will be committed
git status

# Make initial commit
git commit -m "Initial commit: Scientific article writing system

- Agent definitions for literature search and writing
- Unified article search tools
- Configuration and documentation
- Multi-agent orchestration framework"
```

### 3. Create Remote Repository

```bash
# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/scientific-article-system.git

# Push to remote
git branch -M main
git push -u origin main
```

## Typical Git Workflow

### Starting New Research

```bash
# Create feature branch
git checkout -b research/atmospheric-profiles

# Update research config
# Edit input/research_config.md

# Commit configuration
git add input/research_config.md
git commit -m "Add research config for atmospheric profile study"
```

### After Literature Search

```bash
# Search creates: papers_catalog.json, SEARCH_REPORT.md, downloaded/*.pdf
# Only catalog and reports are tracked, PDFs are ignored

git add papers/papers_catalog.json
git add papers/SEARCH_REPORT.md
git add papers/SEARCH_SUMMARY.md
git add papers/search_plan.md

git commit -m "Add literature search results: 24 papers cataloged"
```

### After Analysis

```bash
git add analysis/papers_analyzed.json
git commit -m "Add literature analysis for top 20 papers"
```

### After Writing Sections

```bash
git add sections/introduction.md
git add sections/methods.md
git commit -m "Add Introduction and Methods sections"

# Continue for other sections
git add sections/results.md
git add sections/discussion.md
git commit -m "Add Results and Discussion sections"
```

### After Review

```bash
git add review/feedback.json
git commit -m "Add peer review feedback"
```

### Final Article

```bash
git add FINAL_ARTICLE.md
git add CHANGES.md
git add abstract.md
git add metadata.json
git commit -m "Publish final article: Atmospheric vertical profiles"

git tag -a v1.0 -m "First publication"
git push origin main --tags
```

## Working with Branches

### Feature Branches

```bash
# New research topic
git checkout -b research/new-topic

# Work on research...
git add ...
git commit -m "..."

# Merge when complete
git checkout main
git merge research/new-topic

# Delete branch
git branch -d research/new-topic
```

### Development Branches

```bash
# Tool improvements
git checkout -b dev/improve-search-tool

# Make changes to tools/
git add tools/article_search/relevance_scorer.py
git commit -m "Improve relevance scoring algorithm"

# Test thoroughly, then merge
git checkout main
git merge dev/improve-search-tool
```

## Sharing Research with Collaborators

### Clone Repository

```bash
git clone https://github.com/yourusername/scientific-article-system.git
cd scientific-article-system
```

### Download PDFs Separately

Since PDFs are not tracked, share them separately:

```bash
# Create archive of PDFs
tar -czf papers_pdfs.tar.gz papers/downloaded/

# Share via cloud storage or transfer service
# Recipients extract:
tar -xzf papers_pdfs.tar.gz
```

### Pull Latest Changes

```bash
git pull origin main
```

## Best Practices

### 1. Commit Messages

**Good:**
```bash
git commit -m "Add atmospheric profile search results

- 24 papers cataloged from arXiv and Semantic Scholar
- Average relevance: 9.0/10
- Focus on radiosonde extrapolation methods"
```

**Bad:**
```bash
git commit -m "update"
git commit -m "stuff"
```

### 2. Commit Frequency

- Commit after each major milestone
- Don't commit broken/incomplete work to main
- Use branches for experimental work

### 3. What to Commit

**Do commit:**
- Configuration changes
- New agent definitions
- Source code updates
- Final catalogs and reports
- Article sections
- Documentation

**Don't commit:**
- Downloaded PDFs
- Temporary files
- API keys or credentials
- Personal notes
- Generated Python scripts

### 4. File Size Limits

GitHub limits:
- File size: 100 MB max
- Repository size: 1-5 GB recommended

If you have large PDFs:
- Keep them in `.gitignore`
- Use Git LFS (Large File Storage) if needed
- Share via cloud storage

## Git LFS Setup (Optional)

For tracking large files:

```bash
# Install Git LFS
brew install git-lfs  # macOS
# or: apt-get install git-lfs  # Linux

# Initialize in repo
git lfs install

# Track large files
git lfs track "papers/downloaded/*.pdf"
git lfs track "*.h5"

# Add .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"

# Push LFS files
git push origin main
```

## Troubleshooting

### Accidentally Committed Large File

```bash
# Remove from Git but keep locally
git rm --cached papers/downloaded/large_file.pdf

# Add to .gitignore
echo "papers/downloaded/large_file.pdf" >> .gitignore

# Commit removal
git commit -m "Remove large PDF from tracking"
```

### Clean Up Repository

```bash
# Remove untracked files
git clean -fd

# Remove ignored files
git clean -fdX
```

### Check Ignored Files

```bash
# See what's being ignored
git status --ignored

# Check if specific file is ignored
git check-ignore -v papers/downloaded/paper.pdf
```

## Summary

**Track in Git:**
- Source code and tools
- Agent configurations
- Article content
- Catalogs and reports (JSON/MD)
- Documentation

**Don't track:**
- Downloaded PDFs
- Temporary files
- Python artifacts
- IDE settings
- Personal notes

**Use branches for:**
- New research topics
- Tool development
- Experimental features

**Commit messages should:**
- Be descriptive
- Explain why, not just what
- Reference issues/tasks if applicable

---

**Quick Reference:**

```bash
# Common commands
git status                 # Check status
git add <file>            # Stage files
git commit -m "message"   # Commit changes
git push                  # Push to remote
git pull                  # Pull from remote
git log --oneline         # View history
git diff                  # View changes
```
