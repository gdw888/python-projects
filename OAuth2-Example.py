from flask import Flask, request, jsonify, redirect, url_for
import requests
import time
import jwt
import os
import string
import random
from functools import wraps
from jwt import PyJWKClient
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Configuration
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
AUTHORIZATION_BASE_URL = 'https://provider.com/oauth/authorize'
TOKEN_URL = 'https://provider.com/oauth/token'
USERINFO_URL = 'https://provider.com/oauth/userinfo'
JWKS_URL = 'https://provider.com/.well-known/jwks.json'
REDIRECT_URI = 'http://localhost:5000/callback'

# In-memory storage for idempotency keys
idempotency_keys = {}

# Retrieve public keys from identity provider
jwks_client = PyJWKClient(JWKS_URL)

# Utility function to generate a random string
def generate_random_state(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Utility function to decode and verify the ID token from the identity provider
def decode_id_token(token):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        decoded = jwt.decode(token, key=signing_key.key, algorithms=["RS256"], audience=CLIENT_ID)
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Utility function to decode our own JWT token
def decode_jwt(token):
    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Mock function to check user permissions
def check_permissions(token_info, required_scope):
    scopes = token_info.get('scopes', [])
    if required_scope in scopes:
        return True
    return False

# Decorator to check token and permissions
def token_required(required_scope):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Authorization token required'}), 401
            
            token_info = decode_jwt(token)
            if not token_info:
                return jsonify({'error': 'Invalid or expired token'}), 403
            
            if not check_permissions(token_info, required_scope):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    return 'Welcome to OpenID Connect demo'

@app.route('/login')
def login():
    state = generate_random_state()
    authorization_url = (
        f"{AUTHORIZATION_BASE_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope=openid%20profile&state={state}"
    )
    return jsonify({'authorization_url': authorization_url, 'state': state})

@app.route('/callback')
def callback():
    state = request.args.get('state')
    code = request.args.get('code')
    original_state = request.args.get('original_state')
    
    if state != original_state:
        return jsonify({'error': 'Invalid state parameter'}), 403
    
    token_response = requests.post(TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    token_json = token_response.json()
    id_token = token_json['id_token']
    access_token = token_json['access_token']
    expires_in = token_json['expires_in']
    scopes = token_json['scope'].split()

    # Decode the ID token to get user information
    user_info = decode_id_token(id_token)
    if not user_info:
        return jsonify({'error': 'Failed to decode ID token'}), 403
    
    sub = user_info.get('sub')
    username = user_info.get('preferred_username')
    email = user_info.get('email')

    # Check if the user exists in the database, if not, create a new user
    user = User.query.get(sub)
    if not user:
        user = User(id=sub, username=username, email=email)
        db.session.add(user)
        db.session.commit()

    # Create a JWT to return to the user for accessing our own resources
    jwt_token = jwt.encode({
        'sub': sub,
        'username': username,
        'scopes': scopes,
        'exp': time.time() + expires_in
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'access_token': jwt_token})

@app.route('/resource/<resource_id>', methods=['DELETE', 'PUT', 'PATCH'])
@token_required('write')  # Assuming all methods require 'write' scope
def modify_resource(resource_id):
    token = request.headers.get('Authorization')
    method = request.method.lower()

    # Idempotency key check
    idempotency_key = request.headers.get('Idempotency-Key')
    if not idempotency_key:
        return jsonify({'error': 'Idempotency-Key header required'}), 400

    if idempotency_key in idempotency_keys:
        return jsonify({'error': 'Duplicate request detected'}), 409

    # Mark idempotency key as used
    idempotency_keys[idempotency_key] = True

    # Process the request
    if method == 'delete':
        # Decode the token to get the user information
        token_info = decode_jwt(token)
        if not token_info:
            return jsonify({'error': 'Invalid or expired token'}), 403
        
        sub = token_info.get('sub')
        
        # Find the user by sub
        user = User.query.get(sub)
        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'status': 'Resource deleted'}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    
    elif method == 'put':
        # Implement update logic here
        return jsonify({'status': 'Resource updated'}), 200
    elif method == 'patch':
        # Implement partial update logic here
        return jsonify({'status': 'Resource partially updated'}), 200

if __name__ == '__main__':
    app.run(debug=True)
