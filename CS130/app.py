from flask import Flask, request, render_template, jsonify, Response
from flask_sse import sse
import threading
import queue
import sqlite3
import time
import math
import json
import logging
from threading import Thread

app = Flask(__name__, static_url_path='/static') 
enqueue_count = 0
new_data = []

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Create a queue to hold incoming requests
request_queue = queue.Queue()

# Create a connection to the SQLite database
conn = sqlite3.connect('request_log.db')
cursor = conn.cursor()

# Create a table to store processed requests
cursor.execute('''
    CREATE TABLE IF NOT EXISTS request_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input TEXT,  -- Change data type to TEXT
        result TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Commit and close the database connection
conn.commit()
conn.close()

def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)

def process_queue():
    while True:
        if not request_queue.empty():
            data = request_queue.get()
            result = math.factorial(data)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

            try:
                # Log the processed request to the SQLite database
                db_connection = sqlite3.connect('request_log.db')
                db_cursor = db_connection.cursor()
                db_cursor.execute("INSERT INTO request_log (input, result, timestamp) VALUES (?, ?, ?)",
                                  (str(data), result, timestamp))
                db_connection.commit()
                db_cursor.close()
                db_connection.close()
            except Exception as e:
                app.logger.error(f"Error inserting into database: {str(e)}")

def generate_updates():
    while True:
        if new_data:
            yield bytes(jsonify(new_data.pop(0)).get_data())  # Send the oldest data
        else:
            time.sleep(1)  # Introduce a delay before checking again

# Clear the database upon app startup
def clear_database():
    print("Clearing database")  # Add this line for debugging
    conn = sqlite3.connect('request_log.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM request_log')
    conn.commit()
    conn.close()

def create_table():
    conn = sqlite3.connect('request_log.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS request_log (
        id TEXT PRIMARY KEY,
        input TEXT,
        result TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

# Clear the request log
@app.route('/clear-log', methods=['POST'])
def clear_log():
    conn = sqlite3.connect('request_log.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM request_log')
    conn.commit()
    conn.close()
    return 'Request log cleared', 200

@app.route('/')
def index():
    return render_template('index.html')

# SQLite database connection pool
db_connection_pool = sqlite3.connect('request_log.db', check_same_thread=False)

@app.route('/hook', methods=['POST'])
def hook():
    try:
        data = request.get_json()

        if data is None:
            return 'Invalid JSON data', 400

        if 'number' in data:
            integer = data['number']

            # Decide whether to store as INTEGER or TEXT based on a threshold
            if integer <= 2147483647:  # SQLite maximum INTEGER value
                result = integer
            else:
                result = str(integer)

            # Insert data into the SQLite database
            with db_connection_pool:
                cursor = db_connection_pool.cursor()
                cursor.execute("INSERT INTO request_log (input, result, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)", (integer, result))

            return 'Enqueued', 200
        else:
            return 'Missing integer field', 400
    except Exception as e:
        app.logger.error(f"Error in /hook: {str(e)}")
        return 'Internal Server Error', 500

@app.route('/log')
def log():
    # Retrieve data from the SQLite database
    with db_connection_pool:
        cursor = db_connection_pool.cursor()
        cursor.execute("SELECT input, timestamp FROM request_log ORDER BY timestamp DESC LIMIT 100")
        data = cursor.fetchall()

    return render_template('index.html', data=data)

@app.route('/updates')
def sse_updates():
    def event_stream():
        conn = sqlite3.connect('request_log.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, input, result, timestamp FROM request_log ORDER BY timestamp ASC')
        data = cursor.fetchall()
        conn.close()

        for row in data:
            event = {
                'id': row[0],
                'input': row[1],
                'result': row[2],
                'timestamp': row[3]
            }
            yield 'data: ' + json.dumps(event) + '\n\n'

    return Response(event_stream(), content_type='text/event-stream')


@app.route('/clear-data', methods=['POST'])
def clear_data():
    conn = sqlite3.connect('request_log.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM request_log')
    conn.commit()
    conn.close()
    return 'Data cleared', 200

@app.route('/clear-on-refresh', methods=['GET'])
def clear_on_refresh():
    # Clear the request log
    conn = sqlite3.connect('request_log.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM request_log')
    conn.commit()
    conn.close()
 
    return 'Data cleared on page refresh', 200

@app.after_request
def add_no_cache_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Implement the factorial function as needed
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)


if __name__ == '__main__':
    # Create and start a thread for processing the queue
    processing_thread = threading.Thread(target=process_queue)
    processing_thread.start()

    # Start the Flask web application
    app.run(host="0.0.0.0", port=80, threaded=True)
