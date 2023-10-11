import requests
import random

# Define the URL of your Flask application's /hook endpoint
url = 'http://127.0.0.1:5000/hook'  # Change the URL as needed

# Generate 1000 random integers to simulate the requests
integers = [random.randint(1, 3) for _ in range(5)]

# Send 1000 POST requests to the /hook endpoint
for integer in integers:
    data = {'integer': integer}
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print(f"Enqueued: {integer}")
    else:
        print(f"Failed to enqueue: {integer}")
