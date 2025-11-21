from flask import Flask, request, jsonify, send_file, send_from_directory, abort
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta, timezone
import bcrypt
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from config import Config, get_database, init_db
from icalendar import Calendar, Event
from io import BytesIO


load_dotenv()


app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    static_url_path='/static',
    template_folder=os.path.join(os.path.dirname(__file__), 'templates')
)


app.config.from_object(Config)
CORS(app, resources={r"/*": {"origins": "*"}})


jwt = JWTManager(app)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    return datetime.now(IST)


try:
    init_db()
    print("✅ MongoDB Atlas connected!")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")


def is_admin():
    identity = get_jwt_identity()
    if not identity:
        return False
    db = get_database()
    user = db['users'].find_one({'username': identity})
    return user and user.get('role') == 'administrator'


# ==================== STATIC FILE ROUTES ====================
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')


@app.route('/admin.html')
def admin_dashboard():
    return send_from_directory('templates', 'admin.html')


@app.route('/index.html')
def index_html():
    return send_from_directory('templates', 'index.html')


@app.route('/login.html')
def login():
    return send_from_directory('templates', 'login.html')


@app.route('/signup.html')
def signup():
    return send_from_directory('templates', 'signup.html')


@app.route('/booking.html')
def booking():
    return send_from_directory('templates', 'booking.html')


@app.route('/staff.html')
def staff():
    return send_from_directory('templates', 'staff.html')


@app.route('/principal.html')
def principal():
    return send_from_directory('templates', 'principal.html')


@app.route('/availability.html')
def availability():
    return send_from_directory('templates', 'availability.html')


@app.route('/principal-availability.html')
def principal_availability():
    return send_from_directory('templates', 'principal-availability.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Server is running'})


# =============== AUTH ROUTES ===============
@app.route('/signup', methods=['POST'])
def user_signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all([data.get('username'), data.get('password'), data.get('email'),
                    data.get('role'), data.get('department'), data.get('full_name')]):
            return jsonify({'message': 'Missing required fields'}), 400
        
        # ✅ REMOVED ADMINISTRATOR BLOCK - Now allows admin signup
        
        db = get_database()
        users = db['users']
        
        # Check for existing username
        if users.find_one({'username': data['username']}):
            return jsonify({'message': 'Username already exists'}), 400
        
        # Check for existing email
        if users.find_one({'email': data['email']}):
            return jsonify({'message': 'Email already exists'}), 400
        
        # Hash password
        hashed_pwd = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt())
        
        # Create user document
        user_doc = {
            'username': data['username'],
            'email': data['email'],
            'full_name': data['full_name'],
            'password': hashed_pwd,
            'role': data['role'],
            'department': data['department'],
            'created_at': get_ist_now()
        }
        
        users.insert_one(user_doc)
        return jsonify({'message': 'Account created successfully'}), 201
        
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return jsonify({'message': str(e)}), 500


@app.route('/login', methods=['POST'])
def user_login():
    try:
        data = request.get_json()
        if not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username and password required'}), 400
        
        db = get_database()
        users = db['users']
        user = users.find_one({'username': data['username']})
        
        if not user or not bcrypt.checkpw(data['password'].encode(), user['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        token = create_access_token(identity=user['username'], expires_delta=timedelta(days=30))
        
        return jsonify({
            'token': token,
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'department': user['department'],
            'role': user['role']
        }), 200
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'message': str(e)}), 500


# =============== ASSET (HALL) MANAGEMENT ===============
@app.route('/assets', methods=['GET'])
@jwt_required()
def list_assets():
    db = get_database()
    assets = list(db['assets'].find())
    for a in assets:
        a['_id'] = str(a['_id'])
    return jsonify({'items': assets}), 200


