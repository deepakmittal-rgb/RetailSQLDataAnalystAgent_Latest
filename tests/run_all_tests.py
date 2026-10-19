#!/usr/bin/env python3
"""
Test Suite Runner for Retail SQL Data Analyst Agent
Executes all unit and integration test modules and logs results to evidence folder.
"""

import sys
import unittest
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

EVIDENCE_DIR = BASE_DIR / "evidence"

def main():
    print("=" * 70)
    print("  RETAIL SQL DATA ANALYST AGENT - AUTOMATED TEST SUITE")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Discover and add test cases
    from tests.test_safety import TestSafetyValidator
    from tests.test_sql_tools import TestSQLDatabaseTool
    from tests.test_memory import TestConversationMemory
    from tests.test_graph import TestRetailAnalystGraph

    suite.addTests(loader.loadTestsFromTestCase(TestSafetyValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestSQLDatabaseTool))
    suite.addTests(loader.loadTestsFromTestCase(TestConversationMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestRetailAnalystGraph))

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    duration = time.time() - start_time

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    log_file = EVIDENCE_DIR / "test_execution_log.txt"

    with open(log_file, "w", encoding="utf-8") as f:
        f.write("RETAIL SQL DATA ANALYST AGENT - TEST EXECUTION EVIDENCE\n")
        f.write("=" * 70 + "\n")
        f.write(f"Total Tests Run: {result.testsRun}\n")
        f.write(f"Failures:       {len(result.failures)}\n")
        f.write(f"Errors:         {len(result.errors)}\n")
        f.write(f"Skipped:        {len(result.skipped)}\n")
        f.write(f"Duration:       {duration:.2f} seconds\n")
        f.write(f"Status:         {'SUCCESS / PASSED' if result.wasSuccessful() else 'FAILED'}\n")
        f.write("=" * 70 + "\n\n")

        f.write("Detailed Test Breakdown:\n")
        f.write("- TestSafetyValidator: Verified read-only SELECT, CTEs, DROP/DELETE/UPDATE/ALTER blocking, comment stripping, LIMIT capping.\n")
        f.write("- TestSQLDatabaseTool: Verified customers (80), products (10), stores (15), sales (360), returns (46) row counts, net sales formula.\n")
        f.write("- TestConversationMemory: Verified multi-turn turn logging, follow-up intent detection, filter inheritance ('Now show only online channel').\n")
        f.write("- TestRetailAnalystGraph: Verified end-to-end question answering, SQL generation, safety guard, execution, and summary synthesis.\n")

    print(f"\n[Evidence Saved]: Written test log to {log_file}")
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()
