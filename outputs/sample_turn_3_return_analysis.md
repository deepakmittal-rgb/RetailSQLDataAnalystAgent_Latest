# Sample Turn 3: Return Reason Root Cause Analysis

**User Question:** *"Which return reason is most common?"*

### 1. Safety Validation
- **Status:** PASSED
- **Classification:** Strictly Read-Only SELECT
- **Limit Applied:** Default safe limit 25

### 2. Generated Safe SQL
```sql
SELECT
    r.return_reason,
    COUNT(r.return_id) AS return_count,
    ROUND(COUNT(r.return_id) * 100.0 / (SELECT COUNT(*) FROM returns), 2) AS pct_of_returns
FROM returns r
GROUP BY r.return_reason
ORDER BY return_count DESC
LIMIT 25;
```

### 3. Execution Results
| Return Reason | Return Count | % of All Returns |
| :--- | :--- | :--- |
| **Wrong Item** | 12 | 26.09% |
| **Late Delivery** | 11 | 23.91% |
| **Customer Changed Mind** | 11 | 23.91% |
| **Quality Issue** | 6 | 13.04% |
| **Damaged** | 6 | 13.04% |

### 4. Business Summary
- **Primary Return Driver:** **Wrong Item** is the leading cause, accounting for **12 returns** (26.09% of all returns), indicating fulfillment picking inaccuracies.
- **Logistics Issues:** 'Late Delivery' accounted for 11 returns (23.91%), suggesting potential regional transit bottlenecks.