@app.route('/assets', methods=['POST'])
@jwt_required()
def create_asset():
    if not is_admin():
        return jsonify({"message": "Admins only"}), 403
    
    data = request.get_json()
    name = data.get('name')
    seats = data.get('seats')
    description = data.get('description', '')
    image_url = data.get('image_url', '')
    
    if not name or not seats:
        return jsonify({"message": "Name and seats required"}), 400
    
    db = get_database()
    assets = db['assets']
    
    if assets.find_one({'name': name}):
        return jsonify({"message": "Asset with this name already exists"}), 400
    
    asset_doc = {
        'name': name,
        'seats': seats,
        'description': description,
        'image_url': image_url
    }
    
    result = assets.insert_one(asset_doc)
    return jsonify({"message": "Asset created", "id": str(result.inserted_id)}), 201


@app.route('/assets/<asset_id>', methods=['PUT'])
@jwt_required()
def update_asset(asset_id):
    if not is_admin():
        return jsonify({"message": "Admins only"}), 403
    
    data = request.get_json()
    update_fields = {field: data[field] for field in ['name', 'seats', 'description', 'image_url'] if field in data}
    
    db = get_database()
    assets = db['assets']
    result = assets.update_one({'_id': ObjectId(asset_id)}, {'$set': update_fields})
    
    if result.matched_count == 0:
        return jsonify({"message": "Asset not found"}), 404
    
    return jsonify({"message": "Asset updated"}), 200


@app.route('/assets/<asset_id>', methods=['DELETE'])
@jwt_required()
def delete_asset(asset_id):
    if not is_admin():
        return jsonify({"message": "Admins only"}), 403
    
    db = get_database()
    assets = db['assets']
    result = assets.delete_one({'_id': ObjectId(asset_id)})
    
    if result.deleted_count == 0:
        return jsonify({"message": "Asset not found"}), 404
    
    return jsonify({"message": "Asset deleted"}), 200


def seed_assets():
    """Seed initial assets if collection is empty"""
    db = get_database()
    assets = db['assets']
    
    if assets.count_documents({}) == 0:
        initial_assets = [
            {
                "name": "Auditorium",
                "seats": 500,
                "description": "Large events, ceremonies, and cultural programs",
                "image_url": "/static/images/auditorium.png"
            },
            {
                "name": "Seminar Hall",
                "seats": 250,
                "description": "Workshops, talks, seminars, and presentations",
                "image_url": "/static/images/seminar.png"
            },
            {
                "name": "Board Room",
                "seats": 60,
                "description": "Meetings, reviews, and administrative sessions",
                "image_url": "/static/images/board.png"
            }
        ]
        assets.insert_many(initial_assets)
        print("✅ Seeded initial asset list.")


# =============== BOOKING ROUTES ===============
@app.route('/book', methods=['POST'])
@jwt_required()
def create_booking():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        db = get_database()
        bookings = db['bookings']
        
        booking_doc = {
            'hall': data.get('hall'),
            'date': data.get('date'),
            'time': data.get('time'),
            'department': data.get('dept'),
            'hod': data.get('hod'),
            'purpose': data.get('purpose'),
            'seats': data.get('seats'),
            'details': data.get('details', ''),
            'createdBy': current_user,
            'status': 'Pending',
            'createdAt': get_ist_now()
        }
        
        result = bookings.insert_one(booking_doc)
        return jsonify({'message': 'Booking created', 'id': str(result.inserted_id)}), 201
        
    except Exception as e:
        print(f"❌ Booking error: {e}")
        return jsonify({'message': str(e)}), 500


@app.route('/bookings', methods=['GET'])
def get_bookings_public():
    try:
        db = get_database()
        bookings = db['bookings']
        
        # Only show Approved events publicly unless user is logged in
        status = request.args.get('status')
        if status:
            query = {'status': status}
        else:
            query = {'status': 'Approved'}
        items = list(bookings.find(query))
        for item in items:
            item['_id'] = str(item['_id'])
        return jsonify({'items': items}), 200
    except Exception as e:
        print(f"❌ Get bookings error: {e}")
        return jsonify({'message': str(e)}), 500


