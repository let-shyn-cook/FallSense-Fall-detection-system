from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

auth_bp = Blueprint('auth', __name__)

try:
    # Kết nối MongoDB sử dụng URI từ biến môi trường
    client = MongoClient(os.getenv('MONGODB_URI'))
    # Kiểm tra kết nối
    client.admin.command('ping')
    db = client[os.getenv('MONGODB_DB')]
    users_collection = db['users']
except ConnectionFailure:
    print("Không thể kết nối đến MongoDB. Đảm bảo MongoDB đang chạy.")
    raise

# Lấy SECRET_KEY từ biến môi trường
SECRET_KEY = os.getenv('SECRET_KEY')

@auth_bp.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Dữ liệu không hợp lệ'}), 400
    except Exception as e:
        return jsonify({'message': f'Lỗi khi xử lý dữ liệu: {str(e)}'}), 400
    
    # Kiểm tra dữ liệu đầu vào
    if not all(k in data for k in ('username', 'email', 'password', 'phone')):
        return jsonify({'message': 'Thiếu thông tin đăng ký'}), 400
    
    # Kiểm tra định dạng số điện thoại
    if not data['phone'].isdigit() or len(data['phone']) != 10:
        return jsonify({'message': 'Số điện thoại không hợp lệ'}), 400
    
    # Kiểm tra username đã tồn tại
    if users_collection.find_one({'username': data['username']}):
        return jsonify({'message': 'Tên đăng nhập đã tồn tại'}), 400
    
    # Kiểm tra email đã tồn tại
    if users_collection.find_one({'email': data['email']}):
        return jsonify({'message': 'Email đã tồn tại'}), 400
    
    # Kiểm tra số điện thoại đã tồn tại
    if users_collection.find_one({'phone': data['phone']}):
        return jsonify({'message': 'Số điện thoại đã tồn tại'}), 400
    
    # Tạo user mới
    new_user = {
        'username': data['username'],
        'email': data['email'],
        'phone': data['phone'],
        'password': generate_password_hash(data['password']),
        'created_at': datetime.utcnow()
    }
    
    # Lưu vào database
    users_collection.insert_one(new_user)
    
    return jsonify({'message': 'Đăng ký thành công'}), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Dữ liệu không hợp lệ'}), 400
    except Exception as e:
        return jsonify({'message': f'Lỗi khi xử lý dữ liệu: {str(e)}'}), 400
    
    # Kiểm tra dữ liệu đầu vào
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'message': 'Thiếu thông tin đăng nhập'}), 400
    
    # Tìm user
    user = users_collection.find_one({'username': data['username']})
    
    # Kiểm tra mật khẩu
    if user and check_password_hash(user['password'], data['password']):
        # Tạo token
        token = jwt.encode({
            'user_id': str(user['_id']),
            'username': user['username'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, SECRET_KEY)
        
        return jsonify({
            'message': 'Đăng nhập thành công',
            'token': token
        }), 200
    
    return jsonify({'message': 'Tên đăng nhập hoặc mật khẩu không đúng'}), 401

# Middleware để xác thực token
def token_required(f):
    def token_wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token không tồn tại'}), 401
        
        try:
            # Kiểm tra định dạng token
            if not token.startswith('Bearer '):
                return jsonify({'message': 'Định dạng token không hợp lệ'}), 401
                
            # Xác thực token
            data = jwt.decode(token.split(' ')[1], SECRET_KEY, algorithms=['HS256'])
            current_user = users_collection.find_one({'_id': ObjectId(data['user_id'])})
            
            if not current_user:
                return jsonify({'message': 'Người dùng không tồn tại'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token đã hết hạn'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token không hợp lệ'}), 401
        except Exception as e:
            return jsonify({'message': 'Lỗi xác thực: ' + str(e)}), 401
            
        return f(current_user, *args, **kwargs)
    
    token_wrapper.__name__ = f.__name__
    return token_wrapper