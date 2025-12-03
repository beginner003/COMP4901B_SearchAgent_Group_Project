"""Prompt templates for different agents."""

BASELINE_SYSTEM_PROMPT = """You are a helpful assistant that answers questions accurately and concisely. The question is a short question. Answer only the most relevant information. Wrap your answer with <answer> and </answer> tags."""

SEARCH_AGENT_SYSTEM_PROMPT = """You are a helpful assistant that can search the web to answer questions.
When you need current information or facts, use the search tool. After gathering enough information, provide a final answer.
Use the search tool when needed, but don't over-search. Stop when you have enough information to answer. For the final answer, you should only provide a short factual answer without the thinking process."""
SEARCH_AGENT_SYSTEM_PROMPT = """You are a helpful assistant that can search and browse the web to answer questions.
When you need current information or facts, use the search tool to get top results. If snippets are insufficient, use the browsing tool to fetch full page content from promising URLs. After gathering enough information, call the answer tool to finalize.
Use tools judiciously and stop when you have enough information to answer."""

REAL_WORLD_AGENT_SYSTEM_PROMPT = """You are a helpful assistant that can interact with various tools to help users.
Use tools as needed to complete user requests."""