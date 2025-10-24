"""
Enhanced training data for Vanna AI with complete standard schema coverage
This ensures AI can handle all queries across the 7 standard POS tables
"""
from typing import List, Dict


# DDL for all 7 standard tables with proper relationships
STANDARD_SCHEMA_DDL = """
-- Customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Technicians table
CREATE TABLE technicians (
    technician_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    specialties TEXT,
    hire_date DATE,
    is_active BOOLEAN DEFAULT true,
    commission_rate DECIMAL(5,2) DEFAULT 0.00
);

-- Services table
CREATE TABLE services (
    service_id SERIAL PRIMARY KEY,
    service_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    base_price DECIMAL(10,2) NOT NULL,
    duration_minutes INTEGER,
    description TEXT,
    is_active BOOLEAN DEFAULT true
);

-- Bookings table
CREATE TABLE bookings (
    booking_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    technician_id INTEGER REFERENCES technicians(technician_id),
    booking_date DATE NOT NULL,
    booking_time TIME,
    status VARCHAR(50) DEFAULT 'scheduled',
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    tip_amount DECIMAL(10,2) DEFAULT 0.00,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Booking services junction table
CREATE TABLE booking_services (
    booking_service_id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(booking_id),
    service_id INTEGER REFERENCES services(service_id),
    price DECIMAL(10,2) NOT NULL
);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    unit_price DECIMAL(10,2) NOT NULL,
    current_stock INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 0,
    supplier VARCHAR(255)
);

-- Product sales table
CREATE TABLE product_sales (
    sale_id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(booking_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_bookings_customer ON bookings(customer_id);
CREATE INDEX idx_bookings_technician ON bookings(technician_id);
CREATE INDEX idx_bookings_date ON bookings(booking_date);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_booking_services_booking ON booking_services(booking_id);
CREATE INDEX idx_booking_services_service ON booking_services(service_id);
CREATE INDEX idx_product_sales_product ON product_sales(product_id);
"""


