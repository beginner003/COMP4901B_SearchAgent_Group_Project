from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

# Use absolute imports for consistency
from src.utils import load_config
"""
Tool definitions and execution functions.
========================================
Tools:
- search: Search the web using Google Search via Serper API.
- browse: Browse a web page using BeautifulSoup.
- answer: Information gathered are enough to answer the user query. 
- read_notion_database: Read pages from a Notion database (Part II)
- create_notion_page: Create a new page in a Notion database (Part II)
- update_notion_page: Update an existing Notion page (Part II)
"""
def get_tools_schema(include_browse: bool = False, include_part2_tools: bool = False) -> List[Dict[str, Any]]:
    """Get schema for search tool for DeepSeek function calling format."""
    schemas = [{
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the web using Google Search via Serper API. Use this to find current information, facts, or recent events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of search results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
            }]
    if include_browse:
        schemas.append({
            "type": "function",
        "function": {
            "name": "browse",
            "description": "Fetch and extract text content from a web page URL. Use this when search results only provide snippets and you need full page content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the web page to browse"
                    }
                },
                "required": ["url"]
            }
        }
        })
    schemas.append({
        "type": "function",
        "function": {
            "name": "answer",
            "description": "Information gathered are enough to answer the user query. Use this when you have enough information to answer the user query.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    })
    
    # Part II tools - Notion API
    if include_part2_tools:
        schemas.extend([
            {
                "type": "function",
                "function": {
                    "name": "read_notion_database",
                    "description": "Read pages from a Notion database. Use this to retrieve existing meeting agendas, check meeting history, or get project status from the FYP database. You can filter by any combination of properties. Leave filter parameters empty if not needed. The database ID is automatically retrieved from configuration.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status_filter": {
                                "type": "object",
                                "description": "Filter by Status property. Leave empty if not filtering by status.",
                                "properties": {
                                    "condition": {
                                        "type": "string",
                                        "enum": ["equals", "does_not_equal", "is_empty", "is_not_empty"],
                                        "description": "Filter condition: 'equals' (e.g., 'Scheduled', 'Ongoing', 'Completed', 'Cancelled'), 'does_not_equal', 'is_empty', 'is_not_empty'"
                                    },
                                    "value": {
                                        "type": "string",
                                        "description": "Value to filter by (required for 'equals' and 'does_not_equal', ignored for 'is_empty'/'is_not_empty')"
                                    }
                                },
                                "required": ["condition"]
                            },
                            "meeting_date_filter": {
                                "type": "object",
                                "description": "Filter by Meeting Date property. Leave empty if not filtering by date.",
                                "properties": {
                                    "condition": {
                                        "type": "string",
                                        "enum": ["equals", "after", "before", "on_or_after", "on_or_before", "is_empty", "is_not_empty"],
                                        "description": "Filter condition: 'equals', 'after', 'before', 'on_or_after', 'on_or_before', 'is_empty', 'is_not_empty'"
                                    },
                                    "value": {
                                        "type": "string",
                                        "description": "Date value in ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Required for date comparisons, ignored for 'is_empty'/'is_not_empty'"
                                    }
                                },
                                "required": ["condition"]
                            },
                            "attendees_filter": {
                                "type": "object",
                                "description": "Filter by Attendees property (multi-select). Leave empty if not filtering by attendees.",
                                "properties": {
                                    "condition": {
                                        "type": "string",
                                        "enum": ["contains", "is_empty", "is_not_empty"],
                                        "description": "Filter condition: 'contains' (check if attendee name is in the list), 'is_empty', 'is_not_empty'"
                                    },
                                    "value": {
                                        "type": "string",
                                        "description": "Attendee name to search for (required for 'contains', ignored for 'is_empty'/'is_not_empty')"
                                    }
                                },
                                "required": ["condition"]
                            },
                            "discussion_topics_filter": {
                                "type": "object",
                                "description": "Filter by Discussion Topics property (rich text). Leave empty if not filtering by discussion topics.",
                                "properties": {
                                    "condition": {
                                        "type": "string",
                                        "enum": ["equals", "contains", "is_empty", "is_not_empty"],
                                        "description": "Filter condition: 'equals' (exact match), 'contains' (substring search), 'is_empty', 'is_not_empty'"
                                    },
                                    "value": {
                                        "type": "string",
                                        "description": "Text to search for (required for 'equals' and 'contains', ignored for 'is_empty'/'is_not_empty')"
                                    }
                                },
                                "required": ["condition"]
                            },
                            "action_items_filter": {
                                "type": "object",
                                "description": "Filter by Action Items property (rich text). Leave empty if not filtering by action items.",
                                "properties": {
                                    "condition": {
                                        "type": "string",
                                        "enum": ["equals", "contains", "is_empty", "is_not_empty"],
                                        "description": "Filter condition: 'equals' (exact match), 'contains' (substring search), 'is_empty', 'is_not_empty'"
                                    },
                                    "value": {
                                        "type": "string",
                                        "description": "Text to search for (required for 'equals' and 'contains', ignored for 'is_empty'/'is_not_empty')"
                                    }
                                },
                                "required": ["condition"]
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of pages to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_notion_page",
                    "description": "Create a new page in a Notion database. Use this to add a new meeting agenda entry to the FYP database. Leave property parameters empty if not setting that property. The database ID is automatically retrieved from configuration.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title of the new page (e.g., 'FYP Meeting - 2024-12-05')"
                            },
                            "meeting_date": {
                                "type": "string",
                                "description": "Meeting date in ISO 8601 format (YYYY-MM-DD). Leave empty if not setting date."
                            },
                            "status": {
                                "type": "string",
                                "enum": ["Scheduled", "Ongoing", "Completed", "Cancelled"],
                                "description": "Meeting status. Leave empty if not setting status."
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of attendee names. Leave empty if not setting attendees."
                            },
                            "discussion_topics": {
                                "type": "string",
                                "description": "Topics discussed in the meeting. Leave empty if not setting discussion topics."
                            },
                            "action_items": {
                                "type": "string",
                                "description": "Follow-up tasks and action items. Leave empty if not setting action items."
                            },
                            "children": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "description": "Content block following Notion API format. Each block must have 'object': 'block', 'type', and a property matching the type.",
                                    "properties": {
                                        "object": {
                                            "type": "string",
                                            "enum": ["block"],
                                            "description": "Must be 'block'"
                                        },
                                        "type": {
                                            "type": "string",
                                            "enum": ["heading_2", "heading_3", "paragraph", "bulleted_list_item", "numbered_list_item"],
                                            "description": "Type of content block"
                                        },
                                        "heading_2": {
                                            "type": "object",
                                            "description": "Content for heading_2 block (required if type is heading_2)",
                                            "properties": {
                                                "rich_text": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "type": {"type": "string", "enum": ["text"]},
                                                            "text": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "content": {"type": "string"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        "heading_3": {
                                            "type": "object",
                                            "description": "Content for heading_3 block (required if type is heading_3)",
                                            "properties": {
                                                "rich_text": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "type": {"type": "string", "enum": ["text"]},
                                                            "text": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "content": {"type": "string"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        "paragraph": {
                                            "type": "object",
                                            "description": "Content for paragraph block (required if type is paragraph)",
                                            "properties": {
                                                "rich_text": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "type": {"type": "string", "enum": ["text"]},
                                                            "text": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "content": {"type": "string"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        "bulleted_list_item": {
                                            "type": "object",
                                            "description": "Content for bulleted_list_item block (required if type is bulleted_list_item)",
                                            "properties": {
                                                "rich_text": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "type": {"type": "string", "enum": ["text"]},
                                                            "text": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "content": {"type": "string"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        "numbered_list_item": {
                                            "type": "object",
                                            "description": "Content for numbered_list_item block (required if type is numbered_list_item)",
                                            "properties": {
                                                "rich_text": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "type": {"type": "string", "enum": ["text"]},
                                                            "text": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "content": {"type": "string"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "required": ["object", "type"]
                                },
                                "description": "Content blocks (children) for the page following Notion API format. Leave empty if not adding content blocks."
                            }
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_notion_page",
                    "description": "Update an existing Notion page. Use this to modify meeting agenda properties. Leave property parameters empty if not updating that property.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "page_id": {
                                "type": "string",
                                "description": "The ID of the Notion page to update"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["Scheduled", "Ongoing", "Completed", "Cancelled"],
                                "description": "Update Status property. Leave empty if not updating status."
                            },
                            "meeting_date": {
                                "type": "string",
                                "description": "Update Meeting Date property in ISO 8601 format (YYYY-MM-DD). Leave empty if not updating date."
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Update Attendees property (list of attendee names). Leave empty if not updating attendees."
                            },
                            "discussion_topics": {
                                "type": "string",
                                "description": "Update Discussion Topics property. Leave empty if not updating discussion topics."
                            },
                            "action_items": {
                                "type": "string",
                                "description": "Update Action Items property. Leave empty if not updating action items."
                            }
                        },
                        "required": ["page_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send an email notification using Gmail API. Use this to send meeting agendas, reminders, or updates to attendees.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of recipient email addresses"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject line"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body content (plain text or HTML)"
                            },
                            "cc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of CC email addresses. Leave empty if not needed."
                            },
                            "bcc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of BCC email addresses. Leave empty if not needed."
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_calendar_event",
                    "description": "Create a calendar event using Google Calendar API. Use this to schedule meetings and send calendar invitations.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Event title/summary"
                            },
                            "description": {
                                "type": "string",
                                "description": "Event description/details. Leave empty if not needed."
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Event start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) or RFC3339 format. Include timezone if possible."
                            },
                            "end_time": {
                                "type": "string",
                                "description": "Event end time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) or RFC3339 format. Include timezone if possible."
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of attendee email addresses. Leave empty if no attendees."
                            },
                            "location": {
                                "type": "string",
                                "description": "Event location (physical address or meeting link). Leave empty if not needed."
                            },
                            "timezone": {
                                "type": "string",
                                "description": "Timezone for the event (e.g., 'Asia/Hong_Kong', 'America/New_York'). Defaults to system timezone if not specified."
                            }
                        },
                        "required": ["summary", "start_time", "end_time"]
                    }
                }
            }
        ])
    
    return schemas


def search_tool(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using Google Search via Serper API.
    
    Returns a dictionary with:
    - query: The search query
    - num_docs_requested: Number of documents requested
    - retrieved_documents: List of dicts with title, snippet, url
    - llm_readable: Formatted string for LLM to read
    """
    config = load_config()
    api_key = config.get("SERPER_API_KEY")
    
    if not api_key:
        return {
            "query": query,
            "num_docs_requested": num_results,
            "retrieved_documents": [],
            "llm_readable": "[search] Missing SERPER_API_KEY"
        }
    
    try:
        payload = {"q": query, "num": num_results}
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        resp = requests.post("https://google.serper.dev/search", json=payload, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            error_msg = f"[search] HTTP {resp.status_code}: {resp.text[:200]}"
            return {
                "query": query,
                "num_docs_requested": num_results,
                "retrieved_documents": [],
                "llm_readable": error_msg
            }
        
        data = resp.json()
        organic = data.get("organic", [])
        
        # Build retrieved_documents list
        retrieved_documents = []
        llm_lines = []
        
        for i, item in enumerate(organic[:num_results], start=1):
            title = item.get("title") or ""
            snippet = item.get("snippet") or ""
            url = item.get("link") or ""  
            
            # Add to retrieved_documents
            retrieved_documents.append({
                "title": title,
                "snippet": snippet,
                "url": url
            })
            
            # Build LLM-readable format
            llm_lines.append(f"{i}. {title}\n{snippet}\nURL: {url}")
        
        llm_readable = "\n\n".join(llm_lines) if llm_lines else "[search] No results"
        
        return {
            "query": query,
            "num_docs_requested": num_results,
            "retrieved_documents": retrieved_documents,
            "llm_readable": llm_readable
        }
        
    except Exception as e:
        error_msg = f"[search] Error: {e}"
        return {
            "query": query,
            "num_docs_requested": num_results,
            "retrieved_documents": [],
            "llm_readable": error_msg
        }


def browse_tool(url: str) -> str:
    """
    Browse a web page using BeautifulSoup.
    """
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            return f"[browse] HTTP {resp.status_code}: {resp.text[:200]}"
        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
        text = "\n\n".join(paragraphs)
        return {"content": text[:5000] if text else "[browse] No textual content", "url": url}
    except Exception as e:
        return {"content": f"[browse] Error: {e}", "url": url}  

def answer_tool() -> bool:
    """
    Information gathered are enough to answer the user query.
    """
    return True

"""
Extra tools for Part II --  Realistic agent with multiple tools.
"""


# ============================================================================
# Notion API Tools for FYP Meeting Agenda Automation
# ============================================================================

def read_notion_database(
    status_filter: Optional[Dict[str, Any]] = None,
    meeting_date_filter: Optional[Dict[str, Any]] = None,
    attendees_filter: Optional[Dict[str, Any]] = None,
    discussion_topics_filter: Optional[Dict[str, Any]] = None,
    action_items_filter: Optional[Dict[str, Any]] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Query a Notion database and retrieve pages.
    
    This function uses the Notion API v2025-09-03 which requires querying data sources
    rather than databases directly. It will:
    1. Retrieve the database to get the data source ID(s)
    2. Query the first data source (most databases have only one)
    
    Filter by database properties using separate filter parameters:
    - status_filter: Filter by Status (e.g., {"condition": "equals", "value": "Scheduled"})
    - meeting_date_filter: Filter by Meeting Date (e.g., {"condition": "after", "value": "2024-01-01"})
    - attendees_filter: Filter by Attendees (e.g., {"condition": "contains", "value": "John"})
    - discussion_topics_filter: Filter by Discussion Topics (e.g., {"condition": "contains", "value": "agenda"})
    - action_items_filter: Filter by Action Items (e.g., {"condition": "contains", "value": "review"})
    
    Multiple filters are combined with AND logic. Leave filter parameters empty if not needed.
    
    Returns:
        {
            "database_id": "...",
            "pages": [...],
            "total_found": 5,
            "llm_readable": "Found 5 meeting agendas:\n..."
        }
    """
    
    config = load_config()
    api_key = config.get("NOTION_API_KEY")
    database_id = config.get("NOTION_DATABASE_ID")
    
    if not api_key or not database_id:
        return {
            "database_id": database_id,
            "pages": [],
            "total_found": 0,
            "llm_readable": "[notion] Missing NOTION_API_KEY or DATABASE_ID"
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }
        
        # Step 1: Retrieve the database to get the data source ID(s)
        # According to Notion API v2025-09-03, databases contain data sources
        # We need to query the data source, not the database directly
        retrieve_db_url = f"https://api.notion.com/v1/databases/{database_id}"
        db_resp = requests.get(retrieve_db_url, headers=headers, timeout=10)
        
        if db_resp.status_code != 200:
            error_text = db_resp.text[:500]
            raise Exception(f"Failed to retrieve database {db_resp.status_code}: {error_text}")
        
        try:
            db_data = db_resp.json()
        except Exception as e:
            raise Exception(f"Failed to parse database response: {e}")
        
        if db_data is None:
            raise Exception("Database response is None")
        
        data_sources = db_data.get("data_sources", [])
        
        if not data_sources:
            raise Exception("Database has no data sources")
        
        # Use the first data source (most databases have only one)
        first_data_source = data_sources[0]
        if first_data_source is None:
            raise Exception("First data source is None")
        
        if not isinstance(first_data_source, dict):
            raise Exception(f"Data source is not a dictionary: {type(first_data_source)}")
        
        data_source_id = first_data_source.get("id")
        if not data_source_id:
            raise Exception("Data source ID not found")
        
        # Step 2: Query the data source using the data source ID
        query_url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
        
        payload = {
            "page_size": min(max_results, 100)
        }
        
        # Build filters from separate parameters
        filter_parts = []
        
        # Process status filter
        if status_filter and status_filter.get("condition"):
            condition = status_filter["condition"]
            value = status_filter.get("value")
            
            if condition == "equals":
                filter_parts.append({"property": "Status", "status": {"equals": value}})
            elif condition == "does_not_equal":
                filter_parts.append({"property": "Status", "status": {"does_not_equal": value}})
            elif condition == "is_empty":
                filter_parts.append({"property": "Status", "status": {"is_empty": True}})
            elif condition == "is_not_empty":
                filter_parts.append({"property": "Status", "status": {"is_not_empty": True}})
        
        # Process meeting date filter
        if meeting_date_filter and meeting_date_filter.get("condition"):
            condition = meeting_date_filter["condition"]
            value = meeting_date_filter.get("value")
            
            if condition == "equals":
                filter_parts.append({"property": "Meeting Date", "date": {"equals": value}})
            elif condition == "after":
                filter_parts.append({"property": "Meeting Date", "date": {"after": value}})
            elif condition == "before":
                filter_parts.append({"property": "Meeting Date", "date": {"before": value}})
            elif condition == "on_or_after":
                filter_parts.append({"property": "Meeting Date", "date": {"on_or_after": value}})
            elif condition == "on_or_before":
                filter_parts.append({"property": "Meeting Date", "date": {"on_or_before": value}})
            elif condition == "is_empty":
                filter_parts.append({"property": "Meeting Date", "date": {"is_empty": True}})
            elif condition == "is_not_empty":
                filter_parts.append({"property": "Meeting Date", "date": {"is_not_empty": True}})
        
        # Process attendees filter
        if attendees_filter and attendees_filter.get("condition"):
            condition = attendees_filter["condition"]
            value = attendees_filter.get("value")
            
            if condition == "contains":
                filter_parts.append({"property": "Attendees", "multi_select": {"contains": value}})
            elif condition == "is_empty":
                filter_parts.append({"property": "Attendees", "multi_select": {"is_empty": True}})
            elif condition == "is_not_empty":
                filter_parts.append({"property": "Attendees", "multi_select": {"is_not_empty": True}})
        
        # Process discussion topics filter
        if discussion_topics_filter and discussion_topics_filter.get("condition"):
            condition = discussion_topics_filter["condition"]
            value = discussion_topics_filter.get("value")
            
            if condition == "equals":
                filter_parts.append({"property": "Discussion Topics", "rich_text": {"equals": value}})
            elif condition == "contains":
                filter_parts.append({"property": "Discussion Topics", "rich_text": {"contains": value}})
            elif condition == "is_empty":
                filter_parts.append({"property": "Discussion Topics", "rich_text": {"is_empty": True}})
            elif condition == "is_not_empty":
                filter_parts.append({"property": "Discussion Topics", "rich_text": {"is_not_empty": True}})
        
        # Process action items filter
        if action_items_filter and action_items_filter.get("condition"):
            condition = action_items_filter["condition"]
            value = action_items_filter.get("value")
            
            if condition == "equals":
                filter_parts.append({"property": "Action Items", "rich_text": {"equals": value}})
            elif condition == "contains":
                filter_parts.append({"property": "Action Items", "rich_text": {"contains": value}})
            elif condition == "is_empty":
                filter_parts.append({"property": "Action Items", "rich_text": {"is_empty": True}})
            elif condition == "is_not_empty":
                filter_parts.append({"property": "Action Items", "rich_text": {"is_not_empty": True}})
        
        # Build final filter: combine multiple filters with AND, or use single filter
        filter_dict = None
        if filter_parts:
            if len(filter_parts) == 1:
                filter_dict = filter_parts[0]
            else:
                filter_dict = {"and": filter_parts}
        
        if filter_dict:
            payload["filter"] = filter_dict
        
        # Handle pagination - collect all pages up to max_results
        all_results = []
        has_more = True
        start_cursor = None
        
        while has_more and len(all_results) < max_results:
            if start_cursor:
                payload["start_cursor"] = start_cursor
            
            resp = requests.post(query_url, json=payload, headers=headers, timeout=10)
            if resp.status_code != 200:
                error_text = resp.text[:500]
                raise Exception(f"Notion API error {resp.status_code}: {error_text}")
            
            try:
                response = resp.json()
            except Exception as e:
                raise Exception(f"Failed to parse query response: {e}")
            
            if response is None:
                raise Exception("Query response is None")
            
            if not isinstance(response, dict):
                raise Exception(f"Query response is not a dictionary: {type(response)}")
            
            results = response.get("results", [])
            if results is None:
                results = []
            
            all_results.extend(results)
            
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
            
            # Break if no more results or we've collected enough
            if not has_more or len(all_results) >= max_results:
                break
        
        # Limit to max_results
        pages = []
        llm_lines = []
        
        for page in all_results[:max_results]:
            # Extract Meeting Title (title property)
            title = "Untitled"
            properties = page.get("properties")
            
            for prop_name, prop_value in properties.items():
                if prop_value is None:
                    continue
                if prop_value.get("type") == "title":
                    title_parts = prop_value.get("title", [])
                    if title_parts:
                        title = title_parts[0].get("plain_text", "Untitled")
                    break
            
            # Extract other properties
            page_props = {}
            for prop_name, prop_value in properties.items():
                if prop_value is None:
                    continue
                prop_type = prop_value.get("type")
                
                if prop_name == "Meeting Date" and prop_type == "date":
                    date_obj = prop_value.get("date")
                    if date_obj and isinstance(date_obj, dict):
                        page_props["Meeting Date"] = date_obj.get("start", "")
                    else:
                        page_props["Meeting Date"] = ""
                
                elif prop_name == "Status" and prop_type == "status":
                    status_obj = prop_value.get("status")
                    if status_obj and isinstance(status_obj, dict):
                        page_props["Status"] = status_obj.get("name", "")
                    else:
                        page_props["Status"] = ""
                
                elif prop_name == "Attendees" and prop_type == "multi_select":
                    attendees_list = prop_value.get("multi_select", [])
                    page_props["Attendees"] = [opt.get("name") for opt in attendees_list if isinstance(opt, dict) and opt.get("name")]
                
                elif prop_name == "Discussion Topics" and prop_type == "rich_text":
                    rich_text = prop_value.get("rich_text", [])
                    page_props["Discussion Topics"] = rich_text[0].get("plain_text", "") if rich_text and isinstance(rich_text[0], dict) else ""
                
                elif prop_name == "Action Items" and prop_type == "rich_text":
                    rich_text = prop_value.get("rich_text", [])
                    page_props["Action Items"] = rich_text[0].get("plain_text", "") if rich_text and isinstance(rich_text[0], dict) else ""
            
            # Check if this is a blank page (empty title and all properties empty)
            is_blank = (title == "Untitled" and 
                       (not page_props.get("Meeting Date") and 
                        not page_props.get("Status") and 
                        not page_props.get("Attendees") and 
                        not page_props.get("Discussion Topics") and 
                        not page_props.get("Action Items")))
            
            if is_blank:
                # Skip blank pages
                continue
            
            page_info = {
                "page_id": page.get("id"),
                "title": title,
                "properties": page_props,
                "url": page.get("url", "")
            }
            pages.append(page_info)
            
            # Build LLM-readable format
            # Add page id
            props_str = ", ".join([f"{k}: {v}" for k, v in page_props.items()])
            llm_lines.append(f"- Title: {title} | Properties: {props_str} | Page ID: {page.get('id')} | URL: {page.get('url', '')}")
        
        llm_readable = f"Found {len(pages)} pages:\n" + "\n".join(llm_lines) if llm_lines else "No pages found"
        
        return {
            "database_id": database_id,
            "pages": pages,
            "total_found": len(pages),
            "llm_readable": llm_readable
        }
        
    except Exception as e:
        import traceback
        error_details = str(e)
        tb_str = traceback.format_exc()
        error_msg = f"[notion] Error: {error_details}"
        # Include traceback in error message for debugging
        if "NoneType" in error_details or "object has no attribute 'get'" in error_details:
            error_msg += f"\nTraceback: {tb_str}"
        return {
            "database_id": database_id,
            "pages": [],
            "total_found": 0,
            "llm_readable": error_msg
        }


def create_notion_page(
    title: str,
    meeting_date: Optional[str] = None,
    status: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    discussion_topics: Optional[str] = None,
    action_items: Optional[str] = None,
    children: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create a new page in a Notion database using POST request.
    
    According to Notion API v2025-09-03: POST /v1/pages
    See: https://developers.notion.com/reference/post-page
    
    The database ID is automatically retrieved from configuration (NOTION_DATABASE_ID).
    
    Parameters:
        title: Title of the new page
        meeting_date: Optional date in ISO 8601 format (YYYY-MM-DD)
        status: Optional status (Scheduled, Ongoing, Completed, Cancelled)
        attendees: Optional list of attendee names
        discussion_topics: Optional discussion topics text
        action_items: Optional action items text
        children: Optional list of content blocks following Notion API format
    
    Returns:
        {
            "page_id": "...",
            "title": "...",
            "url": "https://notion.so/...",
            "created": True,
            "llm_readable": "Created new page '...' at https://notion.so/..."
        }
    """
    config = load_config()
    api_key = config.get("NOTION_API_KEY")
    database_id = config.get("NOTION_DATABASE_ID")
    
    if not api_key:
        return {
            "page_id": "",
            "title": title,
            "url": "",
            "created": False,
            "llm_readable": "[notion] Missing NOTION_API_KEY"
        }
    
    if not database_id:
        return {
            "page_id": "",
            "title": title,
            "url": "",
            "created": False,
            "llm_readable": "[notion] Missing NOTION_DATABASE_ID in configuration"
        }
    
    try:
        # First, get the data source ID from the database
        # According to Notion API v2025-09-03, we need to use data_source_id as parent
        retrieve_db_url = f"https://api.notion.com/v1/databases/{database_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }
        
        db_resp = requests.get(retrieve_db_url, headers=headers, timeout=10)
        if db_resp.status_code != 200:
            error_text = db_resp.text[:500]
            raise Exception(f"Failed to retrieve database {db_resp.status_code}: {error_text}")
        
        db_data = db_resp.json()
        data_sources = db_data.get("data_sources", [])
        
        if not data_sources:
            raise Exception("Database has no data sources")
        
        # Use the first data source
        data_source_id = data_sources[0].get("id")
        if not data_source_id:
            raise Exception("Data source ID not found")
        
        # Build properties dict
        page_properties = {
            "Meeting Title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        }
        
        # Add Meeting Date if provided
        if meeting_date:
            page_properties["Meeting Date"] = {
                "date": {
                    "start": meeting_date
                }
            }
        
        # Add Status if provided
        if status:
            valid_statuses = ["Scheduled", "Ongoing", "Completed", "Cancelled"]
            if status in valid_statuses:
                page_properties["Status"] = {
                    "status": {
                        "name": status
                    }
                }
            else:
                raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        # Add Attendees if provided
        if attendees is not None:
            if isinstance(attendees, list):
                page_properties["Attendees"] = {
                    "multi_select": [
                        {"name": attendee} for attendee in attendees
                    ]
                }
            else:
                raise ValueError("Attendees must be a list")
        
        # Add Discussion Topics if provided
        if discussion_topics is not None:
            page_properties["Discussion Topics"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": str(discussion_topics)
                        }
                    }
                ]
            }
        
        # Add Action Items if provided
        if action_items is not None:
            page_properties["Action Items"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": str(action_items)
                        }
                    }
                ]
            }
        
        # Build payload
        payload = {
            "parent": {
                "type": "data_source_id",
                "data_source_id": data_source_id
            },
            "properties": page_properties
        }
        
        # Add children if provided (use as-is, assuming they follow Notion API format)
        if children:
            payload["children"] = children
        
        # Create page using POST request
        create_url = "https://api.notion.com/v1/pages"
        resp = requests.post(create_url, json=payload, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            error_text = resp.text[:500]
            raise Exception(f"Notion API error {resp.status_code}: {error_text}")
        
        # Get created page data
        page_data = resp.json()
        page_id = page_data.get("id", "")
        page_url = page_data.get("url", "")
        
        return {
            "page_id": page_id,
            "title": title,
            "url": page_url,
            "created": True,
            "llm_readable": f"Created new page '{title}' with page id {page_id}"
        }
        
    except Exception as e:
        error_msg = f"[notion] Error: {e}"
        return {
            "page_id": "",
            "title": title,
            "url": "",
            "created": False,
            "llm_readable": error_msg
        }


def update_notion_page(
    page_id: str,
    status: Optional[str] = None,
    meeting_date: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    discussion_topics: Optional[str] = None,
    action_items: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing Notion page using PATCH request.
    
    Updates page properties based on provided parameters. Leave parameters empty if not updating that property.
    
    According to Notion API v2025-09-03: PATCH /v1/pages/{page_id}
    See: https://developers.notion.com/reference/patch-page
    
    Returns:
        {
            "page_id": "...",
            "updated": True,
            "url": "https://notion.so/...",
            "llm_readable": "Updated page at https://notion.so/..."
        }
    """
    config = load_config()
    api_key = config.get("NOTION_API_KEY")
    
    if not api_key:
        return {
            "page_id": page_id,
            "updated": False,
            "url": "",
            "llm_readable": "[notion] Missing NOTION_API_KEY"
        }
    
    try:
        # Build properties update dict
        properties_update = {}
        
        # Update Status if provided
        if status:
            valid_statuses = ["Scheduled", "Ongoing", "Completed", "Cancelled"]
            if status in valid_statuses:
                properties_update["Status"] = {
                    "status": {
                        "name": status
                    }
                }
            else:
                raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        # Update Meeting Date if provided
        if meeting_date:
            properties_update["Meeting Date"] = {
                "date": {
                    "start": meeting_date
                }
            }
        
        # Update Attendees if provided
        if attendees is not None:
            if isinstance(attendees, list):
                properties_update["Attendees"] = {
                    "multi_select": [
                        {"name": attendee} for attendee in attendees
                    ]
                }
            else:
                raise ValueError("Attendees must be a list")
        
        # Update Discussion Topics if provided
        if discussion_topics is not None:
            properties_update["Discussion Topics"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": str(discussion_topics)
                        }
                    }
                ]
            }
        
        # Update Action Items if provided
        if action_items is not None:
            properties_update["Action Items"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": str(action_items)
                        }
                    }
                ]
            }
        
        # If no properties to update, return early
        if not properties_update:
            return {
                "page_id": page_id,
                "updated": False,
                "url": "",
                "llm_readable": "[notion] No properties provided to update"
            }
        
        # Make PATCH request to update page
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }
        
        payload = {
            "properties": properties_update
        }
        
        resp = requests.patch(update_url, json=payload, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            error_text = resp.text[:500]
            raise Exception(f"Notion API error {resp.status_code}: {error_text}")
        
        # Get updated page data
        page_data = resp.json()
        page_url = page_data.get("url", "")
        
        return {
            "page_id": page_id,
            "updated": True,
            "url": page_url,
            "llm_readable": f"Updated page with page id {page_id}"
        }
        
    except Exception as e:
        error_msg = f"[notion] Error: {e}"
        return {
            "page_id": page_id,
            "updated": False,
            "url": "",
            "llm_readable": error_msg
        }

# ============================================================================
# Email and Calendar Tools for FYP Meeting Agenda Automation
# ============================================================================

def send_email(
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send an email notification using Gmail API.
    
    Parameters:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content (plain text or HTML)
        cc: Optional list of CC email addresses
        bcc: Optional list of BCC email addresses
    
    Returns:
        {
            "sent": True/False,
            "id": "message_id",
            "threadId": "thread_id",
            "recipients": [...],
            "llm_readable": "Email sent successfully to ..."
        }
    """
    import base64
    config = load_config()
    token = config.get("GMAIL_ACCESS_TOKEN")
    
    if not token:
        return {
            "sent": False,
            "error": "Missing GMAIL_ACCESS_TOKEN",
            "recipients": to,
            "llm_readable": "[email] Missing GMAIL_ACCESS_TOKEN"
        }
    
    # Clean token (remove whitespace, newlines)
    token = token.strip()
    
    try:
        # Build email headers
        to_header = ", ".join(to)
        headers_list = [f"To: {to_header}", f"Subject: {subject}"]
        
        if cc:
            headers_list.append(f"Cc: {', '.join(cc)}")
        if bcc:
            headers_list.append(f"Bcc: {', '.join(bcc)}")
        
        headers_list.append("Content-Type: text/plain; charset=utf-8")
        headers_str = "\r\n".join(headers_list)
        
        # Build raw email message
        raw = f"{headers_str}\r\n\r\n{body}".encode("utf-8")
        b64 = base64.urlsafe_b64encode(raw).decode("utf-8")
        
        # Send email via Gmail API
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        # Ensure token is clean (no whitespace/newlines)
        token_clean = token.strip()
        headers = {"Authorization": f"Bearer {token_clean}", "Content-Type": "application/json"}
        payload = {"raw": b64}
        
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            error_text = resp.text[:500]
            error_details = ""
            try:
                error_json = resp.json()
                error_details = f" - {error_json.get('error', {}).get('message', '')}"
            except:
                pass
            
            return {
                "sent": False,
                "error": f"HTTP {resp.status_code}{error_details}: {error_text}",
                "recipients": to,
                "llm_readable": f"[email] Failed to send: HTTP {resp.status_code}{error_details}"
            }
        
        data = resp.json()
        all_recipients = to + (cc or []) + (bcc or [])
        
        return {
            "sent": True,
            "id": data.get("id", ""),
            "threadId": data.get("threadId", ""),
            "recipients": all_recipients,
            "llm_readable": f"Email sent successfully to {', '.join(to)}"
        }
        
    except Exception as e:
        error_msg = f"[email] Error: {e}"
        return {
            "sent": False,
            "error": str(e),
            "recipients": to,
            "llm_readable": error_msg
        }


def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    location: Optional[str] = None,
    timezone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a calendar event using Google Calendar API.
    
    Parameters:
        summary: Event title/summary
        start_time: Event start time in ISO 8601 or RFC3339 format
        end_time: Event end time in ISO 8601 or RFC3339 format
        description: Optional event description/details
        attendees: Optional list of attendee email addresses
        location: Optional event location (physical address or meeting link)
        timezone: Optional timezone (e.g., 'Asia/Hong_Kong', 'America/New_York')
    
    Returns:
        {
            "created": True/False,
            "id": "event_id",
            "htmlLink": "calendar_link",
            "llm_readable": "Calendar event created: ..."
        }
    """
    config = load_config()
    token = config.get("GOOGLE_CALENDAR_ACCESS_TOKEN") or config.get("GMAIL_ACCESS_TOKEN")
    
    if not token:
        return {
            "created": False,
            "error": "Missing GOOGLE_CALENDAR_ACCESS_TOKEN",
            "id": "",
            "htmlLink": "",
            "llm_readable": "[calendar] Missing GOOGLE_CALENDAR_ACCESS_TOKEN"
        }
    
    try:
        calendar_id = "primary"
        # Ensure token is clean (no whitespace/newlines)
        token_clean = token.strip()
        headers = {"Authorization": f"Bearer {token_clean}", "Content-Type": "application/json"}
        
        # Build event body
        body: Dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time}
        }
        
        if description:
            body["description"] = description
        
        if attendees:
            body["attendees"] = [{"email": email} for email in attendees]
        
        if location:
            body["location"] = location
        
        if timezone:
            body["start"]["timeZone"] = timezone
            body["end"]["timeZone"] = timezone
        
        # Create event via Google Calendar API
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        resp = requests.post(url, json=body, headers=headers, timeout=15)
        
        if resp.status_code not in (200, 201):
            error_text = resp.text[:500]
            error_details = ""
            try:
                error_json = resp.json()
                error_msg = error_json.get('error', {}).get('message', '')
                error_details = f" - {error_msg}"
                if 'insufficientPermissions' in error_text or 'insufficient' in error_msg.lower():
                    error_details += "\n  → You need to authorize Google Calendar API scope in OAuth Playground"
                    error_details += "\n  → Required scope: https://www.googleapis.com/auth/calendar"
            except:
                pass
            
            return {
                "created": False,
                "error": f"HTTP {resp.status_code}{error_details}: {error_text}",
                "id": "",
                "htmlLink": "",
                "llm_readable": f"[calendar] Failed to create event: HTTP {resp.status_code}{error_details}"
            }
        
        data = resp.json()
        event_id = data.get("id", "")
        html_link = data.get("htmlLink", "")
        
        return {
            "created": True,
            "id": event_id,
            "htmlLink": html_link,
            "llm_readable": f"Calendar event created: {summary} at {html_link}"
        }
        
    except Exception as e:
        error_msg = f"[calendar] Error: {e}"
        return {
            "created": False,
            "error": str(e),
            "id": "",
            "htmlLink": "",
            "llm_readable": error_msg
        }