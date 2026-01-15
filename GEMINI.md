# GEMINI.md

This file provides guidance to Gemini CLI when working with this scientific article writing system.

## System Overview

This is an **automated scientific article writing system** that uses specialized AI workflows to transform literature analysis into publication-ready manuscripts. The system supports meteorology, machine learning, and climate science papers written in Russian academic language.

## Core Workflow

```
PDFs → Analyzer → JSON → Writers (sequential) → Sections → Reviewer → Feedback → Editor → Final Article
```

**Key principle**: Each stage is a specialized workflow with clear inputs, outputs, and triggers. Stages run based on file dependencies and completion status.

## Directory Structure

```
scientific-article-system/
├── .gemini/
│   ├── commands/                  # Custom slash commands
│   │   ├── analyze.toml          # /analyze - Literature analysis
│   │   ├── write-intro.toml      # /write-intro
│   │   ├── write-methods.toml    # /write-methods
│   │   ├── write-results.toml    # /write-results
│   │   ├── experiment-reproducer.toml    # /experiment-reproducer
│   │   ├── write-discussion.toml # /write-discussion
│   │   ├── review.toml           # /review - Peer review
│   │   └── edit.toml             # /edit - Final editing
│   ├── workflows/                 # Workflow instruction templates
│   │   ├── analyzer.md
│   │   ├── writer-intro.md
│   │   ├── writer-methods.md
│   │   ├── writer-results.md
│   │   ├── experiment-reproducer.md
│   │   ├── writer-discussion.md
│   │   ├── reviewer.md
│   │   └── editor.md
│   └── settings.json              # Gemini CLI configuration
│
├── input/
│   └── research_config.md         # Research topic, scope, requirements
│
├── papers/                        # Source PDFs for analysis
│   ├── vaswani2017.pdf
│   ├── lam2023_graphcast.pdf
│   └── ...
│
├── analysis/
│   └── papers_analyzed.json       # Structured literature analysis
│
├── sections/                      # Modular article sections
│   ├── introduction.md
│   ├── methods.md
│   ├── results.md
│   └── discussion.md
│
├── review/
│   └── feedback.json              # Peer review with scores
│
├── WORKFLOW_ORCHESTRATION.md      # Orchestration guide
├── FINAL_ARTICLE.md               # Camera-ready manuscript
├── CHANGES.md                     # Editorial change log
└── GEMINI.md                      # This file
```

## Workflow Stages

### Stage 1: Analyzer
**Command**: `gemini /analyze` or `gemini "analyze papers"`
**Input**: `papers/*.pdf`, `input/research_config.md`
**Output**: `analysis/papers_analyzed.json` (structured JSON with relevance scores)
**Model**: gemini-2.5-pro
**Next**: Enables all writer stages

**Workflow instructions**: Load from `.gemini/workflows/analyzer.md`

### Stage 2: Writer Workflows (Must run sequentially)

#### writer-intro
**Command**: `gemini /write-intro`
**Trigger**: `analysis/papers_analyzed.json` exists
**Input**: `@analysis/papers_analyzed.json`, `@input/research_config.md`
**Output**: `sections/introduction.md` (500-700 words, Russian)
**Dependencies**: analyzer

#### writer-methods
**Command**: `gemini /write-methods`
**Trigger**: `sections/introduction.md` exists
**Input**: `@analysis/papers_analyzed.json`, `@input/research_config.md`
**Output**: `sections/methods.md` (400-600 words, Russian)
**Dependencies**: writer-intro

#### writer-results
**Command**: `gemini /write-results`
**Trigger**: `sections/methods.md` exists (reads metric definitions)
**Input**: `@analysis/papers_analyzed.json`, `@sections/methods.md`
**Output**: `sections/results.md` (400-600 words, Russian)
**Dependencies**: writer-methods

#### writer-discussion
**Command**: `gemini /write-discussion`
**Trigger**: All other sections exist
**Input**: `@sections/*.md`, `@analysis/papers_analyzed.json`
**Output**: `sections/discussion.md` (500-700 words, Russian)
**Dependencies**: writer-intro, writer-methods, writer-results

