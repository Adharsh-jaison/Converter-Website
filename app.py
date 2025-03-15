from flask import Flask, request, jsonify
from datetime import datetime
import pytz
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('conversions.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, email TEXT, timestamp TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS conversions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  from_tz TEXT,
                  to_tz TEXT,
                  converted_time TEXT,
                  timestamp TEXT)''')
    
    # New table for unit conversions
    c.execute('''CREATE TABLE IF NOT EXISTS unit_conversions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  conversion_type TEXT,
                  from_unit TEXT,
                  to_unit TEXT,
                  input_value REAL,
                  converted_value REAL,
                  timestamp TEXT)''')
    
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

# Store user data after Google Sign-In
@app.route('/store_user', methods=['POST'])
def store_user():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')  # Optional: Store email if available
        timestamp = datetime.now().isoformat()

        if not username:
            return jsonify({'error': 'Username is required'}), 400

        conn = sqlite3.connect('conversions.db')
        c = conn.cursor()
        
        # Insert or update user data
        c.execute('''INSERT OR IGNORE INTO users (username, email, timestamp)
                     VALUES (?, ?, ?)''', (username, email, timestamp))
        
        conn.commit()
        conn.close()

        return jsonify({'message': 'User data stored successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Store conversion history
@app.route('/store_conversion', methods=['POST'])
def store_conversion():
    try:
        data = request.json
        username = data.get('username')
        from_tz = data.get('from_tz')
        to_tz = data.get('to_tz')
        converted_time = data.get('converted_time')
        timestamp = datetime.now().isoformat()

        if not username or not from_tz or not to_tz or not converted_time:
            return jsonify({'error': 'Missing required parameters'}), 400

        conn = sqlite3.connect('conversions.db')
        c = conn.cursor()
        
        # Insert conversion history
        c.execute('''INSERT INTO conversions (username, from_tz, to_tz, converted_time, timestamp)
                     VALUES (?, ?, ?, ?, ?)''',
                  (username, from_tz, to_tz, converted_time, timestamp))
        
        conn.commit()
        conn.close()

        return jsonify({'message': 'Conversion history stored successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Store unit conversion history
@app.route('/store_unit_conversion', methods=['POST'])
def store_unit_conversion():
    try:
        data = request.json
        username = data.get('username')
        conversion_type = data.get('conversion_type')
        from_unit = data.get('from_unit')
        to_unit = data.get('to_unit')
        input_value = data.get('input_value')
        converted_value = data.get('converted_value')
        timestamp = datetime.now().isoformat()

        if not username or not conversion_type or not from_unit or not to_unit or not input_value or not converted_value:
            return jsonify({'error': 'Missing required parameters'}), 400

        conn = sqlite3.connect('conversions.db')
        c = conn.cursor()
        
        # Insert unit conversion history
        c.execute('''INSERT INTO unit_conversions (username, conversion_type, from_unit, to_unit, input_value, converted_value, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (username, conversion_type, from_unit, to_unit, input_value, converted_value, timestamp))
        
        conn.commit()
        conn.close()

        return jsonify({'message': 'Unit conversion history stored successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get user-specific conversion history
@app.route('/get_conversion_history', methods=['GET'])
def get_conversion_history():
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400

        conn = sqlite3.connect('conversions.db')
        c = conn.cursor()
        
        # Fetch conversion history for the user
        c.execute('''SELECT from_tz, to_tz, converted_time, timestamp
                     FROM conversions
                     WHERE username = ?''', (username,))
        
        user_history = [{'from_tz': row[0], 'to_tz': row[1], 'converted_time': row[2], 'timestamp': row[3]}
                        for row in c.fetchall()]
        
        conn.close()

        return jsonify({'conversion_history': user_history}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get user-specific unit conversion history
@app.route('/get_unit_conversion_history', methods=['GET'])
def get_unit_conversion_history():
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400

        conn = sqlite3.connect('conversions.db')
        c = conn.cursor()
        
        # Fetch unit conversion history for the user
        c.execute('''SELECT conversion_type, from_unit, to_unit, input_value, converted_value, timestamp
                     FROM unit_conversions
                     WHERE username = ?''', (username,))
        
        user_history = [{'conversion_type': row[0], 'from_unit': row[1], 'to_unit': row[2], 'input_value': row[3], 'converted_value': row[4], 'timestamp': row[5]}
                        for row in c.fetchall()]
        
        conn.close()

        return jsonify({'unit_conversion_history': user_history}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Timezone conversion endpoint
@app.route('/convert', methods=['GET'])
def convert_timezone():
    try:
        dt_str = request.args.get('datetime')  # Expected format: 'YYYY-MM-DD HH:MM:SS'
        from_tz = request.args.get('from_tz')
        to_tz_list = request.args.getlist('to_tz')

        if not dt_str or not from_tz or not to_tz_list:
            return jsonify({'error': 'Missing required parameters'}), 400

        # Parse datetime string
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        
        # Convert to source timezone
        from_timezone = pytz.timezone(from_tz)
        dt = from_timezone.localize(dt)

        # Convert to target timezones
        converted_times = []
        for to_tz in to_tz_list:
            to_timezone = pytz.timezone(to_tz)
            converted_dt = dt.astimezone(to_timezone)
            converted_times.append({
                'converted_datetime': converted_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'converted_timezone': to_tz
            })

        return jsonify({
            'original_datetime': dt_str,
            'original_timezone': from_tz,
            'converted_times': converted_times
        })

    except pytz.exceptions.UnknownTimeZoneError:
        return jsonify({'error': 'Invalid timezone'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Home route
@app.route('/')
def home():
    return "Timezone Converter Backend is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)