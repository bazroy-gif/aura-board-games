import streamlit as st
import db
import json
import datetime
import calendar

# --- 0. CALCULATE HOURS FUNCTION ---
def calculate_hours(start_str, end_str, break_min):
    try:
        def fix_time(t_str):
            t_str = t_str.strip()
            if t_str == "12": return "00:00"
            if ":" not in t_str: return f"{t_str}:00"
            return t_str
        
        fmt = "%H:%M"
        t1 = datetime.datetime.strptime(fix_time(start_str), fmt)
        t2 = datetime.datetime.strptime(fix_time(end_str), fmt)
        
        if t2 <= t1: t2 += datetime.timedelta(days=1)
        
        diff = (t2 - t1).total_seconds() / 3600
        net_hours = diff - (break_min / 60)
        return max(0, net_hours)
    except: return 0

# --- 1. CONFIGURATION & CSS ---
st.set_page_config(page_title="Aura Board Games", layout="wide")

st.markdown("""
    <style>
    :root { --bg-dark: #0f172a; --text-main: #1f2937; --card-bg: #ffffff; --border: #e5e7eb; --accent: #db2777; --text-dim: #6b7280; }
    .stApp { background-color: #f3f4f6; color: #1f2937; }
    .dashboard { max-width: 1100px; margin: auto; background: var(--card-bg); border-radius: 16px; padding: 24px; border: 1px solid var(--border); color: #1f2937; }
    .nav-bar { display: flex; justify-content: space-between; align-items: center; background: #fff1f2; padding: 12px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border); }
    .day-box { background: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 6px; }
    .day-label { font-size: 11px; font-weight: bold; color: #db2777; text-transform: uppercase; border-bottom: 1px solid #fff1f2; padding-bottom: 2px; }
    
    /* فرض ألوان واضحة وثابتة لمربعات الإدخال والنصوص لتجنب اختفائها بالـ Dark Mode */
    .stTextInput input, .stTextArea textarea { font-size: 12px; background-color: #ffffff !important; color: #1f2937 !important; border: 1px solid #cbd5e1 !important; }
    .hours-display { font-size: 11px; font-weight: bold; color: #db2777; margin-top: 5px; }
    
    h1, h2, h3, h4, h5, h6, p, span, label { color: #1f2937 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION & DATE MANAGEMENT ---
if 'selected_date' not in st.session_state: st.session_state['selected_date'] = datetime.date.today()

# --- 3. AUTH ---
if 'user' not in st.session_state:
    st.markdown('<div class="dashboard" style="max-width: 400px;">', unsafe_allow_html=True)
    st.title("🎀 Aura Board Games")
    data = db.get_data()
    selected_name = st.selectbox("Select Your Profile:", data['employees'])
    passkey = st.text_input("Passkey:", type="password")
    if st.button("Access Dashboard"):
        if data['creds'].get(selected_name) == passkey:
            st.session_state['user'] = selected_name
            st.session_state['is_admin'] = selected_name in data['admins']
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # التوقيع على شاشة تسجيل الدخول
    st.markdown("""
        <div style="text-align: center; margin-top: 30px; font-size: 11px; color: #6b7280;">
            Aura Board Games Schedule App • Designed by Roudy • Developed by Roy Baz
        </div>
    """, unsafe_allow_html=True)

else:
    user = st.session_state['user']
    is_admin = st.session_state['is_admin']
    data = db.get_data()
    if 'schedules' not in data: data['schedules'] = {}
    if 'admins' not in data: data['admins'] = ["Anna"]
    
    st.markdown('<div class="dashboard">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    c1.title(f"🎀 Welcome, {user}")
    if c2.button("Logout"): st.session_state.clear(); st.rerun()

    # --- NAV BAR ---
    st.markdown('<div class="nav-bar">', unsafe_allow_html=True)
    nav_cols = st.columns([1, 3, 1])
    if nav_cols[0].button("◀️ Wk"): st.session_state['selected_date'] -= datetime.timedelta(days=7); st.rerun()
    
    new_date = nav_cols[1].date_input("Select Date", st.session_state['selected_date'], label_visibility="collapsed")
    if new_date != st.session_state['selected_date']: st.session_state['selected_date'] = new_date; st.rerun()
    
    if nav_cols[2].button("Wk ▶️"): st.session_state['selected_date'] += datetime.timedelta(days=7); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- MONTHLY REPORT SECTION ---
    if is_admin:
        with st.expander("📊 Monthly Report"):
            months = ["06", "07", "08", "09", "10", "11", "12"]
            selected_month = st.selectbox("Select Month:", months, format_func=lambda x: f"2026-{x}")
            if st.button("Generate Report"):
                report_data = {}
                y, m_num = 2026, int(selected_month)
                num_days = calendar.monthrange(y, m_num)[1]
                
                for emp in data['employees']:
                    total_m = 0
                    for day_num in range(1, num_days + 1):
                        d_str = f"2026-{selected_month}-{day_num:02d}"
                        # إذا كان اليوم مسجلاً بالـ database نحسب ساعاته، وإلا نفترض الأوقات الافتراضية (15:00 إلى 01:00 = 10 ساعات)
                        if d_str in data.get('schedules', {}) and emp in data['schedules'][d_str]:
                            for day_data in data['schedules'][d_str][emp].values():
                                if not day_data.get('off', False):
                                    total_m += calculate_hours(day_data.get('s', '15:00'), day_data.get('e', '01:00'), day_data.get('b', 0))
                        else:
                            # افتراضي 10 ساعات لكل يوم طالما لم يتم تعيين إجازة صريحة
                            total_m += 10.0
                    report_data[emp] = f"{total_m:.1f} hrs"
                st.table(report_data)

    # --- EMPLOYEES DASHBOARD ---
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    sel_date = st.session_state['selected_date']
    start_of_week = sel_date - datetime.timedelta(days=sel_date.weekday())
    
    for emp in data['employees']:
        if is_admin or emp == user:
            with st.expander(f"👤 {emp}", expanded=True):
                weekly_hours = 0
                cols = st.columns(7)
                
                for i, day in enumerate(days):
                    curr_date = start_of_week + datetime.timedelta(days=i)
                    curr_date_str = str(curr_date)
                    
                    if curr_date_str not in data['schedules']: data['schedules'][curr_date_str] = {}
                    if emp not in data['schedules'][curr_date_str]: data['schedules'][curr_date_str][emp] = {}
                    
                    with cols[i]:
                        st.markdown('<div class="day-box">', unsafe_allow_html=True)
                        st.markdown(f'<div class="day-label">{day}<br>{curr_date.strftime("%d/%m")}</div>', unsafe_allow_html=True)
                        
                        d = data['schedules'][curr_date_str][emp].get(day, {"s": "15:00", "e": "01:00", "b": 0, "n": "", "off": False})
                        
                        s = st.text_input("Start", d["s"], key=f"s_{emp}_{day}_{curr_date_str}", disabled=not is_admin, label_visibility="collapsed")
                        e = st.text_input("End", d["e"], key=f"e_{emp}_{day}_{curr_date_str}", disabled=not is_admin, label_visibility="collapsed")
                        b = st.number_input("Break:", 0, 60, d["b"], key=f"b_{emp}_{day}_{curr_date_str}", disabled=not is_admin, label_visibility="collapsed")
                        off = st.checkbox("Day Off", d["off"], key=f"off_{emp}_{day}_{curr_date_str}", disabled=not is_admin)
                        
                        day_h = 0 if off else calculate_hours(s, e, b)
                        weekly_hours += day_h
                        
                        st.markdown(f'<div class="hours-display">{day_h:.1f} hrs</div>', unsafe_allow_html=True)
                        n = st.text_area("Notes...", d["n"], height=40, key=f"n_{emp}_{day}_{curr_date_str}", disabled=not is_admin, label_visibility="collapsed")
                        
                        data['schedules'][curr_date_str][emp][day] = {"s": s, "e": e, "b": b, "n": n, "off": off}
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # --- حساب المجموع الشهري الكامل لكل أيام الشهر الحالي بدقة (من يوم 1 لآخر الشهر) ---
                monthly_total = 0
                target_year = sel_date.year
                target_month = sel_date.month
                num_days_in_month = calendar.monthrange(target_year, target_month)[1]
                
                for day_num in range(1, num_days_in_month + 1):
                    d_obj = datetime.date(target_year, target_month, day_num)
                    d_str = str(d_obj)
                    
                    # نتحقق إذا كان اليوم مخزن بالداتا بيس أو نأخذ القيم الافتراضية
                    if d_str in data.get('schedules', {}) and emp in data['schedules'][d_str]:
                        for day_name, day_data in data['schedules'][d_str][emp].items():
                            if not day_data.get('off', False):
                                monthly_total += calculate_hours(day_data.get('s', '15:00'), day_data.get('e', '01:00'), day_data.get('b', 0))
                    else:
                        # افتراضياً كل يوم عمله 10 ساعات إذا لم يتم تعديله أو تعيينه كإجازة
                        monthly_total += 10.0

                # --- إظهار المجاميع وزر الحفظ حصراً للـ Admin ---
                if is_admin:
                    st.write(f"**Weekly Total: {weekly_hours:.1f} hours | Monthly Total ({sel_date.strftime('%B %Y')}): {monthly_total:.1f} hours**")
                    if st.button(f"Save {emp} Changes", key=f"save_{emp}_{sel_date}"):
                        if db.save_data(data, user):
                            st.success(f"Changes for {emp} saved!")
                        else:
                            st.error(f"Error saving {emp} changes. Check database connection.")

    # --- ADMIN SETTINGS: ADD, DELETE & CHANGE PASSWORD ---
    if is_admin:
        with st.expander("⚙️ Admin Settings"):
            st.subheader("Add New Member / Admin")
            new_name = st.text_input("New Member Name")
            new_pass = st.text_input("New Member Passkey", type="password")
            make_admin = st.checkbox("Grant Admin Privileges")
            
            if st.button("Add Member Profile"):
                if new_name and new_name not in data['employees']:
                    data['employees'].append(new_name)
                    data['creds'][new_name] = new_pass
                    if make_admin and new_name not in data['admins']:
                        data['admins'].append(new_name)
                    if db.save_data(data, user): 
                        st.success(f"Member {new_name} added successfully!")
                        st.rerun()
                    else: st.error("Error adding member.")
                else:
                    st.error("Please enter a valid or unique name.")
            
            st.markdown("---")
            st.subheader("Change Member Password")
            target_emp = st.selectbox("Select Member to Change Passkey:", data['employees'], key="pwd_target")
            new_emp_pass = st.text_input("New Passkey", type="password", key="new_pwd_input")
            if st.button("Update Passkey"):
                if new_emp_pass:
                    data['creds'][target_emp] = new_emp_pass
                    if db.save_data(data, user):
                        st.success(f"Passkey for {target_emp} updated successfully!")
                    else:
                        st.error("Error updating passkey.")
                else:
                    st.error("Please enter a valid passkey.")

            st.markdown("---")
            st.subheader("Delete Member Profile")
            member_to_delete = st.selectbox("Select Member to Remove:", [emp for emp in data['employees'] if emp != user])
            if st.button("Delete Selected Member"):
                if member_to_delete in data['employees']:
                    data['employees'].remove(member_to_delete)
                    if member_to_delete in data['creds']: del data['creds'][member_to_delete]
                    if member_to_delete in data['admins']: data['admins'].remove(member_to_delete)
                    if db.save_data(data, user):
                        st.success(f"Member {member_to_delete} deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Error deleting member.")

            st.markdown("---")
            if st.button("Save All Changes"):
                if db.save_data(data, user): st.success("Data Saved Successfully!")
                else: st.error("Error saving all data. Check database connection.")

    # --- FOOTER SIGNATURE ---
    st.markdown("""
        <div style="text-align: center; margin-top: 30px; font-size: 11px; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 10px;">
            Aura Board Games Schedule App • Designed by Roudy • Developed by Roy Baz
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
