from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import redis
import json
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
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

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_redis_connection():
    """Create Redis connection"""
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        return None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    health_status = {
        'service': 'user-service',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Check database
    conn = get_db_connection()
    if conn:
        health_status['database'] = 'connected'
        conn.close()
    else:
        health_status['database'] = 'disconnected'
        health_status['status'] = 'unhealthy'
    
    # Check Redis
    r = get_redis_connection()
    if r:
        try:
            r.ping()
            health_status['redis'] = 'connected'
        except:
            health_status['redis'] = 'disconnected'
    else:
        health_status['redis'] = 'disconnected'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/api/v1/users', methods=['GET'])
def get_users():
    """Get all users"""
    # Try cache first
    r = get_redis_connection()
    if r:
        cached_users = r.get('users:all')
        if cached_users:
            logger.info("Cache hit for users")
            return jsonify({
                'users': json.loads(cached_users),
                'source': 'cache'
            })
    
    # Fetch from database
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT id, username, email, created_at FROM users ORDER BY id')
            users = cur.fetchall()
            
            # Convert datetime to string
            for user in users:
                user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
            
            # Cache the result
            if r:
                r.setex('users:all', 60, json.dumps(users))  # Cache for 60 seconds
                logger.info("Cached users data")
            
            return jsonify({
                'users': users,
                'source': 'database',
                'count': len(users)
            })
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    # Try cache first
    r = get_redis_connection()
    cache_key = f'user:{user_id}'
    
    if r:
        cached_user = r.get(cache_key)
        if cached_user:
            logger.info(f"Cache hit for user {user_id}")
            return jsonify({
                'user': json.loads(cached_user),
                'source': 'cache'
            })
    
    # Fetch from database
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT id, username, email, created_at FROM users WHERE id = %s', (user_id,))
            user = cur.fetchone()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Convert datetime to string
            user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
            
            # Cache the result
            if r:
                r.setex(cache_key, 300, json.dumps(user))  # Cache for 5 minutes
                logger.info(f"Cached user {user_id} data")
            
            return jsonify({
                'user': user,
                'source': 'database'
            })
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/v1/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'email' not in data:
        return jsonify({'error': 'Username and email are required'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                'INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id, username, email, created_at',
                (data['username'], data['email'])
            )
            user = cur.fetchone()
            conn.commit()
            
            # Convert datetime to string
            user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
            
            # Invalidate cache
            r = get_redis_connection()
            if r:
                r.delete('users:all')
                logger.info("Invalidated users cache")
            
            logger.info(f"Created user: {user['username']}")
            return jsonify({
                'user': user,
                'message': 'User created successfully'
            }), 201
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'Username or email already exists'}), 409
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

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
                'timestamp': datetime.utcnow().isoformat()
            })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

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
    app.run(host='0.0.0.0', port=5000, debug=True)