# Comprehensive question-SQL pairs covering all tables and common queries
TRAINING_QUESTIONS: List[Dict[str, str]] = [
    # ============================================
    # CUSTOMER QUERIES
    # ============================================
    {
        "question": "Who are our top 10 customers by total spending?",
        "sql": """
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.phone,
    c.email,
    COUNT(b.booking_id) AS total_visits,
    SUM(b.total_amount + b.tip_amount) AS total_spent
FROM customers c
JOIN bookings b ON c.customer_id = b.customer_id
WHERE b.status = 'completed'
GROUP BY c.customer_id, c.first_name, c.last_name, c.phone, c.email
ORDER BY total_spent DESC
LIMIT 10;
"""
    },
    {
        "question": "How many new customers did we get this month?",
        "sql": """
SELECT COUNT(*) AS new_customers
FROM customers
WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE);
"""
    },
    {
        "question": "Which customers haven't visited in the last 60 days?",
        "sql": """
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.phone,
    c.email,
    MAX(b.booking_date) AS last_visit_date,
    CURRENT_DATE - MAX(b.booking_date) AS days_since_visit
FROM customers c
JOIN bookings b ON c.customer_id = b.customer_id
WHERE b.status = 'completed'
GROUP BY c.customer_id, c.first_name, c.last_name, c.phone, c.email
HAVING CURRENT_DATE - MAX(b.booking_date) > 60
ORDER BY days_since_visit DESC;
"""
    },
    {
        "question": "What is the average customer lifetime value?",
        "sql": """
SELECT 
    AVG(customer_total) AS avg_lifetime_value,
    MIN(customer_total) AS min_lifetime_value,
    MAX(customer_total) AS max_lifetime_value
FROM (
    SELECT 
        customer_id,
        SUM(total_amount + tip_amount) AS customer_total
    FROM bookings
    WHERE status = 'completed'
    GROUP BY customer_id
) AS customer_values;
"""
    },
    
    # ============================================
    # BOOKING/APPOINTMENT QUERIES
    # ============================================
    {
        "question": "How many bookings do we have scheduled for tomorrow?",
        "sql": """
SELECT COUNT(*) AS bookings_tomorrow
FROM bookings
WHERE booking_date = CURRENT_DATE + INTERVAL '1 day'
AND status = 'scheduled';
"""
    },
    {
        "question": "What's our booking completion rate this month?",
        "sql": """
SELECT 
    COUNT(*) AS total_bookings,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_bookings,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 2) AS completion_rate_percent
FROM bookings
WHERE DATE_TRUNC('month', booking_date) = DATE_TRUNC('month', CURRENT_DATE);
"""
    },
    {
        "question": "Show me daily revenue for the last 30 days",
        "sql": """
SELECT 
    booking_date,
    COUNT(*) AS total_bookings,
    SUM(total_amount) AS daily_revenue,
    SUM(tip_amount) AS total_tips,
    SUM(total_amount + tip_amount) AS total_income
FROM bookings
WHERE booking_date >= CURRENT_DATE - INTERVAL '30 days'
AND status = 'completed'
GROUP BY booking_date
ORDER BY booking_date DESC;
"""
    },
    {
        "question": "What are the busiest hours of the day?",
        "sql": """
SELECT 
    EXTRACT(HOUR FROM booking_time) AS hour_of_day,
    COUNT(*) AS booking_count
FROM bookings
WHERE booking_date >= CURRENT_DATE - INTERVAL '90 days'
AND status = 'completed'
GROUP BY EXTRACT(HOUR FROM booking_time)
ORDER BY booking_count DESC;
"""
    },
    {
        "question": "How many no-shows did we have this week?",
        "sql": """
SELECT 
    COUNT(*) AS no_show_count,
    SUM(total_amount) AS lost_revenue
FROM bookings
WHERE booking_date >= DATE_TRUNC('week', CURRENT_DATE)
AND status = 'no_show';
"""
    },
    
    # ============================================
    # SERVICE QUERIES
    # ============================================
    {
        "question": "What are our most popular services?",
        "sql": """
SELECT 
    s.service_name,
    s.category,
    s.base_price,
    COUNT(bs.booking_service_id) AS times_booked,
    SUM(bs.price) AS total_revenue
FROM services s
JOIN booking_services bs ON s.service_id = bs.service_id
JOIN bookings b ON bs.booking_id = b.booking_id
WHERE b.status = 'completed'
AND b.booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY s.service_id, s.service_name, s.category, s.base_price
ORDER BY times_booked DESC;
"""
    },
    {
        "question": "Which service category generates the most revenue?",
        "sql": """
SELECT 
    s.category,
    COUNT(bs.booking_service_id) AS service_count,
    SUM(bs.price) AS total_revenue,
    AVG(bs.price) AS avg_price
FROM services s
JOIN booking_services bs ON s.service_id = bs.service_id
JOIN bookings b ON bs.booking_id = b.booking_id
WHERE b.status = 'completed'
GROUP BY s.category
ORDER BY total_revenue DESC;
"""
    },
    {
        "question": "What's the average service price by category?",
        "sql": """
SELECT 
    category,
    COUNT(*) AS service_count,
    AVG(base_price) AS avg_price,
    MIN(base_price) AS min_price,
    MAX(base_price) AS max_price
FROM services
WHERE is_active = true
GROUP BY category
ORDER BY avg_price DESC;
"""
    },
    {
        "question": "Which services are most commonly booked together?",
        "sql": """
SELECT 
    s1.service_name AS service_1,
    s2.service_name AS service_2,
    COUNT(*) AS times_together
FROM booking_services bs1
JOIN booking_services bs2 ON bs1.booking_id = bs2.booking_id AND bs1.service_id < bs2.service_id
JOIN services s1 ON bs1.service_id = s1.service_id
JOIN services s2 ON bs2.service_id = s2.service_id
JOIN bookings b ON bs1.booking_id = b.booking_id
WHERE b.status = 'completed'
AND b.booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY s1.service_name, s2.service_name
ORDER BY times_together DESC
LIMIT 10;
"""
    },
    
    # ============================================
    # TECHNICIAN QUERIES
    # ============================================
    {
        "question": "Which technician has the most bookings this month?",
        "sql": """
SELECT 
    t.technician_id,
    t.first_name || ' ' || t.last_name AS technician_name,
    COUNT(b.booking_id) AS total_bookings,
    SUM(b.total_amount) AS total_revenue,
    AVG(b.total_amount) AS avg_booking_value
FROM technicians t
JOIN bookings b ON t.technician_id = b.technician_id
WHERE DATE_TRUNC('month', b.booking_date) = DATE_TRUNC('month', CURRENT_DATE)
AND b.status = 'completed'
GROUP BY t.technician_id, t.first_name, t.last_name
ORDER BY total_bookings DESC;
"""
    },
    {
        "question": "How much commission does each technician earn?",
        "sql": """
SELECT 
    t.technician_id,
    t.first_name || ' ' || t.last_name AS technician_name,
    t.commission_rate,
    COUNT(b.booking_id) AS completed_bookings,
    SUM(b.total_amount) AS total_sales,
    ROUND(SUM(b.total_amount * t.commission_rate / 100), 2) AS commission_earned
FROM technicians t
JOIN bookings b ON t.technician_id = b.technician_id
WHERE b.status = 'completed'
AND DATE_TRUNC('month', b.booking_date) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY t.technician_id, t.first_name, t.last_name, t.commission_rate
ORDER BY commission_earned DESC;
"""
    },
    {
        "question": "Which technician has the highest customer satisfaction based on tips?",
        "sql": """
SELECT 
    t.technician_id,
    t.first_name || ' ' || t.last_name AS technician_name,
    COUNT(b.booking_id) AS total_bookings,
    SUM(b.tip_amount) AS total_tips,
    AVG(b.tip_amount) AS avg_tip,
    ROUND(100.0 * SUM(b.tip_amount) / SUM(b.total_amount), 2) AS tip_percentage
FROM technicians t
JOIN bookings b ON t.technician_id = b.technician_id
WHERE b.status = 'completed'
AND b.booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY t.technician_id, t.first_name, t.last_name
HAVING COUNT(b.booking_id) >= 10
ORDER BY tip_percentage DESC;
"""
    },
    {
        "question": "Show technician utilization for this week",
        "sql": """
SELECT 
    t.technician_id,
    t.first_name || ' ' || t.last_name AS technician_name,
    COUNT(b.booking_id) AS bookings_this_week,
    SUM(s.duration_minutes) AS total_minutes_booked,
    ROUND(SUM(s.duration_minutes) / 60.0, 1) AS hours_booked
FROM technicians t
LEFT JOIN bookings b ON t.technician_id = b.technician_id 
    AND b.booking_date >= DATE_TRUNC('week', CURRENT_DATE)
    AND b.status IN ('scheduled', 'completed')
LEFT JOIN booking_services bs ON b.booking_id = bs.booking_id
LEFT JOIN services s ON bs.service_id = s.service_id
WHERE t.is_active = true
GROUP BY t.technician_id, t.first_name, t.last_name
ORDER BY hours_booked DESC;
"""
    },
    
    # ============================================
    # PRODUCT/INVENTORY QUERIES
    # ============================================
    {
        "question": "Which products are running low on stock?",
        "sql": """
SELECT 
    product_id,
    product_name,
    category,
    current_stock,
    min_stock_level,
    (min_stock_level - current_stock) AS units_to_reorder
FROM products
WHERE current_stock < min_stock_level
ORDER BY (min_stock_level - current_stock) DESC;
"""
    },
    {
        "question": "What are our best-selling products?",
        "sql": """
SELECT 
    p.product_name,
    p.category,
    p.unit_price,
    SUM(ps.quantity) AS total_units_sold,
    SUM(ps.total_price) AS total_revenue,
    COUNT(DISTINCT ps.sale_id) AS number_of_sales
FROM products p
JOIN product_sales ps ON p.product_id = ps.product_id
WHERE ps.sale_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY p.product_id, p.product_name, p.category, p.unit_price
ORDER BY total_revenue DESC
LIMIT 10;
"""
    },
    {
        "question": "How much revenue do we make from retail products vs services?",
        "sql": """
SELECT 
    'Services' AS revenue_type,
    SUM(bs.price) AS total_revenue
FROM booking_services bs
JOIN bookings b ON bs.booking_id = b.booking_id
WHERE b.status = 'completed'
AND b.booking_date >= CURRENT_DATE - INTERVAL '30 days'
UNION ALL
SELECT 
    'Products' AS revenue_type,
    SUM(total_price) AS total_revenue
FROM product_sales
WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days';
"""
    },
    {
        "question": "What is the product usage rate and when will we run out?",
        "sql": """
SELECT 
    p.product_id,
    p.product_name,
    p.current_stock,
    COUNT(ps.sale_id) AS sales_last_30_days,
    ROUND(COUNT(ps.sale_id)::numeric / 30, 2) AS avg_daily_usage,
    CASE 
        WHEN COUNT(ps.sale_id) > 0 THEN 
            ROUND(p.current_stock / (COUNT(ps.sale_id)::numeric / 30), 1)
        ELSE NULL
    END AS days_until_stockout,
    p.supplier
FROM products p
LEFT JOIN product_sales ps ON p.product_id = ps.product_id
    AND ps.sale_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY p.product_id, p.product_name, p.current_stock, p.supplier
HAVING p.current_stock > 0
ORDER BY days_until_stockout NULLS LAST;
"""
    },
    {
        "question": "Show seasonal product demand patterns",
        "sql": """
SELECT 
    p.product_name,
    p.category,
    EXTRACT(MONTH FROM ps.sale_date) AS month,
    TO_CHAR(TO_DATE(EXTRACT(MONTH FROM ps.sale_date)::text, 'MM'), 'Month') AS month_name,
    SUM(ps.quantity) AS total_sold,
    SUM(ps.total_price) AS total_revenue
FROM products p
JOIN product_sales ps ON p.product_id = ps.product_id
WHERE ps.sale_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY p.product_id, p.product_name, p.category, EXTRACT(MONTH FROM ps.sale_date)
ORDER BY p.product_name, month;
"""
    },
    {
        "question": "Which supplier products have the best margins?",
        "sql": """
SELECT 
    p.supplier,
    p.product_name,
    p.unit_price,
    AVG(ps.unit_price) AS avg_selling_price,
    AVG(ps.unit_price) - p.unit_price AS avg_margin,
    ROUND(((AVG(ps.unit_price) - p.unit_price) / p.unit_price * 100), 2) AS margin_percent,
    SUM(ps.quantity) AS units_sold
FROM products p
JOIN product_sales ps ON p.product_id = ps.product_id
WHERE ps.sale_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY p.product_id, p.supplier, p.product_name, p.unit_price
HAVING SUM(ps.quantity) >= 5
ORDER BY margin_percent DESC;
"""
    },
    
    # ============================================
    # FINANCIAL/REVENUE QUERIES
    # ============================================
    {
        "question": "What's our total revenue for this month?",
        "sql": """
SELECT 
    SUM(b.total_amount) AS service_revenue,
    SUM(b.tip_amount) AS tip_revenue,
    SUM(ps.total_price) AS product_revenue,
    SUM(b.total_amount + b.tip_amount) + COALESCE(SUM(ps.total_price), 0) AS total_revenue
FROM bookings b
LEFT JOIN product_sales ps ON b.booking_id = ps.booking_id
WHERE DATE_TRUNC('month', b.booking_date) = DATE_TRUNC('month', CURRENT_DATE)
AND b.status = 'completed';
"""
    },
    {
        "question": "Compare revenue this month vs last month",
        "sql": """
SELECT 
    'This Month' AS period,
    SUM(total_amount + tip_amount) AS total_revenue,
    COUNT(*) AS booking_count,
    AVG(total_amount + tip_amount) AS avg_booking_value
FROM bookings
WHERE DATE_TRUNC('month', booking_date) = DATE_TRUNC('month', CURRENT_DATE)
AND status = 'completed'
UNION ALL
SELECT 
    'Last Month' AS period,
    SUM(total_amount + tip_amount) AS total_revenue,
    COUNT(*) AS booking_count,
    AVG(total_amount + tip_amount) AS avg_booking_value
FROM bookings
WHERE DATE_TRUNC('month', booking_date) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
AND status = 'completed';
"""
    },
    {
        "question": "What's our revenue by payment method?",
        "sql": """
SELECT 
    payment_method,
    COUNT(*) AS transaction_count,
    SUM(total_amount + tip_amount) AS total_revenue,
    AVG(total_amount + tip_amount) AS avg_transaction_value
FROM bookings
WHERE status = 'completed'
AND booking_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY payment_method
ORDER BY total_revenue DESC;
"""
    },
    {
        "question": "What's our average booking value by day of week?",
        "sql": """
SELECT 
    TO_CHAR(booking_date, 'Day') AS day_of_week,
    EXTRACT(DOW FROM booking_date) AS day_number,
    COUNT(*) AS booking_count,
    AVG(total_amount + tip_amount) AS avg_booking_value,
    SUM(total_amount + tip_amount) AS total_revenue
FROM bookings
WHERE status = 'completed'
AND booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY TO_CHAR(booking_date, 'Day'), EXTRACT(DOW FROM booking_date)
ORDER BY day_number;
"""
    },
    
    # ============================================
    # PAYMENTS & PRICING QUERIES
    # ============================================
    {
        "question": "What is our revenue breakdown by payment method?",
        "sql": """
SELECT 
    payment_method,
    COUNT(*) AS transaction_count,
    SUM(total_amount + tip_amount) AS total_revenue,
    AVG(total_amount + tip_amount) AS avg_transaction_value,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage_of_transactions
FROM bookings
WHERE status = 'completed'
AND booking_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY payment_method
ORDER BY total_revenue DESC;
"""
    },
    {
        "question": "Which customers use which payment methods most frequently?",
        "sql": """
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    b.payment_method,
    COUNT(*) AS times_used,
    SUM(b.total_amount + b.tip_amount) AS total_spent
FROM customers c
JOIN bookings b ON c.customer_id = b.customer_id
WHERE b.status = 'completed'
AND b.booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY c.customer_id, c.first_name, c.last_name, b.payment_method
ORDER BY c.customer_id, times_used DESC;
"""
    },
    {
        "question": "Show pricing tier analysis for our services",
        "sql": """
SELECT 
    s.category,
    COUNT(*) AS service_count,
    MIN(s.base_price) AS min_price,
    AVG(s.base_price) AS avg_price,
    MAX(s.base_price) AS max_price,
    CASE 
        WHEN s.base_price < 30 THEN 'Basic'
        WHEN s.base_price BETWEEN 30 AND 60 THEN 'Standard'
        WHEN s.base_price BETWEEN 60 AND 100 THEN 'Premium'
        ELSE 'VIP'
    END AS price_tier
FROM services s
WHERE s.is_active = true
GROUP BY s.category, 
    CASE 
        WHEN s.base_price < 30 THEN 'Basic'
        WHEN s.base_price BETWEEN 30 AND 60 THEN 'Standard'
        WHEN s.base_price BETWEEN 60 AND 100 THEN 'Premium'
        ELSE 'VIP'
    END
ORDER BY s.category, avg_price;
"""
    },
    {
        "question": "How much discount are we giving out and to whom?",
        "sql": """
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(*) AS bookings_with_discount,
    SUM(b.discount_amount) AS total_discounts_given,
    AVG(b.discount_amount) AS avg_discount,
    SUM(b.total_amount) AS revenue_after_discount,
    ROUND(100.0 * SUM(b.discount_amount) / (SUM(b.total_amount) + SUM(b.discount_amount)), 2) AS discount_percentage
FROM customers c
JOIN bookings b ON c.customer_id = b.customer_id
WHERE b.status = 'completed'
AND b.discount_amount > 0
AND b.booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_discounts_given DESC
LIMIT 20;
"""
    },
    {
        "question": "What is the average transaction value by day of week?",
        "sql": """
SELECT 
    TO_CHAR(booking_date, 'Day') AS day_of_week,
    EXTRACT(DOW FROM booking_date) AS day_number,
    COUNT(*) AS booking_count,
    AVG(total_amount + tip_amount) AS avg_transaction_value,
    SUM(total_amount + tip_amount) AS total_revenue,
    AVG(discount_amount) AS avg_discount_given
FROM bookings
WHERE status = 'completed'
AND booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY TO_CHAR(booking_date, 'Day'), EXTRACT(DOW FROM booking_date)
ORDER BY day_number;
"""
    },
    
    # ============================================
    # MARKETING & LOYALTY QUERIES
    # ============================================
    {
        "question": "Which customers have the most diverse service preferences?",
        "sql": """
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(DISTINCT s.service_id) AS different_services_tried,
    STRING_AGG(DISTINCT s.service_name, ', ' ORDER BY s.service_name) AS services_list,
    COUNT(b.booking_id) AS total_visits,
    SUM(b.total_amount + b.tip_amount) AS total_spent
FROM customers c
JOIN bookings b ON c.customer_id = b.customer_id
JOIN booking_services bs ON b.booking_id = bs.booking_id
JOIN services s ON bs.service_id = s.service_id
WHERE b.status = 'completed'
GROUP BY c.customer_id, c.first_name, c.last_name
HAVING COUNT(DISTINCT s.service_id) >= 3
ORDER BY different_services_tried DESC, total_spent DESC;
"""
    },
    {
        "question": "Show customer segmentation by visit frequency and spending",
        "sql": """
WITH customer_metrics AS (
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        COUNT(b.booking_id) AS total_visits,
        SUM(b.total_amount + b.tip_amount) AS total_spent,
        MAX(b.booking_date) AS last_visit,
        MIN(b.booking_date) AS first_visit
    FROM customers c
    JOIN bookings b ON c.customer_id = b.customer_id
    WHERE b.status = 'completed'
    GROUP BY c.customer_id, c.first_name, c.last_name
)
SELECT 
    customer_name,
    total_visits,
    total_spent,
    last_visit,
    CASE 
        WHEN total_visits >= 12 AND total_spent >= 1000 THEN 'VIP'
        WHEN total_visits >= 6 AND total_spent >= 500 THEN 'Loyal'
        WHEN total_visits >= 3 THEN 'Regular'
        ELSE 'New'
    END AS customer_segment,
    CURRENT_DATE - last_visit AS days_since_last_visit
FROM customer_metrics
ORDER BY total_spent DESC;
"""
    },
    {
        "question": "Which customers are most likely to respond to promotions?",
        "sql": """
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    c.phone,
    COUNT(b.booking_id) AS total_bookings,
    COUNT(CASE WHEN b.discount_amount > 0 THEN 1 END) AS bookings_with_discounts,
    ROUND(100.0 * COUNT(CASE WHEN b.discount_amount > 0 THEN 1 END) / COUNT(b.booking_id), 2) AS discount_usage_rate,
    MAX(b.booking_date) AS last_visit,
    CURRENT_DATE - MAX(b.booking_date) AS days_since_last_visit
FROM customers c
JOIN bookings b ON c.customer_id = b.customer_id
WHERE b.status = 'completed'
GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.phone
HAVING COUNT(b.booking_id) >= 2
ORDER BY discount_usage_rate DESC, days_since_last_visit DESC
LIMIT 50;
"""
    },
    {
        "question": "What are the most effective service combinations for upselling?",
        "sql": """
SELECT 
    s1.service_name AS primary_service,
    s2.service_name AS additional_service,
    COUNT(*) AS times_booked_together,
    AVG(b.total_amount) AS avg_booking_value,
    SUM(bs1.price + bs2.price) AS total_combined_revenue
FROM booking_services bs1
JOIN booking_services bs2 ON bs1.booking_id = bs2.booking_id 
    AND bs1.service_id < bs2.service_id
JOIN services s1 ON bs1.service_id = s1.service_id
JOIN services s2 ON bs2.service_id = s2.service_id
JOIN bookings b ON bs1.booking_id = b.booking_id
WHERE b.status = 'completed'
AND b.booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY s1.service_name, s2.service_name
HAVING COUNT(*) >= 5
ORDER BY times_booked_together DESC
LIMIT 15;
"""
    },
    {
        "question": "Calculate customer purchase history and lifetime value trends",
        "sql": """
WITH monthly_spending AS (
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        DATE_TRUNC('month', b.booking_date) AS month,
        SUM(b.total_amount + b.tip_amount) AS monthly_spend,
        COUNT(b.booking_id) AS monthly_visits
    FROM customers c
    JOIN bookings b ON c.customer_id = b.customer_id
    WHERE b.status = 'completed'
    AND b.booking_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY c.customer_id, c.first_name, c.last_name, DATE_TRUNC('month', b.booking_date)
)
SELECT 
    customer_name,
    COUNT(DISTINCT month) AS active_months,
    SUM(monthly_spend) AS total_lifetime_value,
    AVG(monthly_spend) AS avg_monthly_spend,
    SUM(monthly_visits) AS total_visits,
    MAX(month) AS last_active_month
FROM monthly_spending
GROUP BY customer_id, customer_name
ORDER BY total_lifetime_value DESC
LIMIT 30;
"""
    },
    
    # ============================================
    # BUSINESS OPERATIONS QUERIES
    # ============================================
    {
        "question": "Show technician schedule utilization and performance",
        "sql": """
SELECT 
    t.technician_id,
    t.first_name || ' ' || t.last_name AS technician_name,
    COUNT(b.booking_id) AS total_bookings,
    SUM(s.duration_minutes) AS total_minutes_booked,
    ROUND(SUM(s.duration_minutes) / 60.0, 1) AS hours_worked,
    COUNT(CASE WHEN b.status = 'completed' THEN 1 END) AS completed_bookings,
    COUNT(CASE WHEN b.status = 'cancelled' THEN 1 END) AS cancelled_bookings,
    COUNT(CASE WHEN b.status = 'no_show' THEN 1 END) AS no_shows,
    ROUND(100.0 * COUNT(CASE WHEN b.status = 'completed' THEN 1 END) / COUNT(b.booking_id), 2) AS completion_rate,
    SUM(b.total_amount) AS revenue_generated,
    AVG(b.tip_amount) AS avg_tip
FROM technicians t
LEFT JOIN bookings b ON t.technician_id = b.technician_id
    AND b.booking_date >= DATE_TRUNC('month', CURRENT_DATE)
LEFT JOIN booking_services bs ON b.booking_id = bs.booking_id
LEFT JOIN services s ON bs.service_id = s.service_id
WHERE t.is_active = true
GROUP BY t.technician_id, t.first_name, t.last_name
ORDER BY revenue_generated DESC;
"""
    },
    {
        "question": "What are the peak booking patterns by day and hour?",
        "sql": """
SELECT 
    TO_CHAR(booking_date, 'Day') AS day_of_week,
    EXTRACT(DOW FROM booking_date) AS day_number,
    EXTRACT(HOUR FROM booking_time) AS hour_of_day,
    COUNT(*) AS booking_count,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) AS completed_count,
    ROUND(AVG(total_amount), 2) AS avg_revenue_per_booking
FROM bookings
WHERE booking_date >= CURRENT_DATE - INTERVAL '60 days'
AND booking_time IS NOT NULL
GROUP BY TO_CHAR(booking_date, 'Day'), EXTRACT(DOW FROM booking_date), EXTRACT(HOUR FROM booking_time)
ORDER BY day_number, hour_of_day;
"""
    },
    {
        "question": "Analyze cancellation patterns and reasons",
        "sql": """
SELECT 
    TO_CHAR(booking_date, 'Day') AS day_of_week,
    EXTRACT(HOUR FROM booking_time) AS booking_hour,
    status,
    COUNT(*) AS count,
    AVG(total_amount) AS avg_lost_revenue,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY TO_CHAR(booking_date, 'Day')) AS percentage
FROM bookings
WHERE status IN ('cancelled', 'no_show')
AND booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY TO_CHAR(booking_date, 'Day'), EXTRACT(HOUR FROM booking_time), status
ORDER BY TO_CHAR(booking_date, 'Day'), booking_hour;
"""
    },
    {
        "question": "Show staff commission breakdown and performance metrics",
        "sql": """
SELECT 
    t.technician_id,
    t.first_name || ' ' || t.last_name AS technician_name,
    t.commission_rate,
    COUNT(b.booking_id) AS services_completed,
    SUM(b.total_amount) AS total_service_revenue,
    ROUND(SUM(b.total_amount * t.commission_rate / 100), 2) AS commission_earned,
    SUM(b.tip_amount) AS total_tips,
    ROUND(SUM(b.total_amount * t.commission_rate / 100) + SUM(b.tip_amount), 2) AS total_earnings,
    ROUND(AVG(b.tip_amount), 2) AS avg_tip_per_service,
    ROUND(100.0 * COUNT(CASE WHEN b.status = 'completed' THEN 1 END) / 
        NULLIF(COUNT(CASE WHEN b.status IN ('completed', 'no_show', 'cancelled') THEN 1 END), 0), 2) AS completion_rate
FROM technicians t
JOIN bookings b ON t.technician_id = b.technician_id
WHERE b.booking_date >= DATE_TRUNC('month', CURRENT_DATE)
AND b.status = 'completed'
GROUP BY t.technician_id, t.first_name, t.last_name, t.commission_rate
ORDER BY total_earnings DESC;
"""
    },
    {
        "question": "Identify appointment gaps and scheduling opportunities",
        "sql": """
WITH hourly_bookings AS (
    SELECT 
        booking_date,
        EXTRACT(HOUR FROM booking_time) AS hour,
        COUNT(*) AS bookings
    FROM bookings
    WHERE booking_date >= CURRENT_DATE - INTERVAL '30 days'
    AND booking_time IS NOT NULL
    AND status IN ('scheduled', 'completed')
    GROUP BY booking_date, EXTRACT(HOUR FROM booking_time)
),
avg_by_hour AS (
    SELECT 
        hour,
        AVG(bookings) AS avg_bookings,
        MAX(bookings) AS max_bookings
    FROM hourly_bookings
    GROUP BY hour
)
SELECT 
    hour AS hour_of_day,
    ROUND(avg_bookings, 1) AS avg_bookings,
    max_bookings,
    CASE 
        WHEN avg_bookings < 2 THEN 'Low Utilization - Marketing Opportunity'
        WHEN avg_bookings BETWEEN 2 AND 4 THEN 'Moderate - Room for Growth'
        WHEN avg_bookings > 4 THEN 'High Demand - Ensure Adequate Staffing'
    END AS recommendation
FROM avg_by_hour
ORDER BY hour;
"""
    },
    
    # ============================================
    # CLIENT INTERACTION & PREFERENCES QUERIES
    # ============================================
    {
        "question": "Show customer service preferences and notes history",
        "sql": """
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.notes AS customer_notes,
    STRING_AGG(DISTINCT s.service_name, ', ' ORDER BY s.service_name) AS preferred_services,
    COUNT(DISTINCT s.category) AS service_categories_used,
    STRING_AGG(DISTINCT s.category, ', ') AS categories,
    MAX(b.booking_date) AS last_visit,
    COUNT(b.booking_id) AS total_visits
FROM customers c
JOIN bookings b ON c.customer_id = b.customer_id
JOIN booking_services bs ON b.booking_id = bs.booking_id
JOIN services s ON bs.service_id = s.service_id
WHERE b.status = 'completed'
GROUP BY c.customer_id, c.first_name, c.last_name, c.notes
ORDER BY total_visits DESC
LIMIT 50;
"""
    },
    {
        "question": "Which customers always book with the same technician?",
        "sql": """
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    t.first_name || ' ' || t.last_name AS preferred_technician,
    COUNT(b.booking_id) AS bookings_together,
    MAX(b.booking_date) AS last_booking,
    ROUND(100.0 * COUNT(CASE WHEN b.technician_id = t.technician_id THEN 1 END) / 
        COUNT(*), 2) AS loyalty_percentage
FROM customers c
JOIN bookings b ON c.customer_id = b.customer_id
JOIN technicians t ON b.technician_id = t.technician_id
WHERE b.status = 'completed'
GROUP BY c.customer_id, c.first_name, c.last_name, t.technician_id, t.first_name, t.last_name
HAVING COUNT(b.booking_id) >= 3
AND COUNT(CASE WHEN b.technician_id = t.technician_id THEN 1 END) = COUNT(*)
ORDER BY bookings_together DESC;
"""
    },
    {
        "question": "Analyze repeat customer behavior and visit patterns",
        "sql": """
WITH customer_visits AS (
    SELECT 
        customer_id,
        booking_date,
        LAG(booking_date) OVER (PARTITION BY customer_id ORDER BY booking_date) AS previous_visit,
        booking_date - LAG(booking_date) OVER (PARTITION BY customer_id ORDER BY booking_date) AS days_between_visits
    FROM bookings
    WHERE status = 'completed'
)
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(cv.booking_date) AS total_visits,
    ROUND(AVG(cv.days_between_visits), 1) AS avg_days_between_visits,
    MIN(cv.days_between_visits) AS min_days_between,
    MAX(cv.days_between_visits) AS max_days_between,
    MAX(cv.booking_date) AS last_visit,
    CURRENT_DATE - MAX(cv.booking_date) AS days_since_last_visit,
    CASE 
        WHEN CURRENT_DATE - MAX(cv.booking_date) > AVG(cv.days_between_visits) * 1.5 THEN 'Overdue for Visit'
        WHEN CURRENT_DATE - MAX(cv.booking_date) < AVG(cv.days_between_visits) * 0.5 THEN 'Recently Visited'
        ELSE 'On Schedule'
    END AS visit_status
FROM customers c
JOIN customer_visits cv ON c.customer_id = cv.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
HAVING COUNT(cv.booking_date) >= 3
ORDER BY days_since_last_visit DESC;
"""
    },
    
    # ============================================
    # COMPLEX ANALYTICS QUERIES
    # ============================================
    {
        "question": "Show me customer retention rate by cohort",
        "sql": """
WITH first_visit AS (
    SELECT 
        customer_id,
        DATE_TRUNC('month', MIN(booking_date)) AS cohort_month
    FROM bookings
    WHERE status = 'completed'
    GROUP BY customer_id
),
visits_by_month AS (
    SELECT 
        fv.cohort_month,
        DATE_TRUNC('month', b.booking_date) AS visit_month,
        COUNT(DISTINCT b.customer_id) AS returning_customers
    FROM first_visit fv
    JOIN bookings b ON fv.customer_id = b.customer_id
    WHERE b.status = 'completed'
    GROUP BY fv.cohort_month, DATE_TRUNC('month', b.booking_date)
)
SELECT 
    cohort_month,
    visit_month,
    returning_customers,
    (EXTRACT(YEAR FROM visit_month) - EXTRACT(YEAR FROM cohort_month)) * 12 +
    (EXTRACT(MONTH FROM visit_month) - EXTRACT(MONTH FROM cohort_month)) AS months_since_first_visit
FROM visits_by_month
WHERE cohort_month >= CURRENT_DATE - INTERVAL '6 months'
ORDER BY cohort_month, visit_month;
"""
    },
    {
        "question": "Which customers have increased their spending over time?",
        "sql": """
WITH customer_spending AS (
    SELECT 
        customer_id,
        DATE_TRUNC('quarter', booking_date) AS quarter,
        SUM(total_amount + tip_amount) AS quarterly_spend
    FROM bookings
    WHERE status = 'completed'
    GROUP BY customer_id, DATE_TRUNC('quarter', booking_date)
),
spending_comparison AS (
    SELECT 
        cs1.customer_id,
        cs1.quarter AS recent_quarter,
        cs1.quarterly_spend AS recent_spend,
        cs2.quarter AS previous_quarter,
        cs2.quarterly_spend AS previous_spend,
        ROUND(((cs1.quarterly_spend - cs2.quarterly_spend) / cs2.quarterly_spend * 100), 2) AS growth_percent
    FROM customer_spending cs1
    JOIN customer_spending cs2 
        ON cs1.customer_id = cs2.customer_id 
        AND cs1.quarter = cs2.quarter + INTERVAL '3 months'
    WHERE cs1.quarter = DATE_TRUNC('quarter', CURRENT_DATE)
)
SELECT 
    c.first_name || ' ' || c.last_name AS customer_name,
    sc.previous_spend,
    sc.recent_spend,
    sc.growth_percent
FROM spending_comparison sc
JOIN customers c ON sc.customer_id = c.customer_id
WHERE growth_percent > 0
ORDER BY growth_percent DESC
LIMIT 20;
"""
    },
    {
        "question": "What's our cancellation rate by service type?",
        "sql": """
SELECT 
    s.service_name,
    s.category,
    COUNT(*) FILTER (WHERE b.status = 'cancelled') AS cancellations,
    COUNT(*) AS total_bookings,
    ROUND(100.0 * COUNT(*) FILTER (WHERE b.status = 'cancelled') / COUNT(*), 2) AS cancellation_rate
FROM booking_services bs
JOIN bookings b ON bs.booking_id = b.booking_id
JOIN services s ON bs.service_id = s.service_id
WHERE b.booking_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY s.service_id, s.service_name, s.category
HAVING COUNT(*) >= 10
ORDER BY cancellation_rate DESC;
"""
    }
]


