
import os
import csv
import uuid
from datetime import datetime
from typing import List, Dict


LEAVE_CSV = "leave_requests.csv"
LEAVE_COLUMNS = ["id", "name", "roll_number", "leave_start_date", "leave_end_date", "status", "submitted_at"]

def ensure_leave_csv() -> None:
    
    if not os.path.exists(LEAVE_CSV):
        with open(LEAVE_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LEAVE_COLUMNS)
            writer.writeheader()

def append_leave_request(name: str, roll_number: str, start_date: str, end_date: str) -> str:
    
    ensure_leave_csv()
    row = {
        "id": str(uuid.uuid4()),
        "name": name.strip(),
        "roll_number": roll_number.strip(),
        "leave_start_date": start_date.strip(),
        "leave_end_date": end_date.strip(),
        "status": "Pending",
        "submitted_at": datetime.utcnow().strftime("%Y-%m-%d")
    }
    with open(LEAVE_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEAVE_COLUMNS)
        writer.writerow(row)
    return row["id"]

def read_all_leave_requests() -> List[Dict[str, str]]:

    ensure_leave_csv()
    rows = []
    with open(LEAVE_CSV, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

def find_leave_request(request_id: str) -> Dict[str, str] | None:
    
    ensure_leave_csv()
    with open(LEAVE_CSV, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("id") == request_id:
                return r
    return None

def update_leave_status(request_id: str, new_status: str) -> bool:
    
    ensure_leave_csv()
    updated = False
    path = LEAVE_CSV + ".tmp"
    with open(LEAVE_CSV, mode="r", newline="", encoding="utf-8") as rf, \
         open(path, mode="w", newline="", encoding="utf-8") as wf:
        reader = csv.DictReader(rf)
        writer = csv.DictWriter(wf, fieldnames=LEAVE_COLUMNS)
        writer.writeheader()
        for row in reader:
            if row.get("id") == request_id:
                row["status"] = new_status
                updated = True
            writer.writerow(row)
    os.replace(path, LEAVE_CSV)
    return updated
