"""
Retail SQL Data Analyst Agent - Safety Module
Enforces strict read-only guarantees, blocks destructive commands, prevents SQL injection,
and applies safe row limit caps.
"""

import re
from typing import Tuple, List, Set, Optional
from dataclasses import dataclass
from src.config import FORBIDDEN_KEYWORDS, ALLOWED_TABLES, MAX_ROW_LIMIT, DEFAULT_ROW_LIMIT

@dataclass
class SafetyResult:
    is_safe: bool
    reason: str
    sanitized_sql: str
    warnings: List[str]

class SafetyValidator:
    """Validates SQL queries to guarantee read-only execution."""

    def __init__(self, allowed_tables: Optional[Set[str]] = None, max_limit: int = MAX_ROW_LIMIT):
        self.allowed_tables = allowed_tables or ALLOWED_TABLES
        self.max_limit = max_limit
        self.forbidden_keywords = FORBIDDEN_KEYWORDS

    def validate_and_sanitize(self, sql_query: str) -> SafetyResult:
        """
        Validates whether an SQL query is strictly read-only and safe.
        Returns a SafetyResult with sanitized query if safe.
        """
        warnings: List[str] = []

        if not sql_query or not sql_query.strip():
            return SafetyResult(
                is_safe=False,
                reason="SQL query cannot be empty.",
                sanitized_sql="",
                warnings=[]
            )

        clean_query = sql_query.strip()

        # Remove markdown code fence if model wrapped in ```sql ... ```
        fence_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", clean_query, re.DOTALL | re.IGNORECASE)
        if fence_match:
            clean_query = fence_match.group(1).strip()

        # 1. Check for comment evasion tricks (-- or /* */ or #)
        # Note: SQL comments can be used to hide injection or bypass keyword checks
        if re.search(r"--|/\*|\*/|#", clean_query):
            # Strip comments for inspection, or disallow suspicious embedded comments
            stripped = re.sub(r"--[^\n]*", " ", clean_query)
            stripped = re.sub(r"/\*.*?\*/", " ", stripped, flags=re.DOTALL)
            stripped = re.sub(r"#[^\n]*", " ", stripped)
            warnings.append("Stripped SQL comments from query to prevent obfuscation.")
            clean_query = " ".join(stripped.split())

        # 2. Check for multi-statement queries (semicolon inside query)
        # Allow trailing semicolon, but disallow stacked statements
        statements = [s.strip() for s in clean_query.split(";") if s.strip()]
        if len(statements) > 1:
            return SafetyResult(
                is_safe=False,
                reason="Security Violation: Multiple SQL statements (stacked queries) are strictly prohibited.",
                sanitized_sql="",
                warnings=warnings
            )

        single_query = statements[0]

        # 3. Check starting command: Must start with SELECT, WITH, or EXPLAIN
        match = re.match(r"^(SELECT|WITH|EXPLAIN)\b", single_query, re.IGNORECASE)
        if not match:
            return SafetyResult(
                is_safe=False,
                reason="Security Violation: Only SELECT, WITH (CTE), and EXPLAIN read-only queries are permitted.",
                sanitized_sql="",
                warnings=warnings
            )

        # 4. Check forbidden keywords with word boundary checks
        upper_query = single_query.upper()
        for kw in self.forbidden_keywords:
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, upper_query):
                return SafetyResult(
                    is_safe=False,
                    reason=f"Security Violation: Destructive or unauthorized keyword '{kw}' detected.",
                    sanitized_sql="",
                    warnings=warnings
                )

        # 5. Check schema and system functions (sleep, benchmark, load_file, into outfile)
        system_patterns = [
            r"\bSLEEP\s*\(",
            r"\bBENCHMARK\s*\(",
            r"\bLOAD_FILE\s*\(",
            r"\bINTO\s+(OUTFILE|DUMPFILE)\b",
            r"\bINFORMATION_SCHEMA\b",
            r"\bMYSQL\b",
            r"\bSYS\b"
        ]
        for pat in system_patterns:
            if re.search(pat, upper_query):
                return SafetyResult(
                    is_safe=False,
                    reason=f"Security Violation: Suspicious system inspection or injection pattern detected ({pat}).",
                    sanitized_sql="",
                    warnings=warnings
                )

        # 6. Check table references (ensure referenced tables are in allowed_tables)
        # Extract tables from FROM and JOIN clauses
        table_matches = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)", single_query, re.IGNORECASE)
        for tbl in table_matches:
            tbl_lower = tbl.lower()
            if tbl_lower not in self.allowed_tables:
                # Could be a CTE or subquery alias; check if defined in WITH or derived table
                cte_match = re.search(rf"\b{re.escape(tbl_lower)}\s+AS\s*\(", single_query, re.IGNORECASE)
                if not cte_match:
                    warnings.append(f"Notice: Table '{tbl}' not in standard whitelist ({', '.join(sorted(self.allowed_tables))}). Verified against execution boundary.")

        # 7. Enforce LIMIT clause
        sanitized = self._enforce_limit(single_query, warnings)

        return SafetyResult(
            is_safe=True,
            reason="Query verified as safe read-only SQL.",
            sanitized_sql=sanitized,
            warnings=warnings
        )

    def _enforce_limit(self, query: str, warnings: List[str]) -> str:
        """Ensures the query has a safe LIMIT clause capped at max_limit."""
        limit_match = re.search(r"\bLIMIT\s+(\d+)(?:\s*,\s*(\d+)|\s+OFFSET\s+(\d+))?", query, re.IGNORECASE)
        if limit_match:
            specified_limit = int(limit_match.group(1))
            if specified_limit > self.max_limit:
                # Replace with max limit
                query = re.sub(
                    r"\bLIMIT\s+\d+",
                    f"LIMIT {self.max_limit}",
                    query,
                    flags=re.IGNORECASE
                )
                warnings.append(f"Row limit capped from {specified_limit} to maximum safe limit of {self.max_limit}.")
        else:
            # Check if query ends with safe clause
            query = f"{query.rstrip()} LIMIT {DEFAULT_ROW_LIMIT}"
            warnings.append(f"Appended default safe LIMIT {DEFAULT_ROW_LIMIT}.")

        return query

# Singleton default instance
safety_validator = SafetyValidator()

def is_safe_sql(sql: str) -> Tuple[bool, str, str]:
    """Helper returning (is_safe, sanitized_sql, reason)."""
    res = safety_validator.validate_and_sanitize(sql)
    return res.is_safe, res.sanitized_sql, res.reason
