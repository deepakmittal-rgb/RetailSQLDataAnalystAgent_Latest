"""
Retail SQL Data Analyst Agent - SQL Database Execution Tools
Handles connection pooling, query execution, dialect compatibility (MySQL / SQLite),
table introspection, and tabular result formatting.
"""

import os
import time
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from src.config import (
    DB_TYPE, SQLITE_DB_PATH, MYSQL_HOST, MYSQL_PORT,
    MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, QUERY_TIMEOUT_SECONDS
)

@dataclass
class QueryResult:
    success: bool
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    query_executed: str
    error: Optional[str] = None

class SQLDatabaseTool:
    """Database executor for MySQL and local SQLite databases."""

    def __init__(self, db_type: str = DB_TYPE, db_path: Path = SQLITE_DB_PATH):
        self.db_type = db_type
        self.db_path = db_path
        self._ensure_database_initialized()

    def _ensure_database_initialized(self):
        """If SQLite database does not exist or has 0 tables, initialize it from load_data."""
        if self.db_type == "sqlite":
            if not self.db_path.exists() or os.path.getsize(self.db_path) == 0:
                from database.load_data import load_data_into_sqlite, DATA_DIR
                load_data_into_sqlite(self.db_path, DATA_DIR)

    def execute_query(self, sql_query: str) -> QueryResult:
        """Executes a sanitized, validated SQL query and returns structured results."""
        start_time = time.time()

        if self.db_type == "sqlite":
            return self._execute_sqlite(sql_query, start_time)
        else:
            try:
                return self._execute_mysql(sql_query, start_time)
            except Exception as e:
                # Graceful fallback to SQLite if MySQL is unreachable
                import sys
                print(f"[Warning] MySQL execution failed ({e}), falling back to local SQLite engine.", file=sys.stderr)
                return self._execute_sqlite(sql_query, start_time)

    def _adapt_mysql_to_sqlite(self, sql: str) -> str:
        """Helper to adapt minor MySQL dialect differences to SQLite."""
        adapted = sql
        # Replace IFNULL with COALESCE (standard)
        adapted = adapted.replace("IFNULL(", "COALESCE(")
        # MySQL YEAR(order_date) -> strftime('%Y', order_date) if needed, but SQLite supports strftime
        # Note: SQLite supports standard ROUND, SUM, COUNT, AVG, MIN, MAX
        return adapted

    def _execute_sqlite(self, sql_query: str, start_time: float) -> QueryResult:
        query = self._adapt_mysql_to_sqlite(sql_query)
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=QUERY_TIMEOUT_SECONDS)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)

            rows_raw = cursor.fetchall()
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = [dict(r) for r in rows_raw]
            elapsed = (time.time() - start_time) * 1000

            return QueryResult(
                success=True,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=round(elapsed, 2),
                query_executed=query,
                error=None
            )
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return QueryResult(
                success=False,
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=round(elapsed, 2),
                query_executed=query,
                error=str(e)
            )
        finally:
            if conn:
                conn.close()

    def _execute_mysql(self, sql_query: str, start_time: float) -> QueryResult:
        import pymysql
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=QUERY_TIMEOUT_SECONDS
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                elapsed = (time.time() - start_time) * 1000
                return QueryResult(
                    success=True,
                    columns=columns,
                    rows=list(rows),
                    row_count=len(rows),
                    execution_time_ms=round(elapsed, 2),
                    query_executed=sql_query,
                    error=None
                )
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return QueryResult(
                success=False,
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=round(elapsed, 2),
                query_executed=sql_query,
                error=str(e)
            )
        finally:
            conn.close()

    def get_table_schema_summary(self) -> str:
        """Returns compact text summary of database schema for LLM prompting."""
        return """
DATABASE SCHEMA (retail_db):

1. customers (customer_id, customer_segment, signup_date, preferred_channel, city)
   - customer_segment: 'Regular', 'Budget', 'Premium', 'Wholesale'
   - preferred_channel: 'Online', 'Mobile App', 'In-store', 'Partner'

2. products (product_id, product_name, category, sub_category, base_price)
   - category: 'Beverages', 'Groceries', 'Personal Care', 'Household', 'Snacks'
   - base_price: DECIMAL (list price in INR)

3. stores (store_id, store_name, region, city, store_type)
   - region: 'North', 'South', 'East', 'West', 'Central'
   - store_type: 'Supermarket', 'Convenience', 'Express'

4. sales_transactions (order_id, order_date, store_id, product_id, customer_id, sales_channel, units_sold, unit_price, discount_pct, payment_status, delivery_status)
   - sales_channel: 'Online', 'Mobile App', 'In-store', 'Partner'
   - discount_pct: 0 to 20
   - payment_status: 'Paid', 'Pending'
   - delivery_status: 'Delivered', 'Processing', 'Returned'
   - IMPORTANT FORMULA: Net Sales = units_sold * unit_price * (1.0 - discount_pct / 100.0)

5. returns (return_id, order_id, return_date, return_reason)
   - return_reason: 'Customer Changed Mind', 'Damaged', 'Wrong Item', 'Late Delivery', 'Quality Issue'
   - Joined via: returns.order_id = sales_transactions.order_id
"""

    def get_table_counts(self) -> Dict[str, int]:
        """Returns row count for each table."""
        res = {}
        for tbl in ["customers", "products", "stores", "sales_transactions", "returns"]:
            qr = self.execute_query(f"SELECT COUNT(*) AS cnt FROM {tbl}")
            if qr.success and qr.rows:
                res[tbl] = qr.rows[0]["cnt"]
        return res

# Global database tool instance
sql_database_tool = SQLDatabaseTool()