@app.route('/approve/<booking_id>', methods=['POST'])
@jwt_required()
def approve_booking(booking_id):
    try:
        db = get_database()
        bookings = db['bookings']
        
        result = bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {'status': 'Approved', 'approvedAt': get_ist_now()}}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Booking not found'}), 404
        
        return jsonify({'message': 'Booking approved'}), 200
        
    except Exception as e:
        print(f"❌ Approve error: {e}")
        return jsonify({'message': str(e)}), 500


@app.route('/reject/<booking_id>', methods=['POST'])
@jwt_required()
def reject_booking(booking_id):
    try:
        db = get_database()
        bookings = db['bookings']
        
        result = bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {'status': 'Rejected', 'approvedAt': get_ist_now()}}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Booking not found'}), 404
        
        return jsonify({'message': 'Booking rejected'}), 200
        
    except Exception as e:
        print(f"❌ Reject error: {e}")
        return jsonify({'message': str(e)}), 500


# =============== ICS EXPORT ROUTE ===============
@app.route('/bookings/export/ics', methods=['POST'])
@jwt_required()
def export_bookings_ics():
    try:
        data = request.get_json()
        booking_ids = data.get('booking_ids', [])
        
        if not booking_ids:
            return jsonify({'message': 'No bookings provided'}), 400
        
        db = get_database()
        bookings = db['bookings']
        
        cal = Calendar()
        cal.add('prodid', '-//CIET Hall Booking System//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', 'CIET Hall Bookings')
        cal.add('x-wr-timezone', 'Asia/Kolkata')
        
        event_count = 0
        
        for booking_id in booking_ids:
            try:
                booking = bookings.find_one({'_id': ObjectId(booking_id)})
                if not booking:
                    continue
                
                booking_date = datetime.strptime(booking['date'], '%Y-%m-%d')
                time_slot = booking['time']
                
                if time_slot == 'FN':
                    start_time = booking_date.replace(hour=9, minute=0)
                    end_time = booking_date.replace(hour=13, minute=0)
                elif time_slot == 'AN':
                    start_time = booking_date.replace(hour=14, minute=0)
                    end_time = booking_date.replace(hour=18, minute=0)
                else:
                    start_time = booking_date.replace(hour=9, minute=0)
                    end_time = booking_date.replace(hour=18, minute=0)
                
                event = Event()
                event.add('summary', f"{booking['hall']} - {booking['purpose']}")
                event.add('dtstart', start_time)
                event.add('dtend', end_time)
                event.add('dtstamp', get_ist_now())
                event.add('location', f"CIET {booking['hall']}")
                event.add('description', f"Dept: {booking['department']}\nHOD: {booking['hod']}\nSeats: {booking['seats']}")
                event.add('status', 'CONFIRMED')
                event.add('uid', str(booking['_id']) + '@ciet.edu')
                
                cal.add_component(event)
                event_count += 1
                
            except Exception as e:
                print(f"Error processing booking {booking_id}: {e}")
                continue
        
        if event_count == 0:
            return jsonify({'message': 'No bookings to export'}), 400
        
        ics_content = cal.to_ical()
        
        return send_file(
            BytesIO(ics_content),
            mimetype='text/calendar',
            as_attachment=True,
            download_name='ciet_bookings.ics'
        )
        
    except Exception as e:
        print(f"❌ ICS export error: {e}")
        return jsonify({'message': str(e)}), 500


# =============== ERROR HANDLERS ===============
@app.errorhandler(404)
def not_found(e):
    if '.' in request.path:
        return jsonify({'message': 'File not found'}), 404
    try:
        return send_from_directory('templates', 'index.html')
    except:
        return jsonify({'message': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'message': 'Internal server error', 'error': str(e)}), 500


if __name__ == '__main__':
    seed_assets()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
