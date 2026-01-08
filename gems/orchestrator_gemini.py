#!/usr/bin/env python3
"""
Gemini Orchestrator for Scientific Article Writing.
This script demonstrates how to use the 'Gems' (agent definitions) to drive the workflow.
"""

import os
import sys
import argparse
import json
import glob
from pathlib import Path

# Try to import google.generativeai, but handle if missing
try:
    import google.generativeai as genai
except ImportError:
    print("Error: 'google-generativeai' package is not installed.")
    print("Please install it using: pip install google-generativeai")
    sys.exit(1)

def load_gem_instruction(gem_name):
    """Loads the system instruction from the gems/ directory."""
    gem_path = Path(f"gems/{gem_name}.md")
    if not gem_path.exists():
        raise FileNotFoundError(f"Gem definition not found: {gem_path}")
    return gem_path.read_text(encoding="utf-8")

def get_model(gem_name):
    """Configures and returns a GenerativeModel with the Gem's instruction."""
    system_instruction = load_gem_instruction(gem_name)
    
    # Configure generation config (can be tuned per agent if needed)
    generation_config = {
        "temperature": 0.2, # Low temperature for factual scientific writing
        "top_p": 0.95,
        "max_output_tokens": 8192,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest", # Or gemini-1.5-flash
        generation_config=generation_config,
        system_instruction=system_instruction
    )
    return model

def run_agent(agent_name, input_context, output_file=None):
    """Runs a specific agent with the provided input context."""
    print(f"🤖 Invoking Agent: {agent_name}...")
    
    model = get_model(agent_name)
    
    # Construct the prompt
    prompt = f"""
    CONTEXT:
    {input_context}
    
    TASK:
    Perform your role as defined in the system instruction.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Output saved to {output_file}")
        else:
            print("Output:")
            print(content)
            
        return content
        
    except Exception as e:
        print(f"❌ Error running agent {agent_name}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Gemini Scientific Article Orchestrator")
    parser.add_argument("--agent", choices=[
        "analyzer", "writer-intro", "writer-methods", "writer-results", 
        "writer-discussion", "reviewer", "editor"
    ], help="Run a specific agent")
    parser.add_argument("--mode", choices=["full", "single"], default="single", help="Run mode")
    
    args = parser.parse_args()
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        sys.exit(1)
        
    genai.configure(api_key=api_key)

    if args.agent == "analyzer":
        # Example context loading for analyzer
        print("Reading configuration...")
        config = Path("input/research_config.md").read_text() if Path("input/research_config.md").exists() else "No config found."
        
        # In a real scenario, we would read PDFs here. 
        # For this demo, we'll assume we pass file lists or text content.
        pdf_list = glob.glob("papers/*.pdf")
        context = f"Research Config:\n{config}\n\nFiles to analyze: {pdf_list}\n(Note: This script requires PDF text extraction logic to fully function as the Analyzer. This is a scaffold.)"
        
        run_agent("analyzer", context, "analysis/papers_analyzed.json")

    elif args.agent == "writer-intro":
        analysis = Path("analysis/papers_analyzed.json").read_text() if Path("analysis/papers_analyzed.json").exists() else "{}"
        config = Path("input/research_config.md").read_text() if Path("input/research_config.md").exists() else ""
        context = f"Research Config:\n{config}\n\nAnalysis Data:\n{analysis}"
        
        run_agent("writer-intro", context, "sections/introduction.md")
        
    # ... Add other agents similarly ...
    
    else:
        print("Please specify an agent to run (e.g., --agent writer-intro).")
        print("See gems/ directory for available definitions.")

if __name__ == "__main__":
    main()
