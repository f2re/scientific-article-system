# CLAUDE.md

This file provides guidance to Claude Code when working with this scientific article writing system.

## System Overview

This is an **automated scientific article writing system** that uses specialized AI agents to transform literature analysis into publication-ready manuscripts. The system supports meteorology, machine learning, and climate science papers written in Russian academic language.

## Core Workflow

```
PDFs → Analyzer → JSON → Writers (parallel) → Sections → Reviewer → Feedback → Editor → Final Article
```

**Key principle**: Each agent is a specialist with clear inputs, outputs, and triggers. Agents run sequentially or in parallel based on dependencies.

## Directory Structure

```
scientific-article-system/
├── .claude/
│   └── agents/                    # Agent definitions (7 specialists)
│       ├── analyzer.md            # Literature analysis
│       ├── writer-intro.md        # Introduction writer
│       ├── writer-methods.md      # Methods writer
│       ├── writer-results.md      # Results writer
│       ├── writer-discussion.md   # Discussion writer
│       ├── reviewer.md            # Peer review agent
│       └── editor.md              # Final editing
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
├── MULTI_AGENT_PLAN.md            # Orchestration guide
├── FINAL_ARTICLE.md               # Camera-ready manuscript
├── CHANGES.md                     # Editorial change log
└── CLAUDE.md                      # This file
```

## Agent Coordination

### 1. Analyzer Agent
**Trigger**: New PDFs in `papers/` OR user requests "analyze papers"
**Input**: `papers/*.pdf`, `input/research_config.md`
**Output**: `analysis/papers_analyzed.json` (structured JSON with relevance scores)
**Model**: sonnet
**Next**: Enables all writer agents

### 2. Writer Agents (Can run in parallel)

#### writer-intro
**Trigger**: `analysis/papers_analyzed.json` exists
**Input**: `analysis/papers_analyzed.json`, `input/research_config.md`
**Output**: `sections/introduction.md` (500-700 words, Russian)
**Dependencies**: analyzer

#### writer-methods
**Trigger**: `analysis/papers_analyzed.json` exists
**Input**: `analysis/papers_analyzed.json`, `input/research_config.md`
**Output**: `sections/methods.md` (400-600 words, Russian)
**Dependencies**: analyzer

#### writer-results
**Trigger**: `sections/methods.md` exists (reads metric definitions)
**Input**: `analysis/papers_analyzed.json`, `sections/methods.md`
**Output**: `sections/results.md` (400-600 words, Russian)
**Dependencies**: analyzer, writer-methods

#### writer-discussion
**Trigger**: All other sections exist
**Input**: All sections + `analysis/papers_analyzed.json`
**Output**: `sections/discussion.md` (500-700 words, Russian)
**Dependencies**: writer-intro, writer-methods, writer-results

### 3. Reviewer Agent
**Trigger**: All 4 main sections complete (intro, methods, results, discussion)
**Input**: `sections/*.md`, optional `bibliography.bib`
**Output**: `review/feedback.json` (scores + issues + recommendation)
**Blocking conditions**:
- Any section missing or <200 words
- Placeholder text ([TODO], [TBD])
**Next**: editor (if accept/minor_revisions) OR rewrite (if major_revisions)

### 4. Editor Agent
**Trigger**: `review/feedback.json` with status = accept/minor_revisions
**Input**: `sections/*.md`, `review/feedback.json`, optional `bibliography.bib`
**Output**: `FINAL_ARTICLE.md`, `CHANGES.md`, `abstract.md`, `metadata.json`
**Responsibilities**:
- Apply 100% of critical issues
- Apply 90%+ of minor improvements
- Format references (IEEE numerical)
- Generate IMRAD abstract (150-250 words)
- Quality assurance checks

## Orchestration Guidelines

### Starting a New Article

**User command**: "Write article on [topic]"

**Orchestrator steps**:
1. Check `input/research_config.md` exists (or create it)
2. Check `papers/` has PDFs (or request them)
3. Invoke `analyzer` agent → produces `analysis/papers_analyzed.json`
4. Invoke writer agents **in parallel**:
   - `writer-intro` (depends only on analysis)
   - `writer-methods` (depends only on analysis)
5. After methods complete, invoke `writer-results`
6. After intro/methods/results complete, invoke `writer-discussion`
7. After all sections complete, invoke `reviewer`
8. If reviewer status = accept/minor_revisions, invoke `editor`
9. If reviewer status = major_revisions, flag issues for user
10. If reviewer status = reject, halt and report fundamental problems

### Parallel Execution Strategy

