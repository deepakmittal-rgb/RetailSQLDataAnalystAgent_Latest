# Retail Analytics Database - Schema Reference & Data Dictionary

This document details the relational data model, table definitions, relationships, data types, business calculation formulas, and standard analysis patterns for the **Retail SQL Data Analyst Agent**.

---

## 1. Relational Entity Relationship Diagram (ERD)

```
       +--------------------+          +--------------------+
       |     customers      |          |      products      |
       +--------------------+          +--------------------+
       | PK customer_id     |          | PK product_id      |
       |    customer_segment|          |    product_name    |
       |    signup_date     |          |    category        |
       |    preferred_chan. |          |    sub_category    |
       |    city            |          |    base_price      |
       +---------+----------+          +---------+----------+
                 |                               |
                 | 1                             | 1
                 |                               |
                 | M                             | M
       +---------+-------------------------------+----------+
       |                 sales_transactions                 |
       +----------------------------------------------------+
       | PK order_id                                        |
       |    order_date                                      |
       | FK store_id ----------------> +--------------------+
       | FK product_id                 |       stores       |
       | FK customer_id                +--------------------+
       |    sales_channel              | PK store_id        |
       |    units_sold                 |    store_name      |
       |    unit_price                 |    region          |
       |    discount_pct               |    city            |
       |    payment_status             |    store_type      |
       |    delivery_status            +--------------------+
       +---------+------------------------------------------+
                 | 1
                 |
                 | 0..1
       +---------+----------+
       |      returns       |
       +--------------------+
       | PK return_id       |
       | FK order_id        |
       |    return_date     |
       |    return_reason   |
       +--------------------+
```

---

## 2. Table Specifications

### 2.1 `customers`
- **Primary Key:** `customer_id` (e.g. `C-0001` to `C-0080`)
- **Row Count:** 80 customer profiles
- **Columns:**
  - `customer_id` (VARCHAR(32)): Unique identifier for the customer
  - `customer_segment` (VARCHAR(32)): Customer demographic tier: `Regular`, `Budget`, `Premium`, `Wholesale`
  - `signup_date` (DATE): Account creation date (`YYYY-MM-DD`)
  - `preferred_channel` (VARCHAR(32)): Channel preference: `Online`, `Mobile App`, `In-store`, `Partner`
  - `city` (VARCHAR(64)): Residential city in India (e.g., Mumbai, Delhi, Bengaluru, Jaipur, etc.)

### 2.2 `products`
- **Primary Key:** `product_id` (e.g. `P-001` to `P-010`)
- **Row Count:** 10 core retail products
- **Columns:**
  - `product_id` (VARCHAR(32)): Unique SKU identifier
  - `product_name` (VARCHAR(128)): Commercial title (e.g. "Tea Premium", "Rice 5kg", "Protein Bar")
  - `category` (VARCHAR(64)): High-level department (`Beverages`, `Groceries`, `Personal Care`, `Household`, `Snacks`)
  - `sub_category` (VARCHAR(64)): Granular classification (`Tea`, `Cold`, `Rice`, `Cooking`, `Herbal`, `Face`, `Detergent`, `Floor`, `Protein`, `Trail`)
  - `base_price` (DECIMAL(10,2)): List retail MSRP in INR (₹)

### 2.3 `stores`
- **Primary Key:** `store_id` (e.g. `ST-001` to `ST-015`)
- **Row Count:** 15 retail store locations
- **Columns:**
  - `store_id` (VARCHAR(32)): Unique store location ID
  - `store_name` (VARCHAR(128)): Facility name (e.g. "Delhi Superstore", "Chennai Mart")
  - `region` (VARCHAR(32)): Geographic division (`North`, `South`, `East`, `West`, `Central`)
  - `city` (VARCHAR(64)): Operating metropolitan area
  - `store_type` (VARCHAR(32)): Format: `Supermarket`, `Convenience`, `Express`

