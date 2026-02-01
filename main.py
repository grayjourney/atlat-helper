#!/usr/bin/env python3
"""
Project Management Agent - Entry Point (Hello World)
=====================================================

This file demonstrates the basic LangGraph workflow without external dependencies.
It serves as a verification that the stack is working correctly.

Run with:
    python main.py

What this demonstrates:
1. TypedDict for state management (like Go structs)
2. LangGraph nodes as pure functions
3. Graph compilation and execution
4. Async/await patterns
5. State persistence with checkpointers

Author: Gray
License: MIT
"""

# ============================================
# ⚠️  ASYNC BLOCKING WARNING ⚠️
# ============================================
# Python's asyncio is SINGLE-THREADED. If you block the event loop,
# the ENTIRE application freezes (no other requests can be processed).
#
# ❌ DO NOT USE THESE (they block the event loop):
#    - requests.get()           # Use httpx.AsyncClient() instead
#    - time.sleep()             # Use asyncio.sleep() instead
#    - open().read()            # Use aiofiles instead
#    - psycopg2 (sync driver)   # Use asyncpg instead
#
# ✅ ALWAYS USE ASYNC ALTERNATIVES:
#    - httpx (async HTTP client)
#    - asyncpg (async PostgreSQL)
#    - aiofiles (async file I/O)
#    - asyncio.sleep() (async sleep)
#
# === PHP Comparison ===
# PHP-FPM spawns new processes per request, so blocking is "okay".
# Python async is like Node.js - one blocked call = all users wait!
#
# === Go Comparison ===
# Go's goroutines are preemptively scheduled by the runtime.
# Python's asyncio is COOPERATIVE - YOU must yield control with `await`.
# If you forget `await`, the function runs synchronously and blocks!
#
# Example:
#   async def bad():
#       requests.get("...")  # ❌ BLOCKS! No await, runs sync
#
#   async def good():
#       await httpx.get("...")  # ✅ Yields control while waiting
# ============================================

# ============================================
# IMPORTS
# ============================================
# In Python, imports are at the top of the file (like Go).
# Unlike PHP's autoloading, Python explicitly imports what it needs.

from typing import TypedDict, Annotated
import operator

# Note: LangGraph import will fail if not installed.
# Run: pip install langgraph langchain-core
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️  LangGraph not installed. Running without graph execution.")
    print("   Install with: pip install langgraph langchain-core")



# ============================================
# STATE DEFINITION
# ============================================

class AgentState(TypedDict):
    """
    Agent State - The data that flows through the graph.
    
    TypedDict creates a dictionary with type hints.
    This is how LangGraph tracks state between nodes.
    
    === PHP Comparison ===
    In PHP, you might use a DTO (Data Transfer Object):
    
        class AgentState {
            public function __construct(
                public string $ticketId,
                public string $status,
                public array $messages,
                public int $step
            ) {}
        }
    
    === Go Comparison ===
    In Go, you'd use a struct:
    
        type AgentState struct {
            TicketID string   `json:"ticket_id"`
            Status   string   `json:"status"`
            Messages []string `json:"messages"`
            Step     int      `json:"step"`
        }
    
    === Key Difference ===
    TypedDict is still a regular dict at runtime, just with type hints.
    Access is via bracket notation: state["ticket_id"]
    Not dot notation like Go/PHP: state.TicketId or $state->ticketId
    """
    ticket_id: str
    status: str
    messages: Annotated[list[str], operator.add]  # Messages accumulate
    step: int


# ============================================
# NODE FUNCTIONS (The Processing Units)
# ============================================

def fetch_ticket_node(state: AgentState) -> dict:
    """
    Node A: Fetch Ticket Status (Mock Implementation)
    
    In LangGraph, each node is a function that:
    1. Receives the current state
    2. Returns a dict of updates to merge into state
    
    This is similar to:
    - Go: A middleware handler in a chain
    - PHP: A pipeline stage that transforms data
    
    === The Function Signature ===
    
    def fetch_ticket_node(state: AgentState) -> dict:
        ^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^     ^^^^
        function name     type hint for       return type
                          input parameter
    
    In Go:  func FetchTicketNode(state AgentState) map[string]any
    In PHP: function fetchTicketNode(AgentState $state): array
    """
    # Simulate fetching ticket (will connect to MCP later)
    ticket_id = state["ticket_id"]
    
    # Return updates to merge into state
    # Only return keys you want to update
    return {
        "status": "In Progress",
        "messages": [f"✅ Fetched ticket {ticket_id}: Status is 'In Progress'"],
        "step": state["step"] + 1,
    }


