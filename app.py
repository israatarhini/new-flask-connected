from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_mysqldb import MySQL
import os

# Load .env variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Secret Key (if needed)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

@app.route('/')
def home():
    return jsonify({"message": "Flask API is running!"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if email == "test@example.com" and password == "123456":
        return jsonify({"status": "success", "message": "Login successful"})
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/api/profile', methods=['GET'])
def get_profile():
    return jsonify({"data": { "firstName" : "Zahraa", "Major": "CSC"}})

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"data": ["Apple", "Banana", "Cherry"]})

if __name__ == '__main__':
    from os import getenv
    app.run(debug=True, host="127.0.0.1", port=5000)
