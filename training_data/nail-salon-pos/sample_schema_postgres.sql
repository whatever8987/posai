-- PostgreSQL Sample Database Schema for Nail Salon POS System

-- Drop existing tables
DROP TABLE IF EXISTS product_sales CASCADE;
DROP TABLE IF EXISTS booking_services CASCADE;
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS services CASCADE;
DROP TABLE IF EXISTS technicians CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_created_at ON customers(created_at);

-- Technicians table
CREATE TABLE technicians (
    technician_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    specialties TEXT,
    hire_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    commission_rate DECIMAL(5,2) DEFAULT 50.00
);

CREATE INDEX idx_technicians_is_active ON technicians(is_active);

-- Services table
CREATE TABLE services (
    service_id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    duration_minutes INT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_services_category ON services(category);
CREATE INDEX idx_services_is_active ON services(is_active);

-- Bookings table
CREATE TABLE bookings (
    booking_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    technician_id INT NOT NULL,
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show')),
    total_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    tip_amount DECIMAL(10,2) DEFAULT 0,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (technician_id) REFERENCES technicians(technician_id)
);

CREATE INDEX idx_bookings_booking_date ON bookings(booking_date);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_customer ON bookings(customer_id);
CREATE INDEX idx_bookings_technician ON bookings(technician_id);
CREATE INDEX idx_bookings_created_at ON bookings(created_at);

-- Booking Services junction table
CREATE TABLE booking_services (
    booking_service_id SERIAL PRIMARY KEY,
    booking_id INT NOT NULL,
    service_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id)
);

CREATE INDEX idx_booking_services_booking ON booking_services(booking_id);
CREATE INDEX idx_booking_services_service ON booking_services(service_id);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    unit_price DECIMAL(10,2) NOT NULL,
    cost_price DECIMAL(10,2),
    current_stock INT DEFAULT 0,
    min_stock_level INT DEFAULT 10,
    supplier VARCHAR(100),
    sku VARCHAR(50) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_stock ON products(current_stock);