def analyze_blocker_node(state: AgentState) -> dict:
    """
    Node B: Analyze Blockers (Mock LLM Call)
    
    This simulates calling an LLM to analyze the ticket.
    Will be replaced with actual LLM call later.
    
    === Why return a dict, not AgentState? ===
    
    LangGraph merges returned dict into existing state.
    You only need to return the keys you're updating.
    
    state = {"a": 1, "b": 2}
    node returns: {"b": 3, "c": 4}
    new state = {"a": 1, "b": 3, "c": 4}  # Merged!
    """
    status = state["status"]
    
    # Mock LLM analysis
    analysis = f"Analyzed ticket with status '{status}'. No blockers detected."
    
    return {
        "messages": [f"🔍 {analysis}"],
        "step": state["step"] + 1,
    }


def propose_update_node(state: AgentState) -> dict:
    """
    Node C: Propose Update
    
    Final node that proposes what action to take.
    
    === Accessing state values ===
    
    In Python TypedDict:  state["ticket_id"]
    In Go struct:         state.TicketID
    In PHP object:        $state->ticketId
    In PHP array:         $state['ticket_id']
    """
    ticket_id = state["ticket_id"]
    
    proposal = f"Recommend moving ticket {ticket_id} to 'Ready for Review'"
    
    return {
        "status": "Ready for Review",
        "messages": [f"📝 Proposal: {proposal}"],
        "step": state["step"] + 1,
    }


# ============================================
# GRAPH BUILDER
# ============================================

def build_agent_graph(checkpointer=None):
    """
    Build the LangGraph workflow with optional persistence.
    
    This connects the nodes in sequence:
    START -> fetch_ticket -> analyze_blocker -> propose_update -> END
    
    Args:
        checkpointer: Optional checkpointer for state persistence.
                     Use MemorySaver for dev, PostgresSaver for prod.
                     If None, graph runs without persistence.
    
    === Graph Concept ===
    
    LangGraph uses a directed graph where:
    - Nodes = Processing functions
    - Edges = Flow between nodes
    - State = Data passed through the graph
    - Checkpointer = Saves state after each node (NEW!)
    
    Think of it like:
    - Go: A pipeline of handlers with shared context
    - PHP: Laravel's Pipeline with stages
    
    === StateGraph[AgentState] ===
    
    The [AgentState] part is a "generic type parameter".
    It tells Python what type of state this graph manages.
    
    Go equivalent:  StateGraph[AgentState]
    PHP equivalent: StateGraph<AgentState> (PHPStan)
    
    === Checkpointer (State Persistence) ===
    
    The checkpointer saves state after each node execution.
    This enables:
    - Resume after server restart
    - Time travel to previous states
    - Conversation threading (multiple users)
    
    PHP equivalent: Laravel's Cache or Session storage
    Go equivalent:  Saving state to Redis/Postgres between steps
    """
    if not LANGGRAPH_AVAILABLE:
        return None
    
    # Create a new graph with our state type
    # The "graph_builder" is like a factory that creates the workflow
    graph_builder = StateGraph(AgentState)
    
    # ----------------------------------------
    # Add nodes to the graph
    # ----------------------------------------
    # graph_builder.add_node(name, function)
    # - name: String identifier for the node
    # - function: The function to execute
    
    graph_builder.add_node("fetch_ticket", fetch_ticket_node)
    graph_builder.add_node("analyze_blocker", analyze_blocker_node)
    graph_builder.add_node("propose_update", propose_update_node)
    
    # ----------------------------------------
    # Connect nodes with edges
    # ----------------------------------------
    # Edges define the flow: A -> B -> C
    
    # START is a special constant from langgraph
    # It means "this is where the graph begins"
    graph_builder.add_edge(START, "fetch_ticket")
    graph_builder.add_edge("fetch_ticket", "analyze_blocker")
    graph_builder.add_edge("analyze_blocker", "propose_update")
    graph_builder.add_edge("propose_update", END)
    
    # ----------------------------------------
    # Compile the graph (with optional persistence)
    # ----------------------------------------
    # .compile() returns an executable graph
    # This is like "building" in compiled languages
    #
    # If checkpointer is provided, state is saved after each node.
    # This is crucial for production systems!
    
    if checkpointer is not None:
        return graph_builder.compile(checkpointer=checkpointer)
    
    return graph_builder.compile()


# ============================================
# MAIN EXECUTION
# ============================================

