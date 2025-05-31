from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_mysqldb import MySQL
import os

# Load .env variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# MySQL configurations
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')          # e.g. trolley.proxy.rlwy.net
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')          # e.g. root
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')  # your Railway password
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')              # e.g. railway
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))  # e.g. 10655

mysql = MySQL(app)

@app.route('/')
def home():
    return jsonify({"message": "Flask API is running!"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    cur = mysql.connection.cursor()
    query = "SELECT * FROM users WHERE email = %s AND password = %s"
    cur.execute(query, (email, password))
    user = cur.fetchone()
    cur.close()

    if user:
        return jsonify({"status": "success", "message": "Login successful"})
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/api/profile', methods=['GET'])
def get_profile():
    return jsonify({"data": {"firstName": "Zahraa", "Major": "CSC"}})

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"data": ["Apple", "Banana", "Cherry"]})

@app.route('/api/save-name', methods=['POST'])
def save_name():
    name = request.form.get('name')  # Reading form field 'name' from Android app

    if not name:
        return jsonify({"status": "error", "message": "Name is required"}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO table1 (name) VALUES (%s)", (name,))
        mysql.connection.commit()
        cur.close()
        return jsonify({"status": "success", "message": "Name saved successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