-- Product Sales table
CREATE TABLE product_sales (
    sale_id SERIAL PRIMARY KEY,
    booking_id INT,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX idx_product_sales_sale_date ON product_sales(sale_date);
CREATE INDEX idx_product_sales_product ON product_sales(product_id);
CREATE INDEX idx_product_sales_booking ON product_sales(booking_id);

-- Insert sample data

-- Sample Customers
INSERT INTO customers (first_name, last_name, phone, email, date_of_birth) VALUES
('Sarah', 'Johnson', '555-0101', 'sarah.j@email.com', '1990-05-15'),
('Emily', 'Davis', '555-0102', 'emily.d@email.com', '1985-08-22'),
('Michael', 'Brown', '555-0103', 'michael.b@email.com', '1992-03-10'),
('Jessica', 'Wilson', '555-0104', 'jessica.w@email.com', '1988-11-30'),
('Ashley', 'Martinez', '555-0105', 'ashley.m@email.com', '1995-07-18'),
('Jennifer', 'Garcia', '555-0106', 'jennifer.g@email.com', '1987-12-05'),
('Amanda', 'Rodriguez', '555-0107', 'amanda.r@email.com', '1993-09-25'),
('Melissa', 'Lee', '555-0108', 'melissa.l@email.com', '1991-04-14'),
('Nicole', 'Taylor', '555-0109', 'nicole.t@email.com', '1989-06-08'),
('Lisa', 'Anderson', '555-0110', 'lisa.a@email.com', '1994-02-20');

-- Sample Technicians
INSERT INTO technicians (first_name, last_name, phone, specialties, hire_date, commission_rate) VALUES
('Maria', 'Santos', '555-0201', 'Gel manicures, Nail art', '2020-01-15', 50.00),
('Linda', 'Nguyen', '555-0202', 'Acrylic extensions, Pedicures', '2019-06-01', 55.00),
('Kim', 'Park', '555-0203', 'All services, Spa treatments', '2021-03-10', 50.00),
('Anna', 'Chen', '555-0204', 'Nail art, Gel polish', '2022-01-20', 45.00),
('Sofia', 'Lopez', '555-0205', 'Pedicures, Manicures', '2020-09-15', 50.00);

-- Sample Services
INSERT INTO services (service_name, category, base_price, duration_minutes, description) VALUES
('Basic Manicure', 'Manicure', 25.00, 30, 'Nail shaping, cuticle care, and regular polish'),
('Gel Manicure', 'Gel/Shellac', 45.00, 45, 'Long-lasting gel polish with UV curing'),
('Basic Pedicure', 'Pedicure', 35.00, 45, 'Foot soak, nail care, and regular polish'),
('Spa Pedicure', 'Spa Services', 60.00, 60, 'Deluxe pedicure with massage and hot stones'),
('Acrylic Full Set', 'Acrylic/Extensions', 65.00, 90, 'Complete set of acrylic nail extensions'),
('Acrylic Fill', 'Acrylic/Extensions', 45.00, 60, 'Maintenance for existing acrylic nails'),
('Nail Art (per nail)', 'Nail Art', 5.00, 10, 'Custom designs and decorations'),
('Polish Change', 'Manicure', 15.00, 20, 'Quick polish change only'),
('Gel Removal', 'Gel/Shellac', 15.00, 20, 'Safe removal of gel polish'),
('Dipping Powder', 'Manicure', 50.00, 60, 'Dip powder manicure');

-- Sample Products
INSERT INTO products (product_name, category, unit_price, cost_price, current_stock, min_stock_level, sku) VALUES
('OPI Nail Polish - Red', 'Polish', 12.99, 6.50, 25, 10, 'OPI-RED-001'),
('CND Shellac - Pink', 'Gel Polish', 14.99, 7.50, 30, 15, 'CND-PINK-001'),
('Cuticle Oil', 'Care Products', 8.99, 4.00, 50, 20, 'CARE-OIL-001'),
('Hand Lotion', 'Care Products', 15.99, 8.00, 40, 15, 'CARE-LOTION-001'),
('Nail File Set', 'Tools', 6.99, 3.00, 100, 30, 'TOOL-FILE-001'),
('Nail Buffer', 'Tools', 4.99, 2.00, 80, 25, 'TOOL-BUFFER-001'),
('Quick Dry Top Coat', 'Polish', 10.99, 5.50, 35, 15, 'POLISH-TC-001'),
('Nail Strengthener', 'Care Products', 12.99, 6.50, 20, 10, 'CARE-STRENGTH-001'),
('Acetone', 'Supplies', 7.99, 3.50, 15, 20, 'SUPPLY-ACE-001'),
('Cotton Pads (100ct)', 'Supplies', 5.99, 2.50, 8, 15, 'SUPPLY-COTTON-001');

-- Sample Bookings (using current date functions)
INSERT INTO bookings (customer_id, technician_id, booking_date, booking_time, status, total_amount, tip_amount, payment_method) VALUES
(1, 1, CURRENT_DATE - INTERVAL '2 days', '10:00:00', 'completed', 45.00, 9.00, 'credit_card'),
(2, 2, CURRENT_DATE - INTERVAL '2 days', '11:00:00', 'completed', 60.00, 12.00, 'credit_card'),
(3, 3, CURRENT_DATE - INTERVAL '1 day', '14:00:00', 'completed', 35.00, 7.00, 'cash'),
(4, 1, CURRENT_DATE - INTERVAL '1 day', '15:30:00', 'completed', 65.00, 13.00, 'credit_card'),
(5, 4, CURRENT_DATE, '09:00:00', 'scheduled', 50.00, 0.00, 'credit_card'),
(6, 2, CURRENT_DATE, '13:00:00', 'scheduled', 45.00, 0.00, 'credit_card'),
(7, 5, CURRENT_DATE + INTERVAL '1 day', '10:00:00', 'scheduled', 60.00, 0.00, NULL),
(8, 3, CURRENT_DATE + INTERVAL '1 day', '14:00:00', 'scheduled', 35.00, 0.00, NULL),
(1, 1, CURRENT_DATE - INTERVAL '15 days', '11:00:00', 'completed', 45.00, 9.00, 'credit_card'),
(2, 2, CURRENT_DATE - INTERVAL '12 days', '13:00:00', 'completed', 50.00, 10.00, 'cash'),
(3, 3, CURRENT_DATE - INTERVAL '10 days', '15:00:00', 'cancelled', 35.00, 0.00, NULL),
(9, 4, CURRENT_DATE - INTERVAL '8 days', '10:30:00', 'completed', 65.00, 13.00, 'credit_card'),
(10, 5, CURRENT_DATE - INTERVAL '7 days', '16:00:00', 'completed', 60.00, 12.00, 'credit_card'),
(4, 1, CURRENT_DATE - INTERVAL '5 days', '11:00:00', 'no_show', 45.00, 0.00, NULL),
(5, 2, CURRENT_DATE - INTERVAL '4 days', '14:00:00', 'completed', 70.00, 14.00, 'credit_card');

-- Sample Booking Services
INSERT INTO booking_services (booking_id, service_id, price) VALUES
(1, 2, 45.00),
(2, 4, 60.00),
(3, 3, 35.00),
(4, 5, 65.00),
(5, 10, 50.00),
(6, 2, 45.00),
(7, 4, 60.00),
(8, 3, 35.00),
(9, 2, 45.00),
(10, 10, 50.00),
(11, 3, 35.00),
(12, 5, 65.00),
(13, 4, 60.00),
(14, 2, 45.00),
(15, 2, 45.00),
(15, 7, 25.00);

-- Sample Product Sales
INSERT INTO product_sales (booking_id, product_id, quantity, unit_price, total_price) VALUES
(1, 2, 1, 14.99, 14.99),
(2, 4, 1, 15.99, 15.99),
(4, 1, 1, 12.99, 12.99),
(9, 3, 1, 8.99, 8.99),
(10, 2, 1, 14.99, 14.99),
(13, 4, 2, 15.99, 31.98),
(15, 7, 1, 10.99, 10.99);

-- Verification queries
SELECT 'Database setup complete!' as status;
SELECT COUNT(*) as customer_count FROM customers;
SELECT COUNT(*) as technician_count FROM technicians;
SELECT COUNT(*) as service_count FROM services;
SELECT COUNT(*) as booking_count FROM bookings;
SELECT COUNT(*) as product_count FROM products;

