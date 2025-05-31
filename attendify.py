from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_mysqldb import MySQL
import os
import traceback


load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

mysql = MySQL(app)

@app.route('/')
def home():
    return jsonify({"message": "Flask API is running!"})

@app.route('/api/save-employee', methods=['POST'])
def save_employee():
    try:
        # STEP 1: Check if JSON was received
        data = request.json
        print("🟡 Received data:", data)

        # STEP 2: Print individual fields
        full_name = data.get('full_name')
        username = data.get('username')
        phone_number = data.get('phone_number')
        email = data.get('email')
        password = data.get('password')
        occupation = data.get('occupation')
        faculty = data.get('faculty')

        print(f"🟡 Parsed fields: Full Name: {full_name}, Username: {username}, Phone: {phone_number}, Email: {email}, Password: {password}, Occupation: {occupation}, Faculty: {faculty}")

        # STEP 3: Execute insert
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO Employee (full_name, username, phone_number, email, password, occupation, faculty)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (full_name, username, phone_number, email, password, occupation, faculty))

        # STEP 4: Print number of affected rows
        print("🟢 Row count after insert:", cur.rowcount)  # Should be 1

        # STEP 5: Commit and close
        mysql.connection.commit()
        cur.close()
        print("🟢 Insert successful and committed to DB")

        # STEP 6: Optional - test select to confirm it exists in DB
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT * FROM Employee ORDER BY empid DESC LIMIT 1")
        new_entry = cur2.fetchone()
        print("🟢 Latest employee in DB:", new_entry)
        cur2.close()

        return jsonify({"message": "Employee added successfully"}), 201

    except Exception as e:
        print("🔴 Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT DATABASE()')  # STEP 7: Check which DB you're connected to
        db_name = cur.fetchone()
        print("🟡 Connected to database:", db_name)
        cur.close()
        return jsonify({"status": "success", "message": "DB connected!", "database": db_name})
    except Exception as e:
        print("🔴 DB connection error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login_employee():
    try:
        data = request.json
        print("🔐 Received login data:", data)

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        cur = mysql.connection.cursor()
        cur.execute("SELECT empid FROM Employee WHERE BINARY username = %s AND BINARY password = %s", (username, password))
        result = cur.fetchone()
        cur.close()

        if result:
            return jsonify({"success": True, "empid": result[0]})
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401

    except Exception as e:
        print("🔴 Login error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get-employee/<int:empid>', methods=['GET'])
def get_employee(empid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT full_name, email FROM Employee WHERE empid = %s", (empid,))
        result = cur.fetchone()
        cur.close()

        if result:
            return jsonify({
                "success": True,
                "full_name": result[0],
                "email": result[1]
            }), 200
        else:
            return jsonify({"success": False, "message": "Employee not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get-employee-full/<int:empid>', methods=['GET'])
def get_employee_full(empid):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT full_name, username, email, phone_number, occupation, faculty, empPhoto
            FROM Employee
            WHERE empid = %s
        """, (empid,))
        row = cur.fetchone()
        cur.close()

        if row:
            # Convert empPhoto (bytes) to base64
            import base64
            # empPhoto_base64 = base64.b64encode(row[6]).decode('utf-8') if row[6] else None

            return jsonify({
                "full_name": row[0],
                "username": row[1],
                "email": row[2],
                "phone_number": row[3],
                "occupation": row[4],
                "faculty": row[5],
                # "empPhoto": empPhoto_base64
            })
        else:
            return jsonify({"error": "Employee not found"}), 404
    except Exception as e:
        print("🔴 Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/checkin', methods=['POST'])
def checkin():
    try:
        data = request.json
        empid = data.get('empid')
        date = data.get('date')
        time = data.get('time')

        cur = mysql.connection.cursor()
        # Insert or update checkin time for the employee on that date
        cur.execute("""
            INSERT INTO attendance (empid, checkinDate, checkinTime)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE checkinTime = VALUES(checkinTime)
        """, (empid, date, time))

        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Check-in saved successfully"}), 201

    except Exception as e:
        print("Check-in error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/checkout', methods=['POST'])
def check_out():
    try:
        data = request.json
        empid = data.get('empid')
        date = data.get('date')
        time = data.get('time')

        if not all([empid, date, time]):
            return jsonify({"error": "Missing required fields"}), 400

        cur = mysql.connection.cursor()

        # Check if a record exists for this employee and checkout date
        cur.execute("SELECT id FROM attendance WHERE empid = %s AND checkoutDate = %s", (empid, date))
        result = cur.fetchone()

        if result:
            # Record exists — update checkoutTime
            cur.execute("UPDATE attendance SET checkoutTime = %s WHERE empid = %s AND checkoutDate = %s",
                        (time, empid, date))
        else:
            # No record — insert new row
            cur.execute("INSERT INTO attendance (empid, checkoutDate, checkoutTime) VALUES (%s, %s, %s)",
                        (empid, date, time))

        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Check-out saved"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/coffee-break', methods=['POST'])
def save_coffee_break():
    try:
        data = request.json
        empid = data.get('empid')
        time = data.get('time')
        date = data.get('date')

        if not all([empid, time, date]):
            return jsonify({"error": "Missing required fields"}), 400

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO schedule (start_coffee_break, break_date, empid)
            VALUES (%s, %s, %s)
        """, (time, date, empid))

        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Coffee break saved successfully"}), 201

    except Exception as e:
        print("Coffee break error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/get-all-employees', methods=['GET'])
def get_all_employees():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT empid, full_name, email, username, phone_number, occupation, faculty FROM Employee")
        rows = cur.fetchall()
        cur.close()

        employees = []
        for row in rows:
            employees.append({
                "empid": row[0],
                "full_name": row[1],
                "email": row[2],
                "username": row[3],
                "phone_number": row[4],
                "occupation": row[5],
                "faculty": row[6]
            })

        return jsonify({"employees": employees}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/submit-leave', methods=['POST'])
def submit_leave():
    try:
        data = request.json
        empid = data.get('empid')
        start_date = data.get('leave_start_date')
        end_date = data.get('leave_end_date')
        status = data.get('status')
        leave_type = data.get('leave_type')

        cur = mysql.connection.cursor()
        
        # Insert into main leave_request table
        cur.execute("""
            INSERT INTO leave_request (empid, leave_start_date, leave_end_date, status, leave_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (empid, start_date, end_date, status, leave_type))
        
        # Insert into specific leave type table
        if leave_type == 'annual leave':
            cur.execute("""
                INSERT INTO annual_leave (empid, leave_start_date, leave_end_date, status, leave_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (empid, start_date, end_date, status, leave_type))
        elif leave_type == 'sick leave':
            cur.execute("""
                INSERT INTO sick_leave (empid, leave_start_date, leave_end_date, status, leave_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (empid, start_date, end_date, status, leave_type))
        elif leave_type == 'maternity leave':
            cur.execute("""
                INSERT INTO maternity_leave (empid, leave_start_date, leave_end_date, status, leave_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (empid, start_date, end_date, status, leave_type))
        elif leave_type == 'bereavement leave':
            cur.execute("""
                INSERT INTO bereavement_leave (empid, leave_start_date, leave_end_date, status, leave_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (empid, start_date, end_date, status, leave_type))

        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Leave request submitted successfully"}), 201

    except Exception as e:
        print("🔴 Leave submission error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/leave-count/<int:empid>', methods=['GET'])
def get_leave_counts(empid):
    try:
        cur = mysql.connection.cursor()

        # Query to count leaves from each table
        queries = {
            'annual_leave': "SELECT COUNT(*) FROM annual_leave WHERE empid = %s",
            'sick_leave': "SELECT COUNT(*) FROM sick_leave WHERE empid = %s",
            'maternity_leave': "SELECT COUNT(*) FROM maternity_leave WHERE empid = %s",
            'bereavement_leave': "SELECT COUNT(*) FROM bereavement_leave WHERE empid = %s"
        }

        results = {}
        for leave_type, query in queries.items():
            cur.execute(query, (empid,))
            count = cur.fetchone()[0]
            results[leave_type] = count

        cur.close()

        return jsonify({
            "success": True,
            "empid": empid,
            "leave_counts": results
        }), 200

    except Exception as e:
        print("🔴 Error in get_leave_counts:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/leave-count', methods=['GET'])
def get_leave_count_by_employee():
    emp_id = request.args.get('empId')
    status = request.args.get('status')

    if not emp_id or not status:
        return jsonify({'error': 'Missing empId or status'}), 400

    leave_types = ["Annual Leave", "Sick Leave", "Maternity Leave", "Bereavement Leave"]
    leave_counts = []

    try:
        cur = mysql.connection.cursor()
        for leave_type in leave_types:
            cur.execute(
                "SELECT COUNT(*) FROM leave_request WHERE empid = %s AND leave_type = %s AND status = %s",
                (emp_id, leave_type, status)
            )
            result = cur.fetchone()
            count = result[0] if result else 0
            leave_counts.append(f"{leave_type}: {count} requests ({status})")
        cur.close()
        return jsonify(leave_counts)

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/total-count', methods=['GET'])
def total_count():
    employee_id = request.args.get('employeeId', type=int)
    status = request.args.get('status')

    if employee_id is None or not status:
        return jsonify({"error": "Missing required query parameters: employeeId and status"}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM leave_request WHERE empid = %s AND status = %s",
            (employee_id, status)
        )
        count = cur.fetchone()[0]
        cur.close()

        return jsonify({
            "count": count,  # ← change here
            "success": True,
            "employeeId": employee_id,
            "status": status
        }), 200


    except Exception as e:
        print("🔴 Error in total_count:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pending-leave-requests', methods=['GET'])
def get_pending_leave_requests():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT 
                lr.request_id, lr.empid, e.full_name, 
                lr.leave_start_date, lr.leave_end_date, 
                lr.status, lr.leave_type
            FROM 
                leave_request lr
            JOIN 
                Employee e ON lr.empid = e.empid
            WHERE 
                lr.status = 'pending'
        """)
        rows = cur.fetchall()
        cur.close()

        leave_requests = []
        for row in rows:
            leave_requests.append({
                "requestId": row[0],
                "empId": row[1],
                "employeeName": row[2],
                "leaveStartDate": row[3],
                "leaveEndDate": row[4],
                "status": row[5],
                "leaveType": row[6],
            })

        return jsonify(leave_requests), 200

    except Exception as e:
        print("🔴 Error retrieving pending leave requests:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/update-leave-status', methods=['POST'])
def update_leave_status():
    try:
        data = request.json
        leave_id = data.get('leave_id')
        new_status = data.get('status')
        leave_type = data.get('leave_type')

        cur = mysql.connection.cursor()

        # Update the main leave_request table
        cur.execute("""
            UPDATE leave_request SET status = %s WHERE request_id = %s
        """, (new_status, leave_id))

        # Update the corresponding leave type table
        if leave_type == 'annual leave':
            cur.execute("""
                UPDATE annual_leave SET status = %s WHERE id = %s
            """, (new_status, leave_id))
        elif leave_type == 'sick leave':
            cur.execute("""
                UPDATE sick_leave SET status = %s WHERE id = %s
            """, (new_status, leave_id))
        elif leave_type == 'maternity leave':
            cur.execute("""
                UPDATE maternity_leave SET status = %s WHERE id = %s
            """, (new_status, leave_id))
        elif leave_type == 'bereavement leave':
            cur.execute("""
                UPDATE bereavement_leave SET status = %s WHERE id = %s
            """, (new_status, leave_id))

        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Leave status updated successfully"}), 200

    except Exception as e:
        print("🔴 Error in updating leave status:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/leave-dates', methods=['GET'])
def get_leave_dates():
    empid = request.args.get('empid')  # 🔽 Get empid from query string

    if not empid:
        return jsonify({"error": "empid is required"}), 400

    try:
        cur = mysql.connection.cursor()

        # ✅ Fetch accepted leaves only for the logged-in employee
        cur.execute("SELECT empid, leave_start_date, leave_end_date FROM leave_request WHERE status = 'accepted' AND empid = %s", (empid,))
        rows = cur.fetchall()
        cur.close()

        leave_data = []
        for row in rows:
            leave_data.append({
                "empid": row[0],
                "leave_start_date": row[1],
                "leave_end_date": row[2]
            })

        return jsonify({"leave_dates": leave_data}), 200

    except Exception as e:
        print("🔴 Error in get_leave_dates:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/update-employee/<int:empid>', methods=['PUT'])
def update_employee(empid):
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        full_name = data.get('full_name')
        username = data.get('username')
        email = data.get('email')
        phone_number = data.get('phone_number')
        occupation = data.get('occupation')
        faculty = data.get('faculty')

        # Validate required fields if you want (optional)
        # For example, check if full_name or username is missing

        cur = mysql.connection.cursor()

        # Update statement
        update_query = """
            UPDATE Employee
            SET full_name = %s,
                username = %s,
                email = %s,
                phone_number = %s,
                occupation = %s,
                faculty = %s
            WHERE empid = %s
        """

        cur.execute(update_query, (full_name, username, email, phone_number, occupation, faculty, empid))
        mysql.connection.commit()
        rows_affected = cur.rowcount
        cur.close()

        if rows_affected > 0:
            return jsonify({"message": "Profile updated successfully"}), 200
        else:
            return jsonify({"message": "Update failed or no changes made"}), 400

    except Exception as e:
        print("🔴 Update error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/save-meeting', methods=['POST'])
def save_meeting():
    try:
        data = request.json
        print("🟡 Received meeting data:", data)

        title = data.get('title')
        meeting_date = data.get('meeting_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        location = data.get('location')
        organizer_id = data.get('organizer_id')  # optional for now; hardcoded below

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO meetings (title, meeting_date, start_time, end_time, location, organizer_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, meeting_date, start_time, end_time, location, organizer_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Meeting added successfully"}), 201

    except Exception as e:
        print("🔴 Error saving meeting:", e)
        return jsonify({"error": str(e)}), 500


# STEP 8: Ensure Flask is in debug mode for full error logs
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host="0.0.0.0", port=5001)
