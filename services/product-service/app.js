// Initialize tracing first
require('./tracing');

const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const redis = require('redis');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Database configuration
const pool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  database: process.env.DB_NAME || 'labdb',
  user: process.env.DB_USER || 'labuser',
  password: process.env.DB_PASSWORD || 'labpass',
  port: process.env.DB_PORT || 5432,
});

// Redis configuration
const redisClient = redis.createClient({
  socket: {
    host: process.env.REDIS_HOST || 'redis',
    port: process.env.REDIS_PORT || 6379
  }
});

redisClient.on('error', (err) => console.log('Redis Client Error', err));
redisClient.on('connect', () => console.log('Redis Connected'));

// Connect to Redis
(async () => {
  try {
    await redisClient.connect();
  } catch (err) {
    console.error('Failed to connect to Redis:', err);
  }
})();

// Health check endpoint
app.get('/health', async (req, res) => {
  const health = {
    service: 'product-service',
    status: 'healthy',
    timestamp: new Date().toISOString()
  };

  try {
    // Check database
    await pool.query('SELECT 1');
    health.database = 'connected';
  } catch (err) {
    health.database = 'disconnected';
    health.status = 'unhealthy';
  }

  // Check Redis
  try {
    await redisClient.ping();
    health.redis = 'connected';
  } catch (err) {
    health.redis = 'disconnected';
  }

  const statusCode = health.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(health);
});

// Get all products
app.get('/api/v1/products', async (req, res) => {
  try {
    // Try cache first
    const cacheKey = 'products:all';
    const cachedData = await redisClient.get(cacheKey);

    if (cachedData) {
      console.log('Cache hit for products');
      return res.json({
        products: JSON.parse(cachedData),
        source: 'cache'
      });
    }

    // Fetch from database
    const result = await pool.query(
      'SELECT id, name, description, price, stock, category, created_at FROM products ORDER BY id'
    );

    const products = result.rows.map(p => ({
      ...p,
      price: parseFloat(p.price),
      created_at: p.created_at ? p.created_at.toISOString() : null
    }));

    // Cache for 60 seconds
    await redisClient.setEx(cacheKey, 60, JSON.stringify(products));
    console.log('Cached products data');

    res.json({
      products,
      source: 'database',
      count: products.length
    });
  } catch (err) {
    console.error('Error fetching products:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get product by ID
app.get('/api/v1/products/:id', async (req, res) => {
  const productId = parseInt(req.params.id);

  try {
    // Try cache first
    const cacheKey = `product:${productId}`;
    const cachedData = await redisClient.get(cacheKey);

    if (cachedData) {
      console.log(`Cache hit for product ${productId}`);
      return res.json({
        product: JSON.parse(cachedData),
        source: 'cache'
      });
    }

    // Fetch from database
    const result = await pool.query(
      'SELECT id, name, description, price, stock, category, created_at FROM products WHERE id = $1',
      [productId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }

    const product = {
      ...result.rows[0],
      price: parseFloat(result.rows[0].price),
      created_at: result.rows[0].created_at ? result.rows[0].created_at.toISOString() : null
    };

    // Cache for 5 minutes
    await redisClient.setEx(cacheKey, 300, JSON.stringify(product));
    console.log(`Cached product ${productId} data`);

    res.json({
      product,
      source: 'database'
    });
  } catch (err) {
    console.error(`Error fetching product ${productId}:`, err);
    res.status(500).json({ error: err.message });
  }
});

// Create product
app.post('/api/v1/products', async (req, res) => {
  const { name, description, price, stock, category } = req.body;

  if (!name || !price) {
    return res.status(400).json({ error: 'Name and price are required' });
  }

  try {
    const result = await pool.query(
      'INSERT INTO products (name, description, price, stock, category) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [name, description, price, stock || 0, category || 'General']
    );

    const product = {
      ...result.rows[0],
      price: parseFloat(result.rows[0].price),
      created_at: result.rows[0].created_at ? result.rows[0].created_at.toISOString() : null
    };

    // Invalidate cache
    await redisClient.del('products:all');
    console.log('Invalidated products cache');

    res.status(201).json({
      product,
      message: 'Product created successfully'
    });
  } catch (err) {
    console.error('Error creating product:', err);
    res.status(500).json({ error: err.message });
  }
});

// Update product stock
app.patch('/api/v1/products/:id/stock', async (req, res) => {
  const productId = parseInt(req.params.id);
  const { quantity } = req.body;

  if (quantity === undefined) {
    return res.status(400).json({ error: 'Quantity is required' });
  }

  try {
    const result = await pool.query(
      'UPDATE products SET stock = stock + $1 WHERE id = $2 RETURNING *',
      [quantity, productId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }

    const product = {
      ...result.rows[0],
      price: parseFloat(result.rows[0].price),
      created_at: result.rows[0].created_at ? result.rows[0].created_at.toISOString() : null
    };

    // Invalidate caches
    await redisClient.del('products:all');
    await redisClient.del(`product:${productId}`);
    console.log(`Invalidated cache for product ${productId}`);

    res.json({
      product,
      message: 'Stock updated successfully'
    });
  } catch (err) {
    console.error('Error updating stock:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get products by category
app.get('/api/v1/products/category/:category', async (req, res) => {
  const { category } = req.params;

  try {
    const result = await pool.query(
      'SELECT id, name, description, price, stock, category, created_at FROM products WHERE category = $1 ORDER BY id',
      [category]
    );

    const products = result.rows.map(p => ({
      ...p,
      price: parseFloat(p.price),
      created_at: p.created_at ? p.created_at.toISOString() : null
    }));

    res.json({
      products,
      category,
      count: products.length
    });
  } catch (err) {
    console.error('Error fetching products by category:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get service stats
app.get('/api/v1/stats', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        COUNT(*) as total_products,
        SUM(stock) as total_stock,
        COUNT(DISTINCT category) as total_categories
      FROM products
    `);

    res.json({
      service: 'product-service',
      ...result.rows[0],
      total_products: parseInt(result.rows[0].total_products),
      total_stock: parseInt(result.rows[0].total_stock) || 0,
      total_categories: parseInt(result.rows[0].total_categories),
      timestamp: new Date().toISOString()
    });
  } catch (err) {
    console.error('Error fetching stats:', err);
    res.status(500).json({ error: err.message });
  }
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Product Service',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      products: '/api/v1/products',
      product_by_id: '/api/v1/products/<id>',
      products_by_category: '/api/v1/products/category/<category>',
      stats: '/api/v1/stats'
    }
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Product Service running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing connections...');
  await pool.end();
  await redisClient.quit();
  process.exit(0);
});
