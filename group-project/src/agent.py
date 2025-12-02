import json
from .tools import search_tool, browse_tool, answer_tool, get_tools_schema
from typing import Dict, Any, List, Optional
from .utils import call_deepseek, load_config
from .prompts import BASELINE_SYSTEM_PROMPT, SEARCH_AGENT_SYSTEM_PROMPT, REAL_WORLD_AGENT_SYSTEM_PROMPT

class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, config: Dict[str, str] = None):
        self.config = config or load_config()


class NoSearchAgent(BaseAgent):
    """Agent without search capabilities."""
    def __init__(self, config: Dict[str, str] = None, temperature: float = 0.7, max_tokens: int = 1024, use_reasoning: bool = False):
        super().__init__(config)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_reasoning = use_reasoning

    def answer_question(self, question: str) -> str:
        """Answer question using only the LLM's knowledge"""
        messages = [
            {
                "role": "system",
                "content": BASELINE_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]

        # Call the LLM with the initial message
        response = call_deepseek(
            messages=messages,
            config=self.config,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content.strip()
        


class SearchAgent(BaseAgent):
    """Agent with google search tools"""
    def __init__(self, config: Dict[str, str] = None, temperature: float = 0.7, max_tokens: int = 1024, max_steps: int = 5, use_reasoning: bool = False, include_browse: bool = False):
        super().__init__(config)
        self.temperature = 0.7
        self.max_tokens = 2000
        self.max_steps = max_steps
        self.use_reasoning = use_reasoning
        self.tool_schemas = get_tools_schema(include_browse=include_browse) ## TODO
        self.tools = [search_tool, browse_tool if include_browse else None, answer_tool]
    
    def tools_execution(tool_name: str, tool_args: Dict[str, Any]) -> Any:
        if tool_name == "search":
            return search_tool(tool_args["query"])
        elif tool_name == "browse":
            return browse_tool(tool_args["url"])
        elif tool_name == "answer":
            return answer_tool()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def agent_loop(self, question: str) -> str:
        # Prepare the initial message for the agent loop
        messages = [
            {
                "role": "system",
                "content": SEARCH_AGENT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]
        
        # Print the steps of the agent loop
        steps = []
        steps.append({
            "step_number": 0,
            "action": "system message",
            "message": messages[0]["content"]
        }, {"step_number": 0,
            "action": "user query",
            "message": messages[1]["content"]}
        )
        for step in range(1, self.max_steps + 1):
            response = call_deepseek(
                messages=messages,
                config=self.config,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=self.tool_schemas,
                use_reasoning=self.use_reasoning,
            )
            messages.append(response.choices[0].message)
            
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                tool_name = tool_call.function.name
                # if LLM thinks that it has enough information to answer the user query, it will call the answer tool then we break the loop and proceed to final answering
                if tool_name == "answer":
                    steps.append({
                        "step_number": step,
                        "action": "answer tool call",
                        "message": "LLM thinks that it has enough information to answer the user query"
                    })
                    break
                tool_args = json.loads(tool_call.function.arguments)
                tool_result = self.tools_execution(tool_name, tool_args)
                messages.append({"role": "tool", "content": tool_result, "tool_call_id": tool_call.id})
                steps.append({
                    "step_number": step,
                    "action": "tool call",
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "tool_result": tool_result
                })
            

        final_response = call_deepseek(
            messages=messages,
            config=self.config,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tools=self.tool_schemas,
            use_reasoning=self.use_reasoning,
        )
        final_answer = final_response.choices[0].message.content.strip()    
        steps.append({
            "step_number": step + 1,
            "action": "final answer",
            "message": final_answer
        })
        return {
            "user_query": question,
            "steps": steps,
            "total_steps": steps[-1]["step_number"],
            "final_answer": final_answer
        }
    
    def print_steps(self, steps: List[Dict[str, Any]]) -> None:
        for step in steps:
            print(f"Step {step['step_number']}: {step['action']}")
            if step["action"] == "tool call":
                print(f"Tool name: {step['tool_name']}")
                print(f"Tool args: {step['tool_args']}")
                print(f"Tool result: {step['tool_result']}")
            elif step["action"] == "final answer":
                print(f"Final answer: {step['message']}")
            else:
                print(f"Message: {step['message']}")
            print("="*50)
        

    
class RealWorldAgent(BaseAgent):
    """Agent with multiple tools."""
    def __init__(self, config: Dict[str, str] = None):
        super().__init__(config)

    def answer_question(self, question: str) -> str:
        return None
    
    def run_trajectory(self, user_request: str) -> Dict[str, Any]:
        """Run agent loop for RealWorldAgent."""
        return None
    
