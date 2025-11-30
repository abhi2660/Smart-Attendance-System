import cv2
import pandas as pd
from flask import Flask, render_template, Response, request, jsonify, redirect, url_for, session, flash, make_response, send_file
import threading
import time
import re
from datetime import datetime
import traceback
import leave

from percentage import get_all_students_percentage

app = Flask(__name__)

app.secret_key = 'VeEr_007' 

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"


camera = None
last_scan_time = 0
last_scanned_id = None
scan_cooldown = 3
attendance_status = {"status": "info", "message": "Please scan your QR code."}

# --- Utility Functions ---
def initialize_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("Error: Could not open video stream.")
            camera = None

def release_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None
        print("Camera released.")

def mark_attendance(student_id):
    global attendance_status
    try:
        df = pd.read_csv('students.csv', dtype={'ID': str})

        if 'ID' not in df.columns or 'Name' not in df.columns:
            raise KeyError("students.csv must contain 'ID' and 'Name' columns")

        today_col = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%H:%M:%S')

        if today_col not in df.columns:
            df[today_col] = 'Absent'


        if student_id in df['ID'].values:
            student_name = df.loc[df['ID'] == student_id, 'Name'].values[0]
            current_status = df.loc[df['ID'] == student_id, today_col].values[0]
            
              

            if str(current_status).strip().lower().startswith('abs'):
                df.loc[df['ID'] == student_id, today_col] = f'Present ({timestamp})'
                message = f"Welcome, {student_name}! Marked present at {timestamp}."
                color = "#28a745"
            else:
                message = f"Hi, {student_name}. Already marked present today."
                color = "#17a2b8"
            
            attendance_status = {"status": "success", "message": message, "color": color}
            df.to_csv('students.csv', index=False)

        else:
            attendance_status = {"status": "error", "message": f"Error: Student ID '{student_id}' not found.", "color": "#dc3545"}

        df.to_csv('students.csv', index=False)

    except FileNotFoundError:
        attendance_status = {
            "status": "error",
            "message": "Student database (students.csv) not found.",
            "color": "#dc3545"
        }

    except Exception as e:
        print(f"Error in mark_attendance")
        traceback.print_exc()
        attendance_status = {"status": "error", "message": "Error processing attendance.", "color": "#dc3545"}

def generate_frames():
    global last_scan_time, last_scanned_id, attendance_status
    initialize_camera()
    if camera is None:
        print("Camera not initialized for frame generation.")
        return

    detector = cv2.QRCodeDetector()
    while True:
        if camera is None: break
        success, frame = camera.read()
        if not success: break
        
        try:
            decoded_text, points, _ = detector.detectAndDecode(frame)
            if points is not None and decoded_text:
                student_id = next(iter(re.findall(r'\b\d{13}\b', decoded_text)), None)
                if student_id:
                    current_time = time.time()
                    if student_id != last_scanned_id or (current_time - last_scan_time) > scan_cooldown:
                        mark_attendance(student_id)
                        last_scanned_id = student_id
                        last_scan_time = current_time
        except cv2.error:
            pass
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- Page Routes ---
@app.route('/')
def index():
    release_camera()
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['admin_user'] = username
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials. Please try again.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been successfully logged out.')
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')
        try:
            df = pd.read_csv('students.csv', dtype={'ID': str})
            
            if action == 'add':
                student_id = request.form.get('student_id')
                student_name = request.form.get('student_name')
                if student_id not in df['ID'].values:
                    new_student = pd.DataFrame([{'ID': student_id, 'Name': student_name, 'Status': 'Absent'}])
                    df = pd.concat([df, new_student], ignore_index=True)
                    flash(f'Student {student_name} added successfully.')
                else:
                    flash('Student with this ID already exists.')
            
            elif action == 'edit':
                original_id = request.form.get('original_id')
                new_id = request.form.get('student_id')
                new_name = request.form.get('student_name')
                if new_id != original_id and new_id in df['ID'].values:
                    flash('Error: Another student with this new ID already exists.')
                else:
                    df.loc[df['ID'] == original_id, 'ID'] = new_id
                    df.loc[df['ID'] == new_id, 'Name'] = new_name
                    flash(f'Student {new_name} updated successfully.')

            elif action == 'delete':
                student_id_to_delete = request.form.get('student_id')
                df = df[df.ID != student_id_to_delete]
                flash('Student deleted successfully.')

            df.to_csv('students.csv', index=False)
        except FileNotFoundError:
             flash('Student database not found.')
        except Exception as e:
            flash(f'An error occurred: {e}')
        return redirect(url_for('admin'))

    try:
        df = pd.read_csv('students.csv', dtype={'ID': str})
        students = df.to_dict('records')
    except FileNotFoundError:
        students = []
        flash('Student database (students.csv) not found. Add a student to create it.')
    return render_template('admin.html', students=students)


