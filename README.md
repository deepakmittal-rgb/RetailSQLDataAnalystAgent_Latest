# Retail SQL Data Analyst Agent (Tiger Analytics)

An enterprise-grade, conversational **Retail SQL Data Analyst Agent** powered by LangGraph / LangChain, Tiger Analytics AI Gateway / Gemini API, conversational context memory, safe read-only SQL execution, and concise business intelligence summaries.

---

## 1. Key Capabilities

1. **Natural Language Question Answering**: Accepts analytical retail questions in plain English (e.g. *"What are the top 5 products by net sales?"*).
2. **Safe Read-Only SQL Generation**: Generates compliant, optimized SQL queries conforming strictly to the Retail MySQL schema and read-only policies.
3. **Conversational Context Memory**: Remembers previous questions, entities, and active filters across multiple turns, enabling seamless follow-up questions such as *"Now show only online channel."*
4. **Strict Security Sandbox**: Multilayer `SafetyValidator` blocks destructive commands (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`), multi-statement injection, comment evasion, and automatically enforces a safe row limit (`LIMIT 100`).
5. **Concise Executive Business Summaries**: Returns tailored summaries highlighting key metrics, leaders, channel share, and actionable takeaways in INR (₹).
6. **Dual Database Engine**: Fully compatible with MySQL 8.0+ production instances and includes a zero-configuration SQLite local database preloaded with the attached retail dataset.

---

## 2. Directory Structure

```
├── data/
│   ├── customers.csv              # 80 customer profiles & demographics
│   ├── products.csv               # 10 core catalog SKUs and list prices
│   ├── stores.csv                 # 15 stores across 5 geographic regions
│   ├── sales_transactions.csv     # 360 omnichannel sales transactions
│   └── returns.csv                # 46 return records & customer reasons
├── database/
│   ├── mysql_schema.sql           # MySQL DDL with PKs, FKs, and views
│   ├── load_data.py               # Data loader & verification script
│   └── schema_reference.md        # Detailed schema reference & data dictionary
├── src/
│   ├── app.py                     # CLI and interactive analyst agent runner
│   ├── config.py                  # Environment & parameter configuration
│   ├── graph.py                   # LangGraph / LangChain state graph workflow
│   ├── memory.py                  # Conversational context memory manager
│   ├── safety.py                  # Read-only SQL safety validator & sanitizer
│   ├── sql_tools.py               # Database execution tools & dialect adaptation
│   └── tiger_gateway_client.py    # Tiger Analytics Gateway & Gemini client
├── tests/
│   ├── test_safety.py             # 12 safety & read-only unit tests
│   ├── test_sql_tools.py          # Database integrity & calculation tests
│   ├── test_memory.py             # Multi-turn context memory tests
│   ├── test_graph.py              # End-to-end analyst pipeline tests
│   └── run_all_tests.py           # Automated test runner with report logging
├── outputs/
│   ├── sample_turn_1_overview.json & .md
│   ├── sample_turn_2_online_channel_followup.json & .md
│   └── sample_turn_3_return_analysis.json & .md
├── evidence/
│   ├── data_load_verification.txt # Data row counts verification log
│   ├── test_execution_log.txt     # Test suite pass/fail report
│   ├── sample_agent_run.txt       # Multi-turn run transcript
│   └── safety_audit_report.md     # OWASP and SQL security audit report
├── requirements.txt               # Required Python packages
├── .env.example                   # Environment variable template
├── READ.md                        # Project documentation
└── README.md                      # Project documentation
```

---

## 3. Data Dictionary & Formula Reference

| Table | Primary Key | Row Count | Description |
| :--- | :--- | :--- | :--- |
| `customers` | `customer_id` | 80 | Customer segments (`Regular`, `Budget`, `Premium`, `Wholesale`), cities, signup dates |
| `products` | `product_id` | 10 | Retail SKUs (`Rice 5kg`, `Tea Premium`, `Detergent`), categories, base prices |
| `stores` | `store_id` | 15 | Store outlets across `North`, `South`, `East`, `West`, `Central` |
| `sales_transactions` | `order_id` | 360 | Omnichannel orders (`Online`, `Mobile App`, `In-store`, `Partner`), units, unit prices, discounts |
| `returns` | `return_id` | 46 | Return items, return dates, reasons (`Wrong Item`, `Late Delivery`, `Damaged`, etc.) |

### Key Business Formulas:
- **Net Sales**: `SUM(units_sold * unit_price * (1.0 - discount_pct / 100.0))`
- **Return Rate**: `COUNT(DISTINCT r.order_id) * 100.0 / COUNT(DISTINCT st.order_id)`
- **Average Order Value (AOV)**: `Net Sales / COUNT(DISTINCT order_id)`

---

## 4. Quick Start & Execution

### Setup Python Environment
```bash
pip install -r requirements.txt
```

### 1. Load Data
```bash
python3 database/load_data.py
```

### 2. Run Test Suite
```bash
python3 tests/run_all_tests.py
```

### 3. Run One-Shot Question
```bash
python3 src/app.py --question "What are the top 5 products by net sales?"
```

### 4. Run Multi-Turn Context Benchmark
Demonstrates the agent answering an initial query and resolving the follow-up *"Now show only online channel."*:
```bash
python3 src/app.py --benchmark
```

### 5. Launch Interactive CLI
```bash
python3 src/app.py --interactive
```

---

## 5. Multi-Turn Conversation Example

```text
User: "What are the top 5 products by net sales?"
Agent:
  - Generates: SELECT p.product_name, SUM(st.units_sold * st.unit_price * (1 - st.discount_pct/100)) ...
  - Executes: Rice 5kg (₹87,871.80), Detergent (₹80,003.49), Tea Premium (₹67,170.65)...
  - Summary: Rice 5kg generated the highest net sales at ₹87,871.80 (28.5% of top 5).

User: "Now show only online channel."
Agent:
  - Memory Context: Recognizes previous query was top products by net sales.
  - Applies Delta Filter: WHERE st.sales_channel = 'Online'
  - Executes: Rice 5kg (₹25,676.14, 46 units), Detergent (₹22,086.65, 58 units)...
  - Summary: Rice 5kg maintained its lead in the online channel with ₹25,676.14. (Filtered by: channel='Online')
```

---

## 6. Safety & Read-Only Guarantee

- **Whitelisted Root Operations**: Only `SELECT`, `WITH`, and `EXPLAIN` are accepted.
- **Strict Blacklist**: Immediate rejection of `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `CREATE`, `REPLACE`, `GRANT`, `REVOKE`, `EXEC`.
- **Injection Defenses**: Stacked queries (semicolon delimited) and comment masking (`--`, `/* */`, `#`) are prohibited.
- **Row Limits**: Queries without limits receive an automatic `LIMIT 25`; limits above 100 are clamped to `LIMIT 100`.
