# Scientific Article Writer - Workflow Diagram

**Visual reference for the complete article generation pipeline**

---

## Quick Reference Flow

```
USER INPUT → ANALYZER → WRITERS → REVIEWER → EDITOR → FINAL ARTICLE
  (~2 min)   (8-10 min)  (30-40 min) (15-20 min) (12-18 min)  (COMPLETE)
```

**Total time**: 65-90 minutes (automated)

---

## Detailed Phase Diagram

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PHASE 0: USER PREPARATION                                          ┃
┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
┃                                                                     ┃
┃  ┌─────────────────────────────┐      ┌────────────────────────┐  ┃
┃  │ input/research_config.md    │      │ papers/*.pdf           │  ┃
┃  │                             │      │                        │  ┃
┃  │ • Research topic            │      │ • 10-50 PDFs           │  ┃
┃  │ • Keywords                  │      │ • Related to topic     │  ┃
┃  │ • Scope                     │      │ • Mix of classic +     │  ┃
┃  │ • Target venue              │      │   recent papers        │  ┃
┃  └─────────────────────────────┘      └────────────────────────┘  ┃
┃                                                                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                             │
                             ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PHASE 1: LITERATURE ANALYSIS                    ⏱ 8-10 minutes    ┃
┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
┃                                                                     ┃
┃                    ┌──────────────────────────┐                    ┃
┃                    │  ANALYZER AGENT          │                    ┃
┃                    │  (scientific-paper-      │                    ┃
┃                    │   analyzer)              │                    ┃
┃                    │                          │                    ┃
┃                    │  For each PDF:           │                    ┃
┃                    │  • Read & extract text   │                    ┃
┃                    │  • Score relevance 1-10  │                    ┃
┃                    │  • Extract methodology   │                    ┃
┃                    │  • Extract key findings  │                    ┃
┃                    │  • Identify quality      │                    ┃
┃                    └───────────┬──────────────┘                    ┃
┃                                │                                    ┃
┃                                ▼                                    ┃
┃                 ┌─────────────────────────────┐                    ┃
┃                 │ analysis/papers_analyzed    │                    ┃
┃                 │         .json               │                    ┃
┃                 │                             │                    ┃
┃                 │ [                           │                    ┃
┃                 │   {                         │                    ┃
┃                 │     "title": "...",         │                    ┃
┃                 │     "relevance_score": 9,   │                    ┃
┃                 │     "methodology": {...},   │                    ┃
┃                 │     "key_findings": [...]   │                    ┃
┃                 │   },                        │                    ┃
┃                 │   ...                       │                    ┃
┃                 │ ]                           │                    ┃
┃                 └─────────────────────────────┘                    ┃
┃                                                                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                             │
                             │ (triggers all writers)
                             │
                             ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PHASE 2: SECTION WRITING                        ⏱ 30-40 minutes   ┃
┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
┃                                                                     ┃
┃  ┌────────────────────────────────────────────────────────────┐   ┃
┃  │ PHASE 2a: PARALLEL WRITING               ⏱ 10-12 minutes   │   ┃
┃  │────────────────────────────────────────────────────────────│   ┃
┃  │                                                             │   ┃
┃  │   ┌────────────────────┐      ┌────────────────────┐      │   ┃
┃  │   │ WRITER-INTRO       │      │ WRITER-METHODS     │      │   ┃
┃  │   │                    │      │                    │      │   ┃
┃  │   │ • Context          │      │ • Data/datasets    │      │   ┃
┃  │   │ • Problem          │ ∥    │ • Architecture     │      │   ┃
┃  │   │ • Literature       │ ∥    │ • Training         │      │   ┃
┃  │   │ • Contributions    │ ∥    │ • Metrics          │      │   ┃
┃  │   │                    │      │                    │      │   ┃
┃  │   │ 500-700 words      │      │ 400-600 words      │      │   ┃
┃  │   │ Russian            │      │ Russian            │      │   ┃
┃  │   └─────────┬──────────┘      └─────────┬──────────┘      │   ┃
┃  │             │                           │                  │   ┃
┃  │             ▼                           ▼                  │   ┃
┃  │   sections/introduction.md    sections/methods.md         │   ┃
┃  └────────────────────────────────────────────────────────────┘   ┃
┃                             │                                      ┃
┃                             │ (methods complete)                   ┃
┃                             ▼                                      ┃
┃  ┌────────────────────────────────────────────────────────────┐   ┃
┃  │ PHASE 2b: SEQUENTIAL (depends on methods) ⏱ 8-12 minutes  │   ┃
┃  │────────────────────────────────────────────────────────────│   ┃
┃  │                                                             │   ┃
┃  │                  ┌────────────────────┐                    │   ┃
┃  │                  │ WRITER-RESULTS     │                    │   ┃
┃  │                  │                    │                    │   ┃
┃  │                  │ Reads:             │                    │   ┃
┃  │                  │ • methods.md       │                    │   ┃
┃  │                  │   (metric defs)    │                    │   ┃
┃  │                  │ • analysis JSON    │                    │   ┃
┃  │                  │                    │                    │   ┃
┃  │                  │ Writes:            │                    │   ┃
┃  │                  │ • Tables           │                    │   ┃
┃  │                  │ • Quantitative     │                    │   ┃
┃  │                  │ • Objective facts  │                    │   ┃
┃  │                  │                    │                    │   ┃
┃  │                  │ 400-600 words      │                    │   ┃
┃  │                  │ Russian            │                    │   ┃
┃  │                  └─────────┬──────────┘                    │   ┃
┃  │                            │                                │   ┃
┃  │                            ▼                                │   ┃
┃  │                  sections/results.md                        │   ┃
┃  └────────────────────────────────────────────────────────────┘   ┃
┃                             │                                      ┃
┃                             │ (all 3 sections complete)            ┃
┃                             ▼                                      ┃
┃  ┌────────────────────────────────────────────────────────────┐   ┃
┃  │ PHASE 2c: SEQUENTIAL (depends on all)    ⏱ 10-15 minutes  │   ┃
┃  │────────────────────────────────────────────────────────────│   ┃
┃  │                                                             │   ┃
┃  │                  ┌────────────────────┐                    │   ┃
┃  │                  │ WRITER-DISCUSSION  │                    │   ┃
┃  │                  │                    │                    │   ┃
┃  │                  │ Reads:             │                    │   ┃
┃  │                  │ • introduction.md  │                    │   ┃
┃  │                  │ • methods.md       │                    │   ┃
┃  │                  │ • results.md       │                    │   ┃
┃  │                  │ • analysis JSON    │                    │   ┃
┃  │                  │                    │                    │   ┃
┃  │                  │ Writes:            │                    │   ┃
┃  │                  │ • Interpretation   │                    │   ┃
┃  │                  │ • Comparison       │                    │   ┃
┃  │                  │ • Limitations      │                    │   ┃
┃  │                  │ • Future work      │                    │   ┃
┃  │                  │                    │                    │   ┃
┃  │                  │ 500-700 words      │                    │   ┃
┃  │                  │ Russian            │                    │   ┃
┃  │                  └─────────┬──────────┘                    │   ┃
┃  │                            │                                │   ┃
┃  │                            ▼                                │   ┃
┃  │                  sections/discussion.md                     │   ┃
┃  └────────────────────────────────────────────────────────────┘   ┃
┃                                                                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                             │
                             │ (all 4 sections complete)
                             ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PHASE 3: PEER REVIEW                            ⏱ 15-20 minutes   ┃
┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
┃                                                                     ┃
┃              ┌─────────────────────────────────────┐               ┃
┃              │  REVIEWER AGENT                     │               ┃
┃              │  (reviewer)                         │               ┃
┃              │                                     │               ┃
┃              │  Validates:                         │               ┃
┃              │  • Logic & coherence (25%)          │               ┃
┃              │  • Scientific correctness (30%)     │               ┃
┃              │  • Topic relevance (20%)            │               ┃
┃              │  • Writing quality (15%)            │               ┃
┃              │  • Structure (10%)                  │               ┃
┃              │                                     │               ┃
┃              │  Checks:                            │               ┃
┃              │  • Cross-section consistency        │               ┃
┃              │  • Citation completeness            │               ┃
┃              │  • Reproducibility                  │               ┃
┃              │  • Statistical validity             │               ┃
┃              │                                     │               ┃
┃              └──────────────┬──────────────────────┘               ┃
┃                             │                                       ┃
┃                             ▼                                       ┃
┃              ┌─────────────────────────────────────┐               ┃
┃              │ review/feedback.json                │               ┃
┃              │                                     │               ┃
┃              │ {                                   │               ┃
┃              │   "overall_score": 82,              │               ┃
┃              │   "accept_status": "minor_revisions"│               ┃
┃              │   "critical_issues": [...],         │               ┃
┃              │   "minor_improvements": [...],      │               ┃
┃              │   "section_scores": {...}           │               ┃
┃              │ }                                   │               ┃
┃              └──────────────┬──────────────────────┘               ┃
┃                             │                                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐         ┌──────────┐         ┌─────────┐
    │ ACCEPT  │         │  MINOR   │         │ MAJOR   │
    │   or    │         │REVISIONS │         │REVISIONS│
    │ MINOR   │         │          │         │   or    │
    │ REV.    │         │          │         │ REJECT  │
    └────┬────┘         └─────┬────┘         └────┬────┘
         │                    │                    │
         │                    │                    │
         └────────────────────┘                    │
                  │                                │
                  ▼                                ▼
        ┌──────────────────┐          ┌────────────────────┐
        │  PROCEED TO      │          │  HALT WORKFLOW     │
        │  EDITOR          │          │  Flag for user     │
        └──────────────────┘          └────────────────────┘
                  │
                  ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PHASE 4: FINAL EDITING                          ⏱ 12-18 minutes   ┃
┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
┃                                                                     ┃
┃              ┌─────────────────────────────────────┐               ┃
┃              │  EDITOR AGENT                       │               ┃
┃              │  (editor)                           │               ┃
┃              │                                     │               ┃
┃              │  Phase 1: Apply Feedback            │               ┃
┃              │  • Fix 100% critical issues         │               ┃
┃              │  • Fix 90%+ minor issues            │               ┃
┃              │  • Document all changes             │               ┃
┃              │                                     │               ┃
┃              │  Phase 2: Format References         │               ┃
┃              │  • IEEE numerical style [1], [2]... │               ┃
┃              │  • Order by first appearance        │               ┃
┃              │  • Validate all citations           │               ┃
┃              │                                     │               ┃
┃              │  Phase 3: Generate Abstract         │               ┃
┃              │  • IMRAD structure                  │               ┃
┃              │  • 150-250 words                    │               ┃
┃              │  • Self-contained, no citations     │               ┃
┃              │  • Include key metrics              │               ┃
┃              │                                     │               ┃
┃              │  Phase 4: Quality Assurance         │               ┃
┃              │  • Check all sections present       │               ┃
┃              │  • Validate citations               │               ┃
┃              │  • No placeholders                  │               ┃
┃              │  • Formatting consistent            │               ┃
┃              │                                     │               ┃
┃              └──────────────┬──────────────────────┘               ┃
┃                             │                                       ┃
┃                             ▼                                       ┃
┃   ┌──────────────────────────────────────────────────────┐         ┃
┃   │  OUTPUTS (all files created)                         │         ┃
┃   │──────────────────────────────────────────────────────│         ┃
┃   │                                                       │         ┃
┃   │  1. FINAL_ARTICLE.md                                 │         ┃
┃   │     • Complete camera-ready manuscript               │         ┃
┃   │     • All sections integrated                        │         ┃
┃   │     • Russian academic language                      │         ┃
┃   │     • Formatted references                           │         ┃
┃   │                                                       │         ┃
┃   │  2. CHANGES.md                                       │         ┃
┃   │     • All modifications documented                   │         ┃
┃   │     • Critical issues resolved                       │         ┃
┃   │     • Minor improvements applied                     │         ┃
┃   │                                                       │         ┃
┃   │  3. abstract.md                                      │         ┃
┃   │     • Standalone 150-250 words                       │         ┃
┃   │     • IMRAD structure                                │         ┃
┃   │     • No citations                                   │         ┃
┃   │     • For submission forms                           │         ┃
┃   │                                                       │         ┃
┃   │  4. references/formatted_references.md               │         ┃
┃   │     • IEEE numerical [1], [2]...                     │         ┃
┃   │     • Ordered by appearance                          │         ┃
┃   │                                                       │         ┃
┃   │  5. metadata.json                                    │         ┃
┃   │     • Title, authors, keywords                       │         ┃
┃   │     • Word counts, stats                             │         ┃
┃   │     • Status: ready_for_submission                   │         ┃
┃   │                                                       │         ┃
┃   └──────────────────────────────────────────────────────┘         ┃
┃                                                                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                             │
                             ▼
                    ┌────────────────┐
                    │   ✅ COMPLETE  │
                    │                │
                    │  Ready for     │
                    │  submission!   │
                    └────────────────┘
```

---

## Agent Dependency Graph

```
                     ┌──────────────┐
                     │   ANALYZER   │
                     │              │
                     │ Inputs:      │
                     │ • PDFs       │
                     │ • config     │
                     │              │
                     │ Outputs:     │
                     │ • JSON       │
                     └──────┬───────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
   ┌──────────────┐  ┌──────────────┐  (analysis JSON)
   │WRITER-INTRO  │  │WRITER-METHODS│
   │              │  │              │
   │ Deps: JSON   │  │ Deps: JSON   │
   └──────┬───────┘  └──────┬───────┘
          │                 │
          │                 └────────────┐
          │                              │
          │                              ▼
          │                    ┌──────────────────┐
          │                    │ WRITER-RESULTS   │
          │                    │                  │
          │                    │ Deps:            │
          │                    │ • JSON           │
          │                    │ • methods.md     │
          │                    └────────┬─────────┘
          │                             │
          └──────────────┬──────────────┘
                         │
                         ▼
              ┌────────────────────┐
              │WRITER-DISCUSSION   │
              │                    │
              │ Deps:              │
              │ • intro.md         │
              │ • methods.md       │
              │ • results.md       │
              │ • JSON             │
              └─────────┬──────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │   REVIEWER          │
              │                     │
              │ Deps:               │
              │ • All 4 sections    │
              └─────────┬───────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │   EDITOR            │
              │                     │
              │ Deps:               │
              │ • All sections      │
              │ • feedback.json     │
              └─────────────────────┘
```

---

## File Flow Map

```
INPUT FILES:
├── input/research_config.md      ──┐
└── papers/*.pdf                   ──┼──> ANALYZER
                                     │
                                     ▼
INTERMEDIATE FILES:                  │
└── analysis/papers_analyzed.json <──┘
        │
        ├──> WRITER-INTRO      ──> sections/introduction.md ──┐
        ├──> WRITER-METHODS    ──> sections/methods.md ───────┼─┐
        ├──> WRITER-RESULTS    ──> sections/results.md ←──────┘ │
        └──> WRITER-DISCUSSION ──> sections/discussion.md ←──────┘
                                         │
                                         ▼
REVIEW FILES:                            │
└── review/feedback.json <───────────────┤
        │                                │
        └────────────────────────────────┤
                                         │
                                         ▼
FINAL OUTPUT FILES:                      │
├── FINAL_ARTICLE.md           <─────────┤
├── CHANGES.md                 <─────────┤
├── abstract.md                <─────────┤
├── metadata.json              <─────────┤
└── references/                <─────────┘
    └── formatted_references.md
```

---

## Decision Points

### 1. After Analysis

```
analysis/papers_analyzed.json created
    │
    ├─ Paper count ≥ 10 ─────> PROCEED to writing
    │
    ├─ Paper count 5-9 ──────> WARN user, offer to proceed
    │
    └─ Paper count < 5 ──────> HALT, request more papers
```

### 2. After Review

```
review/feedback.json created
    │
    ├─ Status: accept ────────────> EDITOR (minimal changes)
    │
    ├─ Status: minor_revisions ───> EDITOR (apply fixes)
    │
    ├─ Status: major_revisions ───> HALT (flag issues for user)
    │
    └─ Status: reject ────────────> HALT (report problems)
```

---

## Parallel Execution Optimization

```
SERIAL (slow):
─────────────────────────────────────────────────────
Time: 0    10    20    30    40    50    60    70

│ANALYZER│INTRO│METHODS│RESULTS│DISCUSSION│REVIEW│EDITOR│

Total: ~70 minutes


PARALLEL (optimized):
─────────────────────────────────────────────────────
Time: 0    10    20    30    40    50    60

│ANALYZER│┌INTRO─┐│RESULTS│DISCUSSION│REVIEW│EDITOR│
         └METHODS┘

Total: ~50 minutes

Savings: ~20 minutes (28% faster)
```

---

## Quality Gates

```
┌──────────────┐
│  ANALYZER    │
└──────┬───────┘
       │
       ▼
   ┌────────────────────┐
   │ ✓ Valid JSON?      │
   │ ✓ ≥5 papers?       │◄─── GATE 1: Analysis Quality
   │ ✓ Scores present?  │
   └────┬───────────────┘
        │ PASS
        ▼
┌──────────────┐
│  WRITERS     │
└──────┬───────┘
       │
       ▼
   ┌────────────────────┐
   │ ✓ All files exist? │
   │ ✓ Word count OK?   │◄─── GATE 2: Section Completeness
   │ ✓ No placeholders? │
   │ ✓ ≥200 words each? │
   └────┬───────────────┘
        │ PASS
        ▼
┌──────────────┐
│  REVIEWER    │
└──────┬───────┘
       │
       ▼
   ┌────────────────────┐
   │ ✓ Score ≥75?       │
   │ ✓ Accept/minor?    │◄─── GATE 3: Peer Review
   │ ✓ Not reject?      │
   └────┬───────────────┘
        │ PASS
        ▼
┌──────────────┐
│  EDITOR      │
└──────┬───────┘
       │
       ▼
   ┌────────────────────┐
   │ ✓ All outputs?     │
   │ ✓ Abstract 150-250?│◄─── GATE 4: Final Validation
   │ ✓ No TODOs?        │
   │ ✓ Citations valid? │
   └────┬───────────────┘
        │ PASS
        ▼
    ┌─────────┐
    │ SUCCESS │
    └─────────┘
```

---

## Monitoring & Observability

### Real-time Progress Tracking

```
┌─────────────────────────────────────────────────┐
│ Scientific Article Writer - Live Status         │
├─────────────────────────────────────────────────┤
│                                                  │
│ Current Phase: WRITING                           │
│ Progress: ████████░░ 75%                         │
│                                                  │
│ ✅ Analyzer        [08:23 elapsed]               │
│ ✅ Writer-Intro    [11:45 elapsed]               │
│ ✅ Writer-Methods  [10:12 elapsed]               │
│ ⏳ Writer-Results  [05:30 elapsed] 68% complete  │
│ ⏸  Writer-Discussion (waiting)                  │
│ ⏸  Reviewer       (waiting)                     │
│ ⏸  Editor         (waiting)                     │
│                                                  │
│ Estimated completion: ~25 minutes                │
└─────────────────────────────────────────────────┘
```

---

## Error Recovery

```
┌────────────────┐
│  Error occurs  │
└───────┬────────┘
        │
        ▼
┌─────────────────────────────┐
│ Is error recoverable?       │
└─────┬───────────────────────┘
      │
      ├─ YES ──> Retry with exponential backoff (max 3x)
      │          │
      │          ├─ Success ──> Continue workflow
      │          │
      │          └─ Still fails ──> Log error, escalate to user
      │
      └─ NO ───> Halt workflow
                 │
                 ├─ Save state (workflow_state.json)
                 ├─ Log error details
                 └─ Report to user with recovery instructions
```

---

## Quick Command Reference

### Start new article
```bash
# Full workflow (automated)
python orchestrator.py --mode=full --topic="ML weather forecasting"

# Step-by-step (manual)
python orchestrator.py --mode=step
```

### Resume interrupted workflow
```bash
python orchestrator.py --mode=resume
```

### Dry run (validation only)
```bash
python orchestrator.py --mode=dryrun
```

### Monitor progress
```bash
tail -f workflow.log
```

### Check status
```bash
python orchestrator.py --status
```

---

## Success Metrics

### Expected Outcomes

- **Completion rate**: ~90% for well-structured topics
- **Runtime**: 50-70 minutes (parallel mode)
- **Quality score**: 75-90 (reviewer assessment)
- **Accept rate**: 85% (accept or minor revisions)

### Key Performance Indicators

```
┌──────────────────────┬─────────┬──────────┐
│ Metric               │ Target  │ Actual   │
├──────────────────────┼─────────┼──────────┤
│ Total runtime        │ 60 min  │ [track]  │
│ Reviewer score       │ ≥75     │ [track]  │
│ Accept rate          │ ≥80%    │ [track]  │
│ Critical issues      │ ≤2      │ [track]  │
│ Word count accuracy  │ ±10%    │ [track]  │
│ Citation count       │ 40-60   │ [track]  │
└──────────────────────┴─────────┴──────────┘
```

---

**For detailed orchestration logic, see**: `MULTI_AGENT_PLAN.md`

**For system overview, see**: `CLAUDE.md`

**For individual agent specs, see**: `.claude/agents/*.md`
