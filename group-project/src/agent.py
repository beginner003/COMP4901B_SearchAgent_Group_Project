import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Use absolute imports (works with PYTHONPATH=. and when imported as package)
from src.tools import (
    search_tool, browse_tool, answer_tool, get_tools_schema,
    read_notion_database, create_notion_page, update_notion_page,
    send_email, create_calendar_event
)
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
    """Agent with multiple tools including Notion, Gmail, and Calendar."""
    
    def __init__(
        self, 
        config: Dict[str, str] = None, 
        temperature: float = 0.7, 
        max_tokens: int = 2000, 
        max_steps: int = 10, 
        use_reasoning: bool = False, 
        include_browse: bool = False,
        include_part2_tools: bool = True
    ):
        super().__init__(config)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_steps = max_steps
        self.use_reasoning = use_reasoning
        self.tool_schemas = get_tools_schema(
            include_browse=include_browse, 
            include_part2_tools=include_part2_tools
        )
    
    def tools_execution(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a tool by name and return result."""
        if tool_name == "search":
            num_results = tool_args.get("num_results", 5)
            return search_tool(tool_args.get("query", ""), num_results=num_results)
        elif tool_name == "browse":
            return browse_tool(tool_args.get("url", ""))
        elif tool_name == "answer":
            return answer_tool()
        elif tool_name == "read_notion_database":
            status_filter = tool_args.get("status_filter")
            meeting_date_filter = tool_args.get("meeting_date_filter")
            attendees_filter = tool_args.get("attendees_filter")
            discussion_topics_filter = tool_args.get("discussion_topics_filter")
            action_items_filter = tool_args.get("action_items_filter")
            max_results = tool_args.get("max_results", 10)
            return read_notion_database(
                status_filter=status_filter,
                meeting_date_filter=meeting_date_filter,
                attendees_filter=attendees_filter,
                discussion_topics_filter=discussion_topics_filter,
                action_items_filter=action_items_filter,
                max_results=max_results
            )
        elif tool_name == "create_notion_page":
            title = tool_args.get("title", "")
            meeting_date = tool_args.get("meeting_date")
            status = tool_args.get("status")
            attendees = tool_args.get("attendees")
            discussion_topics = tool_args.get("discussion_topics")
            action_items = tool_args.get("action_items")
            children = tool_args.get("children")
            return create_notion_page(
                title=title,
                meeting_date=meeting_date,
                status=status,
                attendees=attendees,
                discussion_topics=discussion_topics,
                action_items=action_items,
                children=children
            )
        elif tool_name == "update_notion_page":
            page_id = tool_args.get("page_id", "")
            status = tool_args.get("status")
            meeting_date = tool_args.get("meeting_date")
            attendees = tool_args.get("attendees")
            discussion_topics = tool_args.get("discussion_topics")
            action_items = tool_args.get("action_items")
            return update_notion_page(
                page_id=page_id,
                status=status,
                meeting_date=meeting_date,
                attendees=attendees,
                discussion_topics=discussion_topics,
                action_items=action_items
            )
        elif tool_name == "send_email":
            to = tool_args.get("to", [])
            subject = tool_args.get("subject", "")
            body = tool_args.get("body", "")
            cc = tool_args.get("cc")
            bcc = tool_args.get("bcc")
            return send_email(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc
            )
        elif tool_name == "create_calendar_event":
            summary = tool_args.get("summary", "")
            start_time = tool_args.get("start_time", "")
            end_time = tool_args.get("end_time", "")
            description = tool_args.get("description")
            attendees = tool_args.get("attendees")
            location = tool_args.get("location")
            timezone = tool_args.get("timezone")
            return create_calendar_event(
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                description=description,
                attendees=attendees,
                location=location,
                timezone=timezone
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def agent_loop(self, question: str) -> Dict[str, Any]:
        """Main agent loop that handles tool calling and responses."""
        print(f"\n{'='*60}")
        print(f"REAL WORLD AGENT LOOP STARTED")
        print(f"{'='*60}")
        print(f"Question: {question}")
        print(f"Max steps: {self.max_steps}")
        
        # Prepare the initial message for the agent loop
        messages = [
            {
                "role": "system",
                "content": REAL_WORLD_AGENT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": question
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
                        tool_args = {}
                        print(f"      Using empty args dict as fallback")
                    
                    try:
                        tool_result = self.tools_execution(tool_name, tool_args)
                        print(f"      ✓ Tool executed")
                        
                        # Extract llm_readable content for message
                        if isinstance(tool_result, dict):
                            llm_content = tool_result.get("llm_readable", str(tool_result))
                        else:
                            llm_content = str(tool_result)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": llm_content,
                        })
                        
                        # Record step in trajectory format
                        step_record = {
                            "step_number": step,
                            "action": tool_name,
                            "tool_args": tool_args
                        }
                        
                        # Add tool-specific result data
                        if isinstance(tool_result, dict):
                            if tool_name == "search":
                                step_record["query"] = tool_result.get("query", "")
                                step_record["retrieved_documents"] = tool_result.get("retrieved_documents", [])
                            elif tool_name == "read_notion_database":
                                step_record["pages_found"] = tool_result.get("total_found", 0)
                                step_record["pages"] = tool_result.get("pages", [])
                            elif tool_name == "create_notion_page":
                                step_record["page_id"] = tool_result.get("page_id", "")
                                step_record["created"] = tool_result.get("created", False)
                            elif tool_name == "update_notion_page":
                                step_record["page_id"] = tool_result.get("page_id", "")
                                step_record["updated"] = tool_result.get("updated", False)
                            elif tool_name == "send_email":
                                step_record["sent"] = tool_result.get("sent", False)
                                step_record["recipients"] = tool_result.get("recipients", [])
                            elif tool_name == "create_calendar_event":
                                step_record["created"] = tool_result.get("created", False)
                                step_record["event_id"] = tool_result.get("id", "")
                                step_record["html_link"] = tool_result.get("htmlLink", "")
                        
                        steps.append(step_record)
                        print(f"      ✓ {tool_name} step recorded")
                        
                        # Check if answer tool was called
                        if tool_name == "answer":
                            print(f"      → Answer tool called - breaking loop")
                            terminate_loop = True
                            
                    except Exception as e:
                        error_msg = f"Error executing {tool_name}: {str(e)}"
                        print(f"      ✗ {error_msg}")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": error_msg,
                        })
                        steps.append({
                            "step_number": step,
                            "action": tool_name,
                            "error": error_msg,
                            "tool_args": tool_args
                        })
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
        print(f"REAL WORLD AGENT LOOP COMPLETED")
        print(f"{'='*60}")
        print(f"Total steps: {len(steps)}")
        print(f"Final answer: {final_answer}")
        print(f"{'='*60}\n")
        
        return {
            "user_query": question,
            "steps": steps,
            "total_steps": steps[-1]["step_number"],
            "final_answer": final_answer
        }
    
    def print_trajectory(self, result: Dict[str, Any], save_as_json: bool = False) -> None:
        """Print the agent's trajectory in a readable format."""
        trajectory_json = {
            "question": result.get('user_query', 'N/A'),
            "steps": result.get('steps', []),
            "total_steps": result.get('total_steps', 0),
        }
        
        print("\n" + "="*60)
        print("AGENT TRAJECTORY")
        print("="*60)
        print(f"Question: {result.get('user_query', 'N/A')}")
        print(f"Final Answer: {result.get('final_answer', 'N/A')}")
        print(f"Total Steps: {result.get('total_steps', 'N/A')}")
        
        steps = result.get('steps', [])
        print(f"\nSteps ({len(steps)}):")
        for i, step in enumerate(steps, 1):
            action = step.get('action', 'unknown')
            step_num = step.get('step_number', i)
            print(f"\n  Step {step_num}: {action}")
            
            if action == "search":
                print(f"    Query: {step.get('query', 'N/A')}")
                docs = step.get('retrieved_documents', [])
                print(f"    Docs retrieved: {len(docs)}")
            elif action == "read_notion_database":
                print(f"    Pages found: {step.get('pages_found', 0)}")
            elif action == "create_notion_page":
                print(f"    Page ID: {step.get('page_id', 'N/A')}")
                print(f"    Created: {step.get('created', False)}")
            elif action == "update_notion_page":
                print(f"    Page ID: {step.get('page_id', 'N/A')}")
                print(f"    Updated: {step.get('updated', False)}")
            elif action == "send_email":
                print(f"    Sent: {step.get('sent', False)}")
                print(f"    Recipients: {step.get('recipients', [])}")
            elif action == "create_calendar_event":
                print(f"    Created: {step.get('created', False)}")
                print(f"    Event ID: {step.get('event_id', 'N/A')}")
            elif "error" in step:
                print(f"    Error: {step.get('error', 'N/A')}")
        
        print("\n" + "="*60)
        
        if save_as_json:
            return trajectory_json
        return None
    
    def save_trajectory_to_file(self, result: Dict[str, Any], filename: str = None) -> str:
        """Save the agent's trajectory to a human-readable text file."""
        # Create results directory if it doesn't exist
        results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "real_world_agent_scenarios")
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate filename from user query if not provided
        if filename is None:
            user_query = result.get('user_query', 'unknown_query')
            # Sanitize filename: remove special chars, limit length
            safe_name = "".join(c for c in user_query if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:50]  # Limit to 50 chars
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_{timestamp}.txt"
        
        # Ensure .txt extension
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        filepath = os.path.join(results_dir, filename)
        
        # Build human-readable content
        content_lines = []
        content_lines.append("="*80)
        content_lines.append("REAL WORLD AGENT EXECUTION TRAJECTORY")
        content_lines.append("="*80)
        content_lines.append("")
        content_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_lines.append("")
        content_lines.append("-"*80)
        content_lines.append("USER REQUEST")
        content_lines.append("-"*80)
        content_lines.append(result.get('user_query', 'N/A'))
        content_lines.append("")
        content_lines.append("-"*80)
        content_lines.append("FINAL ANSWER")
        content_lines.append("-"*80)
        content_lines.append(result.get('final_answer', 'N/A'))
        content_lines.append("")
        content_lines.append("-"*80)
        content_lines.append(f"EXECUTION STEPS (Total: {result.get('total_steps', 0)})")
        content_lines.append("-"*80)
        content_lines.append("")
        
        steps = result.get('steps', [])
        for i, step in enumerate(steps, 1):
            action = step.get('action', 'unknown')
            step_num = step.get('step_number', i)
            
            content_lines.append(f"Step {step_num}: {action.upper()}")
            content_lines.append("-" * 40)
            
            if action == "search":
                query = step.get('query', 'N/A')
                docs = step.get('retrieved_documents', [])
                content_lines.append(f"  Search Query: {query}")
                content_lines.append(f"  Documents Retrieved: {len(docs)}")
                if docs:
                    content_lines.append("  Top Results:")
                    for j, doc in enumerate(docs[:3], 1):  # Show top 3
                        title = doc.get('title', 'N/A')[:60]
                        content_lines.append(f"    {j}. {title}")
            
            elif action == "read_notion_database":
                pages_found = step.get('pages_found', 0)
                content_lines.append(f"  Pages Found: {pages_found}")
                pages = step.get('pages', [])
                if pages:
                    content_lines.append("  Meeting Pages:")
                    for j, page in enumerate(pages[:5], 1):  # Show first 5
                        title = page.get('title', 'Untitled')[:50]
                        date = page.get('properties', {}).get('Meeting Date', 'N/A')
                        status = page.get('properties', {}).get('Status', 'N/A')
                        content_lines.append(f"    {j}. {title} | Date: {date} | Status: {status}")
            
            elif action == "create_notion_page":
                page_id = step.get('page_id', 'N/A')
                created = step.get('created', False)
                tool_args = step.get('tool_args', {})
                title = tool_args.get('title', 'N/A')
                content_lines.append(f"  Title: {title}")
                content_lines.append(f"  Page ID: {page_id}")
                content_lines.append(f"  Status: {'✓ Created Successfully' if created else '✗ Failed'}")
            
            elif action == "update_notion_page":
                page_id = step.get('page_id', 'N/A')
                updated = step.get('updated', False)
                tool_args = step.get('tool_args', {})
                content_lines.append(f"  Page ID: {page_id}")
                content_lines.append(f"  Status: {'✓ Updated Successfully' if updated else '✗ Failed'}")
                if tool_args:
                    updates = []
                    if tool_args.get('status'):
                        updates.append(f"Status → {tool_args['status']}")
                    if tool_args.get('meeting_date'):
                        updates.append(f"Date → {tool_args['meeting_date']}")
                    if tool_args.get('discussion_topics'):
                        updates.append("Discussion Topics → Updated")
                    if tool_args.get('action_items'):
                        updates.append("Action Items → Updated")
                    if updates:
                        content_lines.append(f"  Updates: {', '.join(updates)}")
            
            elif action == "send_email":
                sent = step.get('sent', False)
                recipients = step.get('recipients', [])
                tool_args = step.get('tool_args', {})
                subject = tool_args.get('subject', 'N/A')
                content_lines.append(f"  Subject: {subject}")
                content_lines.append(f"  Recipients: {', '.join(recipients) if recipients else 'N/A'}")
                content_lines.append(f"  Status: {'✓ Sent Successfully' if sent else '✗ Failed'}")
            
            elif action == "create_calendar_event":
                created = step.get('created', False)
                event_id = step.get('event_id', 'N/A')
                html_link = step.get('html_link', 'N/A')
                tool_args = step.get('tool_args', {})
                summary = tool_args.get('summary', 'N/A')
                start_time = tool_args.get('start_time', 'N/A')
                content_lines.append(f"  Event: {summary}")
                content_lines.append(f"  Start Time: {start_time}")
                content_lines.append(f"  Event ID: {event_id}")
                content_lines.append(f"  Status: {'✓ Created Successfully' if created else '✗ Failed'}")
                if html_link != 'N/A':
                    content_lines.append(f"  Calendar Link: {html_link}")
            
            elif action == "browse":
                url = step.get('url', 'N/A')
                content_lines.append(f"  URL: {url}")
                content_length = len(str(step.get('content', '')))
                content_lines.append(f"  Content Length: {content_length} characters")
            
            elif "error" in step:
                error_msg = step.get('error', 'Unknown error')
                content_lines.append(f"  ✗ Error: {error_msg}")
            
            elif action in ["system message", "user query", "final answer"]:
                message = step.get('message', 'N/A')
                if len(message) > 200:
                    message = message[:200] + "..."
                content_lines.append(f"  {message}")
            
            content_lines.append("")
        
        content_lines.append("="*80)
        content_lines.append("END OF TRAJECTORY")
        content_lines.append("="*80)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
        return filepath
    
