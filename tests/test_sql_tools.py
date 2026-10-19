"""
Unit Tests for SQL Database Tool and Data Verification
"""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.sql_tools import SQLDatabaseTool
from database.load_data import EXPECTED_COUNTS

class TestSQLDatabaseTool(unittest.TestCase):

    def setUp(self):
        self.tool = SQLDatabaseTool()

    def test_database_row_counts(self):
        counts = self.tool.get_table_counts()
        for table, expected in EXPECTED_COUNTS.items():
            self.assertIn(table, counts)
            self.assertEqual(counts[table], expected, f"Row count mismatch for {table}")

    def test_execute_valid_query(self):
        qr = self.tool.execute_query("SELECT COUNT(*) AS total_orders FROM sales_transactions;")
        self.assertTrue(qr.success)
        self.assertIsNone(qr.error)
        self.assertEqual(qr.row_count, 1)
        self.assertEqual(qr.rows[0]["total_orders"], 360)

    def test_net_sales_calculation(self):
        sql = """
        SELECT ROUND(SUM(units_sold * unit_price * (1.0 - discount_pct/100.0)), 2) AS total_revenue
        FROM sales_transactions;
        """
        qr = self.tool.execute_query(sql)
        self.assertTrue(qr.success)
        # Expected baseline net revenue ~ ₹406,797.71
        revenue = qr.rows[0]["total_revenue"]
        self.assertAlmostEqual(revenue, 406797.71, delta=1.0)

    def test_return_count(self):
        qr = self.tool.execute_query("SELECT COUNT(*) AS cnt FROM returns;")
        self.assertTrue(qr.success)
        self.assertEqual(qr.rows[0]["cnt"], 46)

    def test_schema_summary_not_empty(self):
        summary = self.tool.get_table_schema_summary()
        self.assertIn("customers", summary)
        self.assertIn("sales_transactions", summary)
        self.assertIn("returns", summary)

if __name__ == "__main__":
    unittest.main()
