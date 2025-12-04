#!/usr/bin/env python3
"""
Test script for agent.py

Usage:
    python scripts/test_agent.py
    PYTHONPATH=. python scripts/test_agent.py
"""

import sys
import os

# Add parent directory to path so we can import from src
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Now we can import from src
from src.agent import NoSearchAgent, SearchAgent, RealWorldAgent
from src.utils import load_config


def test_no_search_agent():
    """Test the NoSearchAgent (baseline agent)."""
    print("\n" + "="*60)
    print("Testing NoSearchAgent (Baseline)")
    print("="*60)
    
    try:
        agent = NoSearchAgent()
        print("✓ NoSearchAgent initialized successfully")
        
        # Test question
        question = "What is the capital of France?"
        print(f"\nQuestion: {question}")
        print("Generating answer...")
        
        answer = agent.answer_question(question)
        print(f"\nAnswer: {answer}")
        print("\n✓ NoSearchAgent test completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Error testing NoSearchAgent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_agent():
    """Test the SearchAgent."""
    print("\n" + "="*60)
    print("Testing SearchAgent")
    print("="*60)
    
    try:
        agent = SearchAgent(max_steps=3, include_browse=False)
        print("✓ SearchAgent initialized successfully")
        
        # Test question that requires search
        question = "What is the latest news about artificial intelligence?"
        print(f"\nQuestion: {question}")
        print("Running agent (this may take a moment)...")
        
        trajectory = agent.run_trajectory(question)
        
        print(f"\n✓ Trajectory completed:")
        print(f"  - Total search steps: {trajectory.get('total_search_steps', 0)}")
        print(f"  - Final answer: {trajectory.get('final_answer', 'N/A')[:200]}...")
        
        if trajectory.get('steps'):
            print(f"\n  Search steps:")
            for i, step in enumerate(trajectory['steps'][:3], 1):  # Show first 3 steps
                print(f"    Step {i}: {step.get('action', 'unknown')} - {step.get('query', '')[:50]}")
        
        print("\n✓ SearchAgent test completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Error testing SearchAgent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loading():
    """Test configuration loading."""
    print("\n" + "="*60)
    print("Testing Configuration Loading")
    print("="*60)
    
    try:
        config = load_config()
        print("✓ Configuration loaded successfully")
        
        # Check required keys
        required_keys = ['DEEPSEEK_API_KEY', 'SERPER_API_KEY']
        missing_keys = [key for key in required_keys if not config.get(key)]
        
        if missing_keys:
            print(f"\n⚠ Warning: Missing API keys: {', '.join(missing_keys)}")
            print("  Make sure your .env file contains these keys")
        else:
            print("✓ All required API keys found")
        
        print(f"\nConfig keys: {list(config.keys())}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_world_agent():
    """Test the RealWorldAgent."""
    print("\n" + "="*60)
    print("Testing RealWorldAgent")
    print("="*60)
    
    try:
        agent = RealWorldAgent()
        print("✓ RealWorldAgent initialized successfully") 
        input_question = input("Enter your needs: ")
        print("Running agent (this may take a moment)...")
        result = agent.agent_loop(input_question)
        
        # Print trajectory to console
        
        # Save trajectory to file
        try:
            filepath = agent.save_trajectory_to_file(result)
            print(f"\n✓ Trajectory saved to: {filepath}")
        except Exception as e:
            print(f"\n⚠ Warning: Could not save trajectory to file: {e}")
        
        return True
    except Exception as e:
        print(f"\n✗ Error testing RealWorldAgent: {e}")
        import traceback
        traceback.print_exc()
        return False

def interactive_test():
    """Interactive test mode."""
    print("\n" + "="*60)
    print("Interactive Test Mode")
    print("="*60)
    print("\nChoose agent type:")
    print("1. NoSearchAgent (baseline)")
    print("2. SearchAgent")
    print("3. RealWorldAgent")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        agent = NoSearchAgent()
        print("\nEnter your question (or 'exit' to quit):")
        while True:
            question = input("\nQuestion: ").strip()
            if question.lower() == 'exit':
                break
            if question:
                try:
                    answer = agent.answer_question(question)
                    print(f"\nAnswer: {answer}")
                except Exception as e:
                    print(f"\nError: {e}")
    
    elif choice == "2":
        agent = SearchAgent(max_search_steps=3)
        print("\nEnter your question (or 'exit' to quit):")
        while True:
            question = input("\nQuestion: ").strip()
            if question.lower() == 'exit':
                break
            if question:
                try:
                    trajectory = agent.run_trajectory(question)
                    print(f"\nFinal Answer: {trajectory.get('final_answer', 'N/A')}")
                    print(f"Search Steps: {trajectory.get('total_search_steps', 0)}")
                except Exception as e:
                    print(f"\nError: {e}")
    
    elif choice == "3":
        test_real_world_agent()
        print("Test RealWorldAgent completed...")
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid choice")


def main():
    """Main test function."""
    print("\n" + "="*60)
    print("Agent Test Suite")
    print("="*60)
    
    # Test configuration first
    config_ok = test_config_loading()
    
    if not config_ok:
        print("\n⚠ Configuration test failed. Please check your .env file.")
        return
    
    # Run tests
    results = []
    
    # # Test NoSearchAgent
    # results.append(("NoSearchAgent", test_no_search_agent()))
    
    # Test SearchAgent (optional - comment out if you want to skip)
    # results.append(("SearchAgent", test_search_agent()))
    
    # # Print summary
    # print("\n" + "="*60)
    # print("Test Summary")
    # print("="*60)
    # for name, passed in results:
    #     status = "✓ PASSED" if passed else "✗ FAILED"
    #     print(f"{name}: {status}")
    
    # Ask for interactive mode
    print("\n" + "="*60)
    response = input("Run interactive test mode? (y/n): ").strip().lower()
    if response == 'y':
        interactive_test()


if __name__ == "__main__":
    main()

