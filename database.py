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

def create_connection():
    """Create a database connection to the SQLite database"""
    conn = sqlite3.connect('travel.db')
    conn.row_factory = sqlite3.Row 
    return conn

def get_user(telegram_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(telegram_id, first_name, last_name=None, phone_number=None):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (telegram_id, first_name, last_name, phone_number) VALUES (?, ?, ?, ?)",
        (telegram_id, first_name, last_name, phone_number)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def update_user_phone(telegram_id, phone_number):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone_number = ? WHERE telegram_id = ?", (phone_number, telegram_id))
    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def register_driver(user_id, experience, car_license, car_model, car_year, car_id, car_photo=None):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO drivers (user_id, experience, car_license, car_model, car_year, car_id, car_photo) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, experience, car_license, car_model, car_year, car_id, car_photo)
    )
    driver_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return driver_id

def update_driver_car_photo(driver_id, car_photo):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE drivers SET car_photo = ? WHERE id = ?", (car_photo, driver_id))
    conn.commit()
    conn.close()

def get_driver_by_user_id(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drivers WHERE user_id = ?", (user_id,))
    driver = cursor.fetchone()
    conn.close()
    return dict(driver) if driver else None

def get_driver_by_id(driver_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, u.first_name, u.last_name, u.phone_number
        FROM drivers d
        JOIN users u ON d.user_id = u.id
        WHERE d.id = ?
    """, (driver_id,))
    driver = cursor.fetchone()
    conn.close()
    return dict(driver) if driver else None

def create_poster(driver_id, from_location, to_location, price, seat_count, time_to_go, bags_count, 
                 from_latitude=None, from_longitude=None, to_latitude=None, to_longitude=None):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO posters 
           (driver_id, from_location, to_location, price, seat_count, time_to_go, bags_count, is_active,
            from_latitude, from_longitude, to_latitude, to_longitude) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (driver_id, from_location, to_location, price, seat_count, time_to_go, bags_count, True,
         from_latitude, from_longitude, to_latitude, to_longitude)
    )
    poster_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return poster_id

def update_poster(poster_id, from_location=None, to_location=None, price=None, seat_count=None, 
                 time_to_go=None, bags_count=None, is_active=None, from_latitude=None, 
                 from_longitude=None, to_latitude=None, to_longitude=None):
    conn = create_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if from_location is not None:
        updates.append("from_location = ?")
        params.append(from_location)
    if to_location is not None:
        updates.append("to_location = ?")
        params.append(to_location)
    if price is not None:
        updates.append("price = ?")
        params.append(price)
    if seat_count is not None:
        updates.append("seat_count = ?")
        params.append(seat_count)
    if time_to_go is not None:
        updates.append("time_to_go = ?")
        params.append(time_to_go)
    if bags_count is not None:
        updates.append("bags_count = ?")
        params.append(bags_count)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(is_active)
    if from_latitude is not None:
        updates.append("from_latitude = ?")
        params.append(from_latitude)
    if from_longitude is not None:
        updates.append("from_longitude = ?")
        params.append(from_longitude)
    if to_latitude is not None:
        updates.append("to_latitude = ?")
        params.append(to_latitude)
    if to_longitude is not None:
        updates.append("to_longitude = ?")
        params.append(to_longitude)
    
    if updates:
        query = f"UPDATE posters SET {', '.join(updates)} WHERE id = ?"
        params.append(poster_id)
        
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()
    return cursor.rowcount > 0

def cancel_poster(poster_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE posters SET is_active = 0 WHERE id = ?", (poster_id,))
    result = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return result

def get_active_posters():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, d.car_model, d.car_photo, u.first_name, u.last_name 
        FROM posters p
        JOIN drivers d ON p.driver_id = d.id
        JOIN users u ON d.user_id = u.id
        WHERE p.is_active = 1
    """)
    posters = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posters

def get_driver_posters(driver_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, 
               (SELECT COUNT(*) FROM orders WHERE poster_id = p.id AND is_active = 1) as order_count
        FROM posters p
        WHERE p.driver_id = ?
        ORDER BY p.time_to_go DESC
    """, (driver_id,))
    posters = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posters

def get_poster_by_id(poster_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, d.car_model, d.car_photo, u.first_name, u.last_name, u.phone_number,
               d.id as driver_id, u.id as user_id
        FROM posters p
        JOIN drivers d ON p.driver_id = d.id
        JOIN users u ON d.user_id = u.id
        WHERE p.id = ?
    """, (poster_id,))
    poster = cursor.fetchone()
    conn.close()
    return dict(poster) if poster else None

def create_order(poster_id, user_id, seat_count, baggage_weight=0):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO orders 
           (poster_id, user_id, seat_count, is_active, baggage_weight, status) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (poster_id, user_id, seat_count, True, baggage_weight, 'pending')
    )
    
    cursor.execute(
        "UPDATE posters SET seat_count = seat_count - ? WHERE id = ?",
        (seat_count, poster_id)
    )
    
    cursor.execute(
        "UPDATE posters SET is_active = 0 WHERE id = ? AND seat_count <= 0",
        (poster_id,)
    )
    
    order_id = cursor.lastrowid
    
    cursor.execute("""
        SELECT d.user_id
        FROM posters p
        JOIN drivers d ON p.driver_id = d.id
        WHERE p.id = ?
    """, (poster_id,))
    driver_data = cursor.fetchone()
    
    if driver_data:
        cursor.execute(
            """INSERT INTO notifications (user_id, message, type, reference_id)
               VALUES (?, ?, ?, ?)""",
            (driver_data['user_id'], f"New booking for your ride!", "new_booking", order_id)
        )
    
    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id, status, cancel_reason=None):
    conn = create_connection()
    cursor = conn.cursor()
    
    if status == 'cancelled' and cancel_reason:
        cursor.execute(
            "UPDATE orders SET status = ?, cancel_reason = ? WHERE id = ?",
            (status, cancel_reason, order_id)
        )
    else:
        cursor.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id)
        )
    
    if status == 'cancelled':
        cursor.execute("""
            SELECT o.seat_count, o.poster_id
            FROM orders o
            WHERE o.id = ? AND o.is_active = 1
        """, (order_id,))
        order_data = cursor.fetchone()
        
        if order_data:
            cursor.execute(
                "UPDATE posters SET seat_count = seat_count + ? WHERE id = ?",
                (order_data['seat_count'], order_data['poster_id'])
            )
            
            cursor.execute(
                "UPDATE posters SET is_active = 1 WHERE id = ?",
                (order_data['poster_id'],)
            )
            
            cursor.execute(
                "UPDATE orders SET is_active = 0 WHERE id = ?",
                (order_id,)
            )
            
            cursor.execute("""
                SELECT o.user_id, p.driver_id 
                FROM orders o
                JOIN posters p ON o.poster_id = p.id
                JOIN drivers d ON p.driver_id = d.id
                WHERE o.id = ?
            """, (order_id,))
            data = cursor.fetchone()
            
            if data:
                cursor.execute("SELECT user_id FROM drivers WHERE id = ?", (data['driver_id'],))
                driver_data = cursor.fetchone()
                
                if driver_data:
                    cursor.execute(
                        """INSERT INTO notifications (user_id, message, type, reference_id)
                           VALUES (?, ?, ?, ?)""",
                        (driver_data['user_id'], f"A booking has been cancelled", "booking_cancelled", order_id)
                    )
    
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def get_user_orders(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, p.from_location, p.to_location, p.time_to_go, p.price, 
               u_driver.first_name as driver_first_name, u_driver.last_name as driver_last_name,
               u_driver.phone_number as driver_phone, d.id as driver_id, p.id as poster_id
        FROM orders o
        JOIN posters p ON o.poster_id = p.id
        JOIN drivers d ON p.driver_id = d.id
        JOIN users u_driver ON d.user_id = u_driver.id
        WHERE o.user_id = ? AND o.is_active = 1
        ORDER BY p.time_to_go ASC
    """, (user_id,))
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders

def get_poster_orders(poster_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, u.first_name, u.last_name, u.phone_number
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.poster_id = ? AND o.is_active = 1
        ORDER BY o.id ASC
    """, (poster_id,))
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders

