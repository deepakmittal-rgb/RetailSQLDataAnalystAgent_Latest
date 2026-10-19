"""
Unit Tests for Conversation Memory and Follow-Up Resolution
"""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.memory import ConversationMemory

class TestConversationMemory(unittest.TestCase):

    def setUp(self):
        self.memory = ConversationMemory(window_size=3, session_file=None)

    def test_add_and_retrieve_turn(self):
        turn = self.memory.add_turn(
            user_query="What are the top 5 products by net sales?",
            generated_sql="SELECT * FROM products LIMIT 5;",
            sanitized_sql="SELECT * FROM products LIMIT 5;",
            summary="Top product is Rice 5kg.",
            row_count=5,
            filters={"category": "Groceries"}
        )
        self.assertEqual(turn.turn_id, 1)
        self.assertEqual(len(self.memory.turns), 1)
        self.assertEqual(self.memory.active_context["category"], "Groceries")

    def test_followup_detection(self):
        self.memory.add_turn(
            user_query="What are the top 5 products?",
            generated_sql="SELECT * FROM products;",
            sanitized_sql="SELECT * FROM products;",
            summary="Top products shown.",
            row_count=5
        )

        self.assertTrue(self.memory.is_followup_question("Now show only online channel."))
        self.assertTrue(self.memory.is_followup_question("What about in-store?"))
        self.assertTrue(self.memory.is_followup_question("Break down by region."))
        self.assertFalse(self.memory.is_followup_question("How many customers do we have in total?"))

    def test_resolve_channel_followup(self):
        self.memory.add_turn(
            user_query="Show sales by product",
            generated_sql="SELECT * FROM products;",
            sanitized_sql="SELECT * FROM products;",
            summary="Top products shown.",
            row_count=5
        )

        res = self.memory.resolve_followup("Now show only online channel.")
        self.assertTrue(res["is_followup"])
        self.assertEqual(res["delta_filters"].get("channel"), "Online")

    def test_sliding_window_eviction(self):
        mem = ConversationMemory(window_size=2, session_file=None)
        for i in range(10):
            mem.add_turn(f"Question {i}", f"SQL {i}", f"SQL {i}", f"Summary {i}", 1)
        self.assertLessEqual(len(mem.turns), 4)

    def test_clear_memory(self):
        self.memory.add_turn("Q1", "SQL1", "SQL1", "Sum1", 1)
        self.memory.clear()
        self.assertEqual(len(self.memory.turns), 0)
        self.assertIsNone(self.memory.active_context["channel"])

if __name__ == "__main__":
    unittest.main()
