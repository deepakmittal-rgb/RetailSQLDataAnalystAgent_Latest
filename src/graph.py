"""
Retail SQL Data Analyst Agent - Graph Orchestrator
Implements the LangGraph / LangChain state graph workflow for retail SQL analysis:
Context Retrieval -> SQL Generation -> Safety Validation -> Execution -> Business Summary.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, TypedDict

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.safety import safety_validator, SafetyResult
from src.sql_tools import sql_database_tool, QueryResult
from src.memory import conversation_memory
from src.tiger_gateway_client import tiger_gateway_client

class RetailAnalystState(TypedDict, total=False):
    question: str
    original_question: str
    is_followup: bool
    conversation_history: str
    active_filters: Dict[str, Any]
    generated_sql: str
    sanitized_sql: str
    is_safe: bool
    safety_reason: str
    safety_warnings: List[str]
    query_result: Optional[Dict[str, Any]]
    business_summary: str
    error: Optional[str]
    retry_count: int

# --- NODE DEFINITIONS ---

def node_retrieve_context(state: RetailAnalystState) -> RetailAnalystState:
    """Node 1: Evaluates conversational memory, checks for follow-up signals and delta filters."""
    question = state["question"]
    followup_meta = conversation_memory.resolve_followup(question)

    merged_filters = dict(followup_meta["active_context"])
    merged_filters.update(followup_meta["delta_filters"])

    history_str = conversation_memory.format_history_for_prompt()

    return {
        **state,
        "is_followup": followup_meta["is_followup"],
        "active_filters": merged_filters,
        "conversation_history": history_str,
        "retry_count": state.get("retry_count", 0)
    }

def node_generate_sql(state: RetailAnalystState) -> RetailAnalystState:
    """Node 2: Generates MySQL query using Tiger Gateway LLM or domain generator."""
    question = state["question"]
    history = state.get("conversation_history", "")
    filters = state.get("active_filters", {})
    schema_context = sql_database_tool.get_table_schema_summary()

    sql = tiger_gateway_client.generate_sql(
        question=question,
        schema_context=schema_context,
        conversation_history=history,
        active_filters=filters
    )

    return {
        **state,
        "generated_sql": sql
    }

def node_validate_safety(state: RetailAnalystState) -> RetailAnalystState:
    """Node 3: Safety Guard - verifies query is strictly read-only and caps row limits."""
    sql = state.get("generated_sql", "")
    safety_res: SafetyResult = safety_validator.validate_and_sanitize(sql)

    return {
        **state,
        "is_safe": safety_res.is_safe,
        "safety_reason": safety_res.reason,
        "sanitized_sql": safety_res.sanitized_sql,
        "safety_warnings": safety_res.warnings
    }

def node_execute_sql(state: RetailAnalystState) -> RetailAnalystState:
    """Node 4: Executes safe SQL query against the retail database."""
    if not state.get("is_safe", False):
        return {
            **state,
            "error": state.get("safety_reason", "Query blocked by safety policy."),
            "query_result": {
                "success": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "error": state.get("safety_reason")
            }
        }

    sanitized = state.get("sanitized_sql", "")
    qr: QueryResult = sql_database_tool.execute_query(sanitized)

    qr_dict = {
        "success": qr.success,
        "columns": qr.columns,
        "rows": qr.rows,
        "row_count": qr.row_count,
        "execution_time_ms": qr.execution_time_ms,
        "query_executed": qr.query_executed,
        "error": qr.error
    }

    if not qr.success:
        return {
            **state,
            "error": f"Execution Error: {qr.error}",
            "query_result": qr_dict
        }

    return {
        **state,
        "query_result": qr_dict,
        "error": None
    }

def node_summarize_insights(state: RetailAnalystState) -> RetailAnalystState:
    """Node 5: Synthesizes a concise executive business intelligence summary."""
    qr = state.get("query_result")
    if not qr or not qr.get("success", False):
        summary = f"Unable to produce summary: {state.get('error', 'Query did not return data')}."
        return {**state, "business_summary": summary}

    question = state["question"]
    sql = state.get("sanitized_sql", "")
    rows = qr.get("rows", [])
    row_count = qr.get("row_count", 0)
    filters = state.get("active_filters", {})
    context_note = ", ".join(f"{k}='{v}'" for k, v in filters.items() if v)

    summary = tiger_gateway_client.generate_summary(
        user_question=question,
        sql_query=sql,
        query_results=rows,
        row_count=row_count,
        context_notes=context_note
    )

    # Commit turn to conversation memory
    conversation_memory.add_turn(
        user_query=question,
        generated_sql=state.get("generated_sql", ""),
        sanitized_sql=sql,
        summary=summary,
        row_count=row_count,
        filters=filters
    )

    return {
        **state,
        "business_summary": summary
    }

def node_handle_rejection(state: RetailAnalystState) -> RetailAnalystState:
    """Node 6: Handles security rejection or fatal execution errors."""
    reason = state.get("safety_reason") or state.get("error") or "Security check failed."
    explanation = f"⛔ Query Execution Blocked: {reason}\n\nOur security policy enforces strictly read-only SELECT operations and disallows table modifications."
    return {
        **state,
        "business_summary": explanation
    }

# --- GRAPH WORKFLOW CLASS ---

class RetailDataAnalystGraph:
    """
    Workflow orchestrator implementing LangGraph / LangChain graph semantics.
    Supports native LangGraph StateGraph when installed or built-in workflow engine.
    """

    def __init__(self):
        self._setup_graph()

    def _setup_graph(self):
        """Attempts to register LangGraph StateGraph, or falls back to built-in pipeline."""
        self.use_langgraph = False
        try:
            from langgraph.graph import StateGraph, END
            workflow = StateGraph(RetailAnalystState)

            workflow.add_node("retrieve_context", node_retrieve_context)
            workflow.add_node("generate_sql", node_generate_sql)
            workflow.add_node("validate_safety", node_validate_safety)
            workflow.add_node("execute_sql", node_execute_sql)
            workflow.add_node("summarize_insights", node_summarize_insights)
            workflow.add_node("handle_rejection", node_handle_rejection)

            workflow.set_entry_point("retrieve_context")
            workflow.add_edge("retrieve_context", "generate_sql")
            workflow.add_edge("generate_sql", "validate_safety")

            # Conditional routing based on safety
            def route_after_safety(state: RetailAnalystState):
                if state.get("is_safe", False):
                    return "execute_sql"
                return "handle_rejection"

            workflow.add_conditional_edges(
                "validate_safety",
                route_after_safety,
                {
                    "execute_sql": "execute_sql",
                    "handle_rejection": "handle_rejection"
                }
            )

            workflow.add_edge("execute_sql", "summarize_insights")
            workflow.add_edge("summarize_insights", END)
            workflow.add_edge("handle_rejection", END)

            self.compiled_graph = workflow.compile()
            self.use_langgraph = True
        except ImportError:
            self.use_langgraph = False

    def run(self, question: str, session_id: Optional[str] = None) -> RetailAnalystState:
        """Runs the analyst agent workflow for the given question."""
        initial_state: RetailAnalystState = {
            "question": question,
            "original_question": question,
            "is_followup": False,
            "conversation_history": "",
            "active_filters": {},
            "generated_sql": "",
            "sanitized_sql": "",
            "is_safe": False,
            "safety_reason": "",
            "safety_warnings": [],
            "query_result": None,
            "business_summary": "",
            "error": None,
            "retry_count": 0
        }

        if self.use_langgraph and hasattr(self, "compiled_graph"):
            return self.compiled_graph.invoke(initial_state)

        # Built-in deterministic pipeline execution
        s = node_retrieve_context(initial_state)
        s = node_generate_sql(s)
        s = node_validate_safety(s)

        if s.get("is_safe", False):
            s = node_execute_sql(s)
            s = node_summarize_insights(s)
        else:
            s = node_handle_rejection(s)

        return s

# Global agent graph instance
retail_agent_graph = RetailDataAnalystGraph()