### Stage 3: Reviewer
**Command**: `gemini /review`
**Trigger**: All 4 main sections complete (intro, methods, results, discussion)
**Input**: `@sections/*.md`, optional `@bibliography.bib`
**Output**: `review/feedback.json` (scores + issues + recommendation)
**Blocking conditions**:
- Any section missing or <200 words
- Placeholder text ([TODO], [TBD])
**Next**: editor (if accept/minor_revisions) OR rewrite (if major_revisions)

### Stage 4: Editor
**Command**: `gemini /edit`
**Trigger**: `review/feedback.json` with status = accept/minor_revisions
**Input**: `@sections/*.md`, `@review/feedback.json`, optional `@bibliography.bib`
**Output**: `FINAL_ARTICLE.md`, `CHANGES.md`, `abstract.md`, `metadata.json`
**Responsibilities**:
- Apply 100% of critical issues
- Apply 90%+ of minor improvements
- Format references (IEEE numerical)
- Generate IMRAD abstract (150-250 words)
- Quality assurance checks

## Role and Behavior

You are an **orchestrator** for scientific article generation. Your responsibilities:

1. **Check preconditions** before executing any workflow stage
2. **Load context files** using @ syntax (`@analysis/papers_analyzed.json`)
3. **Execute workflows** by loading instructions from `.gemini/workflows/`
4. **Validate outputs** after each stage completion
5. **Guide the user** through the sequential process
6. **Track state** using file existence and content validation

### Core Principles

- **Sequential execution**: Unlike Claude's parallel Task(), Gemini runs stages one at a time
- **Context awareness**: Always load relevant files with @ before processing
- **Validation first**: Check file existence and quality before proceeding
- **Russian output**: All article content in formal Russian academic style
- **Transparency**: Log all stage transitions and validation results

## Orchestration Logic

### Starting a New Article

**User command**: `gemini "write article on [topic]"` or `gemini /start`

**Orchestration steps**:

```bash
# Step 1: Validate setup
if [ ! -f input/research_config.md ]; then
  echo "❌ Missing research_config.md. Creating template..."
  # Create template
fi

if [ -z "$(ls papers/*.pdf 2>/dev/null)" ]; then
  echo "❌ No PDFs found in papers/. Please add source papers."
  exit 1
fi

# Step 2: Run analyzer
echo "🔍 Stage 1/6: Analyzing literature..."
gemini /analyze

# Step 3: Validate analysis output
if [ ! -f analysis/papers_analyzed.json ]; then
  echo "❌ Analysis failed. Check papers/ directory."
  exit 1
fi

# Step 4: Write introduction
echo "✍️ Stage 2/6: Writing introduction..."
gemini /write-intro

# Step 5: Write methods
echo "⚙️ Stage 3/6: Writing methods..."
gemini /write-methods

# Step 6: Write results
echo "📊 Stage 4/6: Writing results..."
gemini /write-results

# Step 7: Write discussion
echo "💬 Stage 5/6: Writing discussion..."
gemini /write-discussion

# Step 8: Review
echo "🔎 Stage 6/6: Peer review..."
gemini /review

# Step 9: Check review outcome
status=$(jq -r '.recommendation' review/feedback.json)
if [ "$status" = "accept" ] || [ "$status" = "minor_revisions" ]; then
  echo "✅ Review passed. Generating final article..."
  gemini /edit
  echo "🎉 FINAL_ARTICLE.md ready for submission!"
else
  echo "⚠️ Major revisions needed. Check review/feedback.json"
  exit 1
fi
```

### Execution Strategy

**Phase 1**: analyzer (sequential)
**Phase 2**: writer-intro → writer-methods → writer-results → writer-discussion (sequential pipeline)
**Phase 3**: reviewer (sequential)
**Phase 4**: editor (sequential)

**Rationale**: Gemini CLI executes workflows sequentially. Each stage depends on the previous stage's output. Use checkpoint saving after each stage for fault tolerance.

### File Dependencies Graph

```
papers/*.pdf ──┐
               ├──> analysis/papers_analyzed.json ──> sections/introduction.md
input/research_config.md ──────────────────────────────────────────┘
                                                            │
                                                            v
                                                   sections/methods.md
                                                            │
                                                            v
                                                   sections/results.md
                                                            │
                                                            v
                                                   sections/discussion.md
                                                            │
                                                            v
                                                   review/feedback.json
                                                            │
                                                            v
                                             FINAL_ARTICLE.md + CHANGES.md
```

