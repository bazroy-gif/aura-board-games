import streamlit as st
import json
import os

DB_FILE = "local_aura_data.json"

# بيانات افتراضية أولية متكاملة تضمن عمل التطبيق فوراً بدون انقطاع
DEFAULT_DATA = {
    "employees": ["Anna", "Christa", "Mira"],
    "creds": {"Anna": "0000", "Christa": "1234", "Mira": "5678"},
    "admins": ["Anna"],
    "schedules": {}
}

def get_data():
    """قراءة البيانات من الملف المحلي لضمان السرعة وتجاوز مشاكل الشبكة تماماً"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # التأكد من وجود المفاتيح الأساسية
                for key in DEFAULT_DATA:
                    if key not in data:
                        data[key] = DEFAULT_DATA[key]
                return data
    except Exception as e:
        print(f"Read Error: {e}")
    
    # في حال عدم وجود الملف، يتم إنشاؤه بالبيانات الافتراضية
    save_local_data(DEFAULT_DATA)
    return DEFAULT_DATA

def save_local_data(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Save Local Error: {e}")
        return False

def save_data(data, user_name):
    """حفظ البيانات محلياً وبشكل فوري بدون أي أخطاء DNS أو تعقيدات خارجية"""
    try:
        success = save_local_data(data)
        if success:
            return True
        else:
            st.error("خطأ في حفظ البيانات محلياً.")
            return False
    except Exception as e:
        st.error(f"خطأ تقني: {e}")
        return False
