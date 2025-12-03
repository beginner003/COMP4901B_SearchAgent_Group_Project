#!/usr/bin/env python3
"""
Minimal test script for Notion API tools

Usage:
    PYTHONPATH=. python scripts/test_notion_tools.py
"""

import sys
import os

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.tools import read_notion_database, create_notion_page, update_notion_page
from src.utils import load_config


def test_read_database():
    """Test reading from Notion database."""
    print("\n" + "="*60)
    print("Test 1: Read Notion Database")
    print("="*60)
    
    config = load_config()
    database_id = config.get("NOTION_DATABASE_ID") or input("Enter Notion database ID: ").strip()
    
    if not database_id:
        print("⚠ Skipping test - no database ID provided")
        return False
    
    try:
        print(f"Reading from database: {database_id[:20]}...")
        print("  (No filters applied - retrieving all pages)")
        result = read_notion_database(database_id, max_results=10)
        
        print(f"\n✓ Success!")
        print(f"  Total found: {result.get('total_found', 0)}")
        print(f"\n  LLM readable output:")
        print(f"  {result.get('llm_readable', 'N/A')}")
        
        if result.get('pages'):
            print(f"\n  Pages retrieved ({len(result['pages'])}):")
            for i, page in enumerate(result['pages'], 1):
                print(f"\n  Page {i}:")
                print(f"    Title: {page.get('title', 'N/A')}")
                print(f"    Page ID: {page.get('page_id', 'N/A')}")
                print(f"    Properties:")
                props = page.get('properties', {})
                for prop_name, prop_value in props.items():
                    print(f"      - {prop_name}: {prop_value}")
        else:
            print("\n  No pages found (or all pages were blank and skipped)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_page():
    """Test creating a new Notion page."""
    print("\n" + "="*60)
    print("Test 2: Create Notion Page")
    print("="*60)
    
    config = load_config()
    database_id = config.get("NOTION_DATABASE_ID") or input("Enter Notion database ID: ").strip()
    
    if not database_id:
        print("⚠ Skipping test - no database ID provided")
        return False
    
    try:
        test_title = "Test Meeting - " + str(os.urandom(4).hex())
        print(f"Creating page with title: {test_title}")
        
        result = create_notion_page(
            database_id=database_id,
            title=test_title,
            meeting_date="2024-12-10",
            status="Scheduled",
            attendees=["Test User 1", "Test User 2"],
            discussion_topics="Testing Notion API integration",
            action_items="Verify tool works correctly",
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Test Agenda"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Test item 1"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Test item 2"
                                }
                            }
                        ]
                    }
                }
            ]
        )
        
        print(f"\n✓ Success!")
        print(f"  Created: {result.get('created', False)}")
        print(f"  Page ID: {result.get('page_id', 'N/A')[:20]}...")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  LLM readable: {result.get('llm_readable', 'N/A')}")
        
        # Return page_id for cleanup/update test
        return result.get('page_id')
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_update_page(page_id: str):
    """Test updating a Notion page."""
    print("\n" + "="*60)
    print("Test 3: Update Notion Page")
    print("="*60)
    
    if not page_id:
        print("⚠ Skipping test - no page ID available")
        return False
    
    try:
        print(f"Updating page: {page_id[:20]}...")
        
        result = update_notion_page(
            page_id=page_id,
            status="Completed",
            discussion_topics="Updated: testing update_notion_page function",
            action_items="1. testing update_notion_page function\n2. testing update_notion_page function"
        )
        
        print(f"\n✓ Success!")
        print(f"  Updated: {result.get('updated', False)}")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  LLM readable: {result.get('llm_readable', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_meeting_agenda():
    """Test creating a meeting agenda for tomorrow's meeting."""
    print("\n" + "="*60)
    print("Test: Create Meeting Agenda (Tomorrow)")
    print("="*60)
    
    config = load_config()
    database_id = config.get("NOTION_DATABASE_ID") or input("Enter Notion database ID: ").strip()
    
    if not database_id:
        print("⚠ Skipping test - no database ID provided")
        return False
    
    try:
        from datetime import datetime, timedelta
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        title = f"FYP Meeting - {tomorrow_str}"
        print(f"Creating meeting agenda: {title}")
        
        result = create_notion_page(
            database_id=database_id,
            title=title,
            meeting_date=tomorrow_str,
            status="Scheduled",
            discussion_topics="System Architecture Diagram - Review and discuss the current system architecture design, components, and integration points. AI Model Training Progress - Update on model training status, performance metrics, challenges encountered, and next steps.",
            action_items="To be discussed during meeting",
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Meeting Agenda"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "1. System Architecture Diagram"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Review and discuss the current system architecture design, components, and integration points."
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "2. AI Model Training Progress"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Update on model training status, performance metrics, challenges encountered, and next steps."
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "3. Action Items & Next Steps"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "To be discussed during meeting"
                                }
                            }
                        ]
                    }
                }
            ]
        )
        
        print(f"\n✓ Success!")
        print(f"  Created: {result.get('created', False)}")
        print(f"  Page ID: {result.get('page_id', 'N/A')}")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  LLM readable: {result.get('llm_readable', 'N/A')}")
        
        return result.get('created', False)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_read_database_with_filters():
    """Test reading from Notion database with new filter parameters."""
    print("\n" + "="*60)
    print("Test 1b: Read Notion Database with Filters")
    print("="*60)
    
    config = load_config()
    database_id = config.get("NOTION_DATABASE_ID") or input("Enter Notion database ID: ").strip()
    
    if not database_id:
        print("⚠ Skipping test - no database ID provided")
        return False
    
    try:
        print("Testing with Status filter: Scheduled")
        result = read_notion_database(
            database_id=database_id,
            discussion_topics_filter={"condition": "contains", "value": "testing"},
            max_results=5
        )
        
        print(f"\n✓ Success!")
        print(f"  Total found: {result.get('total_found', 0)}")
        print(f"  LLM readable:\n{result.get('llm_readable', 'N/A')[:200]}...")
        
        # Test with multiple filters
        print("\nTesting with multiple filters: Status=Scheduled AND Meeting Date after 2024-01-01")
        result2 = read_notion_database(
            database_id=database_id,
            status_filter={"condition": "equals", "value": "Scheduled"},
            meeting_date_filter={"condition": "after", "value": "2024-01-01"},
            max_results=5
        )
        
        print(f"\n✓ Success!")
        print(f"  Total found: {result2.get('total_found', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run selected Notion API tool test."""
    print("="*60)
    print("Notion API Tools Test Suite")
    print("="*60)
    
    # Check config
    config = load_config()
    if not config.get("NOTION_API_KEY"):
        print("\n⚠ Warning: NOTION_API_KEY not found in .env")
        print("  Add it to your .env file to run tests")
        return
    
    print("✓ NOTION_API_KEY found")
    
    # Menu for selecting test
    print("\n" + "="*60)
    print("Select test to run:")
    print("="*60)
    print("1. Read Database (no filters)")
    print("2. Read Database (with filters)")
    print("3. Create Page")
    print("4. Update Page")
    print("5. Create Meeting Agenda (Tomorrow)")
    print("="*60)
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    result = None
    test_name = ""
    
    if choice == "1":
        test_name = "Read Database (No Filters)"
        result = test_read_database()
    elif choice == "2":
        test_name = "Read Database (With Filters)"
        result = test_read_database_with_filters()
    elif choice == "3":
        test_name = "Create Page"
        created_page_id = test_create_page()
        result = created_page_id is not None
    elif choice == "4":
        test_name = "Update Page"
        # Allow user to specify page ID or use default
        page_id = input("\nEnter page ID to update (or press Enter for default: 2bee7c813e1c818c9307cc30152eaeac): ").strip()
        if not page_id:
            page_id = "2bee7c813e1c818c9307cc30152eaeac"
        result = test_update_page(page_id)
    elif choice == "5":
        test_name = "Create Meeting Agenda (Tomorrow)"
        result = test_create_meeting_agenda()
    else:
        print(f"\n✗ Invalid choice: {choice}")
        return
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    if result is not None:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    else:
        print(f"{test_name}: Not run")
    print("="*60)


if __name__ == "__main__":
    main()