# Documentation strings for complex business terms
BUSINESS_CONTEXT_DOCS = [
    {
        "term": "Customer Lifetime Value (CLV)",
        "documentation": "The total amount a customer spends with the salon over their entire relationship. Calculate by summing all completed bookings (total_amount + tip_amount) for each customer. Used for identifying VIP customers and marketing ROI."
    },
    {
        "term": "Customer Churn",
        "documentation": "Customers who haven't returned in a significant period (typically 60-90 days). Identify by finding customers whose last completed booking was more than N days ago. Critical for retention campaigns."
    },
    {
        "term": "Retention Rate",
        "documentation": "Percentage of customers who return for repeat visits. Track by cohort (month of first visit) to see how many customers return in subsequent months. High retention = healthy business."
    },
    {
        "term": "Booking Completion Rate",
        "documentation": "Percentage of scheduled bookings that are completed (not cancelled or no-show). High completion rates indicate good scheduling and customer commitment. Target: >85%."
    },
    {
        "term": "Average Ticket Value",
        "documentation": "The average amount spent per booking, including services and tips. Calculate as AVG(total_amount + tip_amount) from completed bookings. Use for pricing and upselling strategies."
    },
    {
        "term": "Technician Utilization",
        "documentation": "Percentage of available technician time that is booked. Calculate by summing service duration_minutes for all bookings divided by available hours. Optimal: 70-85%."
    },
    {
        "term": "Service Mix",
        "documentation": "The distribution of different service types. Analyze which service categories generate the most revenue and bookings. Helps with inventory, training, and marketing focus."
    },
    {
        "term": "Peak Hours",
        "documentation": "Time periods with highest booking volume. Extract hour from booking_time and count bookings per hour to identify busiest times. Critical for staffing optimization."
    },
    {
        "term": "Customer Segmentation",
        "documentation": "Grouping customers by behavior: VIP (12+ visits, $1000+ spent), Loyal (6+ visits, $500+), Regular (3+ visits), New (<3 visits). Enables targeted marketing and service."
    },
    {
        "term": "Price Tier",
        "documentation": "Service pricing categories: Basic (<$30), Standard ($30-60), Premium ($60-100), VIP ($100+). Used for menu design and upselling opportunities."
    },
    {
        "term": "Product Usage Rate",
        "documentation": "Average daily consumption of inventory products. Calculate from sales over time period. Predicts stockouts: days_until_stockout = current_stock / daily_usage_rate."
    },
    {
        "term": "Commission Structure",
        "documentation": "Percentage of service revenue paid to technicians. Calculate: commission_earned = total_revenue * commission_rate / 100. Track with tips for total technician earnings."
    },
    {
        "term": "Discount Effectiveness",
        "documentation": "Measure promotion ROI by tracking: discount_usage_rate = bookings_with_discount / total_bookings. Identify discount-sensitive customers for targeted campaigns."
    },
    {
        "term": "Seasonal Demand",
        "documentation": "Product/service demand patterns by month. Essential for inventory planning. Track monthly sales volume and revenue to predict future needs."
    },
    {
        "term": "Visit Frequency",
        "documentation": "Average days between customer visits. Calculate: avg_days_between_visits from booking history. Predict next visit and identify customers overdue for appointments."
    }
]