def run_hello_world():
    """
    Run the Hello World agent workflow with state persistence.
    
    This function:
    1. Creates a MemorySaver checkpointer
    2. Builds the agent graph with persistence
    3. Creates initial state with a thread_id
    4. Invokes the graph
    5. Prints the result
    
    === Entry Point Pattern ===
    
    In Python, we check __name__ == "__main__" to run code
    only when the file is executed directly (not imported).
    
    Go equivalent:  func main()
    PHP equivalent: if (php_sapi_name() === 'cli') { ... }
    """
    print("=" * 60)
    print("🚀 Project Management Agent - Hello World (with Persistence)")
    print("=" * 60)
    print()
    
    if not LANGGRAPH_AVAILABLE:
        print("❌ Cannot run workflow: LangGraph not installed")
        print()
        print("To install dependencies:")
        print("  pip install -r requirements.txt")
        print()
        print("Or install LangGraph directly:")
        print("  pip install langgraph langchain-core")
        return
    
    # ----------------------------------------
    # Create checkpointer for state persistence
    # ----------------------------------------
    # MemorySaver stores state in memory (lost on restart).
    # For production, use PostgresSaver:
    #   from langgraph.checkpoint.postgres import PostgresSaver
    #   checkpointer = PostgresSaver(connection_string)
    #
    # === PHP Comparison ===
    # Like choosing session driver: 'file', 'redis', 'database'
    #
    # === Go Comparison ===
    # Like injecting a StateStore interface implementation
    
    print("💾 Creating MemorySaver checkpointer...")
    checkpointer = MemorySaver()
    print("✅ Checkpointer ready (in-memory, dev mode)")
    print()
    
    # Build the graph with persistence
    print("📦 Building agent graph with persistence...")
    graph = build_agent_graph(checkpointer=checkpointer)
    print("✅ Graph compiled with checkpointer!")
    print()
    
    # Create initial state
    # ----------------------------------------
    # In Python, we just create a dict that matches TypedDict structure
    # No need to instantiate a class like in PHP/Go
    
    initial_state: AgentState = {
        "ticket_id": "PROJ-123",
        "status": "Unknown",
        "messages": ["🎬 Starting agent workflow..."],
        "step": 0,
    }
    
    # ----------------------------------------
    # Thread ID for conversation tracking
    # ----------------------------------------
    # Each unique thread_id maintains its own state history.
    # This enables:
    # - Multiple users with separate conversations
    # - Resume a specific conversation later
    # - Time travel to previous states
    #
    # === PHP Comparison ===
    # Like a session ID: session_id() in PHP
    #
    # === Go Comparison ===
    # Like a context key for tracing: ctx.Value("conversation_id")
    
    thread_id = "demo-thread-001"
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"📋 Initial State:")
    print(f"   Ticket ID: {initial_state['ticket_id']}")
    print(f"   Status: {initial_state['status']}")
    print(f"   Step: {initial_state['step']}")
    print(f"   Thread ID: {thread_id}")
    print()
    
    # Invoke the graph
    # ----------------------------------------
    # .invoke() runs the entire workflow synchronously
    # Returns the final state after all nodes execute
    #
    # The config with thread_id tells the checkpointer:
    # "Save this state under 'demo-thread-001'"
    
    print("⚙️  Running workflow...")
    print("-" * 40)
    
    final_state = graph.invoke(initial_state, config)
    
    print("-" * 40)
    print()
    
    # Print results
    # ----------------------------------------
    print("📊 Final State:")
    print(f"   Ticket ID: {final_state['ticket_id']}")
    print(f"   Status: {final_state['status']}")
    print(f"   Steps completed: {final_state['step']}")
    print()
    
    print("📜 Message Log:")
    for i, msg in enumerate(final_state["messages"], 1):
        print(f"   {i}. {msg}")
    print()
    
    # ----------------------------------------
    # Demonstrate state retrieval
    # ----------------------------------------
    print("💾 Persistence Demo:")
    print(f"   State saved under thread_id: '{thread_id}'")
    print("   In production, this would survive server restarts!")
    print("   (Currently using MemorySaver - state lost on exit)")
    print()
    
    print("=" * 60)
    print("✅ Hello World agent flow completed successfully!")
    print("=" * 60)


# ============================================
# SCRIPT ENTRY POINT
# ============================================

if __name__ == "__main__":
    """
    Python Entry Point Guard
    
    This block only runs when you execute:
        python main.py
    
    It does NOT run when you import this module:
        from main import build_agent_graph
    
    === Comparison ===
    
    Go:
        func main() {
            // This is the entry point
        }
    
    PHP (CLI):
        if (php_sapi_name() === 'cli') {
            // Running from command line
        }
    
    Python:
        if __name__ == "__main__":
            # Running as script, not imported
    
    __name__ is a special variable:
    - When running directly: __name__ == "__main__"
    - When imported: __name__ == "main" (the module name)
    """
    run_hello_world()
