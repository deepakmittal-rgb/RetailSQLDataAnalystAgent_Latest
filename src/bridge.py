#!/usr/bin/env python3
"""
Python Bridge Interface for Express Fullstack Server
Processes JSON commands and returns structured results from the Retail SQL Analyst Agent.
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.graph import retail_agent_graph
from src.memory import conversation_memory
from src.safety import safety_validator
from src.sql_tools import sql_database_tool

def handle_query(payload: dict) -> dict:
    question = payload.get("question", "").strip()
    if payload.get("reset"):
        conversation_memory.clear()

    if not question:
        return {"error": "Question is required."}

    state = retail_agent_graph.run(question)
    return {
        "question": state.get("question"),
        "is_followup": state.get("is_followup", False),
        "active_filters": state.get("active_filters", {}),
        "generated_sql": state.get("generated_sql", ""),
        "sanitized_sql": state.get("sanitized_sql", ""),
        "is_safe": state.get("is_safe", False),
        "safety_reason": state.get("safety_reason", ""),
        "safety_warnings": state.get("safety_warnings", []),
        "query_result": state.get("query_result"),
        "business_summary": state.get("business_summary", ""),
        "error": state.get("error")
    }

def handle_schema() -> dict:
    counts = sql_database_tool.get_table_counts()
    tables_meta = []
    for tbl in ["customers", "products", "stores", "sales_transactions", "returns"]:
        qr_cols = sql_database_tool.execute_query(f"PRAGMA table_info({tbl});")
        sample_qr = sql_database_tool.execute_query(f"SELECT * FROM {tbl} LIMIT 3;")
        tables_meta.append({
            "name": tbl,
            "row_count": counts.get(tbl, 0),
            "columns": [dict(r) for r in qr_cols.rows] if qr_cols.success else [],
            "sample_rows": sample_qr.rows if sample_qr.success else []
        })

    return {
        "tables": tables_meta,
        "total_tables": len(tables_meta),
        "counts": counts
    }

def handle_validate(payload: dict) -> dict:
    sql = payload.get("sql", "").strip()
    res = safety_validator.validate_and_sanitize(sql)
    return {
        "sql": sql,
        "is_safe": res.is_safe,
        "reason": res.reason,
        "sanitized_sql": res.sanitized_sql,
        "warnings": res.warnings
    }

def handle_reset() -> dict:
    conversation_memory.clear()
    return {"status": "cleared", "message": "Conversation context memory has been reset."}

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"error": "Empty input"}))
            return

        payload = json.loads(raw_input)
        action = payload.get("action", "query")

        if action == "query":
            out = handle_query(payload)
        elif action == "schema":
            out = handle_schema()
        elif action == "validate_sql":
            out = handle_validate(payload)
        elif action == "reset":
            out = handle_reset()
        else:
            out = {"error": f"Unknown action '{action}'"}

        print(json.dumps(out, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
