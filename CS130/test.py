import requests
import random

# Define the URL of your app's /hook endpoint
url = 'http://127.0.0.1:5000/hook'  # Change the URL as needed

# Generate 1000 random integers to simulate the requests
integers = [random.randint(1, 1000) for _ in range(1000)]

# Send 1000 POST requests to the /hook endpoint
for integer in integers:
    data = {'integer': integer}
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print(f"Enqueued: {integer}")
    else:
        print(f"Failed to enqueue: {integer}")
