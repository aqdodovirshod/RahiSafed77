import sqlite3
from datetime import datetime

def setup_database():
    """Create database tables if they don't exist"""
    conn = sqlite3.connect('travel.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            phone_number VARCHAR(255),
            telegram_id BIGINT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY,
            experience INTEGER,
            car_license VARCHAR(255),
            car_photo VARCHAR(255),
            car_model VARCHAR(255),
            car_year INTEGER,
            car_id VARCHAR(255),
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posters (
            id INTEGER PRIMARY KEY,
            from_location VARCHAR(255),
            to_location VARCHAR(255),
            price DECIMAL(10, 2),
            seat_count INTEGER,
            time_to_go TIMESTAMP,
            bags_count INTEGER,
            driver_id INTEGER,
            is_active BOOLEAN,
            from_latitude REAL,
            from_longitude REAL,
            to_latitude REAL,
            to_longitude REAL,
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            poster_id INTEGER,
            user_id INTEGER,
            seat_count INTEGER,
            is_active BOOLEAN,
            baggage_weight INTEGER DEFAULT 0,
            status VARCHAR(50) DEFAULT 'pending',
            cancel_reason TEXT,
            FOREIGN KEY (poster_id) REFERENCES posters (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            sender_id INTEGER,
            receiver_id INTEGER,
            poster_id INTEGER,
            message_text TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id),
            FOREIGN KEY (poster_id) REFERENCES posters (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            message TEXT,
            type VARCHAR(50),
            reference_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database setup completed!")