### 2.4 `sales_transactions`
- **Primary Key:** `order_id` (e.g. `O-00001` to `O-00360`)
- **Row Count:** 360 sales transaction records (spanning Jan 2026 – Apr 2026)
- **Foreign Keys:**
  - `store_id` -> `stores.store_id`
  - `product_id` -> `products.product_id`
  - `customer_id` -> `customers.customer_id`
- **Columns:**
  - `order_id` (VARCHAR(32)): Order transaction ID
  - `order_date` (DATE): Transaction timestamp (`2026-01-01` through `2026-04-30`)
  - `store_id` (VARCHAR(32)): Fulfillment store
  - `product_id` (VARCHAR(32)): Purchased SKU
  - `customer_id` (VARCHAR(32)): Purchasing customer
  - `sales_channel` (VARCHAR(32)): Channel where purchase occurred: `Online`, `Mobile App`, `In-store`, `Partner`
  - `units_sold` (INT): Quantity of units purchased (1 to 9)
  - `unit_price` (DECIMAL(10,2)): Transacted item price in INR
  - `discount_pct` (DECIMAL(5,2)): Promotional discount percentage applied (e.g., 0, 5, 10, 15, 20)
  - `payment_status` (VARCHAR(32)): Settlement state: `Paid`, `Pending`
  - `delivery_status` (VARCHAR(32)): Fulfillment state: `Delivered`, `Processing`, `Returned`

### 2.5 `returns`
- **Primary Key:** `return_id` (e.g. `R-0001` to `R-0046`)
- **Row Count:** 46 verified return events
- **Foreign Key:** `order_id` -> `sales_transactions.order_id`
- **Columns:**
  - `return_id` (VARCHAR(32)): Return authorization ID
  - `order_id` (VARCHAR(32)): Matched sales transaction ID
  - `return_date` (DATE): Timestamp return was logged
  - `return_reason` (VARCHAR(128)): Customer cited reason: `Customer Changed Mind`, `Damaged`, `Wrong Item`, `Late Delivery`, `Quality Issue`

---

## 3. Standard Business Metrics & Formulas

| Metric Name | Business Definition | SQL Implementation Formula |
| :--- | :--- | :--- |
| **Gross Sales** | Total transacted value before discounts | `SUM(units_sold * unit_price)` |
| **Net Sales (Revenue)** | Actual realized revenue after discounts | `SUM(units_sold * unit_price * (1.0 - (discount_pct / 100.0)))` |
| **Total Units** | Total item volume moved | `SUM(units_sold)` |
| **Average Order Value (AOV)** | Mean Net Sales per transaction | `SUM(units_sold * unit_price * (1.0 - (discount_pct / 100.0))) / COUNT(DISTINCT order_id)` |
| **Return Rate (%)** | Fraction of orders returned | `COUNT(DISTINCT r.order_id) * 100.0 / COUNT(DISTINCT st.order_id)` |
| **Return Loss (Value)** | Value of goods returned | `SUM(CASE WHEN r.return_id IS NOT NULL THEN units_sold * unit_price * (1.0 - (discount_pct/100.0)) ELSE 0 END)` |
| **Average Discount (%)** | Volume-weighted discount rate | `SUM(units_sold * discount_pct) / SUM(units_sold)` |

---

## 4. Query Guidelines for Agent

1. **Always use Read-Only operations**: Queries must start with `SELECT` or `WITH`. No `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, etc.
2. **Channel Filtering**: When questions ask about channels, filter on `sales_transactions.sales_channel` (`'Online'`, `'Mobile App'`, `'In-store'`, `'Partner'`).
3. **Product & Store Joins**: Always JOIN on matching foreign keys (`st.product_id = p.product_id`, `st.store_id = s.store_id`, `st.customer_id = c.customer_id`).
4. **Returns Joins**: Always use `LEFT JOIN returns r ON st.order_id = r.order_id` to include non-returned orders when aggregating total sales or return rates.
5. **LIMIT Clause**: Enforce a safe maximum row limit (default `LIMIT 100`) on tabular queries.
