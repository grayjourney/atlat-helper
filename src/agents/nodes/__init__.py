"""
Agent Nodes - Individual Processing Units

Each node is a pure function that:
1. Receives the current agent state
2. Performs a specific task
3. Returns updates to merge into the state

Nodes in this package:
- fetch_ticket.py: Node A - Fetch ticket from Jira via MCP
- analyze_blocker.py: Node B - Analyze blockers using LLM
- propose_update.py: Node C - Propose ticket updates

Think of each node like:
- Go: A middleware handler in a chain
- PHP: A pipeline stage or job handler
"""
