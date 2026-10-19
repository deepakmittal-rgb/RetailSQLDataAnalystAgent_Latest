-- =====================================================================
-- Retail SQL Data Analyst Agent - MySQL Schema Definition
-- Database: retail_db
-- Dialect: MySQL 8.0+ / MariaDB / Compatible with ANSI SQL
-- Description: Core relational schema for retail analytics
-- =====================================================================

CREATE DATABASE IF NOT EXISTS retail_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE retail_db;

-- ---------------------------------------------------------------------
-- 1. Customers Table
-- Stores demographic, segmentation, and acquisition channel data
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(32) NOT NULL,
    customer_segment ENUM('Regular', 'Budget', 'Premium', 'Wholesale') NOT NULL,
    signup_date DATE NOT NULL,
    preferred_channel VARCHAR(32) NOT NULL,
    city VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id),
    INDEX idx_customers_segment (customer_segment),
    INDEX idx_customers_city (city),
    INDEX idx_customers_preferred_channel (preferred_channel),
    INDEX idx_customers_signup_date (signup_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Customer profiles and behavioral segments';

-- ---------------------------------------------------------------------
-- 2. Products Table
-- Catalog metadata, hierarchies, and baseline catalog pricing
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(32) NOT NULL,
    product_name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL,
    sub_category VARCHAR(64) NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id),
    INDEX idx_products_category (category),
    INDEX idx_products_sub_category (sub_category),
    INDEX idx_products_name (product_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Product catalog with hierarchies and base prices';

-- ---------------------------------------------------------------------
-- 3. Stores Table
-- Physical stores and fulfillment node hierarchies
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stores (
    store_id VARCHAR(32) NOT NULL,
    store_name VARCHAR(128) NOT NULL,
    region VARCHAR(32) NOT NULL,
    city VARCHAR(64) NOT NULL,
    store_type VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (store_id),
    INDEX idx_stores_region (region),
    INDEX idx_stores_city (city),
    INDEX idx_stores_type (store_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Retail store outlets and regional mapping';

-- ---------------------------------------------------------------------
-- 4. Sales Transactions Table
-- Individual order line items across omni-channel fulfillment
-- Net Sales Calculation: units_sold * unit_price * (1 - discount_pct/100)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales_transactions (
    order_id VARCHAR(32) NOT NULL,
    order_date DATE NOT NULL,
    store_id VARCHAR(32) NOT NULL,
    product_id VARCHAR(32) NOT NULL,
    customer_id VARCHAR(32) NOT NULL,
    sales_channel VARCHAR(32) NOT NULL,
    units_sold INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_pct DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    payment_status VARCHAR(32) NOT NULL,
    delivery_status VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id),
    CONSTRAINT fk_sales_store FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE RESTRICT,
    CONSTRAINT fk_sales_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT,
    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT,
    INDEX idx_sales_date (order_date),
    INDEX idx_sales_channel (sales_channel),
    INDEX idx_sales_store (store_id),
    INDEX idx_sales_product (product_id),
    INDEX idx_sales_customer (customer_id),
    INDEX idx_sales_payment_status (payment_status),
    INDEX idx_sales_delivery_status (delivery_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Transaction ledger for omnichannel sales';

-- ---------------------------------------------------------------------
-- 5. Returns Table
-- Post-purchase order returns, timestamps, and customer reasons
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS returns (
    return_id VARCHAR(32) NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    return_date DATE NOT NULL,
    return_reason VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (return_id),
    CONSTRAINT fk_returns_order FOREIGN KEY (order_id) REFERENCES sales_transactions(order_id) ON DELETE RESTRICT,
    INDEX idx_returns_order (order_id),
    INDEX idx_returns_date (return_date),
    INDEX idx_returns_reason (return_reason)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Customer returns and reasons';

-- ---------------------------------------------------------------------
-- 6. Analytics Helper Views (Optional convenience views for analysts)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_sales_extended AS
SELECT
    st.order_id,
    st.order_date,
    st.store_id,
    s.store_name,
    s.region,
    s.city AS store_city,
    s.store_type,
    st.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    st.customer_id,
    c.customer_segment,
    c.city AS customer_city,
    st.sales_channel,
    st.units_sold,
    st.unit_price,
    st.discount_pct,
    ROUND(st.units_sold * st.unit_price * (1.0 - (st.discount_pct / 100.0)), 2) AS net_sales_amount,
    st.payment_status,
    st.delivery_status,
    CASE WHEN r.return_id IS NOT NULL THEN 1 ELSE 0 END AS is_returned,
    r.return_id,
    r.return_date,
    r.return_reason
FROM sales_transactions st
INNER JOIN stores s ON st.store_id = s.store_id
INNER JOIN products p ON st.product_id = p.product_id
INNER JOIN customers c ON st.customer_id = c.customer_id
LEFT JOIN returns r ON st.order_id = r.order_id;