## Custom Commands Setup

Create these files in `.gemini/commands/`:

### `.gemini/commands/analyze.toml`
```toml
description = "Analyze literature PDFs and extract structured data"

prompt = """
Load workflow instructions from @.gemini/workflows/analyzer.md

Context files to load:
- @input/research_config.md
- @papers/ (all PDFs)

Tasks:
1. Read all PDFs in papers/ directory
2. Extract: title, authors, year, methodology, key results, relevance scores
3. Structure output as JSON per analyzer.md specifications
4. Save to analysis/papers_analyzed.json
5. Validate JSON structure before completion

Output format: Follow template in analyzer.md exactly.
Language: Russian for summaries, English for metadata.
"""
```

### `.gemini/commands/write-intro.toml`
```toml
description = "Write introduction section (500-700 words, Russian)"

prompt = """
Load workflow instructions from @.gemini/workflows/writer-intro.md

Preconditions:
- analysis/papers_analyzed.json must exist
- input/research_config.md must exist

Context files to load:
- @analysis/papers_analyzed.json
- @input/research_config.md

Tasks:
1. Load structured analysis data
2. Write introduction following IMRAD structure
3. Include 15-20 citations from analyzed papers
4. Ensure 500-700 words in Russian academic style
5. Self-assess quality (target: 8-10/10)
6. Save to sections/introduction.md

Language: Russian (formal academic)
Citation style: IEEE numerical,, etc.[1][2]
"""
```

### `.gemini/commands/review.toml`
```toml
description = "Peer review complete draft with quality scoring"

prompt = """
Load workflow instructions from @.gemini/workflows/reviewer.md

Preconditions check:
- All 4 sections must exist: introduction.md, methods.md, results.md, discussion.md
- Each section must have >200 words
- No [TODO], [TBD], or placeholder text

Context files to load:
- @sections/introduction.md
- @sections/methods.md
- @sections/results.md
- @sections/discussion.md
- @bibliography.bib (if exists)

Tasks:
1. Evaluate each section on 10-point scale
2. Check coherence, citations, reproducibility
3. Identify Type A (critical), Type B (minor), Type C (major) issues
4. Provide recommendation: accept / minor_revisions / major_revisions / reject
5. Save structured feedback to review/feedback.json

Output: JSON with scores, issues arrays, and recommendation.
"""
```

## Language Requirements

- **Article content**: Russian academic language (formal, GOST standards)
- **Workflow instructions**: English (internal)
- **Metadata/logs**: English (for debugging)
- **Code/commands**: English

## Workflow Invocation Pattern

### Using slash commands

```bash
# Start from project root
cd scientific-article-system

# Interactive mode
gemini
> /analyze
> /write-intro
> /write-methods
> /write-results
> /write-discussion
> /review
> /edit

# Non-interactive mode (automation)
gemini /analyze --yolo
gemini /write-intro --yolo
gemini /review --output review/feedback.json
```

### Loading context files

Always use @ syntax for file references:
```
@analysis/papers_analyzed.json  # Load entire file
@sections/                      # Load all files in directory
```

### Checking preconditions

Before invoking any workflow, validate:

```bash
# Example: Before /write-results
check_preconditions() {
  [ ! -f analysis/papers_analyzed.json ] && echo "❌ Run /analyze first" && return 1
  [ ! -f sections/methods.md ] && echo "❌ Run /write-methods first" && return 1
  [ $(wc -w < sections/methods.md) -lt 200 ] && echo "❌ Methods too short" && return 1
  echo "✅ Preconditions met"
  return 0
}
```

## Quality Standards

All sections must meet these thresholds before proceeding:

- **Word counts**: Introduction (500-700), Methods (400-600), Results (400-600), Discussion (500-700)
- **Citations**: Introduction (15-20), Methods (10-15), Discussion (10-15)
- **Quality scores**: All sections must score ≥8/10 on self-assessment
- **Language**: Russian academic style with formal terminology
- **Reproducibility**: Methods must enable exact replication

## Error Handling

