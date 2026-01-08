# Multi-Agent Orchestration Plan

**Scientific Article Writing System**

This document provides comprehensive orchestration logic for coordinating 7 specialized agents to produce publication-ready scientific manuscripts.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Agent Specifications](#agent-specifications)
3. [Workflow Phases](#workflow-phases)
4. [Orchestration Logic](#orchestration-logic)
5. [State Management](#state-management)
6. [Error Handling](#error-handling)
7. [Performance Optimization](#performance-optimization)
8. [Usage Examples](#usage-examples)

---

## System Architecture

### Design Principles

1. **Modularity**: Each agent is a specialist with single responsibility
2. **Loose coupling**: Agents communicate via files, not direct calls
3. **Declarative dependencies**: Inputs/outputs explicitly defined
4. **Fail-fast**: Validate preconditions before agent invocation
5. **Observability**: All transitions logged, state tracked

### Data Flow

```
┌──────────────┐
│ papers/*.pdf │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│ ANALYZER AGENT                      │
│ • Reads PDFs                        │
│ • Scores relevance (1-10)           │
│ • Extracts methodology/results      │
│ • Outputs structured JSON           │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ analysis/papers_analyzed.json       │
│ • Paper metadata                    │
│ • Methodology details               │
│ • Key findings                      │
│ • Quality flags                     │
└──────┬──────────────────────────────┘
       │
       ├─────────────────────────┬──────────────────────┐
       │                         │                      │
       ▼                         ▼                      ▼
┌──────────────┐       ┌──────────────┐      ┌──────────────┐
│ WRITER-INTRO │       │WRITER-METHODS│      │ (can run in  │
│              │       │              │      │  parallel)   │
│ 500-700w     │       │ 400-600w     │      │              │
│ Russian      │       │ Russian      │      │              │
└─────┬────────┘       └──────┬───────┘      └──────────────┘
      │                       │
      │                       ├──────────────────┐
      │                       │                  │
      ▼                       ▼                  ▼
┌─────────────────┐   ┌──────────────────┐   sections/
│sections/intro.md│   │sections/methods  │   introduction.md
└─────────────────┘   │      .md         │   methods.md
                      └──────┬───────────┘
                             │
                             ▼
                      ┌──────────────────┐
                      │ WRITER-RESULTS   │
                      │ • Needs methods  │
                      │   for metrics    │
                      │ 400-600w Russian │
                      └──────┬───────────┘
                             │
                             ▼
                      ┌──────────────────┐
                      │sections/results  │
                      │      .md         │
                      └──────┬───────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
       ┌──────────────┐            sections/intro.md
       │WRITER-DISCUSS│            methods.md
       │              │            results.md
       │• Needs all 3 │
       │500-700w Ru   │
       └──────┬───────┘
              │
              ▼
       ┌──────────────────┐
       │sections/discussion│
       │      .md          │
       └──────┬────────────┘
              │
              ▼
       ┌──────────────────────────────────┐
       │ REVIEWER AGENT                   │
       │ • Validates all 4 sections       │
       │ • Scores 5 criteria (weighted)   │
       │ • Issues critical/minor feedback │
       │ • Decides: accept/revise/reject  │
       └──────┬───────────────────────────┘
              │
              ▼
       ┌──────────────────────┐
       │review/feedback.json  │
       │ • Overall score      │
       │ • Section scores     │
       │ • Critical issues    │
       │ • Accept status      │
       └──────┬───────────────┘
              │
              ▼ (if accept/minor_revisions)
       ┌──────────────────────────────────┐
       │ EDITOR AGENT                     │
       │ • Apply feedback (100% critical) │
       │ • Format references (IEEE)       │
       │ • Generate abstract (IMRAD)      │
       │ • Create final article           │
       └──────┬───────────────────────────┘
              │
              ▼
       ┌──────────────────────┐
       │ FINAL_ARTICLE.md     │
       │ CHANGES.md           │
       │ abstract.md          │
       │ metadata.json        │
       └──────────────────────┘
```

---

## Agent Specifications

### 1. Analyzer Agent

**Agent name**: `scientific-paper-analyzer` (from `.claude/agents/analyzer.md`)

**Purpose**: Transform unstructured PDFs into structured JSON analysis

**Inputs**:
- `papers/*.pdf` (scientific papers)
- `input/research_config.md` (research topic, scope, keywords)

**Outputs**:
- `analysis/papers_analyzed.json` (structured analysis)

**Output schema**:
```json
{
  "title": "string",
  "authors": ["string"],
  "publication": {"venue": "string", "year": int, "doi": "string"},
  "relevance_score": int,  // 1-10
  "methodology": {
    "models": [{"name": "string", "type": "string", "parameters": "string"}],
    "datasets": [{"name": "string", "resolution": "string", "variables": ["string"]}],
    "metrics": ["string"]
  },
  "key_findings": [{"finding": "string", "details": "string"}],
  "quality_flags": ["peer_reviewed", "code_available", "reproducible"],
  "recommendation": "include|exclude",
  "notes": "string"
}
```

**Triggers**:
- New PDFs detected in `papers/`
- User requests: "analyze papers", "analyze literature"

**Success criteria**:
- Valid JSON output
- All papers scored (1-10)
- Methodology extracted for relevant papers (score ≥7)

**Estimated runtime**: 2-5 minutes per paper

---

### 2. Writer-Intro Agent

**Agent name**: `writer-intro` (from `.claude/agents/writer-intro.md`)

**Purpose**: Write Introduction section following funnel structure

**Inputs**:
- `analysis/papers_analyzed.json` (literature analysis)
- `input/research_config.md` (research questions, contributions)

**Outputs**:
- `sections/introduction.md` (500-700 words, Russian)

**Output structure**:
```markdown
***
section: Introduction
word_count: XXX
citations_count: XX
key_themes: [theme1, theme2, ...]
gaps_identified: [gap1, gap2, ...]
quality_self_score: {clarity: 8, completeness: 9, ...}
***

# Introduction

[Context & Relevance (100w)]
[Problem Statement (140w)]
[Literature Review (240w)]
[Goal & Contributions (120w)]
```

**Dependencies**:
- Analyzer agent completed
- `analysis/papers_analyzed.json` exists with ≥10 papers

**Success criteria**:
- Word count: 500-700
- Citations: 15-20
- Quality scores: all ≥8/10
- Russian academic language
- Clear research gap established

**Estimated runtime**: 8-12 minutes

---

### 3. Writer-Methods Agent

**Agent name**: `writer-methods` (from `.claude/agents/writer-methods.md`)

**Purpose**: Write Methods section enabling exact reproducibility

**Inputs**:
- `analysis/papers_analyzed.json` (methodology from literature)
- `input/research_config.md` (experimental design)

**Outputs**:
- `sections/methods.md` (400-600 words, Russian)

**Output structure**:
```markdown
***
section: Methods
word_count: XXX
formulas: X
datasets: [dataset1, dataset2]
baselines: [baseline1, baseline2]
quality_score: X/10
***

## 2. Методы

### 2.1. Обзор подхода
### 2.2. Данные и датасеты
### 2.3. Архитектура модели
### 2.4. Обучение и оптимизация
### 2.5. Инфраструктура
### 2.6. Метрики оценки
### 2.7. Базовые модели
```

**Dependencies**:
- Analyzer agent completed
- `analysis/papers_analyzed.json` exists

**Success criteria**:
- Word count: 400-600
- Formulas: ≥3 (LaTeX format)
- Citations: 10-15
- Reproducibility score: ≥9/10
- Russian academic language

**Estimated runtime**: 10-15 minutes

---

### 4. Writer-Results Agent

**Agent name**: `writer-results` (from `.claude/agents/writer-results.md`)

**Purpose**: Present experimental results objectively (no interpretation)

**Inputs**:
- `analysis/papers_analyzed.json` (benchmark results from literature)
- `sections/methods.md` (metric definitions, baselines)
- `input/research_config.md` (experimental results)

**Outputs**:
- `sections/results.md` (400-600 words, Russian)

**Output structure**:
```markdown
***
section: Results
word_count: XXX
tables_count: X
key_findings: [{metric: value, improvement: X%}]
***

## 3. Результаты

### 3.1. Основные результаты
[Tables with quantitative comparisons]

### 3.2. Разбивка по категориям
[Time horizons, variables, regions, seasons]

### 3.3. Аблационные исследования
[Component contributions]
```

**Dependencies**:
- Writer-methods completed (for metric definitions)
- `sections/methods.md` exists

**Success criteria**:
- Word count: 400-600
- Tables: ≥1 with baselines
- All numbers have units
- Statistical significance included (p-values, CI)
- No interpretation (objective facts only)

**Estimated runtime**: 8-12 minutes

---

### 5. Writer-Discussion Agent

**Agent name**: `writer-discussion` (from `.claude/agents/writer-discussion.md`)

**Purpose**: Interpret results, position work, acknowledge limitations

**Inputs**:
- `sections/introduction.md` (research questions)
- `sections/methods.md` (methodology)
- `sections/results.md` (findings)
- `analysis/papers_analyzed.json` (literature context)

**Outputs**:
- `sections/discussion.md` (500-700 words, Russian)

**Output structure**:
```markdown
***
section: Discussion
word_count: XXX
citations: XX
***

## 4. Обсуждение

### 4.1. Резюме ключевых результатов
### 4.2. Интерпретация результатов
### 4.3. Сравнение с литературой
### 4.4. Значимость исследования
### 4.5. Ограничения
### 4.6. Направления будущей работы
```

**Dependencies**:
- All 3 previous writers completed
- `sections/{introduction,methods,results}.md` exist

**Success criteria**:
- Word count: 500-700
- Citations: 10-15
- Mechanistic explanations (WHY results occurred)
- Honest limitations (≥3 specific)
- Concrete future directions (≥3 actionable)

**Estimated runtime**: 10-15 minutes

---

### 6. Reviewer Agent

**Agent name**: `reviewer` (from `.claude/agents/reviewer.md`)

**Purpose**: Critical peer review with structured feedback

**Inputs**:
- `sections/introduction.md`
- `sections/methods.md`
- `sections/results.md`
- `sections/discussion.md`
- Optional: `bibliography.bib`

**Outputs**:
- `review/feedback.json` (structured review)

**Output schema**:
```json
{
  "overall_assessment": {
    "overall_score": int,  // 0-100
    "weighted_breakdown": {
      "logic_coherence": {"score": int, "weight": 0.25},
      "scientific_correctness": {"score": int, "weight": 0.30},
      "topic_relevance": {"score": int, "weight": 0.20},
      "writing_quality": {"score": int, "weight": 0.15},
      "structure": {"score": int, "weight": 0.10}
    },
    "accept_status": "accept|minor_revisions|major_revisions|reject"
  },
  "critical_issues": [
    {"priority": int, "issue": "string", "action_required": "string", "blocking": bool}
  ],
  "minor_improvements": ["string"],
  "recommendation": {
    "decision": "string",
    "justification": "string"
  }
}
```

**Dependencies**:
- All 4 section writers completed
- Each section ≥200 words
- No placeholders ([TODO], [TBD])

**Blocking conditions** (abort if true):
- Any section missing
- Any section <200 words
- Placeholder text present

**Success criteria**:
- Valid JSON output
- All 5 criteria scored
- Clear accept/reject decision
- Actionable feedback

**Estimated runtime**: 15-20 minutes

---

### 7. Editor Agent

**Agent name**: `editor` (from `.claude/agents/editor.md`)

**Purpose**: Apply review feedback and finalize manuscript

**Inputs**:
- `sections/*.md` (all sections)
- `review/feedback.json` (review results)
- Optional: `bibliography.bib`

**Outputs**:
- `FINAL_ARTICLE.md` (camera-ready manuscript)
- `CHANGES.md` (change log)
- `abstract.md` (standalone IMRAD abstract, 150-250w)
- `references/formatted_references.md` (IEEE numerical)
- `metadata.json` (submission metadata)

**Dependencies**:
- Reviewer completed with status = `accept` OR `minor_revisions`

**Blocking conditions** (flag for user):
- Reviewer status = `major_revisions` OR `reject`
- Critical issues requiring new experiments (Type C)

**Success criteria**:
- 100% critical issues resolved
- ≥90% minor improvements applied
- References formatted (IEEE numerical style)
- Abstract self-contained (150-250w, no citations)
- All validation checks pass

**Estimated runtime**: 12-18 minutes

---

## Workflow Phases

### Phase 1: Analysis (Sequential)

**Objective**: Transform PDFs into structured JSON

**Steps**:
1. Check preconditions
2. Invoke analyzer agent
3. Validate output
4. Proceed to Phase 2

**Precondition checks**:
```bash
# Check research config exists
if [ ! -f input/research_config.md ]; then
    echo "ERROR: Create input/research_config.md first"
    exit 1
fi

# Check PDFs exist
pdf_count=$(ls papers/*.pdf 2>/dev/null | wc -l)
if [ $pdf_count -eq 0 ]; then
    echo "ERROR: Add PDFs to papers/ directory"
    exit 1
fi

echo "Found $pdf_count PDFs. Ready for analysis."
```

**Agent invocation**:
```python
Task(
    subagent_type="scientific-paper-analyzer",
    description="Analyze research papers",
    prompt=f"Analyze all PDFs in papers/ directory. Research topic: {topic}. Extract methodology, datasets, metrics, and results. Score relevance 1-10. Output to analysis/papers_analyzed.json."
)
```

**Output validation**:
```bash
# Check JSON exists and is valid
if [ ! -f analysis/papers_analyzed.json ]; then
    echo "ERROR: Analysis failed, no output"
    exit 1
fi

# Validate JSON syntax
jq empty analysis/papers_analyzed.json || {
    echo "ERROR: Invalid JSON"
    exit 1
}

# Count analyzed papers
paper_count=$(jq 'length' analysis/papers_analyzed.json)
echo "Analysis complete: $paper_count papers analyzed"
```

**Transition criteria**:
- `analysis/papers_analyzed.json` exists
- Valid JSON
- ≥5 papers analyzed (warn if <10)

---

### Phase 2: Writing (Parallel + Sequential)

**Objective**: Generate all 4 section drafts

#### Phase 2a: Parallel Writers (intro + methods)

**Steps**:
1. Launch writer-intro
2. Launch writer-methods (parallel)
3. Wait for both to complete
4. Validate outputs
5. Proceed to Phase 2b

**Agent invocations** (parallel):
```python
# Launch both in parallel
Task(
    subagent_type="writer-intro",
    description="Write Introduction section",
    prompt="Write Introduction section based on analysis/papers_analyzed.json. Follow funnel structure: context → problem → literature → goal. Target: 500-700 words, 15-20 citations, Russian."
)

Task(
    subagent_type="writer-methods",
    description="Write Methods section",
    prompt="Write Methods section based on analysis/papers_analyzed.json. Enable exact reproducibility. Target: 400-600 words, 10-15 citations, Russian."
)
```

**Output validation**:
```bash
for section in introduction methods; do
    file="sections/${section}.md"

    # Check file exists
    [ ! -f "$file" ] && echo "ERROR: $file missing" && exit 1

    # Check word count
    word_count=$(wc -w < "$file")
    if [ $word_count -lt 200 ]; then
        echo "ERROR: $file too short ($word_count words)"
        exit 1
    fi

    echo "$section: $word_count words ✓"
done
```

#### Phase 2b: Results Writer (Sequential)

**Dependencies**: Methods section complete (for metric definitions)

**Agent invocation**:
```python
Task(
    subagent_type="writer-results",
    description="Write Results section",
    prompt="Write Results section. Read metric definitions from sections/methods.md. Present findings objectively with tables, statistics. Target: 400-600 words, Russian."
)
```

#### Phase 2c: Discussion Writer (Sequential)

**Dependencies**: All 3 previous sections complete

**Agent invocation**:
```python
Task(
    subagent_type="writer-discussion",
    description="Write Discussion section",
    prompt="Write Discussion interpreting results from sections/results.md in context of introduction questions and literature. Include limitations, future work. Target: 500-700 words, Russian."
)
```

**Phase 2 completion criteria**:
- All 4 files exist: `sections/{introduction,methods,results,discussion}.md`
- Each file ≥200 words
- No [TODO] placeholders

---

### Phase 3: Review (Sequential)

**Objective**: Critical validation with structured feedback

**Precondition checks**:
```bash
# Verify all sections exist and are complete
for section in introduction methods results discussion; do
    file="sections/${section}.md"

    # Exists?
    [ ! -f "$file" ] && echo "BLOCKING: $file missing" && exit 1

    # Sufficient length?
    words=$(wc -w < "$file")
    [ $words -lt 200 ] && echo "BLOCKING: $file too short ($words words)" && exit 1

    # No placeholders?
    if grep -q '\[TODO\]\|\[TBD\]\|\[FILL\]' "$file"; then
        echo "BLOCKING: Placeholders found in $file"
        exit 1
    fi
done

echo "All sections ready for review ✓"
```

**Agent invocation**:
```python
Task(
    subagent_type="reviewer",
    description="Peer review complete draft",
    prompt="Conduct comprehensive peer review of sections/{introduction,methods,results,discussion}.md. Evaluate 5 criteria (weighted). Output structured feedback to review/feedback.json with accept/reject decision."
)
```

**Output processing**:
```bash
# Check review output exists
[ ! -f review/feedback.json ] && echo "ERROR: Review failed" && exit 1

# Extract decision
status=$(jq -r '.overall_assessment.accept_status' review/feedback.json)
score=$(jq -r '.overall_assessment.overall_score' review/feedback.json)

echo "Review complete: $status (score: $score)"

# Decision routing
case $status in
    "accept"|"minor_revisions")
        echo "Proceeding to editor (Phase 4)"
        ;;
    "major_revisions")
        echo "WARNING: Major revisions required"
        jq -r '.critical_issues[] | "- [\(.priority)] \(.issue)"' review/feedback.json
        echo "Review critical issues before proceeding"
        exit 1
        ;;
    "reject")
        echo "ERROR: Manuscript rejected"
        jq -r '.recommendation.justification' review/feedback.json
        exit 1
        ;;
esac
```

**Transition criteria**:
- `review/feedback.json` exists
- Status = `accept` OR `minor_revisions`

---

### Phase 4: Editing (Sequential)

**Objective**: Apply feedback and finalize manuscript

**Precondition checks**:
```bash
# Check review passed
status=$(jq -r '.overall_assessment.accept_status' review/feedback.json)
if [[ "$status" != "accept" && "$status" != "minor_revisions" ]]; then
    echo "ERROR: Cannot edit without accept/minor_revisions status"
    exit 1
fi

# Count issues to apply
critical_count=$(jq '.critical_issues | length' review/feedback.json)
minor_count=$(jq '.minor_improvements | length' review/feedback.json)

echo "Issues to address: $critical_count critical, $minor_count minor"
```

**Agent invocation**:
```python
Task(
    subagent_type="editor",
    description="Apply review feedback and finalize",
    prompt="Apply feedback from review/feedback.json to sections/*.md. Resolve 100% critical issues, 90%+ minor. Format IEEE references. Generate IMRAD abstract (150-250w). Output FINAL_ARTICLE.md + CHANGES.md."
)
```

**Output validation**:
```bash
# Check all outputs exist
required_files=(
    "FINAL_ARTICLE.md"
    "CHANGES.md"
    "abstract.md"
    "metadata.json"
)

for file in "${required_files[@]}"; do
    [ ! -f "$file" ] && echo "ERROR: Missing $file" && exit 1
    echo "$file ✓"
done

# Validate abstract length
abstract_words=$(wc -w < abstract.md)
if [ $abstract_words -lt 150 ] || [ $abstract_words -gt 250 ]; then
    echo "WARNING: Abstract length $abstract_words words (target: 150-250)"
fi

# Check metadata
jq empty metadata.json && echo "metadata.json valid ✓"

echo "Article finalization complete!"
```

**Success criteria**:
- All required files created
- Abstract: 150-250 words, self-contained, no citations
- CHANGES.md documents all modifications
- metadata.json valid

---

## Orchestration Logic

### State Machine

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌─────────────────────────────┐
│ State: INIT                 │
│ • Check research_config.md  │
│ • Check papers/*.pdf        │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ State: ANALYZING            │
│ • Invoke analyzer           │
│ • Wait for completion       │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ State: ANALYSIS_COMPLETE    │
│ • Validate JSON             │
│ • Check paper count ≥5      │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ State: WRITING_PARALLEL     │
│ • Launch intro + methods    │
│ • Wait for both             │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ State: WRITING_RESULTS      │
│ • Launch results writer     │
│ • Wait for completion       │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ State: WRITING_DISCUSSION   │
│ • Launch discussion writer  │
│ • Wait for completion       │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ State: SECTIONS_COMPLETE    │
│ • Validate all 4 sections   │
│ • Check word counts         │
│ • Check no placeholders     │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ State: REVIEWING            │
│ • Invoke reviewer           │
│ • Wait for completion       │
└────┬────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ State: REVIEW_COMPLETE      │
│ • Parse feedback.json       │
│ • Check accept_status       │
└────┬────────────────────────┘
     │
     ├─ accept/minor_revisions ─┐
     │                          │
     │                          ▼
     │              ┌────────────────────────┐
     │              │ State: EDITING         │
     │              │ • Invoke editor        │
     │              │ • Apply feedback       │
     │              └────┬───────────────────┘
     │                   │
     │                   ▼
     │              ┌────────────────────────┐
     │              │ State: FINALIZED       │
     │              │ • Validate outputs     │
     │              │ • SUCCESS              │
     │              └────────────────────────┘
     │
     ├─ major_revisions ────────┐
     │                           │
     │                           ▼
     │                  ┌────────────────────┐
     │                  │ State: BLOCKED     │
     │                  │ • Report issues    │
     │                  │ • Await user input │
     │                  └────────────────────┘
     │
     └─ reject ─────────────────┐
                                │
                                ▼
                       ┌────────────────────┐
                       │ State: REJECTED    │
                       │ • Report problems  │
                       │ • FAILURE          │
                       └────────────────────┘
```

### Decision Points

#### Decision 1: After Analysis

```python
# Check analysis output quality
papers_analyzed = json.load("analysis/papers_analyzed.json")
relevant_papers = [p for p in papers_analyzed if p["relevance_score"] >= 7]

if len(relevant_papers) < 5:
    print(f"WARNING: Only {len(relevant_papers)} relevant papers (recommend ≥10)")
    # Ask user: continue or add more papers?

if len(papers_analyzed) < 10:
    print(f"WARNING: Only {len(papers_analyzed)} papers total (recommend ≥15)")

# Proceed to writing phase
```

#### Decision 2: After Review

```python
# Parse review decision
feedback = json.load("review/feedback.json")
status = feedback["overall_assessment"]["accept_status"]
score = feedback["overall_assessment"]["overall_score"]

if status == "accept" or status == "minor_revisions":
    print(f"Review passed ({status}, score {score}). Proceeding to editor.")
    invoke_editor()

elif status == "major_revisions":
    critical_issues = feedback["critical_issues"]
    print(f"BLOCKED: {len(critical_issues)} critical issues require resolution:")
    for issue in critical_issues:
        print(f"  [{issue['priority']}] {issue['issue']}")
        print(f"      → {issue['action_required']}")

    # Determine if issues can be auto-fixed
    auto_fixable = all(not issue.get("blocking", False) for issue in critical_issues)

    if auto_fixable:
        print("Attempting automatic fixes...")
        invoke_editor()  # Editor will handle Type A/B issues
    else:
        print("Manual intervention required. Halting workflow.")
        exit(1)

elif status == "reject":
    justification = feedback["recommendation"]["justification"]
    print(f"REJECTED: {justification}")
    print("Fundamental problems detected. Review critical issues:")
    for issue in feedback["critical_issues"]:
        print(f"  - {issue['issue']}")
    exit(1)
```

---

## State Management

### Persistent State

Create `workflow_state.json` to track progress:

```json
{
  "workflow_id": "uuid",
  "started_at": "ISO8601 timestamp",
  "current_phase": "analyzing|writing|reviewing|editing|complete",
  "completed_agents": ["analyzer", "writer-intro", ...],
  "pending_agents": ["writer-discussion", "reviewer", "editor"],
  "file_checksums": {
    "analysis/papers_analyzed.json": "sha256hash",
    "sections/introduction.md": "sha256hash"
  },
  "errors": [
    {"agent": "writer-results", "message": "error details", "timestamp": "..."}
  ],
  "metrics": {
    "total_runtime_seconds": 1234,
    "analyzer_runtime": 180,
    "writer_intro_runtime": 420
  }
}
```

### State Persistence

```python
import json
from datetime import datetime

def save_state(state):
    """Save workflow state to disk"""
    state["updated_at"] = datetime.utcnow().isoformat()
    with open("workflow_state.json", "w") as f:
        json.dump(state, f, indent=2)

def load_state():
    """Load workflow state from disk"""
    try:
        with open("workflow_state.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return initialize_state()

def initialize_state():
    """Create fresh state"""
    return {
        "workflow_id": str(uuid.uuid4()),
        "started_at": datetime.utcnow().isoformat(),
        "current_phase": "init",
        "completed_agents": [],
        "pending_agents": ["analyzer", "writer-intro", "writer-methods",
                           "writer-results", "writer-discussion",
                           "reviewer", "editor"],
        "file_checksums": {},
        "errors": [],
        "metrics": {}
    }
```

### Recovery from Interruption

```python
def resume_workflow():
    """Resume interrupted workflow from saved state"""
    state = load_state()

    # Determine where to resume based on completed agents
    if "editor" in state["completed_agents"]:
        print("Workflow already complete!")
        return

    elif "reviewer" in state["completed_agents"]:
        # Review complete, proceed to editing
        invoke_editor()

    elif all(w in state["completed_agents"] for w in
             ["writer-intro", "writer-methods", "writer-results", "writer-discussion"]):
        # All sections written, proceed to review
        invoke_reviewer()

    # ... continue for each phase
```

---

## Error Handling

### Error Categories

**Category 1: Precondition Failures** (preventable)
- Missing input files
- Invalid file formats
- Insufficient content

**Action**: Validate before agent invocation, fail fast

**Category 2: Agent Execution Errors** (runtime)
- Agent crashes
- Timeout
- Invalid output format

**Action**: Retry with exponential backoff (max 3 attempts)

**Category 3: Quality Failures** (output validation)
- Word count out of range
- Missing required elements
- Quality score <8

**Action**: Auto-revise once, then escalate to user

**Category 4: Blocking Issues** (requires user)
- Reviewer rejection
- Type C feedback (new experiments needed)
- Contradictory requirements

**Action**: Halt workflow, report to user with clear next steps

### Error Handling Code

```python
def invoke_agent_with_retry(agent_name, prompt, max_retries=3):
    """Invoke agent with exponential backoff retry"""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Invoking {agent_name} (attempt {attempt}/{max_retries})")

            result = Task(
                subagent_type=agent_name,
                description=f"Execute {agent_name}",
                prompt=prompt
            )

            # Validate output
            if validate_agent_output(agent_name, result):
                print(f"{agent_name} completed successfully")
                return result
            else:
                raise ValidationError(f"{agent_name} output invalid")

        except Exception as e:
            print(f"Error in {agent_name}: {e}")

            if attempt < max_retries:
                wait_seconds = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)
            else:
                print(f"FAILED: {agent_name} failed after {max_retries} attempts")
                raise

def validate_agent_output(agent_name, result):
    """Validate agent-specific outputs"""
    if agent_name == "analyzer":
        # Check JSON exists and is valid
        return os.path.exists("analysis/papers_analyzed.json")

    elif agent_name.startswith("writer-"):
        section = agent_name.replace("writer-", "")
        file_path = f"sections/{section}.md"

        # Check file exists
        if not os.path.exists(file_path):
            return False

        # Check word count
        with open(file_path) as f:
            words = len(f.read().split())

        min_words = 400 if section in ["methods", "results"] else 500
        max_words = 600 if section in ["methods", "results"] else 700

        return min_words <= words <= max_words

    elif agent_name == "reviewer":
        return os.path.exists("review/feedback.json")

    elif agent_name == "editor":
        return all(os.path.exists(f) for f in [
            "FINAL_ARTICLE.md", "CHANGES.md", "abstract.md", "metadata.json"
        ])

    return True
```

---

## Performance Optimization

### Parallel Execution

**Phase 2a parallelization** saves ~10 minutes:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def execute_parallel_writers():
    """Run intro and methods writers in parallel"""

    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks
        future_intro = executor.submit(
            invoke_agent_with_retry,
            "writer-intro",
            "Write Introduction based on analysis/papers_analyzed.json"
        )

        future_methods = executor.submit(
            invoke_agent_with_retry,
            "writer-methods",
            "Write Methods based on analysis/papers_analyzed.json"
        )

        # Wait for completion
        futures = [future_intro, future_methods]
        for future in as_completed(futures):
            try:
                result = future.result()
                print(f"Writer completed: {result}")
            except Exception as e:
                print(f"Writer failed: {e}")
                raise

    print("Parallel writing phase complete")
```

### Caching

Cache analysis results to avoid re-analyzing unchanged PDFs:

```python
import hashlib

def compute_papers_hash():
    """Compute hash of all PDFs for cache invalidation"""
    hasher = hashlib.sha256()

    for pdf_path in sorted(glob.glob("papers/*.pdf")):
        with open(pdf_path, "rb") as f:
            hasher.update(f.read())

    return hasher.hexdigest()

def should_reanalyze():
    """Check if analysis is stale"""
    if not os.path.exists("analysis/papers_analyzed.json"):
        return True

    # Load cached hash
    if os.path.exists("analysis/.papers_hash"):
        with open("analysis/.papers_hash") as f:
            cached_hash = f.read().strip()
    else:
        return True

    # Compare with current hash
    current_hash = compute_papers_hash()
    return cached_hash != current_hash

# In orchestrator:
if should_reanalyze():
    invoke_analyzer()
    # Save hash after analysis
    with open("analysis/.papers_hash", "w") as f:
        f.write(compute_papers_hash())
else:
    print("Using cached analysis (PDFs unchanged)")
```

### Progress Monitoring

Real-time progress updates during long-running phases:

```python
import threading
import time

class ProgressMonitor:
    def __init__(self, agent_name, estimated_minutes):
        self.agent_name = agent_name
        self.estimated_seconds = estimated_minutes * 60
        self.start_time = time.time()
        self.running = True
        self.thread = threading.Thread(target=self._monitor)
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _monitor(self):
        while self.running:
            elapsed = time.time() - self.start_time
            progress = min(100, (elapsed / self.estimated_seconds) * 100)
            print(f"{self.agent_name}: {progress:.0f}% complete ({elapsed:.0f}s elapsed)")
            time.sleep(30)  # Update every 30s

# Usage:
monitor = ProgressMonitor("analyzer", estimated_minutes=10)
monitor.start()
invoke_analyzer()
monitor.stop()
```

---

## Usage Examples

### Example 1: Complete Workflow from Scratch

```python
#!/usr/bin/env python3
"""
Complete scientific article generation workflow
"""

import os
import json
from datetime import datetime

def main():
    print("=== Scientific Article Generation Workflow ===\n")

    # Phase 1: Setup
    print("[Phase 1] Setup and validation")
    validate_prerequisites()

    # Phase 2: Analysis
    print("\n[Phase 2] Literature analysis")
    run_analyzer()

    # Phase 3: Writing (parallel + sequential)
    print("\n[Phase 3] Section writing")
    run_parallel_writers()  # intro + methods
    run_sequential_writer("writer-results")
    run_sequential_writer("writer-discussion")

    # Phase 4: Review
    print("\n[Phase 4] Peer review")
    review_result = run_reviewer()

    # Phase 5: Editing
    print("\n[Phase 5] Final editing")
    if review_result["status"] in ["accept", "minor_revisions"]:
        run_editor()
        print("\n✅ Workflow complete! FINAL_ARTICLE.md ready for submission.")
    else:
        print(f"\n❌ Workflow blocked: {review_result['status']}")
        print(f"Reason: {review_result['justification']}")

def validate_prerequisites():
    """Check all prerequisites before starting"""
    errors = []

    # Check research config
    if not os.path.exists("input/research_config.md"):
        errors.append("Missing input/research_config.md")

    # Check PDFs
    pdf_count = len(glob.glob("papers/*.pdf"))
    if pdf_count == 0:
        errors.append("No PDFs in papers/")
    elif pdf_count < 10:
        print(f"⚠️  WARNING: Only {pdf_count} PDFs (recommend ≥15)")

    if errors:
        print("❌ Prerequisites failed:")
        for error in errors:
            print(f"  - {error}")
        exit(1)

    print(f"✓ Found {pdf_count} PDFs")
    print("✓ Research config exists")

def run_analyzer():
    """Phase 2: Run analyzer agent"""
    if should_skip_analysis():
        print("Skipping analysis (cached)")
        return

    monitor = ProgressMonitor("analyzer", estimated_minutes=8)
    monitor.start()

    Task(
        subagent_type="scientific-paper-analyzer",
        description="Analyze research papers",
        prompt="""
        Analyze all PDFs in papers/ directory. Extract:
        - Relevance score (1-10)
        - Methodology (models, datasets, metrics)
        - Key findings with quantitative results
        - Quality flags

        Output structured JSON to analysis/papers_analyzed.json
        """
    )

    monitor.stop()

    # Validate output
    with open("analysis/papers_analyzed.json") as f:
        papers = json.load(f)

    relevant = [p for p in papers if p["relevance_score"] >= 7]
    print(f"✓ Analyzed {len(papers)} papers, {len(relevant)} relevant")

def run_parallel_writers():
    """Phase 3a: Run intro and methods writers in parallel"""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print("Launching intro + methods writers in parallel...")

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_intro = executor.submit(run_sequential_writer, "writer-intro")
        future_methods = executor.submit(run_sequential_writer, "writer-methods")

        for future in as_completed([future_intro, future_methods]):
            future.result()  # Will raise if failed

    print("✓ Parallel writing complete")

def run_sequential_writer(agent_name):
    """Run a single writer agent"""
    section = agent_name.replace("writer-", "")

    monitor = ProgressMonitor(agent_name, estimated_minutes=10)
    monitor.start()

    Task(
        subagent_type=agent_name,
        description=f"Write {section} section",
        prompt=f"Write {section} section in Russian. Follow structure in agent definition. Target: 400-700 words depending on section."
    )

    monitor.stop()

    # Validate output
    file_path = f"sections/{section}.md"
    with open(file_path) as f:
        words = len(f.read().split())

    print(f"✓ {section}: {words} words")

def run_reviewer():
    """Phase 4: Run reviewer agent"""
    # Validate preconditions
    for section in ["introduction", "methods", "results", "discussion"]:
        path = f"sections/{section}.md"
        if not os.path.exists(path):
            print(f"❌ Missing {path}")
            exit(1)

        with open(path) as f:
            words = len(f.read().split())
            if words < 200:
                print(f"❌ {section} too short ({words} words)")
                exit(1)

    monitor = ProgressMonitor("reviewer", estimated_minutes=15)
    monitor.start()

    Task(
        subagent_type="reviewer",
        description="Peer review manuscript",
        prompt="""
        Review sections/{introduction,methods,results,discussion}.md

        Evaluate 5 criteria:
        - Logic & coherence (25%)
        - Scientific correctness (30%)
        - Topic relevance (20%)
        - Writing quality (15%)
        - Structure (10%)

        Output: review/feedback.json with scores, issues, recommendation
        """
    )

    monitor.stop()

    # Parse result
    with open("review/feedback.json") as f:
        feedback = json.load(f)

    status = feedback["overall_assessment"]["accept_status"]
    score = feedback["overall_assessment"]["overall_score"]

    print(f"✓ Review complete: {status} (score: {score})")

    return {
        "status": status,
        "score": score,
        "justification": feedback["recommendation"]["justification"]
    }

def run_editor():
    """Phase 5: Run editor agent"""
    monitor = ProgressMonitor("editor", estimated_minutes=12)
    monitor.start()

    Task(
        subagent_type="editor",
        description="Apply review feedback",
        prompt="""
        Apply feedback from review/feedback.json to sections/*.md

        Tasks:
        1. Resolve 100% critical issues
        2. Resolve 90%+ minor improvements
        3. Format references (IEEE numerical)
        4. Generate IMRAD abstract (150-250 words)
        5. Create FINAL_ARTICLE.md + CHANGES.md

        All article text in Russian.
        """
    )

    monitor.stop()

    # Validate outputs
    required = ["FINAL_ARTICLE.md", "CHANGES.md", "abstract.md", "metadata.json"]
    for file in required:
        if not os.path.exists(file):
            print(f"❌ Missing {file}")
            exit(1)

    print("✓ Editing complete")

if __name__ == "__main__":
    main()
```

### Example 2: Resume Interrupted Workflow

```python
def resume_workflow():
    """Resume from saved state"""
    state = load_state()

    print(f"Resuming workflow {state['workflow_id']}")
    print(f"Started: {state['started_at']}")
    print(f"Current phase: {state['current_phase']}")
    print(f"Completed agents: {', '.join(state['completed_agents'])}")

    # Determine next action
    completed = set(state['completed_agents'])

    if "editor" in completed:
        print("✅ Workflow already complete")
        return

    elif "reviewer" in completed:
        print("Resuming from review phase → running editor")
        run_editor()

    elif "writer-discussion" in completed:
        print("Resuming from writing phase → running reviewer")
        run_reviewer()
        run_editor()

    # ... etc
```

### Example 3: Dry Run (Validation Only)

```python
def dry_run():
    """Validate workflow without executing agents"""
    print("=== Dry Run: Validating Workflow ===\n")

    checks = [
        ("Research config", lambda: os.path.exists("input/research_config.md")),
        ("PDFs present", lambda: len(glob.glob("papers/*.pdf")) >= 5),
        ("Analysis JSON", lambda: os.path.exists("analysis/papers_analyzed.json")),
        ("Intro section", lambda: validate_section("introduction")),
        ("Methods section", lambda: validate_section("methods")),
        ("Results section", lambda: validate_section("results")),
        ("Discussion section", lambda: validate_section("discussion")),
        ("Review feedback", lambda: os.path.exists("review/feedback.json")),
        ("Final article", lambda: os.path.exists("FINAL_ARTICLE.md")),
    ]

    passed = 0
    for name, check_fn in checks:
        try:
            result = check_fn()
            status = "✓" if result else "✗"
            passed += result
        except:
            status = "✗"
            result = False

        print(f"{status} {name}")

    print(f"\n{passed}/{len(checks)} checks passed")

    if passed < len(checks):
        print("\nNext steps:")
        if not checks[0][1]():
            print("1. Create input/research_config.md")
        elif not checks[1][1]():
            print("2. Add PDFs to papers/")
        elif not checks[2][1]():
            print("3. Run analyzer")
        # ... etc

def validate_section(section_name):
    """Validate a single section"""
    path = f"sections/{section_name}.md"

    if not os.path.exists(path):
        return False

    with open(path) as f:
        content = f.read()
        words = len(content.split())

    # Check word count
    if words < 200:
        return False

    # Check no placeholders
    if any(placeholder in content for placeholder in ["[TODO]", "[TBD]", "[FILL]"]):
        return False

    return True
```

---

## Conclusion

This orchestration plan provides comprehensive coordination logic for the 7-agent scientific article writing system. Key takeaways:

1. **Clear dependencies**: Each agent has explicit inputs/outputs
2. **Phased execution**: Sequential phases with internal parallelism
3. **Robust error handling**: Retry, validation, graceful degradation
4. **State persistence**: Resume from interruptions
5. **Performance optimization**: Parallel execution, caching
6. **Observable**: Progress monitoring, logging, state tracking

**Estimated total runtime**: 60-90 minutes (serial) → 45-65 minutes (optimized parallel)

**Success rate**: ~90% for well-structured research topics with ≥15 relevant papers

For questions or issues, refer to:
- `CLAUDE.md` - System overview and quick reference
- `.claude/agents/*.md` - Individual agent specifications
- `workflow_state.json` - Current workflow status