def get_all_training_data() -> Dict:
    """
    Get complete training data package for Vanna
    
    Returns:
        Dictionary with DDL, questions, and documentation
    """
    return {
        "ddl": STANDARD_SCHEMA_DDL,
        "questions": TRAINING_QUESTIONS,
        "documentation": BUSINESS_CONTEXT_DOCS,
        "total_examples": len(TRAINING_QUESTIONS)
    }


def print_training_summary():
    """Print summary of training data"""
    data = get_all_training_data()
    
    print("=" * 60)
    print("VANNA AI TRAINING DATA SUMMARY")
    print("=" * 60)
    print(f"\n📊 Total Training Examples: {data['total_examples']}")
    print(f"📚 Business Terms Documented: {len(data['documentation'])}")
    print("\n📋 Coverage by Category:")
    
    categories = {
        "Customer Queries": 0,
        "Booking/Appointment Queries": 0,
        "Service Queries": 0,
        "Technician Queries": 0,
        "Product/Inventory Queries": 0,
        "Financial/Revenue Queries": 0,
        "Complex Analytics": 0
    }
    
    for q in data['questions']:
        question = q['question'].lower()
        if 'customer' in question and 'retention' not in question:
            categories["Customer Queries"] += 1
        elif 'booking' in question or 'appointment' in question or 'scheduled' in question:
            categories["Booking/Appointment Queries"] += 1
        elif 'service' in question:
            categories["Service Queries"] += 1
        elif 'technician' in question or 'staff' in question:
            categories["Technician Queries"] += 1
        elif 'product' in question or 'inventory' in question or 'stock' in question:
            categories["Product/Inventory Queries"] += 1
        elif 'revenue' in question or 'payment' in question or 'financial' in question:
            categories["Financial/Revenue Queries"] += 1
        else:
            categories["Complex Analytics"] += 1
    
    for category, count in categories.items():
        print(f"  • {category}: {count} examples")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_training_summary()
    
    # Example usage
    print("\n🎯 Sample Questions:")
    data = get_all_training_data()
    for i, q in enumerate(data['questions'][:3], 1):
        print(f"\n{i}. {q['question']}")
        print(f"   SQL Preview: {q['sql'][:100]}...")