@app.route('/student')
def student():
    global attendance_status
    attendance_status = {"status": "info", "message": "Please scan your QR code.", "color": "#17a2b8"}
    time.sleep(0.5) 
    return render_template('student.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_status')
def get_status():
    return jsonify(attendance_status)

@app.route('/download_attendance')
def download_attendance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        df = pd.read_csv('students.csv')
        response = make_response(df.to_csv(index=False))
        response.headers["Content-Disposition"] = "attachment; filename=attendance.csv"
        response.headers["Content-Type"] = "text/csv"
        return response
    except FileNotFoundError:
        flash('Could not find students.csv to download.')
        return redirect(url_for('admin'))
    
# show attendance percentages

@app.route('/attendance_percentages')
def attendance_percentages_page():
    
    data = get_all_students_percentage('students.csv')
    # Convert to a sorted list by student name for predictable display
    students = sorted(data.values(), key=lambda x: x.get('student_name', ''))
    return render_template('percentage.html', students=students)




# after reset  data only ID and NAME column will remaining

@app.route('/reset_attendance')
def reset_attendance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        df = pd.read_csv('students.csv', dtype={'ID': str})
        df = df[['ID', 'Name']]
        df.to_csv('students.csv', index=False)
        flash('Attendance has been successfully reset for a new session.')
    except FileNotFoundError:
        flash('Student database (students.csv) not found.')
    except Exception as e:
        flash(f'Error resetting attendance: {e}')
    return redirect(url_for('admin'))


# Leave request 


@app.route("/leave_request", methods=["GET", "POST"])
def leave_request():
    """
    Student-facing: GET shows form, POST validates and appends request to CSV.
    """

    errors = []
    success_msg = None
    form_data = {}

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll = request.form.get("roll_number", "").strip()
        start = request.form.get("leave_start_date", "").strip()
        end = request.form.get("leave_end_date", "").strip()


        form_data = {
            "name": name,
            "roll_number": roll,
            "leave_start_date": start,
            "leave_end_date": end
        } 

        # Basic validation
        
        if not name:
            errors.append("Name is required.")
        if not roll:
            errors.append("Roll number is required.")
        if not start:
            errors.append("Leave start date is required.")
        if not end:
            errors.append("Leave end date is required.")

        # Validate date format (YYYY-MM-DD)
        try:
            sd = datetime.strptime(start, "%Y-%m-%d")
            ed = datetime.strptime(end, "%Y-%m-%d")
            if ed < sd:
                errors.append("End date cannot be earlier than start date.")
        except ValueError:
            errors.append("Dates must be in YYYY-MM-DD format.")

        if not errors:
            # Append to CSV via leave.py
            leave.append_leave_request(name, roll, start, end)
            success_msg = f"Leave request submitted successfully."
            flash(success_msg, "success")
            # clear form after success
            form_data = {}

    # Always load all requests from CSV and pass to the template
    all_requests = leave.read_all_leave_requests()

    # Optionally: sort by submitted_at descending so newest first
    try:
        all_requests.sort(key=lambda r: r.get("submitted_at", ""), reverse=True)
    except Exception:
        pass

    return render_template(
        "leave_request.html",
        errors=errors,
        success=success_msg,
        form=form_data,
        requests=all_requests
    )


@app.route("/admin/leave_requests")
def admin_leave_requests():
    """
    Admin-facing: list leave requests.
    Replace session key check if your app uses a different key for admin auth.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    rows = leave.read_all_leave_requests()
    return render_template("admin_leave_requests.html", requests=rows)


@app.route("/admin/leave_requests/<request_id>/approve", methods=["POST"])
def approve_leave_request(request_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    ok = leave.update_leave_status(request_id, "Approved")
    if ok:
        flash("Leave request approved.", "success")
    else:
        flash("Request not found.", "danger")
    return redirect(url_for("admin_leave_requests"))


@app.route("/admin/leave_requests/<request_id>/reject", methods=["POST"])
def reject_leave_request(request_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    ok = leave.update_leave_status(request_id, "Rejected")
    if ok:
        flash("Leave request rejected.", "info")
    else:
        flash("Request not found.", "danger")
    return redirect(url_for("admin_leave_requests"))


@app.route("/admin/download_leave_requests")
def download_leave_requests():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    leave.ensure_leave_csv()
    return send_file(leave.LEAVE_CSV, as_attachment=True, download_name="leave_requests.csv")





if __name__ == '__main__':
    app.run(debug=True, port=5001)

