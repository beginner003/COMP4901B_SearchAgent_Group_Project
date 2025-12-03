import os
from dotenv import load_dotenv
from typing import Dict, Any, List
from openai import OpenAI
import json

# Load environment variables
load_dotenv()

def load_config() -> Dict[str, str]:
    """Load API keys from environment variables."""
    return {
        "SERPER_API_KEY": os.getenv("SERPER_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
        "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
        "DEEPSEEK_CHAT_MODEL": "deepseek-chat",
        "DEEPSEEK_REASONING_MODEL": "deepseek-reasoner",
        "NOTION_API_KEY": os.getenv("NOTION_API_KEY"),
        "NOTION_DATABASE_ID": os.getenv("NOTION_DATABASE_ID"),
        "GMAIL_ACCESS_TOKEN": os.getenv("GMAIL_ACCESS_TOKEN")
    }

def call_deepseek(
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]] = None,
    config: Dict[str, str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    use_reasoning: bool = False
) -> Dict[str, Any]:
    """
    Wrapper for DeepSeek API calls.
    """
    if config is None:
        config = load_config()
    
    client = OpenAI(
        api_key=config["DEEPSEEK_API_KEY"],
        base_url=config["DEEPSEEK_BASE_URL"]
    )
    
    kwargs = {
        "model": config["DEEPSEEK_CHAT_MODEL"] if not use_reasoning else config["DEEPSEEK_REASONING_MODEL"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    if tools:
        kwargs["tools"] = tools
    
    response = client.chat.completions.create(**kwargs)
    return response

def read_jsonl(filepath: str) -> List[Dict[str, Any]]:
    """Read JSONL file and return list of dicts."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data
 
def write_jsonl(filepath: str, data: List[Dict[str, Any]]):
    """Write list of dicts to JSONL file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')