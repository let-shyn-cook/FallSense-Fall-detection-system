from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from auth import auth_bp, token_required
from modules.camera import VideoCamera
from modules.database import Database
from modules.dashboard_data import DashboardData
import time
import os

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Khởi tạo WebSocket
socketio = SocketIO(app, cors_allowed_origins="*")

# Khởi tạo camera và database
camera = VideoCamera(socketio)
db = Database(socketio=socketio)
dashboard_data = DashboardData()

# Register authentication blueprint
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    token = request.headers.get('Authorization')
    if not token:
        return app.send_static_file('landing.html')
    return app.send_static_file('index.html')

@app.route('/landing-technology')
def landing_technology():
    return app.send_static_file('landing-technology.html')

@app.route('/landing-pricing')
def landing_pricing():
    return app.send_static_file('landing-pricing.html')

@app.route('/landing-docs')
def landing_docs():
    return app.send_static_file('landing-docs.html')

@app.route('/landing-blog')
def landing_blog():
    return app.send_static_file('landing-blog.html')

@app.route('/landing-contact')
def landing_contact():
    return app.send_static_file('landing-contact.html')

@app.route('/monitor')
@token_required
def monitor(current_user):
    return app.send_static_file('monitor.html')

@app.route('/history')
@token_required
def history(current_user):
    # Không dừng camera khi chuyển sang trang history
    return app.send_static_file('history.html')

@app.route('/settings')
@token_required
def settings(current_user):
    return app.send_static_file('settings.html')

@app.route('/api/events')
@token_required
def get_events(current_user):
    events = db.get_fall_events()
    return jsonify(events)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('get_history')
def handle_get_history():
    events = db.get_fall_events()
    socketio.emit('history_update', events)

@socketio.on('get_settings')
def handle_get_settings():
    # Gửi cài đặt hiện tại cho client
    settings = {
        'storage': {
            'used': '2.5GB',
            'total': '10GB',
            'percentage': 25
        }
    }
    socketio.emit('settings_update', settings)

@socketio.on('get_dashboard_data')
def handle_dashboard_data():
    data = dashboard_data.get_dashboard_data()
    socketio.emit('dashboard_data', data)

@socketio.on('fall_event')
def handle_fall_event(data):
    # Update dashboard data when a fall event occurs
    socketio.emit('dashboard_data', dashboard_data.get_dashboard_data())

@app.route('/api/camera/start', methods=['POST'])
def start_camera():
    success = camera.start()
    return jsonify({'success': success})

@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    success = camera.stop()
    return jsonify({'success': success})

@app.route('/api/events/delete', methods=['POST'])
@token_required
def delete_events(current_user):
    db.delete_fall_events()
    return jsonify({'success': True})

@app.route('/api/camera/status', methods=['GET'])
def get_camera_status():
    return jsonify(camera.get_status())

def gen_frames():
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.033)  # ~30 FPS

@app.route('/api/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/static/fall_images/<path:filename>')
def serve_fall_image(filename):
    return send_from_directory(os.path.join(app.static_folder, 'fall_images'), filename)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)