from flask import Flask, render_template, abort, url_for
import requests
from datetime import datetime

app = Flask(__name__)


FIREBASE_DB_URL = "https://qr-attendance-524ca-default-rtdb.asia-southeast1.firebasedatabase.app"

def build_url(path=""):
    base = FIREBASE_DB_URL.rstrip("/")
    if path:
        return f"{base}/attendance_master/{path}.json"
    return f"{base}/attendance_master.json"


def fetch_all():
    try:
        url = build_url()  
        print("Requesting:", url)
        response = requests.get(url)
        response.raise_for_status()
        # print("Response:", response.text)
        return response.json()  
    except Exception as e:
        print("Error fetching all data:", e)
        return None

def fetch_person(key):
    try:
        url = build_url(key)  
        print("Requesting person:", url)
        response = requests.get(url)
        response.raise_for_status()
        # print("Person Response:", response.text)
        return response.json()
    except Exception as e:
        print("Error fetching person:", e)
        return None

def extract(node):
    
    meta = {}
    attendance = []

    for k, v in node.items():
        if k in ("ID", "Name"):
            meta[k] = v
            continue

        
        try:
            date_obj = datetime.strptime(k, "%Y-%m-%d").date()
            attendance.append((date_obj, k, v))
        except:
            meta[k] = v

    
    attendance.sort(key=lambda x: x[0], reverse=True)
    return meta, attendance

@app.route("/")
def index():
    data = fetch_all()
    # print("JSON data:", data.json())
    if not data:
        return "Error fetching Firebase data", 500

    people = []

    for key, node in data.items():
        if not isinstance(node, dict):
            continue

        meta, attendance = extract(node)
        people.append({
            "key": key,
            "id": meta.get("ID", "-"),
            "name": meta.get("Name", "-"),
            "last": attendance[0][2] if attendance else "No record",
            "count": len(attendance)
        })


    people.sort(key=lambda p: p["name"])

    return render_template("dashboard.html", people=people)

@app.route("/person/<key>")
def person_view(key):
    data = fetch_person(key)
    if not data:
        abort(404)

    meta, attendance = extract(data)
    return render_template("person.html", meta=meta, attendance=attendance)
    
if __name__ == "__main__":
    app.run(debug=True,port=5000)
