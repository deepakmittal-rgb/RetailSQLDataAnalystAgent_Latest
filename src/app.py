#!/usr/bin/env python3
"""
Retail SQL Data Analyst Agent - Main Application Interface
Provides command-line interactive analytics, single-query answering,
multi-turn benchmark demonstrations, and report exports.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.graph import retail_agent_graph
from src.memory import conversation_memory
from src.config import OUTPUTS_DIR, EVIDENCE_DIR

def print_banner():
    print("""
================================================================================
             RETAIL SQL DATA ANALYST AGENT (Tiger Analytics)
  Multi-Turn Conversational BI | Safe Read-Only MySQL Execution | Summaries
================================================================================
""")

def run_single_question(question: str, print_output: bool = True) -> dict:
    """Runs a single question through the analyst agent graph."""
    if print_output:
        print(f"\n[User Question]: \"{question}\"")
        print("-" * 70)

    result = retail_agent_graph.run(question)

    if print_output:
        print("[1. Safety Verification]")
        is_safe = result.get("is_safe", False)
        status = "PASSED" if is_safe else "BLOCKED"
        print(f"    Status: {status} | Reason: {result.get('safety_reason')}")
        if result.get("safety_warnings"):
            for w in result["safety_warnings"]:
                print(f"    Notice: {w}")

        print("\n[2. Generated Safe SQL Query]")
        sql = result.get("sanitized_sql") or result.get("generated_sql")
        for line in sql.strip().split("\n"):
            print(f"    {line}")

        qr = result.get("query_result")
        if qr and qr.get("success"):
            print(f"\n[3. Execution Results] ({qr.get('row_count')} rows returned in {qr.get('execution_time_ms')}ms)")
            cols = qr.get("columns", [])
            rows = qr.get("rows", [])
            if cols and rows:
                header = " | ".join(str(c).ljust(18) for c in cols[:6])
                print(f"    {header}")
                print(f"    {'-' * len(header)}")
                for row in rows[:5]:
                    row_str = " | ".join(str(row.get(c, "")).ljust(18) for c in cols[:6])
                    print(f"    {row_str}")
                if len(rows) > 5:
                    print(f"    ... [{len(rows) - 5} more rows]")

        print("\n[4. Business Insights & Summary]")
        for line in result.get("business_summary", "").split("\n"):
            print(f"    {line}")
        print("=" * 70)

    return result

def run_interactive_mode():
    """Runs interactive session in CLI allowing natural follow-ups."""
    print_banner()
    print("Type your retail business question below (or 'exit' / 'clear').")
    print("Example: 'What are the top 5 products by net sales?'")
    print("Follow-up: 'Now show only online channel.'\n")

    while True:
        try:
            q = input("Analyst Agent > ").strip()
            if not q:
                continue
            if q.lower() in ["exit", "quit", "q"]:
                print("Exiting Retail SQL Analyst Agent. Goodbye!")
                break
            if q.lower() == "clear":
                conversation_memory.clear()
                print("Conversation context memory cleared.\n")
                continue

            run_single_question(q, print_output=True)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting session.")
            break

def run_benchmark_suite(export: bool = True):
    """
    Executes a structured multi-turn benchmark demonstrating context memory:
    Turn 1: Initial broad analysis: "What are the top 5 products by net sales?"
    Turn 2: Elliptical follow-up: "Now show only online channel."
    Turn 3: Operational inquiry: "Which stores have the highest returns?"
    """
    print_banner()
    print("[Starting Multi-Turn Context Memory Benchmark Suite]\n")

    conversation_memory.clear()

    turns_data = []

    # Turn 1
    t1_q = "What are the top 5 products by net sales?"
    res1 = run_single_question(t1_q, print_output=True)
    turns_data.append({"turn": 1, "question": t1_q, "result": res1})

    # Turn 2: Follow-up question relying on memory
    t2_q = "Now show only online channel."
    res2 = run_single_question(t2_q, print_output=True)
    turns_data.append({"turn": 2, "question": t2_q, "result": res2})

    # Turn 3: Return reasons analysis
    t3_q = "Which return reason is most common?"
    res3 = run_single_question(t3_q, print_output=True)
    turns_data.append({"turn": 3, "question": t3_q, "result": res3})

    if export:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

        # Save turn outputs
        out_file = OUTPUTS_DIR / "sample_turn_1_overview.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(res1, f, indent=2, default=str)

        out_file2 = OUTPUTS_DIR / "sample_turn_2_online_channel_followup.json"
        with open(out_file2, "w", encoding="utf-8") as f:
            json.dump(res2, f, indent=2, default=str)

        out_file3 = OUTPUTS_DIR / "sample_turn_3_return_analysis.json"
        with open(out_file3, "w", encoding="utf-8") as f:
            json.dump(res3, f, indent=2, default=str)

        # Save evidence run log
        evidence_file = EVIDENCE_DIR / "sample_agent_run.txt"
        with open(evidence_file, "w", encoding="utf-8") as f:
            f.write("RETAIL SQL DATA ANALYST AGENT - MULTI-TURN VERIFICATION LOG\n")
            f.write("=" * 70 + "\n\n")
            for t in turns_data:
                f.write(f"TURN #{t['turn']}: \"{t['question']}\"\n")
                f.write(f"Generated SQL:\n{t['result'].get('sanitized_sql')}\n\n")
                f.write(f"Business Summary:\n{t['result'].get('business_summary')}\n")
                f.write("-" * 70 + "\n\n")

        print(f"\n[Export Success]: Saved outputs to {OUTPUTS_DIR} and evidence to {evidence_file}")

def main():
    parser = argparse.ArgumentParser(description="Retail SQL Data Analyst Agent CLI")
    parser.add_argument("--question", "-q", type=str, help="Natural language question to execute")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive conversation console")
    parser.add_argument("--benchmark", "-b", action="store_true", help="Run multi-turn benchmark suite")
    parser.add_argument("--export", action="store_true", help="Export run outputs to /outputs folder")
    args = parser.parse_args()

    if args.question:
        run_single_question(args.question)
    elif args.benchmark:
        run_benchmark_suite(export=True)
    elif args.interactive or len(sys.argv) == 1:
        # Default to interactive or run benchmark if in non-interactive environment
        if sys.stdin.isatty():
            run_interactive_mode()
        else:
            run_benchmark_suite(export=True)

if __name__ == "__main__":
    main()