**Phase 1 (sequential)**: analyzer only
**Phase 2 (parallel)**: writer-intro + writer-methods
**Phase 3 (sequential)**: writer-results (waits for methods)
**Phase 4 (sequential)**: writer-discussion (waits for all)
**Phase 5 (sequential)**: reviewer (waits for all sections)
**Phase 6 (sequential)**: editor (waits for review)

**Rationale**: Writers can work independently on intro/methods since they share common inputs (analysis JSON). Results needs methods to understand metrics. Discussion needs everything for synthesis.

### File Dependencies Graph

```
papers/*.pdf ──┐
               ├──> analysis/papers_analyzed.json ──┬──> sections/introduction.md ──┐
input/research_config.md ──────────────────────────┼──> sections/methods.md ────────┼─┐
                                                     │                                │ │
                                                     └──> sections/results.md ←───────┘ │
                                                            │                           │
                                                            v                           │
                                                     sections/discussion.md ←───────────┘
                                                            │
                                                            v
                                                     review/feedback.json
                                                            │
                                                            v
                                                     FINAL_ARTICLE.md + CHANGES.md
```

## Language Requirements

- **Article content**: Russian academic language (formal, GOST standards)
- **Agent instructions**: English (internal workflow)
- **Metadata/logs**: English (for clarity)
- **Code/commands**: English

## Agent Invocation Patterns

### Using Task tool

```
Task(
  subagent_type="analyzer",  # NOT the filename
  description="Analyze literature papers",
  prompt="Analyze all PDFs in papers/ directory and extract methodology, results, and relevance scores for research on [topic]. Output to analysis/papers_analyzed.json"
)
```

**Note**: Use the `name` field from agent frontmatter (e.g., `scientific-paper-analyzer`), NOT the filename.

### Checking Preconditions

Before invoking an agent, verify:
1. Required input files exist
2. Input files have sufficient content (>200 words for sections)
3. No blocking conditions (placeholders, missing data)

Example precondition check:
```bash
# Before invoking reviewer
for file in sections/{introduction,methods,results,discussion}.md; do
  [ ! -f "$file" ] && echo "Missing $file" && exit 1
  [ $(wc -w < "$file") -lt 200 ] && echo "$file too short" && exit 1
done
```

## Quality Standards

All sections must meet these thresholds before proceeding:

- **Word counts**: Introduction (500-700), Methods (400-600), Results (400-600), Discussion (500-700)
- **Citations**: Introduction (15-20), Methods (10-15), Discussion (10-15)
- **Quality scores**: All sections must score ≥8/10 on self-assessment
- **Language**: Russian academic style with formal terminology
- **Reproducibility**: Methods must enable exact replication

## Error Handling

- **Missing analysis**: STOP, request analyzer first
- **Insufficient papers**: WARN user, request literature expansion
- **Quality score <8**: AUTO-REVISE once, then request human feedback
- **Reviewer reject**: HALT workflow, report fundamental issues to user
- **Editor blocks**: Flag Type C issues requiring new experiments/data

## Status Tracking

Maintain workflow state:
- `analysis_complete`: papers_analyzed.json exists
- `sections_complete`: All 4 main sections exist and meet quality threshold
- `review_complete`: feedback.json exists
- `ready_for_submission`: FINAL_ARTICLE.md exists and passes validation

Check status before agent invocation to avoid redundant work.

## Best Practices

1. **Always check file existence** before reading
2. **Use Grep for targeted searches** in large JSON files
3. **Validate outputs** after each agent completes
4. **Log all agent transitions** for debugging
5. **Run writers in parallel** when possible to save time
6. **Never skip reviewer** - it catches critical issues
7. **Document all changes** in CHANGES.md for transparency

## Quick Start Example

User: "Write article on ML for weather forecasting"

```bash
# Step 1: Check setup
[ ! -f input/research_config.md ] && echo "Create research config first"
[ -z "$(ls papers/*.pdf 2>/dev/null)" ] && echo "Add PDFs to papers/"

# Step 2: Run analyzer
Task(subagent="analyzer", prompt="Analyze all papers in papers/ for ML weather forecasting")

# Step 3: Wait for analysis/papers_analyzed.json
# Step 4: Run writers in parallel
Task(subagent="writer-intro", prompt="Write introduction")
Task(subagent="writer-methods", prompt="Write methods")

# Step 5: Run results writer
Task(subagent="writer-results", prompt="Write results")

# Step 6: Run discussion writer
Task(subagent="writer-discussion", prompt="Write discussion")

# Step 7: Review
Task(subagent="reviewer", prompt="Review complete draft")

# Step 8: Edit and finalize
Task(subagent="editor", prompt="Apply review feedback and create final article")
```

See `MULTI_AGENT_PLAN.md` for detailed orchestration logic.
