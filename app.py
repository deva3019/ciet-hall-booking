from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import bcrypt
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from config import Config, get_database, init_db
from icalendar import Calendar, Event
from io import BytesIO
from flask import Flask, render_template, send_from_directory

app = Flask(__name__, static_folder='static', static_url_path='/')

# Add this route to serve index.html as default
@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/*": {"origins": Config.CORS_ORIGINS}})
jwt = JWTManager(app)
init_db()

# ==================== UTILITY FUNCTIONS ====================

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_user_by_username(username):
    db = get_database()
    return db.users.find_one({'username': username})

def get_booking_by_id(booking_id):
    db = get_database()
    try:
        return db.bookings.find_one({'_id': ObjectId(booking_id)})
    except:
        return None

def generate_ics_for_booking(booking):
    cal = Calendar()
    cal.add('prodid', '-//CIET Hall Booking//ciet.edu.in//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    
    event = Event()
    event.add('uid', f"{booking['_id']}@ciet.edu.in")
    event.add('dtstamp', datetime.utcnow())
    
    booking_date = datetime.strptime(booking['date'], '%Y-%m-%d')
    
    if booking['time'] == 'FN':
        start_time = booking_date.replace(hour=9, minute=0)
        end_time = booking_date.replace(hour=13, minute=0)
    elif booking['time'] == 'AN':
        start_time = booking_date.replace(hour=14, minute=0)
        end_time = booking_date.replace(hour=18, minute=0)
    else:
        start_time = booking_date.replace(hour=9, minute=0)
        end_time = booking_date.replace(hour=18, minute=0)
    
    event.add('dtstart', start_time)
    event.add('dtend', end_time)
    event.add('summary', f"Hall Booking: {booking['hall']}")
    event.add('description', f"Department: {booking['department']}\nPurpose: {booking['purpose']}\nSeats: {booking['seats']}")
    event.add('location', booking['hall'])
    event.add('status', 'CONFIRMED' if booking['status'] == 'Approved' else 'TENTATIVE')
    
    cal.add_component(event)
    return cal.to_ical()

# ==================== AUTH ROUTES ====================

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        required_fields = ['role', 'email', 'username', 'password', 'department']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
        
        role = data.get('role')
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        department = data.get('department')
        full_name = data.get('full_name', '')
        
        if role not in ['principal', 'staff']:
            return jsonify({'message': 'Invalid role'}), 400
        
        if len(password) < 8:
            return jsonify({'message': 'Password must be at least 8 characters'}), 400
        
        db = get_database()
        if db.users.find_one({'username': username}):
            return jsonify({'message': 'Username already exists'}), 409
        
        if db.users.find_one({'email': email}):
            return jsonify({'message': 'Email already registered'}), 409
        
        user = {
            'username': username,
            'email': email,
            'password': hash_password(password),
            'role': role,
            'department': department,
            'full_name': full_name,
            'createdAt': datetime.utcnow()
        }
        
        result = db.users.insert_one(user)
        
        return jsonify({
            'message': 'Account created successfully',
            'user_id': str(result.inserted_id)
        }), 201
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'message': 'Missing username or password'}), 400
        
        user = get_user_by_username(username)
        
        if not user:
            return jsonify({'message': 'Invalid username or password'}), 401
        
        if not verify_password(password, user['password']):
            return jsonify({'message': 'Invalid username or password'}), 401
        
        access_token = create_access_token(
            identity=username,
            additional_claims={'role': user['role']}
        )
        
        return jsonify({
            'token': access_token,
            'role': user['role'],
            'username': user['username'],
            'email': user['email'],
            'department': user.get('department', ''),
            'full_name': user.get('full_name', user['username'])
        }), 200
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@app.route('/user/<username>', methods=['GET'])
@jwt_required()
def get_user_profile(username):
    try:
        user = get_user_by_username(username)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({
            'username': user['username'],
            'email': user['email'],
            'department': user.get('department', ''),
            'full_name': user.get('full_name', user['username']),
            'role': user['role']
        }), 200
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@app.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        old_password = data.get('old', '')
        new_password = data.get('new', '')
        
        if not old_password or not new_password:
            return jsonify({'message': 'Missing old or new password'}), 400
        
        if len(new_password) < 8:
            return jsonify({'message': 'New password must be at least 8 characters'}), 400
        
        user = get_user_by_username(current_user)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if not verify_password(old_password, user['password']):
            return jsonify({'message': 'Old password is incorrect'}), 401
        
        db = get_database()
        db.users.update_one(
            {'username': current_user},
            {'$set': {'password': hash_password(new_password)}}
        )
        
        return jsonify({'message': 'Password changed successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

# ==================== BOOKING ROUTES ====================

@app.route('/bookings', methods=['GET'])
@jwt_required(optional=True)
def get_bookings():
    try:
        db = get_database()
        
        date = request.args.get('date')
        hall = request.args.get('hall')
        time_slot = request.args.get('time')
        created_by = request.args.get('createdBy')
        status = request.args.get('status')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        filter_query = {}
        
        if date:
            filter_query['date'] = date
        
        if hall:
            filter_query['hall'] = hall
        
        if time_slot:
            filter_query['time'] = time_slot
        
        if created_by:
            filter_query['createdBy'] = created_by
        
        if status:
            filter_query['status'] = status
        
        if start_date or end_date:
            filter_query['date'] = {}
            if start_date:
                filter_query['date']['$gte'] = start_date
            if end_date:
                filter_query['date']['$lte'] = end_date
        
        bookings = list(db.bookings.find(filter_query).sort('createdAt', -1))
        
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
        
        return jsonify({'items': bookings}), 200
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@app.route('/book', methods=['POST'])
@jwt_required()
def create_booking():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['hall', 'dept', 'hod', 'date', 'time', 'seats', 'purpose']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
        
        db = get_database()
        
        if data['time'] != 'Full':
            conflict = db.bookings.find_one({
                'hall': data['hall'],
                'date': data['date'],
                'time': data['time'],
                'status': 'Approved'
            })
        else:
            conflict = db.bookings.find_one({
                'hall': data['hall'],
                'date': data['date'],
                'status': 'Approved'
            })
        
        if conflict:
            return jsonify({'message': 'Hall already booked for this time slot'}), 409
        
        booking = {
            'hall': data['hall'],
            'department': data['dept'],
            'hod': data['hod'],
            'date': data['date'],
            'time': data['time'],
            'seats': int(data['seats']),
            'purpose': data['purpose'],
            'details': data.get('details', ''),
            'status': 'Pending',
            'createdBy': current_user,
            'createdAt': datetime.utcnow()
        }
        
        result = db.bookings.insert_one(booking)
        
        return jsonify({
            'message': 'Booking created successfully',
            'booking_id': str(result.inserted_id)
        }), 201
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@app.route('/approve/<booking_id>', methods=['POST'])
@jwt_required()
def approve_booking(booking_id):
    try:
        current_user = get_jwt_identity()
        db = get_database()
        
        user = get_user_by_username(current_user)
        if user['role'] != 'principal':
            return jsonify({'message': 'Only Principal can approve bookings'}), 403
        
        booking = get_booking_by_id(booking_id)
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {
                'status': 'Approved',
                'approvedBy': current_user,
                'approvedAt': datetime.utcnow()
            }}
        )
        
        return jsonify({'message': 'Booking approved successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@app.route('/reject/<booking_id>', methods=['POST'])
@jwt_required()
def reject_booking(booking_id):
    try:
        current_user = get_jwt_identity()
        db = get_database()
        
        user = get_user_by_username(current_user)
        if user['role'] != 'principal':
            return jsonify({'message': 'Only Principal can reject bookings'}), 403
        
        booking = get_booking_by_id(booking_id)
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {
                'status': 'Rejected',
                'approvedBy': current_user,
                'approvedAt': datetime.utcnow()
            }}
        )
        
        return jsonify({'message': 'Booking rejected successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

# ==================== CALENDAR EXPORT ROUTES ====================

@app.route('/booking/<booking_id>/ics', methods=['GET'])
@jwt_required(optional=True)
def download_booking_ics(booking_id):
    try:
        booking = get_booking_by_id(booking_id)
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        ics_data = generate_ics_for_booking(booking)
        
        return send_file(
            BytesIO(ics_data),
            mimetype='text/calendar',
            as_attachment=True,
            download_name=f"booking_{booking_id}.ics"
        )
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@app.route('/bookings/export/ics', methods=['POST'])
@jwt_required(optional=True)
def export_multiple_ics():
    try:
        data = request.get_json()
        booking_ids = data.get('booking_ids', [])
        
        if not booking_ids:
            return jsonify({'message': 'No booking IDs provided'}), 400
        
        db = get_database()
        cal = Calendar()
        cal.add('prodid', '-//CIET Hall Booking//ciet.edu.in//')
        cal.add('version', '2.0')
        
        for booking_id in booking_ids:
            booking = get_booking_by_id(booking_id)
            if booking:
                event = Event()
                event.add('uid', f"{booking['_id']}@ciet.edu.in")
                event.add('dtstamp', datetime.utcnow())
                
                booking_date = datetime.strptime(booking['date'], '%Y-%m-%d')
                if booking['time'] == 'FN':
                    start_time = booking_date.replace(hour=9, minute=0)
                    end_time = booking_date.replace(hour=13, minute=0)
                elif booking['time'] == 'AN':
                    start_time = booking_date.replace(hour=14, minute=0)
                    end_time = booking_date.replace(hour=18, minute=0)
                else:
                    start_time = booking_date.replace(hour=9, minute=0)
                    end_time = booking_date.replace(hour=18, minute=0)
                
                event.add('dtstart', start_time)
                event.add('dtend', end_time)
                event.add('summary', f"Hall Booking: {booking['hall']}")
                event.add('description', f"Dept: {booking['department']}\nPurpose: {booking['purpose']}")
                event.add('location', booking['hall'])
                
                cal.add_component(event)
        
        ics_data = cal.to_ical()
        
        return send_file(
            BytesIO(ics_data),
            mimetype='text/calendar',
            as_attachment=True,
            download_name='bookings_export.ics'
        )
    
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'CIET Hall Booking API is running'}), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'message': 'Internal server error'}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
