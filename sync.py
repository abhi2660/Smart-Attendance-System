
import csv
import os
import json
from typing import Dict, Any, Tuple
import firebase_admin
from firebase_admin import credentials, db


SERVICE_ACCOUNT = "serviceAccountKey.json"   
DATABASE_URL = "https://qr-attendance-524ca-default-rtdb.asia-southeast1.firebasedatabase.app/"
KEY_COL = "ID"               
FIREBASE_REF = "/attendance_master"   


def init_firebase():
    if not firebase_admin._apps:
        if not os.path.exists(SERVICE_ACCOUNT):
            raise FileNotFoundError(f"Firebase service account key not found at {SERVICE_ACCOUNT}")
        cred = credentials.Certificate(SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})


def read_csv(csv_path: str, key_col: str = KEY_COL) -> Dict[str, Dict[str, str]]:
    rows = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if key_col not in r:
                raise KeyError(f"Key column '{key_col}' not found in CSV headers: {reader.fieldnames}")
            key = r[key_col].strip()
            if not key:
                continue
            # strip and convert None to ""
            cleaned = {k: (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
            rows[key] = cleaned
    return rows

# Compare two dicts 
def compute_diffs(old: Dict[str, Any], new: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Returns (add, update, delete)
    - add: keys in new but not in old
    - update: keys in both but with different content
    - delete: keys in old but not in new
    """
    add = {}
    update = {}
    delete = {}

    old_keys = set(old.keys()) if old else set()
    new_keys = set(new.keys())

    for k in new_keys - old_keys:
        add[k] = new[k]

    for k in new_keys & old_keys:
        # compare the values of csv data and firebase data
        if old.get(k) != new.get(k):
            update[k] = new[k]

    for k in old_keys - new_keys:
        delete[k] = old[k]

    return add, update, delete

# changes to Firebase
def apply_changes(add: Dict, update: Dict, delete: Dict, firebase_ref: str = FIREBASE_REF) -> Dict[str,int]:
    init_firebase()
    ref = db.reference(firebase_ref)

    results = {"added": 0, "updated": 0, "deleted": 0}

    # Bulk writes using update() where possible
    if add:
        data = {k: v for k, v in add.items()}
        ref.update(data)
        results["added"] = len(add)

    if update:
        data = {k: v for k, v in update.items()}
        ref.update(data)
        results["updated"] = len(update)


    for k in delete.keys():
        ref.child(k).delete()
        results["deleted"] += 1

    return results


def sync_csv(csv_path: str, key_col: str = KEY_COL, firebase_ref: str = FIREBASE_REF) -> Dict[str, Any]:
 
    init_firebase()

    new_data = read_csv(csv_path, key_col=key_col)

    # Read data from Firebase
    root_ref = db.reference(firebase_ref)
    existing = root_ref.get() or {}   

    add, update, delete = compute_diffs(existing, new_data)
    results = apply_changes(add, update, delete, firebase_ref=firebase_ref)

    results["total_csv_rows"] = len(new_data)
    return results

