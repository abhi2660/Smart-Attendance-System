import pandas as pd
import os
import csv
from percentage import calculate_attendance_percentage



from email_notify import send_email






PARENT_CSV = "parents.csv"
PARENT_COLUMNS = ["student_id", "parent_name", "email"]

# ✅ Create CSV if not exists
def ensure_parent_csv():
    if not os.path.exists(PARENT_CSV):
        with open(PARENT_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=PARENT_COLUMNS)
            writer.writeheader()


# ✅ Get all parents
def get_all_parents():
    ensure_parent_csv()
    try:
        df = pd.read_csv(PARENT_CSV, dtype=str)
        return df.to_dict("records")
    except:
        return []


# ✅ Add parent
def add_parent(student_id, parent_name, email):
    ensure_parent_csv()
    df = pd.read_csv(PARENT_CSV, dtype=str)

    if str(student_id) in df["student_id"].astype(str).values:
        return False

    new_row = {
        "student_id": str(student_id),
        "parent_name": str(parent_name),
        "email": str(email)
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(PARENT_CSV, index=False)
    return True

def update_parent(student_id, parent_name, email):
    ensure_parent_csv()
    df = pd.read_csv(PARENT_CSV, dtype=str)
    df["student_id"] = df["student_id"].astype(str).str.strip()
    student_id = str(student_id).strip()
    df.loc[df["student_id"] == student_id, "parent_name"] = str(parent_name)
    df.loc[df["student_id"] == student_id, "email"] = str(email)

    df.to_csv(PARENT_CSV, index=False)

# ✅ Delete parent
def delete_parent(student_id):
    ensure_parent_csv()
    df = pd.read_csv(PARENT_CSV, dtype=str)
    df = df[df.student_id.astype(str) != str(student_id)]
    df.to_csv(PARENT_CSV, index=False)




# ✅ Send notifications
def send_attendance_notifications():
    ensure_parent_csv()
    parents = get_all_parents()
    results = []

    for p in parents:
        sid = str(p["student_id"]).strip()
        email = p.get("email", "").strip()

        if not email:
            continue

        data = calculate_attendance_percentage(sid)

        if data.get("ok"):

            if data["percentage"] < 75:
                subject = "⚠️ Low Attendance Alert"
            else:
                subject = "Attendance Report"

            message = f"""
Hello {p['parent_name']},

Student: {data['student_name']}
Attendance: {data['percentage']}%
Present Days: {data['present_count']}
Total Days: {data['total_days']}

Regards,
Attendance System
"""

            try:
                status = send_email(email, subject, message)
            except Exception as e:
                print("Email failed:", e)
                status = False

            results.append({"student_id": sid, "sent": status})

    return results