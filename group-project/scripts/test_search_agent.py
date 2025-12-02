#!/usr/bin/env python3
"""
Minimal test script for SearchAgent

Usage:
    PYTHONPATH=. python scripts/test_search_agent.py
"""

import sys
import os

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.agent import SearchAgent


def main():
    print("="*60)
    print("Minimal SearchAgent Test")
    print("="*60)
    
    # Initialize agent
    print("\n1. Initializing SearchAgent...")
    try:
        agent = SearchAgent(max_steps=10, include_browse=True)
        print("   ✓ SearchAgent initialized")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test question
    question = "Tell me the recent news about the fire in Tai po in Hong Kong."
    print(f"\n2. Testing with question: '{question}'")
    print("   Running agent loop...")
    
    try:
        result = agent.agent_loop(question)
        
        agent.print_trajectory(result)
    except Exception as e:
        print(f"\n✗ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        

if __name__ == "__main__":
    main()

