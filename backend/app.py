from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from flask_cors import CORS
import requests
import threading
import time

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins="http://localhost:3000")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class APIResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database
with app.app_context():
    db.create_all()

# Helper Function to Invoke API
def invoke_api(api_url, frequency, duration):
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=duration)

    while datetime.utcnow() < end_time:
        try:
            print(f"Fetching from API: {api_url}")
            response = requests.get(api_url, timeout=10)  # Timeout added
            if response.status_code == 200:
                print(f"API Response: {response.text}")
                new_response = APIResponse(response=response.text)
                db.session.add(new_response)
                db.session.commit()
                print("Data saved to database successfully")
            else:
                print(f"API returned non-200 status code: {response.status_code}")
        except Exception as e:
            print(f"Error while invoking API: {e}")
        finally:
            time.sleep(3600 / frequency)  # Wait for the next invocation

# Route to Start Invocation
@app.route('/start-invocation', methods=['POST'])
def start_invocation():
    data = request.json
    api_url = data.get('api_url')
    frequency = int(data.get('frequency'))
    duration = int(data.get('duration'))

    if not api_url or not frequency or not duration:
        return jsonify({'error': 'All fields are required'}), 400

    # Start API invocation in a separate thread
    thread = threading.Thread(target=invoke_api, args=(api_url, frequency, duration))
    thread.start()

    return jsonify({'message': 'API invocation started successfully'}), 200

# Route to View Responses
@app.route('/responses', methods=['GET'])
def get_responses():
    responses = APIResponse.query.all()
    return jsonify([
        {'id': r.id, 'response': r.response, 'timestamp': r.timestamp} 
        for r in responses
    ])

# Server start karna
if __name__ == '__main__':
    app.run(debug=True)
