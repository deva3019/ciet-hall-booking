import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ciet_hall_booking')
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:5000',
        'http://localhost:8000',
        'http://127.0.0.1:5000',
        'http://127.0.0.1:3000',
        'https://netlify-deploy.com',
        'https://*.onrender.com'
    ]

def get_mongo_client():
    try:
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ MongoDB Atlas connected!")
        return client
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise

def get_database():
    client = get_mongo_client()
    return client['ciet_hall_booking']

def init_db():
    db = get_database()
    db.users.create_index('username', unique=True)
    db.users.create_index('email', unique=True)
    db.bookings.create_index([('date', 1), ('time', 1), ('hall', 1)])
    db.bookings.create_index('createdBy')
    db.bookings.create_index('status')
    db.bookings.create_index('createdAt')
    print("✅ Database indexes created!")
