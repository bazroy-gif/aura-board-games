import streamlit as st
from supabase import create_client
import socket

# تجاوز مشاكل الـ DNS عبر تثبيت العنوان صراحةً إن وجد
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = "https://xzepnnlyrmvncqapbswag.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh6ZXBubnlybXZuY3FhcGJzd2FnIiwicm9sZSI6InFub24i nonradiative"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        response = supabase.table("schedules").select("*").execute()
        if response.data:
            for item in response.data:
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
            supabase.table("schedules").upsert(records_to_upsert).execute()
        return True
    except Exception as e:
        # حل بديل مؤقت للتخزين المحلي العابر إذا عاند السيرفر لتمنع توقف التطبيق
        st.error(f"خطأ تقني: {e}")
        return False
