#!/usr/bin/env python3
"""
Gemini Orchestrator for Scientific Article Writing.
Updated to use the modern 'google-genai' package.
"""

import os
import sys
import argparse
from pathlib import Path


try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: 'google-genai' package is not installed.")
    print("Please install it using: pip install google-genai")
    sys.exit(1)


def check_api_keys():
    """Check which API keys are available."""
    google_key = os.environ.get("GOOGLE_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if google_key and gemini_key:
        print("Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY.")
        return google_key
    elif google_key:
        print("Using GOOGLE_API_KEY.")
        return google_key
    elif gemini_key:
        print("Using GEMINI_API_KEY.")
        return gemini_key
    else:
        print("❌ No API key found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
        sys.exit(1)


def list_available_models():
    """Lists all available models for the current API key."""
    print("\n📋 Fetching available models...\n")
    
    try:
        api_key = check_api_keys()
        client = genai.Client(api_key=api_key)
        
        models = list(client.models.list())
        
        if not models:
            print("No models found. Check your API key permissions.")
            return
        
        print(f"Found {len(models)} available models:\n")
        
        # Group models by generation
        gemini_3 = []
        gemini_25 = []
        gemini_2 = []
        gemini_15 = []
        other = []
        
        for model in models:
            name = model.name
            if "gemini-3" in name:
                gemini_3.append(model)
            elif "gemini-2.5" in name or "gemini-2-5" in name:
                gemini_25.append(model)
            elif "gemini-2.0" in name or "gemini-2-0" in name:
                gemini_2.append(model)
            elif "gemini-1.5" in name or "gemini-1-5" in name:
                gemini_15.append(model)
            else:
                other.append(model)
        
        # Print grouped models
        if gemini_3:
            print("🔥 Gemini 3 Models (Latest):")
            for m in gemini_3:
                print(f"   ✓ {m.name}")
                print(f"     Supports: {', '.join(m.supported_actions)}")
                print()
        
        if gemini_25:
            print("⚡ Gemini 2.5 Models:")
            for m in gemini_25:
                print(f"   ✓ {m.name}")
                print(f"     Supports: {', '.join(m.supported_actions)}")
                print()
        
        if gemini_2:
            print("📦 Gemini 2.0 Models:")
            for m in gemini_2:
                print(f"   ✓ {m.name}")
                print(f"     Supports: {', '.join(m.supported_actions)}")
                print()
        
        if gemini_15:
            print("📚 Gemini 1.5 Models:")
            for m in gemini_15:
                print(f"   ✓ {m.name}")
                print()
        
        if other:
            print("🔧 Other Models:")
            for m in other:
                print(f"   ✓ {m.name}")
                print()
        
        print("\n💡 Recommended models for production:")
        print("   • gemini-3-flash-preview - Fastest, most balanced (preview)")
        print("   • gemini-2.5-flash - Stable, cost-effective")
        print("   • gemini-2.5-pro - Advanced reasoning")
        print()
        
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        print("\n💡 Common issues:")
        print("   • Check your API key is valid")
        print("   • Ensure you have proper permissions")
        print("   • Free tier may have quota limitations")


def load_gem_instruction(gem_name):
    """Loads the system instruction from the gems/ directory."""
    gem_path = Path(f"gems/{gem_name}.md")
    if not gem_path.exists():
        raise FileNotFoundError(f"Gem definition not found: {gem_path}")
    return gem_path.read_text(encoding="utf-8")


def run_agent(agent_name, input_context, output_file=None, model_id="gemini-2.5-flash"):
    """Runs a specific agent with the provided input context."""
    print(f"🤖 Invoking Agent: {agent_name} using {model_id}...")
    
    # Initialize client
    api_key = check_api_keys()
    client = genai.Client(api_key=api_key)
    
    try:
        system_instruction = load_gem_instruction(agent_name)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return None
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=8192,
    )

    prompt = f"CONTEXT:\n{input_context}\n\nTASK:\nPerform your role as defined."
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=config
        )
        content = response.text
        
        if output_file:
            directory = os.path.dirname(output_file)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Output saved to {output_file}")
        else:
            print("Output:")
            print(content)
            
        return content
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error running agent {agent_name}: {e}")
        
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            print("\n💡 Quota exceeded. Solutions:")
            print("   1. Wait for quota to reset (shown in error message)")
            print("   2. Switch to a different model (gemini-1.5-flash has higher quotas)")
            print("   3. Upgrade to paid tier: https://ai.google.dev/pricing")
            print("   4. Use --list-models to see what's available")
        elif "503" in error_msg or "UNAVAILABLE" in error_msg:
            print("\n💡 Model is overloaded. Try:")
            print("   1. Wait a few minutes and retry")
            print("   2. Use a different model with --model flag")
            print("   3. Use gemini-2.5-flash (more stable)")
        elif "404" in error_msg or "NOT_FOUND" in error_msg:
            print("\n💡 Model not found. Common mistakes:")
            print("   • Use 'gemini-3-flash-preview' (not 'gemini-3.0-flash')")
            print("   • Use 'gemini-2.5-flash' (not 'gemini-2.5-flash-001')")
            print("   • Run --list-models to see available models")
        
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Gemini Scientific Article Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available models
  python3 gems/orchestrator_gemini.py --list-models
  
  # Run with Gemini 3 Flash (latest, preview)
  python3 gems/orchestrator_gemini.py --agent writer-intro --model gemini-3-flash-preview
  
  # Run with Gemini 2.5 Flash (stable, recommended)
  python3 gems/orchestrator_gemini.py --agent writer-intro --model gemini-2.5-flash
  
  # Run with Gemini 1.5 Flash (older, higher quotas)
  python3 gems/orchestrator_gemini.py --agent writer-intro --model gemini-1.5-flash
        """
    )
    
    parser.add_argument("--agent", choices=[
        "analyzer", "writer-intro", "writer-methods", "writer-results", 
        "writer-discussion", "reviewer", "editor"
    ], help="Run a specific agent")
    
    parser.add_argument(
        "--model", 
        default="gemini-2.5-flash",
        help="Model ID to use (default: gemini-2.5-flash). Common options: gemini-3-flash-preview, gemini-2.5-flash, gemini-2.5-pro, gemini-1.5-flash"
    )
    
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List all available models for your API key"
    )
    
    args = parser.parse_args()
    
    # Handle --list-models flag
    if args.list_models:
        list_available_models()
        return
    
    # Run specific agent
    # Helper to safely read file content
    def read_if_exists(path):
        return Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""

    # Load common data
    config = read_if_exists("input/research_config.md")
    analysis = read_if_exists("analysis/papers_analyzed.json")

    # Dispatch based on agent
    if args.agent == "analyzer":
        # In a real scenario, we would read PDF text here. 
        # For this context, we pass the file list and config.
        import glob
        pdf_list = glob.glob("papers/downloaded/*.pdf")
        context = f"Research Config:\n{config}\n\nFiles to analyze: {pdf_list}\n(Note: This agent expects extracted text from PDFs. Ensure text is provided or extracted.)"
        run_agent("analyzer", context, "analysis/papers_analyzed.json", model_id=args.model)

    elif args.agent == "writer-intro":
        context = f"Research Config:\n{config}\n\nAnalysis Data:\n{analysis}"
        run_agent("writer-intro", context, "sections/introduction.md", model_id=args.model)

    elif args.agent == "writer-methods":
        intro = read_if_exists("sections/introduction.md")
        context = f"Research Config:\n{config}\n\nAnalysis Data:\n{analysis}\n\nContext - Introduction:\n{intro}"
        run_agent("writer-methods", context, "sections/methods.md", model_id=args.model)

    elif args.agent == "writer-results":
        methods = read_if_exists("sections/methods.md")
        context = f"Research Config:\n{config}\n\nAnalysis Data:\n{analysis}\n\nContext - Methods:\n{methods}"
        run_agent("writer-results", context, "sections/results.md", model_id=args.model)

    elif args.agent == "writer-discussion":
        intro = read_if_exists("sections/introduction.md")
        results = read_if_exists("sections/results.md")
        context = f"Research Config:\n{config}\n\nContext - Introduction:\n{intro}\n\nContext - Results:\n{results}"
        run_agent("writer-discussion", context, "sections/discussion.md", model_id=args.model)

    elif args.agent == "reviewer":
        # Load all available sections
        full_draft = ""
        for sec in ["introduction", "methods", "results", "discussion"]:
            content = read_if_exists(f"sections/{sec}.md")
            if content:
                full_draft += f"\n\n--- SECTION: {sec.upper()} ---\n{content}"
        
        context = f"Research Config:\n{config}\n\nFull Draft to Review:\n{full_draft}"
        run_agent("reviewer", context, "review/feedback.md", model_id=args.model)

    elif args.agent == "editor":
        # Load draft and feedback
        full_draft = ""
        for sec in ["introduction", "methods", "results", "discussion"]:
            content = read_if_exists(f"sections/{sec}.md")
            if content:
                full_draft += f"\n\n--- SECTION: {sec.upper()} ---\n{content}"
        
        feedback = read_if_exists("review/feedback.md")
        context = f"Research Config:\n{config}\n\nFull Draft:\n{full_draft}\n\nReviewer Feedback:\n{feedback}"
        run_agent("editor", context, "final_manuscript.md", model_id=args.model)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
