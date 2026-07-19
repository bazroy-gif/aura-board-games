from supabase import create_client
import datetime

SUPABASE_URL = "https://xzepnnlyrmvncqapbswag.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh6ZXBubnlybXZuY3FhcGJzd2FnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyODc1NzUsImV4cCI6MjA5OTg2MzU3NX0.VAsBg8EX5ziOThBwWhactpX46iZBuMzHdH8dEqihysI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_data():
    # تعريف الموظفين يدوياً لضمان عدم اختفاء الأسماء أبداً
    data = {
        "employees": ["Anna", "Christa", "Mira"],
        "creds": {"Anna": "0000", "Christa": "1234", "Mira": "5678"},
        "admins": ["Anna"],
        "schedules": {}
    }
    
    try:
        # محاولة جلب الداتا من السيرفر
        schedules_list = supabase.table("schedules").select("*").execute().data
        
        if schedules_list:
            for item in schedules_list:
                d_str = item['work_date']
                emp = item['user_id']
                day_name = item.get('day_name', 'MON')
                
                if d_str not in data['schedules']: data['schedules'][d_str] = {}
                if emp not in data['schedules'][d_str]: data['schedules'][d_str][emp] = {}
                
                data['schedules'][d_str][emp][day_name] = {
                    "s": item['start_time'],
                    "e": item['end_time'],
                    "b": item['break_minutes'],
                    "n": item.get('notes', ''),
                    "off": item['is_off']
                }
    except Exception as e:
        print(f"Server data fetch skipped: {e}")
        
    return data

def save_data(data, user_name):
    """حفظ التغييرات في جدول schedules"""
    try:
        for d_str, scheds in data['schedules'].items():
            for emp, days in scheds.items():
                for day_name, info in days.items():
                    record = {
                        "user_id": emp,
                        "work_date": d_str,
                        "day_name": day_name,
                        "start_time": info['s'],
                        "end_time": info['e'],
                        "break_minutes": info['b'],
                        "is_off": info['off'],
                        "notes": info['n']
                    }
                    # استخدام on_conflict لضمان التحديث وعدم التكرار
                    supabase.table("schedules").upsert(record, on_conflict="user_id,work_date").execute()
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False