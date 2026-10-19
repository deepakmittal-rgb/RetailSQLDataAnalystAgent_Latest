# Sample Turn 1: Product Sales Overview

**User Question:** *"What are the top 5 products by net sales?"*

### 1. Safety Validation
- **Status:** PASSED
- **Classification:** Strictly Read-Only SELECT
- **Limit Applied:** 5

### 2. Generated Safe SQL
```sql
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(st.units_sold) AS total_units_sold,
    ROUND(SUM(st.units_sold * st.unit_price * (1.0 - (st.discount_pct / 100.0))), 2) AS net_sales
FROM sales_transactions st
INNER JOIN products p ON st.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY net_sales DESC
LIMIT 5;
```

### 3. Execution Results
| Product ID | Product Name | Category | Units Sold | Net Sales (₹) |
| :--- | :--- | :--- | :--- | :--- |
| `P-003` | Rice 5kg | Groceries | 155 | ₹87,871.80 |
| `P-007` | Detergent | Household | 210 | ₹80,003.49 |
| `P-001` | Tea Premium | Beverages | 183 | ₹67,170.65 |
| `P-009` | Protein Bar | Snacks | 188 | ₹37,483.14 |
| `P-008` | Floor Cleaner | Household | 153 | ₹36,236.35 |

### 4. Business Summary
- **Top SKU Performance:** **Rice 5kg** generated the highest net sales at **₹87,871.80**, contributing 28.5% of the top 5 total revenue.
- **Runner-up:** Detergent followed closely with ₹80,003.49 across 210 units sold.
