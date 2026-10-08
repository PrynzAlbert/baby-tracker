from datetime import datetime, timedelta
import time
import pandas as pd
import streamlit as st
from supabase import create_client

# Page Configuration
st.set_page_config(
    page_title="Smart Baby", page_icon="🍼", layout="centered", initial_sidebar_state="collapsed"
)

# --- CUSTOM BRIGHT MOBILE-FRIENDLY CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; color: #2D3748; }
    h1, h2, h3, h4 { color: #1A365D !important; }
    
    .stRadio label { color: #1A365D !important; font-weight: 700 !important; font-size: 1.1rem !important; }
    input, textarea { color: #2D3748 !important; background-color: #FFFFFF !important; border: 1px solid #CBD5E0 !important; border-radius: 8px !important; }
    
    .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #2D3748 !important;
        border-radius: 8px !important;
        border: 1px solid #CBD5E0 !important;
    }
    .stSelectbox span { color: #2D3748 !important; }
    
    div[data-baseweb="popover"] div, div[data-baseweb="menu"] div {
        background-color: #FFFFFF !important;
        color: #2D3748 !important;
    }
    div[data-baseweb="menu"] div:hover {
        background-color: #EDF2F7 !important;
        color: #1A365D !important;
    }

    .stButton>button { background-color: #4299E1; color: white; border-radius: 12px; border: none; font-weight: 600; padding: 0.5rem 1rem; }
    .stButton>button:hover { background-color: #3182CE; color: white; }
    .stFormSubmitButton>button { background-color: #48BB78; color: white; border-radius: 12px; border: none; font-weight: 600; width: 100%; }
    
    div[data-testid="stMetric"] { background-color: #FFFFFF; padding: 12px; border-radius: 12px; border: 1px solid #E2E8F0; }
    div[data-testid="stMetric"] label { color: #4A5568 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #2B6CB0 !important; }
    </style>
""", unsafe_allow_html=True)

# Initialize Supabase
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# Session State Init
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = None

try:
    session = supabase.auth.get_session()
    if session and session.user:
        st.session_state.user = session.user
        profile_res = supabase.schema("public").table("profiles").select("*").eq("id", session.user.id).execute()
        if profile_res.data:
            st.session_state.profile = profile_res.data[0]
except:
    pass

# --- AUTHENTICATION & REGISTRATION GATE ---
if not st.session_state.user or not st.session_state.profile:
    st.title("🍼 Smart Baby")
    st.caption("Sign in or register your family tracking profile.")
    
    tab_login, tab_signup = st.tabs(["Sign In", "Register Profile"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.user = res.user
                        p_res = supabase.schema("public").table("profiles").select("*").eq("id", res.user.id).execute()
                        if p_res.data:
                            st.session_state.profile = p_res.data[0]
                            st.rerun()
                        else:
                            st.warning("Signed in, but profile details were not found.")
                except Exception as e:
                    st.error(f"Login failed: {e}")

    with tab_signup:
        with st.form("signup_form"):
            reg_email = st.text_input("Email", key="su_email")
            reg_password = st.text_input("Password", type="password", key="su_pass")
            st.divider()
            caregiver_name = st.text_input("Your Caregiver Username", placeholder="e.g. Albert, Sarah...")
            baby_name = st.text_input("Baby's Name", placeholder="e.g. Leo")
            baby_dob = st.date_input("Baby's Date of Birth", datetime.now().date())
            
            if st.form_submit_button("Create Account & Profile", use_container_width=True):
                if not caregiver_name or not baby_name:
                    st.error("Please fill in your username and baby's name.")
                else:
                    try:
                        auth_res = supabase.auth.sign_up({
                            "email": reg_email,
                            "password": reg_password,
                            "options": {
                                "data": {
                                    "caregiver_name": caregiver_name,
                                    "baby_name": baby_name,
                                    "baby_dob": str(baby_dob)
                                }
                            }
                        })
                        if auth_res.user:
                            st.success("Account & profile created successfully! You can now sign in.")
                    except Exception as e:
                        st.error(f"Registration failed: {e}")

else:
    # --- MAIN APP (Authenticated & Profile Loaded) ---
    profile = st.session_state.profile
    current_caregiver = profile.get("caregiver_name", "Caregiver")
    baby_name = profile.get("baby_name", "Baby")
    baby_dob_str = profile.get("baby_dob")

    # Calculate baby's age
    age_text = ""
    if baby_dob_str:
        try:
            dob = datetime.strptime(baby_dob_str, "%Y-%m-%d").date()
            days_old = (datetime.now().date() - dob).days
            if days_old < 30:
                age_text = f"{days_old} days old"
            elif days_old < 365:
                age_text = f"{round(days_old / 30, 1)} months old"
            else:
                age_text = f"{round(days_old / 365, 1)} years old"
        except:
            pass

    with st.sidebar:
        st.write(f"Signed in as:\n**{current_caregiver}**")
        if baby_name:
            st.caption(f"Baby: **{baby_name}** ({age_text})")
        st.divider()
        if st.button("Log Out", use_container_width=True):
            try: supabase.auth.sign_out()
            except: pass
            st.session_state.user = None
            st.session_state.profile = None
            st.rerun()

    st.title(f"🍼 {baby_name}'s Tracker")
    st.caption(f"Welcome back, **{current_caregiver}**! Tracking live.")

    # --- TODAY'S SUMMARY METRICS ---
    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        dash_res = supabase.schema("public").table("baby_logs").select("type, note, start_date_time").gte("start_date_time", f"{today_str}T00:00:00").execute()
        today_logs = dash_res.data or []
        
        feeds = sum(1 for l in today_logs if l.get("type") == "Feed")
        diapers = sum(1 for l in today_logs if l.get("type") == "Diaper")
        sleep_mins = sum(int(l["note"].split("Slept for ")[1].split(" minutes")[0]) for l in today_logs if l.get("type") == "Sleep" and "Slept for" in l.get("note", ""))
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💤 Sleep", f"{round(sleep_mins/60, 1)}h")
        c2.metric("🍼 Feeds", feeds)
        c3.metric("🧷 Diapers", diapers)
    except:
        pass

    st.divider()

    # --- MAIN APP TABS ---
    tab_track, tab_analytics = st.tabs(["📝 Track & Log", "📊 History & Trends"])

    with tab_track:
        if "sleep_active" not in st.session_state:
            st.session_state.sleep_active = False
            st.session_state.sleep_start_time = None

        action = st.radio("Select Activity", ["Feed", "Sleep", "Diaper", "Note"], horizontal=True)

        def save_log(act_type, note_text, start_time=None):
            data = {
                "type": act_type,
                "created_by_caregiver": current_caregiver,
                "note": note_text,
                "start_date_time": (start_time or datetime.now()).isoformat()
            }
            try:
                supabase.schema("public").table("baby_logs").insert(data).execute()
                st.success(f"{act_type} saved by {current_caregiver}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        if action == "Feed":
            with st.form("feed_form", clear_on_submit=True):
                st.write(f"Logging as: **{current_caregiver}**")
                ftype = st.selectbox("Type", ["Breast Milk", "Formula", "Solid"])
                amt = st.number_input("Amount (ml / oz)", min_value=0.0, step=10.0)
                note = st.text_area("Extra Notes", placeholder="e.g., drank 120ml, burped well...")
                if st.form_submit_button("Save Feed"):
                    final_note = f"{ftype} ({amt}ml) - {note}" if amt > 0 else f"{ftype} - {note}"
                    save_log("Feed", final_note)

        elif action == "Sleep":
            st.subheader("💤 Sleep Tracker")
            st.write(f"Logging as: **{current_caregiver}**")
            
            if not st.session_state.sleep_active:
                mode = st.radio("Mode", ["Start Now", "Add Past Start Time"], horizontal=True)
                past_t = None
                if mode == "Add Past Start Time":
                    d = st.date_input("Date", datetime.now().date())
                    t = st.time_input("Time", (datetime.now() - timedelta(hours=1)).time())
                    past_t = datetime.combine(d, t)

                if st.button("🚀 Start Sleep Timer", use_container_width=True):
                    st.session_state.sleep_active = True
                    st.session_state.sleep_start_time = past_t or datetime.now()
                    st.rerun()
            else:
                st.warning(f"🔴 Sleeping! Started at {st.session_state.sleep_start_time.strftime('%H:%M:%S')}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Stop & Save", type="primary", use_container_width=True):
                        end_t = datetime.now()
                        mins = int((end_t - st.session_state.sleep_start_time).total_seconds() / 60)
                        note = f"Slept for {mins} minutes ({st.session_state.sleep_start_time.strftime('%H:%M')} - {end_t.strftime('%H:%M')})"
                        save_log("Sleep", note, st.session_state.sleep_start_time)
                        st.session_state.sleep_active = False
                with col2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.sleep_active = False
                        st.rerun()

        elif action == "Diaper":
            with st.form("diaper_form", clear_on_submit=True):
                st.write(f"Logging as: **{current_caregiver}**")
                status = st.selectbox("Status", ["Wet", "Dirty", "Both"])
                note = st.text_area("Extra Notes", placeholder="e.g., minor rash, heavy wet...")
                if st.form_submit_button("Save Diaper"):
                    final_note = f"Diaper: {status} - {note}" if note else f"Diaper: {status}"
                    save_log("Diaper", final_note)

        elif action == "Note":
            with st.form("note_form", clear_on_submit=True):
                st.write(f"Logging as: **{current_caregiver}**")
                note = st.text_area("Details", placeholder="Enter milestone, mood, or health note...")
                if st.form_submit_button("Save Note"):
                    save_log("Note", note)

    with tab_analytics:
        st.subheader("📈 Trends & Timeline")
        try:
            chart_res = supabase.schema("public").table("baby_logs").select("type, start_date_time").order("start_date_time", desc=False).limit(100).execute()
            if chart_res.data:
                df = pd.DataFrame(chart_res.data)
                df["date"] = pd.to_datetime(df["start_date_time"]).dt.strftime("%Y-%m-%d")
                chart_data = df.groupby(["date", "type"]).size().unstack(fill_value=0)
                st.bar_chart(chart_data)
        except:
            st.info("Analytics will appear once data is logged.")

        st.divider()
        st.subheader("Recent Activity History")
        try:
            res = supabase.schema("public").table("baby_logs").select("*").order("start_date_time", desc=True).limit(20).execute()
            for log in (res.data or []):
                col_i, col_d = st.columns([5, 1])
                with col_i:
                    st.markdown(f"**{log.get('type').upper()}** — *{log.get('created_by_caregiver')}*")
                    if log.get('note'): st.write(f"📝 {log.get('note')}")
                    st.caption(f"{log.get('start_date_time', '').replace('T', ' ')[:16]}")
                with col_d:
                    if st.button("❌", key=f"del_{log.get('id')}"):
                        supabase.schema("public").table("baby_logs").delete().eq("id", log.get('id')).execute()
                        st.rerun()
                st.write("---")
        except Exception as e:
            st.error(f"Error loading history: {e}")
