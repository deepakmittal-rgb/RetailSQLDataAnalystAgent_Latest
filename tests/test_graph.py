"""
Integration Tests for Retail Analyst Agent Graph Workflow
"""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.graph import retail_agent_graph
from src.memory import conversation_memory

class TestRetailAnalystGraph(unittest.TestCase):

    def setUp(self):
        conversation_memory.clear()

    def test_full_pipeline_top_products(self):
        state = retail_agent_graph.run("What are the top 5 products by net sales?")
        self.assertTrue(state.get("is_safe"))
        self.assertIn("SELECT", state.get("sanitized_sql", ""))
        qr = state.get("query_result")
        self.assertIsNotNone(qr)
        self.assertTrue(qr.get("success"))
        self.assertGreater(qr.get("row_count"), 0)
        self.assertTrue(len(state.get("business_summary", "")) > 10)

    def test_multiturn_followup_channel(self):
        # Turn 1
        s1 = retail_agent_graph.run("What are the top 5 products by net sales?")
        self.assertTrue(s1.get("is_safe"))

        # Turn 2: Follow-up
        s2 = retail_agent_graph.run("Now show only online channel.")
        self.assertTrue(s2.get("is_safe"))
        self.assertIn("Online", s2.get("sanitized_sql", ""))
        qr = s2.get("query_result")
        self.assertTrue(qr.get("success"))
        self.assertIn("Online", s2.get("business_summary", ""))

    def test_rejection_of_destructive_query(self):
        # Even if a malicious prompt is framed, the safety validator will block it
        s = retail_agent_graph.run("DROP TABLE customers;")
        self.assertFalse(s.get("is_safe"))
        self.assertIn("Blocked", s.get("business_summary", ""))

if __name__ == "__main__":
    unittest.main()