def get_order_by_id(order_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, p.from_location, p.to_location, p.time_to_go, p.price, 
               u.first_name, u.last_name, u.phone_number,
               driver.id as driver_id, u_driver.id as driver_user_id
        FROM orders o
        JOIN posters p ON o.poster_id = p.id
        JOIN users u ON o.user_id = u.id
        JOIN drivers driver ON p.driver_id = driver.id
        JOIN users u_driver ON driver.user_id = u_driver.id
        WHERE o.id = ?
    """, (order_id,))
    order = cursor.fetchone()
    conn.close()
    return dict(order) if order else None

def save_message(sender_id, receiver_id, poster_id, message_text):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO messages (sender_id, receiver_id, poster_id, message_text)
           VALUES (?, ?, ?, ?)""",
        (sender_id, receiver_id, poster_id, message_text)
    )
    message_id = cursor.lastrowid
    
    cursor.execute(
        """INSERT INTO notifications (user_id, message, type, reference_id)
           VALUES (?, ?, ?, ?)""",
        (receiver_id, f"New message received", "new_message", message_id)
    )
    
    conn.commit()
    conn.close()
    return message_id

def get_chat_messages(user1_id, user2_id, poster_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, 
               sender.first_name as sender_name,
               receiver.first_name as receiver_name
        FROM messages m
        JOIN users sender ON m.sender_id = sender.id
        JOIN users receiver ON m.receiver_id = receiver.id
        WHERE ((m.sender_id = ? AND m.receiver_id = ?) OR 
               (m.sender_id = ? AND m.receiver_id = ?))
              AND m.poster_id = ?
        ORDER BY m.sent_at ASC
    """, (user1_id, user2_id, user2_id, user1_id, poster_id))
    messages = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        UPDATE messages
        SET is_read = 1
        WHERE receiver_id = ? AND sender_id = ? AND poster_id = ? AND is_read = 0
    """, (user1_id, user2_id, poster_id))
    
    conn.commit()
    conn.close()
    return messages

def get_user_notifications(user_id, limit=10):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    notifications = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notifications
    print("⚠️ Огоҳӣ илова шуд барои user_id=", receiver_id)


def mark_notification_read(notification_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()

def create_notification_for_ride_changes(poster_id, message):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT user_id
        FROM orders
        WHERE poster_id = ? AND is_active = 1
    """, (poster_id,))
    users = cursor.fetchall()
    
    for user in users:
        cursor.execute(
            """INSERT INTO notifications (user_id, message, type, reference_id)
               VALUES (?, ?, ?, ?)""",
            (user['user_id'], message, "ride_change", poster_id)
        )
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
    print("Database initialized successfully.")