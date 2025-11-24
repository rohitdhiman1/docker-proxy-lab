from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
import redis
import json
from datetime import datetime, timezone
import logging
from functools import wraps
import time

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Initialize tracing
def init_tracing():
    """Initialize OpenTelemetry tracing with Jaeger"""
    jaeger_host = os.getenv('JAEGER_HOST', 'jaeger')
    jaeger_port = int(os.getenv('JAEGER_PORT', '6831'))
    
    resource = Resource.create({
        "service.name": "user-service",
        "service.version": "1.0.0",
        "deployment.environment": os.getenv('ENVIRONMENT', 'development')
    })
    
    provider = TracerProvider(resource=resource)
    
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )
    
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(provider)
    
    # Auto-instrument libraries
    FlaskInstrumentor().instrument_app(app)
    Psycopg2Instrumentor().instrument()
    RedisInstrumentor().instrument()
    
    logger.info(f"Tracing initialized with Jaeger at {jaeger_host}:{jaeger_port}")

app = Flask(__name__)
CORS(app)

# Initialize tracing
init_tracing()

# Get tracer for manual spans
tracer = trace.get_tracer(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'database': os.getenv('DB_NAME', 'labdb'),
    'user': os.getenv('DB_USER', 'labuser'),
    'password': os.getenv('DB_PASSWORD', 'labpass'),
    'port': os.getenv('DB_PORT', '5432')
}

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

# Initialize connection pools
db_pool = None
redis_pool = None

def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **DB_CONFIG
        )
        logger.info("Database connection pool created")
        return True
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        return False

def init_redis_pool():
    """Initialize Redis connection pool"""
    global redis_pool
    try:
        redis_pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            max_connections=10
        )
        logger.info("Redis connection pool created")
        return True
    except Exception as e:
        logger.error(f"Failed to create Redis pool: {e}")
        return False

def get_db_connection():
    """Get database connection from pool"""
    if db_pool is None:
        if not init_db_pool():
            return None
    try:
        return db_pool.getconn()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def return_db_connection(conn):
    """Return database connection to pool"""
    if db_pool and conn:
        db_pool.putconn(conn)

def get_redis_connection():
    """Get Redis connection from pool"""
    if redis_pool is None:
        if not init_redis_pool():
            return None
    try:
        return redis.Redis(connection_pool=redis_pool)
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        return None

