from typing import Dict, Any
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
"""
def get_tools_schema(include_browse: bool = False) -> Dict[str, Any]:
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
    schemas.append( {
        "type": "function",
        "function": {
            "name": "answer",
            "description": "Information gathered are enough to answer the user query. Use this when you have enough information to answer the user query.",
            "parameters": {
                "type": "object",
                "properties": {
                },
                "required": []
            }
        }
    })
    
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