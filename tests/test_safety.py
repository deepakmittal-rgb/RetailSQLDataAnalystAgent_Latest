"""
Unit Tests for Safety Module (Safe Read-Only SQL Validator)
"""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.safety import SafetyValidator, MAX_ROW_LIMIT, DEFAULT_ROW_LIMIT

class TestSafetyValidator(unittest.TestCase):

    def setUp(self):
        self.validator = SafetyValidator()

    def test_allow_valid_select(self):
        sql = "SELECT product_name, base_price FROM products WHERE category = 'Groceries';"
        res = self.validator.validate_and_sanitize(sql)
        self.assertTrue(res.is_safe)
        self.assertIn("SELECT", res.sanitized_sql)
        self.assertIn("LIMIT", res.sanitized_sql)

    def test_allow_valid_cte_with_query(self):
        sql = """
        WITH product_summary AS (
            SELECT product_id, SUM(units_sold) AS total_units
            FROM sales_transactions
            GROUP BY product_id
        )
        SELECT p.product_name, ps.total_units
        FROM product_summary ps
        JOIN products p ON ps.product_id = p.product_id;
        """
        res = self.validator.validate_and_sanitize(sql)
        self.assertTrue(res.is_safe)
        self.assertIn("WITH", res.sanitized_sql)

    def test_block_drop_table(self):
        sql = "DROP TABLE sales_transactions;"
        res = self.validator.validate_and_sanitize(sql)
        self.assertFalse(res.is_safe)
        self.assertIn("Security Violation", res.reason)

    def test_block_delete_from(self):
        sql = "DELETE FROM customers WHERE customer_id = 'C-0001';"
        res = self.validator.validate_and_sanitize(sql)
        self.assertFalse(res.is_safe)
        self.assertIn("Security Violation", res.reason)

    def test_block_update(self):
        sql = "UPDATE products SET base_price = 10 WHERE product_id = 'P-001';"
        res = self.validator.validate_and_sanitize(sql)
        self.assertFalse(res.is_safe)
        self.assertIn("Security Violation", res.reason)

    def test_block_insert(self):
        sql = "INSERT INTO returns (return_id, order_id, return_date, return_reason) VALUES ('R-999', 'O-001', '2026-04-20', 'Test');"
        res = self.validator.validate_and_sanitize(sql)
        self.assertFalse(res.is_safe)
        self.assertIn("Security Violation", res.reason)

    def test_block_alter_table(self):
        sql = "ALTER TABLE stores ADD COLUMN manager VARCHAR(50);"
        res = self.validator.validate_and_sanitize(sql)
        self.assertFalse(res.is_safe)

    def test_block_truncate_table(self):
        sql = "TRUNCATE TABLE sales_transactions;"
        res = self.validator.validate_and_sanitize(sql)
        self.assertFalse(res.is_safe)

    def test_block_stacked_queries_sql_injection(self):
        sql = "SELECT * FROM products; DROP TABLE customers;"
        res = self.validator.validate_and_sanitize(sql)
        self.assertFalse(res.is_safe)
        self.assertIn("Multiple SQL statements", res.reason)

    def test_block_system_functions(self):
        sql = "SELECT SLEEP(10) FROM customers;"
        res = self.validator.validate_and_sanitize(sql)
        self.assertFalse(res.is_safe)

    def test_limit_capping(self):
        sql = "SELECT * FROM sales_transactions LIMIT 500;"
        res = self.validator.validate_and_sanitize(sql)
        self.assertTrue(res.is_safe)
        self.assertIn(f"LIMIT {MAX_ROW_LIMIT}", res.sanitized_sql)

    def test_append_default_limit_when_missing(self):
        sql = "SELECT * FROM stores"
        res = self.validator.validate_and_sanitize(sql)
        self.assertTrue(res.is_safe)
        self.assertIn(f"LIMIT {DEFAULT_ROW_LIMIT}", res.sanitized_sql)

if __name__ == "__main__":
    unittest.main()
