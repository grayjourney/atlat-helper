import pytest
from unittest.mock import MagicMock

from src.agents.supervisor import build_supervisor_graph


class TestBuildSupervisorGraph:
    
    def test_returns_compiled_graph(self):
        graph = build_supervisor_graph()
        assert graph is not None
    
    def test_graph_has_expected_nodes(self):
        graph = build_supervisor_graph()
        node_names = list(graph.nodes.keys())
        
        assert "classify_intent" in node_names
        assert "ticket_subgraph" in node_names
        assert "general_chat_node" in node_names
        assert "confluence_subgraph" in node_names
        assert "board_subgraph" in node_names
    
    def test_accepts_checkpointer(self):
        mock_checkpointer = MagicMock()
        graph = build_supervisor_graph(checkpointer=mock_checkpointer)
        assert graph is not None
    
    def test_graph_has_expected_node_count(self):
        graph = build_supervisor_graph()
        node_names = list(graph.nodes.keys())
        # 5 custom nodes + 1 __start__ node added by LangGraph
        assert len(node_names) == 6
