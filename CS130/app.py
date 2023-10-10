from flask import Flask, request, render_template, jsonify
import threading
import queue
import sqlite3
import time
import math
import json
import logging
from threading import Thread

app = Flask(__name__)
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
        input INTEGER,
        result INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Commit and close the database connection
conn.commit()
conn.close()

def process_queue():
    while True:
        if not request_queue.empty():
            data = request_queue.get()
            result = math.factorial(data)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

            try:
                # Log the processed request to the SQLite database as text
                db_connection = sqlite3.connect('database.db')
                db_cursor = db_connection.cursor()
                db_cursor.execute("INSERT INTO requests (input, result, timestamp) VALUES (?, ?, ?)",
                                  (str(data), str(result), timestamp))
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

@app.route('/updates')
def generate_updates():
    def event_stream():
        last_id = 0
        while True:
            conn = sqlite3.connect('request_log.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, input, result, timestamp FROM request_log WHERE id > ?', (last_id,))
            data = cursor.fetchall()
            conn.close()

            for row in data:
                yield f"data: {json.dumps({'id': row[0], 'input': row[1], 'result': row[2], 'timestamp': row[3]})}\n\n"
                last_id = row[0]

            time.sleep(1)  # Sleep for 1 second before checking for updates again

    return Response(event_stream(), content_type='text/event-stream')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/log')
def log():
    conn = sqlite3.connect('request_log.db')
    cursor = conn.cursor()

    # Retrieve all processed requests from the table
    cursor.execute('SELECT input, result, timestamp FROM request_log ORDER BY timestamp DESC')
    data = cursor.fetchall()

    conn.close()

    # Format the data as a list of dictionaries
    processed_requests = [{'input': row[0], 'result': row[1], 'timestamp': row[2]} for row in data]

    return jsonify(processed_requests)

@app.route('/hook', methods=['POST'])
def hook():
    try:
        data = int(request.json['integer'])
        request_queue.put(data)

        # Calculate the factorial
        result = factorial(data)

        # Insert data into the SQLite table
        conn = sqlite3.connect('request_log.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO request_log (input, result) VALUES (?, ?)', (data, result))
        conn.commit()
        conn.close()

        return 'Enqueued', 200
    except ValueError:
        app.logger.error('Invalid input. Please enter a valid integer.')
        return 'Invalid input. Please enter a valid integer.', 400
    except Exception as e:
        app.logger.error(f"Error handling request: {str(e)}")
        return 'Failed to enqueue', 500

if __name__ == '__main__':
     
    # Create and start a thread for processing the queue
    processing_thread = threading.Thread(target=process_queue)
    processing_thread.start()

    # Initialize the SQLite database table with TEXT data type for input and result
    db_connection = sqlite3.connect('database.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute('''CREATE TABLE IF NOT EXISTS requests 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         input TEXT, 
                         result TEXT, 
                         timestamp TEXT)''')
    db_connection.commit()
    db_cursor.close()
    db_connection.close()

    # Start the Flask web application
    app.run(port=5000)
