import json
from tools import search_tool, browse_tool, answer_tool, get_tools_schema_filtered
from typing import Dict, Any, List, Optional

# Use absolute imports (works with PYTHONPATH=. and when imported as package)
from src.tools import search_tool, browse_tool, answer_tool, get_tools_schema
from src.utils import call_deepseek, load_config
from src.prompts import BASELINE_SYSTEM_PROMPT, SEARCH_AGENT_SYSTEM_PROMPT, REAL_WORLD_AGENT_SYSTEM_PROMPT

class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, config: Dict[str, str] = None):
        self.config = config or load_config()

    
def tools_execution(tool_name: str, tool_args: Dict[str, Any]) -> Any:
    if tool_name == "search":
        return search_tool(tool_args["query"])
    elif tool_name == "browse":
        return browse_tool(tool_args["url"])
    elif tool_name == "answer":
        return answer_tool()
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

def agent_loop(question: str, max_steps: int = 6, config: Optional[Dict[str, str]] = None, allowed_tools: Optional[List[str]] = None) -> str:
    cfg = config or load_config()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SEARCH_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Answer concisely with a short factual string. You should only contain the answer in the response without thinking process.\nQuestion: {question}"},
    ]
    tools = get_tools_schema_filtered(allowed_tools or ["search", "browse", "answer"])
    for _ in range(max_steps):
        resp = call_deepseek(messages=messages, tools=tools, config=cfg)
        choice = resp.choices[0]
        msg = choice.message
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            terminate = False
            assistant_tool_calls = []
            for tc in tool_calls:
                name = tc.function.name
                args_str = tc.function.arguments or "{}"
                assistant_tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": name, "arguments": args_str},
                })
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": assistant_tool_calls,
            })
            for tc in tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                result = tools_execution(name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result["text"] if isinstance(result, dict) and "text" in result else (result if isinstance(result, str) else json.dumps(result)),
                })
                if isinstance(result, dict) and result.get("log", {}).get("action") == "answer":
                    terminate = True

            if terminate:

                final = call_deepseek(messages=messages, config=cfg)
                return final.choices[0].message.content
            continue
        content = msg.content or ""
        if content.strip():
            return content
    messages.append({"role": "assistant", "content": "Summarize findings and answer the question succinctly."})
    final = call_deepseek(messages=messages, config=cfg)
    return final.choices[0].message.content

def agent_loop_with_trajectory(question: str, max_steps: int = 6, config: Optional[Dict[str, str]] = None, allowed_tools: Optional[List[str]] = None) -> Dict[str, Any]:
    cfg = config or load_config()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SEARCH_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Answer concisely with a short factual string. You should only contain the answer in the response without thinking process.\nQuestion: {question}"},
    ]
    tools = get_tools_schema_filtered(allowed_tools or ["search", "browse", "answer"])
    steps: List[Dict[str, Any]] = []
    for step_idx in range(1, max_steps + 1):
        resp = call_deepseek(messages=messages, tools=tools, config=cfg)
        msg = resp.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            assistant_tool_calls = []
            for tc in tool_calls:
                name = tc.function.name
                args_str = tc.function.arguments or "{}"
                assistant_tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": name, "arguments": args_str},
                })
            messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": assistant_tool_calls})
            terminate = False
            for tc in tool_calls:
                name = tc.function.name
                args = {}
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    pass
                result = tools_execution(name, args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result["text"] if isinstance(result, dict) else str(result)})
                log = result.get("log") if isinstance(result, dict) else None
                if log:
                    step_log = {"step_number": step_idx, **log}
                    if log.get("action") == "search":
                        steps.append(step_log)
                    elif log.get("action") == "browse":
                        steps.append(step_log)
                    elif log.get("action") == "answer":
                        terminate = True
            if terminate:
                final = call_deepseek(messages=messages, config=cfg)
                final_text = final.choices[0].message.content
                return {
                    "final_answer": final_text,
                    "total_search_steps": sum(1 for s in steps if s.get("action") == "search"),
                    "steps": steps,
                }
            continue
        content = msg.content or ""
        if content.strip():
            return {
                "final_answer": content,
                "total_search_steps": sum(1 for s in steps if s.get("action") == "search"),
                "steps": steps,
            }
    final = call_deepseek(messages=messages + [{"role": "assistant", "content": "Summarize findings and answer the question succinctly."}], config=cfg)
    final_text = final.choices[0].message.content
    return {
        "final_answer": final_text,
        "total_search_steps": sum(1 for s in steps if s.get("action") == "search"),
        "steps": steps,
    }

def generate_no_search(question: str, config: Optional[Dict[str, str]] = None, temperature: float = 0.3, max_tokens: int = 512) -> str:
    cfg = config or load_config()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Answer concisely with a short factual string. You should only contain the answer in the response without thinking process.\nQuestion: {question}"},
    ]
    resp = call_deepseek(messages=messages, config=cfg, temperature=temperature, max_tokens=max_tokens)
    return resp.choices[0].message.content