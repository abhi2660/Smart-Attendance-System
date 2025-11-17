import pandas as pd
import re
import os
from datetime import datetime
from typing import Optional, Dict

DATE_COL_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def _is_present_cell(cell_value: object) -> bool:
   
    try:
        s = str(cell_value).strip().lower()
    except Exception:
        return False
    return s.startswith('present')

def calculate_attendance_percentage(student_id: str, csv_path: str = 'students.csv') -> Dict[str, object]:
   
    if not os.path.exists(csv_path):
        return {"ok": False, "message": "students.csv not found."}

    try:
        df = pd.read_csv(csv_path, dtype={'ID': str})
    except Exception as e:
        return {"ok": False, "message": f"Error reading CSV: {e}"}

    if 'ID' not in df.columns or 'Name' not in df.columns:
        return {"ok": False, "message": "CSV missing required 'ID' or 'Name' columns."}

   
    date_cols = [c for c in df.columns if DATE_COL_RE.match(c)]
   
    if len(date_cols) == 0:
        
        row = df.loc[df['ID'] == student_id]
        if row.empty:
            return {"ok": False, "message": "Student not found.", "student_id": student_id}
        name = row.iloc[0]['Name']
        return {
            "ok": True,
            "message": "No attendance days recorded yet.",
            "student_id": student_id,
            "student_name": name,
            "present_count": 0,
            "total_days": 0,
            "percentage": 0.0
        }

    row = df.loc[df['ID'] == student_id]
    if row.empty:
        return {"ok": False, "message": "Student not found.", "student_id": student_id}

    name = row.iloc[0]['Name']
    present_count = 0
    total_days = 0

    for col in date_cols:
        total_days += 1
        cell = row.iloc[0].get(col, '')
        if _is_present_cell(cell):
            present_count += 1

    percentage = (present_count / total_days) * 100 if total_days > 0 else 0.0
    percentage = round(percentage, 2)

    return {
        "ok": True,
        "message": "Attendance computed.",
        "student_id": student_id,
        "student_name": name,
        "present_count": int(present_count),
        "total_days": int(total_days),
        "percentage": percentage
    }

def get_all_students_percentage(csv_path: str = 'students.csv') -> Dict[str, Dict]:
    
    output = {}
    if not os.path.exists(csv_path):
        return output

    try:
        df = pd.read_csv(csv_path, dtype={'ID': str})
    except Exception:
        return output

    if 'ID' not in df.columns or 'Name' not in df.columns:
        return output

    date_cols = [c for c in df.columns if DATE_COL_RE.match(c)]
    for _, row in df.iterrows():
        sid = str(row['ID'])
        name = row['Name']
        present = 0
        total = len(date_cols)
        for col in date_cols:
            if _is_present_cell(row.get(col, '')):
                present += 1
        pct = round((present / total) * 100, 2) if total > 0 else 0.0
        output[sid] = {
            "student_id": sid,
            "student_name": name,
            "present_count": int(present),
            "total_days": int(total),
            "percentage": pct
        }
    return output
