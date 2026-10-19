"""
Retail SQL Data Analyst Agent - Conversation Context Memory Manager
Preserves conversation history, tracks active filters and dimensions,
and resolves follow-up analytical queries (e.g. "Now show only online channel").
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from src.config import MEMORY_WINDOW_SIZE, OUTPUTS_DIR

SESSION_FILE = OUTPUTS_DIR / ".session_memory.json"

@dataclass
class ConversationTurn:
    turn_id: int
    user_query: str
    generated_sql: str
    sanitized_sql: str
    summary: str
    row_count: int
    applied_filters: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class ConversationMemory:
    """Manages conversational state, active filters, and context resolution."""

    def __init__(self, window_size: int = MEMORY_WINDOW_SIZE, session_file: Optional[Path] = SESSION_FILE):
        self.window_size = window_size
        self.session_file = session_file
        self.turns: List[ConversationTurn] = []
        self.active_context: Dict[str, Any] = {
            "channel": None,
            "region": None,
            "city": None,
            "category": None,
            "customer_segment": None,
            "store_id": None,
            "last_primary_metric": "net_sales",
            "last_dimension": None
        }
        self._load_session()

    def _load_session(self):
        """Loads state from session file if it exists."""
        if self.session_file and self.session_file.exists():
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.active_context = data.get("active_context", self.active_context)
                    loaded_turns = []
                    for t in data.get("turns", []):
                        loaded_turns.append(ConversationTurn(**t))
                    self.turns = loaded_turns[-self.window_size:]
            except Exception:
                pass

    def _save_session(self):
        """Persists state to session file."""
        if self.session_file:
            try:
                self.session_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.session_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "active_context": self.active_context,
                        "turns": [asdict(t) for t in self.turns]
                    }, f, indent=2)
            except Exception:
                pass

    def add_turn(
        self,
        user_query: str,
        generated_sql: str,
        sanitized_sql: str,
        summary: str,
        row_count: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """Adds a completed turn to memory and updates active filters."""
        turn_id = len(self.turns) + 1
        filters = filters or self._extract_filters_from_sql(sanitized_sql)

        # Merge filters into active context
        for k, v in filters.items():
            if v is not None:
                self.active_context[k] = v

        turn = ConversationTurn(
            turn_id=turn_id,
            user_query=user_query,
            generated_sql=generated_sql,
            sanitized_sql=sanitized_sql,
            summary=summary,
            row_count=row_count,
            applied_filters=filters
        )
        self.turns.append(turn)

        # Keep within sliding window size
        if len(self.turns) > self.window_size * 2:
            self.turns = self.turns[-self.window_size:]

        self._save_session()
        return turn

    def get_recent_turns(self, n: Optional[int] = None) -> List[ConversationTurn]:
        """Returns the most recent n turns."""
        limit = n or self.window_size
        return self.turns[-limit:]

    def format_history_for_prompt(self, max_turns: int = 3) -> str:
        """Formats recent conversation history for LLM prompting."""
        recent = self.get_recent_turns(max_turns)
        if not recent:
            return "No previous conversation context (this is the first question)."

        history_lines = ["RECENT CONVERSATION CONTEXT:"]
        for turn in recent:
            history_lines.append(f"Turn #{turn.turn_id}:")
            history_lines.append(f"  User Asked: \"{turn.user_query}\"")
            history_lines.append(f"  Generated SQL: {turn.sanitized_sql}")
            history_lines.append(f"  Summary: {turn.summary}")
            if turn.applied_filters:
                filter_str = ", ".join(f"{k}='{v}'" for k, v in turn.applied_filters.items() if v)
                if filter_str:
                    history_lines.append(f"  Active Filters: {filter_str}")

        if any(self.active_context.values()):
            ctx_str = ", ".join(f"{k}='{v}'" for k, v in self.active_context.items() if v)
            history_lines.append(f"Current Cumulative Filters: {ctx_str}")

        return "\n".join(history_lines)

    def is_followup_question(self, question: str) -> bool:
        """Detects whether a user prompt is an elliptical or follow-up question."""
        if not self.turns:
            return False

        q = question.lower().strip()
        followup_signals = [
            "now show", "only", "what about", "and for", "how about",
            "filter by", "break down by", "instead", "same for",
            "just for", "compare that", "show that", "also show",
            "for online", "for in-store", "for mobile", "for partner"
        ]
        return any(q.startswith(sig) or f" {sig} " in f" {q} " for sig in followup_signals)

    def resolve_followup(self, question: str) -> Dict[str, Any]:
        """
        Analyzes follow-up question against conversation memory.
        Returns extracted delta filters and context instructions.
        """
        q = question.lower()
        delta_filters: Dict[str, Any] = {}
        last_turn = self.turns[-1] if self.turns else None

        # 1. Channel detection
        if "online" in q:
            delta_filters["channel"] = "Online"
        elif "mobile app" in q or "mobile" in q or "app" in q:
            delta_filters["channel"] = "Mobile App"
        elif "in-store" in q or "instore" in q or "store" in q:
            delta_filters["channel"] = "In-store"
        elif "partner" in q:
            delta_filters["channel"] = "Partner"

        # 2. Customer segment detection
        for seg in ["Regular", "Budget", "Premium", "Wholesale"]:
            if seg.lower() in q:
                delta_filters["customer_segment"] = seg

        # 3. Category detection
        for cat in ["Beverages", "Groceries", "Personal Care", "Household", "Snacks"]:
            if cat.lower() in q:
                delta_filters["category"] = cat

        # 4. Region / City detection
        for reg in ["North", "South", "East", "West", "Central"]:
            if reg.lower() in q:
                delta_filters["region"] = reg

        for city in ["Mumbai", "Delhi", "Bengaluru", "Jaipur", "Hyderabad", "Kolkata", "Chennai", "Pune", "Lucknow", "Bhopal", "Nagpur", "Indore", "Guwahati", "Bhubaneswar", "Ahmedabad"]:
            if city.lower() in q:
                delta_filters["city"] = city

        return {
            "is_followup": self.is_followup_question(question),
            "last_turn": last_turn,
            "delta_filters": delta_filters,
            "active_context": self.active_context
        }

    def _extract_filters_from_sql(self, sql: str) -> Dict[str, Any]:
        """Extracts simple filter clauses from SQL string for state tracking."""
        filters = {}
        # Channel
        chan_match = re.search(r"sales_channel\s*=\s*'([^']+)'", sql, re.IGNORECASE)
        if chan_match:
            filters["channel"] = chan_match.group(1)

        # Category
        cat_match = re.search(r"category\s*=\s*'([^']+)'", sql, re.IGNORECASE)
        if cat_match:
            filters["category"] = cat_match.group(1)

        # Region
        reg_match = re.search(r"region\s*=\s*'([^']+)'", sql, re.IGNORECASE)
        if reg_match:
            filters["region"] = reg_match.group(1)

        # Customer Segment
        seg_match = re.search(r"customer_segment\s*=\s*'([^']+)'", sql, re.IGNORECASE)
        if seg_match:
            filters["customer_segment"] = seg_match.group(1)

        return filters

    def clear(self):
        """Clears memory state for a fresh conversation session."""
        self.turns.clear()
        self.active_context = {
            "channel": None,
            "region": None,
            "city": None,
            "category": None,
            "customer_segment": None,
            "store_id": None,
            "last_primary_metric": "net_sales",
            "last_dimension": None
        }
        self._save_session()

# Global memory instance
conversation_memory = ConversationMemory()
