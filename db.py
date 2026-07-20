import streamlit as st
import urllib.request
import json
import datetime

# قراءة الـ Secrets مع Fallback مباشر
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = "https://xzepnnlyrmvncqapbswag.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh6ZXBubnlybXZuY3FhcGJzd2FnIiwicm9sZSI6InFub24iLCJpYXQiOjE3ODQyODc1NzUsImV4cCI6MjA5OTg2MzU3NX0.VAsBg8EX5ziOThBwWhactpX46iZBuMzHdH8dEqihysI"

USER_MAP = {"Anna": 1, "Christa": 2, "Mira": 3}
ID_MAP = {v: k for k, v in USER_MAP.items()}

def get_data():
    data = {
        "employees": ["Anna", "Christa", "Mira"],
        "creds": {"Anna": "0000", "Christa": "1234", "Mira": "5678"},
        "admins": ["Anna"],
        "schedules": {}
    }
    try:
        url = f"{SUPABASE_URL}/rest/v1/schedules?select=*"
        req = urllib.request.Request(
            url, 
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode())
            if res_data:
                for item in res_data:
                    d_str = item['work_date']
                    emp_id = item['user_id']
                    emp_name = ID_MAP.get(emp_id, str(emp_id))
                    day_name = item.get('day_name', 'MON')
                    
                    if d_str not in data['schedules']: data['schedules'][d_str] = {}
                    if emp_name not in data['schedules'][d_str]: data['schedules'][d_str][emp_name] = {}
                    data['schedules'][d_str][emp_name][day_name] = {
                        "s": item['start_time'], "e": item['end_time'], 
                        "b": item['break_minutes'], "n": item.get('notes', ''), "off": item['is_off']
                    }
    except Exception as e:
        print(f"Fetch Error: {e}")
    return data

def save_data(data, user_name):
    try:
        records_to_upsert = []
        for d_str, scheds in data['schedules'].items():
            for emp_name, days in scheds.items():
                emp_id = USER_MAP.get(emp_name, 0)
                for day_name, info in days.items():
                    records_to_upsert.append({
                        "user_id": emp_id,
                        "work_date": d_str,
                        "day_name": day_name,
                        "start_time": info['s'],
                        "end_time": info['e'],
                        "break_minutes": info['b'],
                        "is_off": info['off'],
                        "notes": info['n']
                    })
        
        if records_to_upsert:
            url = f"{SUPABASE_URL}/rest/v1/schedules"
            # استخدام خاصية الـ Upsert عبر الـ REST API مباشرة
            payload = json.dumps(records_to_upsert).encode('utf-8')
            req = urllib.request.Request(
                url, 
                data=payload,
                method="POST",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                }
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                pass
        return True
    except Exception as e:
        st.error(f"خطأ تقني: {e}")
        return False
