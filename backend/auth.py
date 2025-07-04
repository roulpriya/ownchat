from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models import db, User
from config import Config
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    return len(password) >= 8

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print(f"Register request data: {data}")  # Debug logging
        
        if not data or not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'Email, password, and name are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if not validate_password(password):
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        if len(name) < 2:
            return jsonify({'error': 'Name must be at least 2 characters long'}), 400
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        
        user = User(email=email, name=name)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'redirect_url': '/chat'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print(f"Login request data: {data}")  # Debug logging
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        login_user(user)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'redirect_url': '/chat'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    try:
        data = request.get_json()
        
        if not data or not data.get('credential'):
            return jsonify({'error': 'Google credential is required'}), 400
        
        token = data['credential']
        
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            Config.GOOGLE_CLIENT_ID
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return jsonify({'error': 'Invalid token issuer'}), 401
        
        google_id = idinfo['sub']
        email = idinfo['email'].lower().strip()
        name = idinfo['name']
        avatar_url = idinfo.get('picture', '')
        
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            # Check if user exists with same email
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                # Link Google account to existing user
                existing_user.google_id = google_id
                existing_user.avatar_url = avatar_url
                user = existing_user
            else:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    google_id=google_id,
                    avatar_url=avatar_url
                )
                db.session.add(user)
        else:
            # Update existing Google user info
            user.name = name
            user.avatar_url = avatar_url
        
        db.session.commit()
        
        login_user(user)
        
        return jsonify({
            'message': 'Google login successful',
            'user': user.to_dict(),
            'redirect_url': '/chat'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': 'Invalid Google token'}), 401
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Google login failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        return jsonify({'user': current_user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        
        if data.get('name'):
            name = data['name'].strip()
            if len(name) < 2:
                return jsonify({'error': 'Name must be at least 2 characters long'}), 400
            current_user.name = name
        
        if data.get('avatar_url'):
            current_user.avatar_url = data['avatar_url']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    try:
        logout_user()
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'error': 'Logout failed'}), 500