def retry_on_failure(retries=3, delay=1):
    """Decorator to retry operations on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    health_status = {
        'service': 'user-service',
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    # Check database
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
            health_status['database'] = 'connected'
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            health_status['database'] = 'disconnected'
            health_status['status'] = 'unhealthy'
        finally:
            return_db_connection(conn)
    else:
        health_status['database'] = 'disconnected'
        health_status['status'] = 'unhealthy'
    
    # Check Redis
    r = get_redis_connection()
    if r:
        try:
            r.ping()
            health_status['redis'] = 'connected'
        except redis.RedisError as e:
            logger.warning(f"Redis health check failed: {e}")
            health_status['redis'] = 'disconnected'
    else:
        health_status['redis'] = 'disconnected'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/api/v1/users', methods=['GET'])
@retry_on_failure(retries=2, delay=0.5)
def get_users():
    """Get all users with pagination"""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100
    offset = (page - 1) * per_page
    
    # Try cache first
    cache_key = f'users:page:{page}:per_page:{per_page}'
    r = get_redis_connection()
    if r:
        try:
            cached_users = r.get(cache_key)
            if cached_users:
                logger.info(f"Cache hit for users page {page}")
                return jsonify({
                    **json.loads(cached_users),
                    'source': 'cache'
                })
        except redis.RedisError as e:
            logger.warning(f"Redis error: {e}")
    
    # Fetch from database
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get total count
            cur.execute('SELECT COUNT(*) as total FROM users')
            total = cur.fetchone()['total']
            
            # Get paginated results
            cur.execute(
                'SELECT id, username, email, created_at FROM users ORDER BY id LIMIT %s OFFSET %s',
                (per_page, offset)
            )
            users = cur.fetchall()
            
            # Convert datetime to string with timezone
            for user in users:
                if user['created_at']:
                    user['created_at'] = user['created_at'].replace(tzinfo=timezone.utc).isoformat()
            
            response_data = {
                'users': users,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                },
                'source': 'database',
                'count': len(users)
            }
            
            # Cache the result
            if r:
                try:
                    r.setex(cache_key, 60, json.dumps(response_data))  # Cache for 60 seconds
                    logger.info(f"Cached users page {page}")
                except redis.RedisError as e:
                    logger.warning(f"Redis caching error: {e}")
            
            return jsonify(response_data)
    except psycopg2.Error as e:
        logger.error(f"Database error fetching users: {e}")
        return jsonify({'error': 'Database query failed'}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching users: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/v1/users/<int:user_id>', methods=['GET'])
@retry_on_failure(retries=2, delay=0.5)
def get_user(user_id):
    """Get user by ID"""
    # Validate user_id
    if user_id <= 0:
        return jsonify({'error': 'Invalid user ID'}), 400
    
    # Try cache first
    r = get_redis_connection()
    cache_key = f'user:{user_id}'
    
    if r:
        try:
            cached_user = r.get(cache_key)
            if cached_user:
                logger.info(f"Cache hit for user {user_id}")
                return jsonify({
                    'user': json.loads(cached_user),
                    'source': 'cache'
                })
        except redis.RedisError as e:
            logger.warning(f"Redis error: {e}")
    
    # Fetch from database
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                'SELECT id, username, email, created_at FROM users WHERE id = %s',
                (user_id,)
            )
            user = cur.fetchone()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Convert datetime to string with timezone
            if user['created_at']:
                user['created_at'] = user['created_at'].replace(tzinfo=timezone.utc).isoformat()
            
            # Cache the result
            if r:
                try:
                    r.setex(cache_key, 300, json.dumps(user))  # Cache for 5 minutes
                    logger.info(f"Cached user {user_id} data")
                except redis.RedisError as e:
                    logger.warning(f"Redis caching error: {e}")
            
            return jsonify({
                'user': user,
                'source': 'database'
            })
    except psycopg2.Error as e:
        logger.error(f"Database error fetching user {user_id}: {e}")
        return jsonify({'error': 'Database query failed'}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/v1/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    # Validate input
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    
    if not username or not email:
        return jsonify({'error': 'Username and email are required'}), 400
    
    # Basic validation
    if len(username) < 3 or len(username) > 50:
        return jsonify({'error': 'Username must be between 3 and 50 characters'}), 400
    
    if '@' not in email or len(email) > 255:
        return jsonify({'error': 'Invalid email format'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                'INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id, username, email, created_at',
                (username, email)
            )
            user = cur.fetchone()
            conn.commit()
            
            # Convert datetime to string with timezone
            if user['created_at']:
                user['created_at'] = user['created_at'].replace(tzinfo=timezone.utc).isoformat()
            
            # Invalidate all users cache (all pages)
            r = get_redis_connection()
            if r:
                try:
                    # Delete all cached pages
                    for key in r.scan_iter('users:page:*'):
                        r.delete(key)
                    logger.info("Invalidated users cache")
                except redis.RedisError as e:
                    logger.warning(f"Cache invalidation error: {e}")
            
            logger.info(f"Created user: {username} (ID: {user['id']})")
            return jsonify({
                'user': user,
                'message': 'User created successfully'
            }), 201
    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.warning(f"Integrity error creating user: {e}")
        return jsonify({'error': 'Username or email already exists'}), 409
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Database error creating user: {e}")
        return jsonify({'error': 'Database operation failed'}), 500
    except Exception as e:
        conn.rollback()
        logger.error(f"Unexpected error creating user: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get service statistics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT COUNT(*) as total_users FROM users')
            result = cur.fetchone()
            
            return jsonify({
                'service': 'user-service',
                'total_users': result['total_users'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
    except psycopg2.Error as e:
        logger.error(f"Database error fetching stats: {e}")
        return jsonify({'error': 'Database query failed'}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'User Service',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'users': '/api/v1/users',
            'user_by_id': '/api/v1/users/<id>',
            'stats': '/api/v1/stats'
        }
    })

if __name__ == '__main__':
    # Initialize connection pools at startup
    init_db_pool()
    init_redis_pool()
    
    # Use production-safe settings
    debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
