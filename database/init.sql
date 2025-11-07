-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    category VARCHAR(50) DEFAULT 'General',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT INTO users (username, email) VALUES
    ('alice', 'alice@example.com'),
    ('bob', 'bob@example.com'),
    ('charlie', 'charlie@example.com'),
    ('diana', 'diana@example.com')
ON CONFLICT (username) DO NOTHING;

-- Insert sample products
INSERT INTO products (name, description, price, stock, category) VALUES
    ('Laptop', 'High-performance laptop for professionals', 1299.99, 50, 'Electronics'),
    ('Mouse', 'Wireless ergonomic mouse', 29.99, 200, 'Electronics'),
    ('Keyboard', 'Mechanical keyboard with RGB lighting', 89.99, 150, 'Electronics'),
    ('Monitor', '27-inch 4K display', 449.99, 75, 'Electronics'),
    ('Headphones', 'Noise-cancelling wireless headphones', 199.99, 100, 'Electronics'),
    ('Desk Chair', 'Ergonomic office chair', 299.99, 40, 'Furniture'),
    ('Standing Desk', 'Adjustable height standing desk', 599.99, 25, 'Furniture'),
    ('Notebook', 'Premium leather-bound notebook', 24.99, 300, 'Stationery'),
    ('Pen Set', 'Professional fountain pen set', 49.99, 150, 'Stationery'),
    ('Backpack', 'Laptop backpack with USB charging port', 79.99, 120, 'Accessories')
ON CONFLICT DO NOTHING;

-- Insert sample orders
INSERT INTO orders (user_id, product_id, quantity, total_price, status) VALUES
    (1, 1, 1, 1299.99, 'completed'),
    (1, 2, 2, 59.98, 'completed'),
    (2, 3, 1, 89.99, 'shipped'),
    (2, 5, 1, 199.99, 'pending'),
    (3, 4, 1, 449.99, 'processing'),
    (3, 8, 3, 74.97, 'completed'),
    (4, 6, 1, 299.99, 'pending'),
    (4, 7, 1, 599.99, 'processing')
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
