from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
from utils import load_config
"""
Tool definitions and execution functions.
========================================
Tools:
- search: Search the web using Google Search via Serper API.
- browse: Browse a web page using BeautifulSoup.
- answer: Information gathered are enough to answer the user query. 
"""
def get_tools_schema() -> Dict[str, Any]:
    """Get schema for search tool for DeepSeek function calling format."""
    return [{
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
    },
    {"type": "function",
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
    },
    {
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
    }
    ]

def get_tools_schema_filtered(allowed: List[str]) -> List[Dict[str, Any]]:
    full = get_tools_schema()
    return [t for t in full if t.get("function", {}).get("name") in allowed]


def _serper_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    config = load_config()
    api_key = config.get("SERPER_API_KEY")
    if not api_key:
        return []
    payload = {"q": query}
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    resp = requests.post("https://google.serper.dev/search", json=payload, headers=headers, timeout=15)
    if resp.status_code != 200:
        return []
    data = resp.json()
    organic = data.get("organic", [])
    docs = []
    for item in organic[:num_results]:
        docs.append({
            "title": item.get("title") or "",
            "snippet": item.get("snippet") or "",
            "url": item.get("link") or "",
        })
    return docs


def search_tool(query: str) -> Dict[str, Any]:
    """
    Search the web using Google Search via Serper API.
    """
    try:
        docs = _serper_search(query, num_results=5)
        if not docs:
            return {"text": "[search] No results or missing SERPER_API_KEY", "log": {"action": "search", "query": query, "num_docs_requested": 5, "retrieved_documents": []}}
        lines = []
        for i, item in enumerate(docs, start=1):
            lines.append(f"{i}. {item['title']}\n{item['snippet']}\nURL: {item['url']}")
        return {
            "text": "\n\n".join(lines),
            "log": {
                "action": "search",
                "query": query,
                "num_docs_requested": 5,
                "retrieved_documents": [{"title": d["title"], "snippet": d["snippet"]} for d in docs],
            },
        }
    except Exception as e:
        return {"text": f"[search] Error: {e}", "log": {"action": "search", "query": query, "num_docs_requested": 5, "retrieved_documents": []}}


def browse_tool(url: str) -> Dict[str, Any]:
    """
    Browse a web page using BeautifulSoup.
    """
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            return {"text": f"[browse] HTTP {resp.status_code}: {resp.text[:200]}", "log": {"action": "browse", "url": url, "content_preview": ""}}
        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
        text = "\n\n".join(paragraphs)
        preview = text[:500]
        return {"text": text[:5000] if text else "[browse] No textual content", "log": {"action": "browse", "url": url, "content_preview": preview}}
    except Exception as e:
        return {"text": f"[browse] Error: {e}", "log": {"action": "browse", "url": url, "content_preview": ""}}

def answer_tool() -> Dict[str, Any]:
    """
    Information gathered are enough to answer the user query.
    """
    return {"text": "[answer] ready", "log": {"action": "answer"}}

"""
Extra tools for Part II --  Realistic agent with multiple tools.

"""