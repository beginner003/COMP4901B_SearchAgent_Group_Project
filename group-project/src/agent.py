import json
from typing import Dict, Any, List, Optional

# Use absolute imports (works with PYTHONPATH=. and when imported as package)
from src.tools import search_tool, browse_tool, answer_tool, get_tools_schema
from src.utils import call_deepseek, load_config
from src.prompts import BASELINE_SYSTEM_PROMPT, SEARCH_AGENT_SYSTEM_PROMPT, REAL_WORLD_AGENT_SYSTEM_PROMPT

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
                "content": "Answer concisely with a short factual string. You should only contian the answer in the response without the thinking process. Question: " + question
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
    def __init__(self, config: Dict[str, str] = None, temperature: float = 0.7, max_tokens: int = 2000, max_steps: int = 5, use_reasoning: bool = False, include_browse: bool = False):
        super().__init__(config)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_steps = max_steps
        self.use_reasoning = use_reasoning
        self.tool_schemas = get_tools_schema(include_browse=include_browse) ## TODO
        self.tools = [search_tool, browse_tool if include_browse else None, answer_tool]
    
    def tools_execution(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a tool by name and return result."""
        if tool_name == "search":
            num_results = tool_args.get("num_results", 5)
            return search_tool(tool_args.get("query", ""), num_results=num_results)
        elif tool_name == "browse":
            return browse_tool(tool_args.get("url", ""))
        elif tool_name == "answer":
            return answer_tool()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def agent_loop(self, question: str) -> str:
        print(f"\n{'='*60}")
        print(f"AGENT LOOP STARTED")
        print(f"{'='*60}")
        print(f"Question: {question}")
        print(f"Max steps: {self.max_steps}")
        
        # Prepare the initial message for the agent loop
        messages = [
            {
                "role": "system",
                "content": SEARCH_AGENT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": "Answer concisely with a short factual string. You should only contian the answer in the response without the thinking process. Question: "+question
            }
        ]
        
        # Track the steps of the agent loop
        steps = []
        steps.append({
            "step_number": 0,
            "action": "system message",
            "message": messages[0]["content"]
        })
        steps.append({
            "step_number": 0,
            "action": "user query",
            "message": messages[1]["content"]
        })
        
        print(f"\nInitial messages prepared: {len(messages)} messages")
        terminate_loop = False
        for step in range(1, self.max_steps + 1):
            if terminate_loop:
                break
            print(f"\n{'─'*60}")
            print(f"STEP {step}/{self.max_steps}")
            print(f"{'─'*60}")
            
            
            response = call_deepseek(
                messages=messages,
                config=self.config,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=self.tool_schemas,
                use_reasoning=self.use_reasoning,
            )
            
            assistant_message = response.choices[0].message
            print(f"✓ Received response")
            print(f"  Content: {assistant_message.content[:100] if assistant_message.content else 'None'}...")
            print(f"  Tool calls: {len(assistant_message.tool_calls) if assistant_message.tool_calls else 0}")
            
            messages.append(assistant_message)
            
            if assistant_message.tool_calls:
                print(f"\n  → Tool calls detected: {len(assistant_message.tool_calls)}")
                for idx, tool_call in enumerate(assistant_message.tool_calls, 1):
                    tool_name = tool_call.function.name
                    raw_args = tool_call.function.arguments
                    print(f"\n  [{idx}/{len(assistant_message.tool_calls)}] Executing tool: {tool_name}")
                    print(f"      Raw args string: {raw_args[:200]}...")
                    
                    # Parse JSON arguments with error handling
                    try:
                        tool_args = json.loads(raw_args)
                        if not isinstance(tool_args, dict):
                            print(f"      ⚠ Warning: tool_args is not a dict, converting...")
                            tool_args = {}
                        print(f"      Parsed args: {tool_args}")
                    except json.JSONDecodeError as e:
                        print(f"      ✗ JSON decode error: {e}")
                        print(f"      Raw string (first 500 chars): {repr(raw_args[:500])}")
                        # Try to fix common issues or use empty dict
                        tool_args = {}
                        print(f"      Using empty args dict as fallback")
                    
                    tool_result = self.tools_execution(tool_name, tool_args)
                    print(f"      ✓ Tool executed")
                    
                    # Handle different return types
                    if tool_name == "search" and isinstance(tool_result, dict):
                        # search_tool returns a dict, extract llm_readable for message
                        llm_content = tool_result.get("llm_readable", str(tool_result))
                        retrieved_docs = tool_result.get("retrieved_documents", [])
                        query = tool_result.get("query", tool_args.get("query", ""))
                        num_docs = tool_result.get("num_docs_requested", tool_args.get("num_results", 5))
                        
                        print(f"      Search query: {query}")
                        print(f"      Retrieved {len(retrieved_docs)} documents")
                        
                        # Add tool result to messages (LLM reads the formatted string)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": llm_content,
                        })
                    
                        # Record step in trajectory format
                        steps.append({
                            "step_number": step,
                            "action": "search",
                            "query": query,
                            "num_docs_requested": num_docs,
                            "retrieved_documents": retrieved_docs
                        })
                        print(f"      ✓ Search step recorded")
                        
                    elif tool_name == "browse":
                        content = tool_result.get("content", "")
                        url = tool_result.get("url", "")
                        print(f"      Browse result length: {len(content)} chars")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": content,
                        })
                        print(f"      ✓ Browse step completed")

                        # Record step in trajectory format
                        steps.append({
                            "step_number": step,
                            "action": "browse",
                            "url": url,
                            "content": str(content),
                        })
                        print(f"      ✓ Browse step recorded")
                        
                    elif tool_name == "answer":
                        print(f"      → Answer tool called - breaking loop")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(tool_result),
                        })
                        terminate_loop = True
            else:
                print(f"  → No tool calls - assistant provided direct response")
                if assistant_message.content:
                    print(f"  Content: {assistant_message.content[:200]}...")

        print(f"\n{'─'*60}")
        print(f"GENERATING FINAL ANSWER")
        print(f"{'─'*60}")
        print(f"Calling DeepSeek API for final answer ({len(messages)} messages in context)...")
        
        final_response = call_deepseek(
            messages=messages,
            config=self.config,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tools=self.tool_schemas,
            use_reasoning=self.use_reasoning,
        )
        
        final_answer = final_response.choices[0].message.content.strip()
        print(f"✓ Final answer received: {final_answer[:500]}...")
        
        steps.append({
            "step_number": step + 1,
            "action": "final answer",
            "message": final_answer
        })
        
        print(f"\n{'='*60}")
        print(f"AGENT LOOP COMPLETED")
        print(f"{'='*60}")
        print(f"Total steps: {len(steps)}")
        print(f"Search steps: {len([s for s in steps if s.get('action') == 'search'])}")
        print(f"Final answer: {final_answer}")
        print(f"{'='*60}\n")
        
        return {
            "user_query": question,
            "steps": steps,
            "total_steps": steps[-1]["step_number"],
            "final_answer": final_answer
        }
    
    def print_trajectory(self, result: Dict[str, Any], save_as_json: bool = False) -> None:
        if save_as_json:
            trajectory_json = {
                "question": result.get('user_query', 'N/A'),
                "steps": result.get('steps', []),
                "total_search_steps": len([s for s in result.get('steps', []) if s.get('action') == 'search']),
            }
        print("\n3. Results:")
        print(f"   Question: {result.get('user_query', 'N/A')}")
        print(f"   Final Answer: {result.get('final_answer', 'N/A')}")
        print(f"   Total Steps: {result.get('total_steps', 'N/A')}")
        
        steps = result.get('steps', [])
        print(f"\n4. Steps ({len(steps)}):")
        for i, step in enumerate(steps, 1):
            action = step.get('action', 'unknown')
            print(f"   Step {i}: {action}")
            
            if action == "search":
                print(f"      Query: {step.get('query', 'N/A')}")
                print(f"      Docs requested: {step.get('num_docs_requested', 'N/A')}")
                docs = step.get('retrieved_documents', [])
                print(f"      Docs retrieved: {len(docs)}")
                if docs:
                    print(f"      First doc title: {docs[0].get('title', 'N/A')[:50]}...")
        
        print("\n" + "="*60)
        return trajectory_json
        
        

    
class RealWorldAgent(BaseAgent):
    """Agent with multiple tools."""
    def __init__(self, config: Dict[str, str] = None):
        super().__init__(config)

    def answer_question(self, question: str) -> str:
        return None
    
    def run_trajectory(self, user_request: str) -> Dict[str, Any]:
        """Run agent loop for RealWorldAgent."""
        return None
    
