# Gemini Gems for Scientific Article Writing

This project uses a "Chain of Agents" approach to write scientific papers. We have defined 7 specialized "Gems" (Agents) to handle different stages of the process.

## Available Gems

The system instructions for these gems are located in the `gems/` directory:

1.  **Analyzer** (`gems/analyzer.md`): Analyzes PDFs and extracts info to JSON.
2.  **Writer-Intro** (`gems/writer-intro.md`): Writes the Introduction section.
3.  **Writer-Methods** (`gems/writer-methods.md`): Writes the Methods section.
4.  **Writer-Results** (`gems/writer-results.md`): Writes the Results section.
5.  **Writer-Discussion** (`gems/writer-discussion.md`): Writes the Discussion section.
6.  **Reviewer** (`gems/reviewer.md`): Reviews the complete draft.
7.  **Editor** (`gems/editor.md`): Finalizes the paper based on review.

## How to Use in Gemini CLI

You can use these Gems by passing their content as a system instruction (or context) when interacting with the model.

### Option 1: Manual Usage

To act as a specific agent, you can cat the gem file and your input:

```bash
# Example: Analyze papers
cat gems/analyzer.md input/research_config.md | gemini "Analyze the PDFs in the papers/ directory"
```

(Note: You would need to provide the actual PDF content or extraction results to the model context, as the CLI tool `gemini` might not auto-read files unless configured to use tools.)

### Option 2: Using the Orchestrator Script

We have provided a Python script `gems/orchestrator_gemini.py` that simulates the agent workflow using the Gemini API (Google Gen AI SDK).

**Prerequisites:**
- `google-generativeai` python package installed.
- `GOOGLE_API_KEY` environment variable set.

**Usage:**

```bash
# Run the full workflow
python3 gems/orchestrator_gemini.py --mode full --topic "Your Topic"

# Run a specific agent
python3 gems/orchestrator_gemini.py --agent analyzer
python3 gems/orchestrator_gemini.py --agent writer-intro
```

## Gem Descriptions

### Analyzer
- **Input**: PDFs in `papers/`, `input/research_config.md`
- **Output**: `analysis/papers_analyzed.json`
- **Role**: Extracts metadata, methodology, and results from papers. Scores relevance.

### Writers (Intro, Methods, Results, Discussion)
- **Input**: `analysis/papers_analyzed.json`, previous sections.
- **Output**: `sections/*.md`
- **Role**: Write specific sections of the paper in Russian academic style.

### Reviewer
- **Input**: All 4 sections.
- **Output**: `review/feedback.json`
- **Role**: Critiques the draft based on logic, correctness, relevance, writing, and structure.

### Editor
- **Input**: Draft sections, review feedback.
- **Output**: `FINAL_ARTICLE.md`, `CHANGES.md`, `abstract.md`.
- **Role**: Polishes the manuscript, applies fixes, and formats references (IEEE).
