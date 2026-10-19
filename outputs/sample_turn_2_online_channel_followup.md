# Sample Turn 2: Follow-Up Channel Filtering

**User Question:** *"Now show only online channel."*

### 1. Context Memory Resolution
- **Follow-up Detected:** Yes (`is_followup = True`)
- **Previous Turn Anchor:** Top products by net sales
- **Delta Filter Applied:** `st.sales_channel = 'Online'`
- **Inherited Context:** Preserved grouping by product and net sales calculation

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
WHERE st.sales_channel = 'Online'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY net_sales DESC
LIMIT 10;
```

### 3. Execution Results
| Product ID | Product Name | Category | Units Sold | Net Sales (₹) |
| :--- | :--- | :--- | :--- | :--- |
| `P-003` | Rice 5kg | Groceries | 46 | ₹25,676.14 |
| `P-007` | Detergent | Household | 58 | ₹22,086.65 |
| `P-001` | Tea Premium | Beverages | 46 | ₹16,863.74 |
| `P-009` | Protein Bar | Snacks | 69 | ₹14,087.71 |
| `P-004` | Cooking Oil | Groceries | 35 | ₹6,498.35 |

### 4. Business Summary
- **Top SKU Performance:** **Rice 5kg** maintained its lead in the online channel with **₹25,676.14** in net sales across 46 units.
- **Online Channel Share:** Online orders accounted for ~29.2% of total Rice 5kg revenue.
- *(Filtered by: channel='Online')*