- **Missing analysis**: STOP, display: "Run /analyze first to process papers/"
- **Insufficient papers**: WARN user, request literature expansion
- **Quality score <8**: AUTO-REVISE once, then request human feedback
- **Reviewer reject**: HALT workflow, report fundamental issues
- **Editor blocks**: Flag Type C issues requiring new experiments/data

## Status Tracking

Maintain workflow state using file existence checks:

```bash
# Check completion status
check_status() {
  echo "📊 Workflow Status:"
  [ -f analysis/papers_analyzed.json ] && echo "✅ Analysis complete" || echo "⬜ Analysis pending"
  [ -f sections/introduction.md ] && echo "✅ Introduction complete" || echo "⬜ Introduction pending"
  [ -f sections/methods.md ] && echo "✅ Methods complete" || echo "⬜ Methods pending"
  [ -f sections/results.md ] && echo "✅ Results complete" || echo "⬜ Results pending"
  [ -f sections/discussion.md ] && echo "✅ Discussion complete" || echo "⬜ Discussion pending"
  [ -f review/feedback.json ] && echo "✅ Review complete" || echo "⬜ Review pending"
  [ -f FINAL_ARTICLE.md ] && echo "✅ Final article ready" || echo "⬜ Final article pending"
}
```

## Best Practices

1. **Always check file existence** before loading context with @
2. **Use checkpoints** after each stage for fault tolerance
3. **Validate outputs** immediately after each workflow completes
4. **Log all transitions** with timestamps for debugging
5. **Sequential execution** - do not skip stages
6. **Never skip reviewer** - it catches critical issues before final editing
7. **Document all changes** in CHANGES.md for transparency
8. **Self-assess quality** in each writer stage (8-10/10 target)

## Configuration: `.gemini/settings.json`

```json
{
  "contextFileName": ["GEMINI.md", "WORKFLOW_ORCHESTRATION.md"],
  "model": {
    "name": "gemini-2.5-pro",
    "temperature": 0.7
  },
  "yolo": false,
  "web": {
    "enabled": true,
    "search": true
  },
  "checkpoints": {
    "enabled": true,
    "directory": ".gemini/checkpoints"
  }
}
```

## Quick Start Example

User: `gemini "write article on ML for weather forecasting"`

```bash
# Automatic orchestration
cd scientific-article-system

# Step 0: Validate setup
if [ ! -d papers ] || [ -z "$(ls papers/*.pdf 2>/dev/null)" ]; then
  echo "❌ Add PDFs to papers/ directory first"
  exit 1
fi

# Step 1: Analyze
gemini "Load @papers/ and @input/research_config.md. Execute /analyze workflow."

# Step 2: Write sections sequentially
gemini /write-intro
gemini /write-methods
gemini /write-results
gemini /write-discussion

# Step 3: Review
gemini /review

# Step 4: Edit (if review passed)
if jq -e '.recommendation | IN("accept", "minor_revisions")' review/feedback.json; then
  gemini /edit
  echo "✅ FINAL_ARTICLE.md ready!"
else
  echo "⚠️ Review feedback requires attention"
  jq '.issues' review/feedback.json
fi
```

## Differences from Claude System

| Aspect | Claude (MCP) | Gemini CLI |
|--------|-------------|------------|
| **Agent invocation** | Task() with subagent parameter | Slash commands + workflow files |
| **Parallelization** | Native parallel Task() calls | Sequential with checkpoint saving |
| **Context loading** | Automatic in Projects | Explicit @ syntax |
| **Custom commands** | Agent definitions in .claude/ | TOML commands in .gemini/commands/ |
| **State tracking** | Agent status API | File existence checks |
| **Workflow files** | Agents in .claude/agents/ | Workflows in .gemini/workflows/ |

## Troubleshooting

**"Analysis JSON not found"**
→ Run `gemini /analyze` first

**"Section word count too low"**
→ Revise with: `gemini "expand @sections/[name].md to meet 500-word minimum"`

**"Review failed with reject"**
→ Check `review/feedback.json` for Type A issues, may require new experiments

**"Citations missing"**
→ Ensure `@analysis/papers_analyzed.json` loaded in context

**"Russian language errors"**
→ Add to prompt: "Formal Russian academic style per GOST 7.0.11-2011"

See `WORKFLOW_ORCHESTRATION.md` for detailed stage specifications and templates.
