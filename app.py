from datetime import datetime, timedelta
import time
import pandas as pd
import streamlit as st
from supabase import create_client

# Page Configuration
st.set_page_config(
    page_title="Smart Baby", page_icon="🍼", layout="centered", initial_sidebar_state="collapsed"
)

# --- CUSTOM BRIGHT MOBILE-FRIENDLY CSS & WHITE-ON-WHITE FIXES ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; color: #2D3748; }
    h1, h2, h3, h4 { color: #1A365D !important; }
    
    /* Fix radio button visibility */
    .stRadio label { color: #1A365D !important; font-weight: 700 !important; font-size: 1.1rem !important; }
    
    /* Fix input fields, text areas, and selectboxes text/background color */
    input, textarea { color: #2D3748 !important; background-color: #FFFFFF !important; border: 1px solid #CBD5E0 !important; border-radius: 8px !important; }
    
    /* Fix selectbox internal text and background */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #2D3748 !important;
        border-radius: 8px !important;
        border: 1px solid #CBD5E0 !important;
    }
    .stSelectbox span { color: #2D3748 !important; }
    
    /* Fix dropdown popover list items */
    div[data-baseweb="popover"] div, div[data-baseweb="menu"] div {
        background-color: #FFFFFF !important;
        color: #2D3748 !important;
    }
    div[data-baseweb="menu"] div:hover {
        background-color: #EDF2F7 !important;
        color: #1A365D !important;
    }

    /* Buttons */
    .stButton>button { background-color: #4299E1; color: white; border-radius: 12px; border: none; font-weight: 600; padding: 0.5rem 1rem; }
    .stButton>button:hover { background-color: #3182CE; color: white; }
    .stFormSubmitButton>button { background-color: #48BB78; color: white; border-radius: 12px; border: none; font-weight: 600; width: 100%; }
    
    /* Metric Cards */
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

# Session State Auth Init
if "user" not in st.session_state:
    st.session_state.user = None

try:
    session = supabase.auth.get_session()
    if session and session.user:
        st.session_state.user = session.user
except:
    pass

# --- AUTHENTICATION GATE ---
if not st.session_state.user:
    st.title("🍼 Smart Baby")
    st.caption("Sign in to access your secure family tracker.")
    
    tab_login, tab_signup = st.tabs(["Sign In", "Register"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.user = res.user
                        st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

    with tab_signup:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="su_email")
            new_password = st.text_input("Password", type="password", key="su_pass")
            if st.form_submit_button("Create Account", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": new_email, "password": new_password})
                    st.success("Account created! You can now sign in.")
                except Exception as e:
                    st.error(f"Sign up failed: {e}")

else:
    # --- MAIN APP ---
    user_email = st.session_state.user.email
    default_caregiver = user_email.split("@")[0].capitalize()
    caregiver_options = [default_caregiver, "Partner", "Nanny"]

    with st.sidebar:
        st.write(f"Signed in as:\n**{user_email}**")
        if st.button("Log Out", use_container_width=True):
            try: supabase.auth.sign_out()
            except: pass
            st.session_state.user = None
            st.rerun()

    st.title("🍼 Smart Baby")

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

        def save_log(act_type, note_text, caregiver, start_time=None):
            data = {
                "type": act_type,
                "created_by_caregiver": caregiver,
                "note": note_text,
                "start_date_time": (start_time or datetime.now()).isoformat()
            }
            try:
                supabase.schema("public").table("baby_logs").insert(data).execute()
                st.success(f"{act_type} saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        if action == "Feed":
            with st.form("feed_form", clear_on_submit=True):
                cg = st.selectbox("Caregiver", caregiver_options)
                ftype = st.selectbox("Type", ["Breast Milk", "Formula", "Solid"])
                amt = st.number_input("Amount (ml / oz)", min_value=0.0, step=10.0)
                note = st.text_area("Extra Notes", placeholder="e.g., drank 120ml, burped well...")
                if st.form_submit_button("Save Feed"):
                    final_note = f"{ftype} ({amt}ml) - {note}" if amt > 0 else f"{ftype} - {note}"
                    save_log("Feed", final_note, cg)

        elif action == "Sleep":
            st.subheader("💤 Sleep Tracker")
            cg = st.selectbox("Caregiver", caregiver_options, key="sl_cg")
            
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
                        save_log("Sleep", note, cg, st.session_state.sleep_start_time)
                        st.session_state.sleep_active = False
                with col2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.sleep_active = False
                        st.rerun()

        elif action == "Diaper":
            with st.form("diaper_form", clear_on_submit=True):
                cg = st.selectbox("Caregiver", caregiver_options)
                status = st.selectbox("Status", ["Wet", "Dirty", "Both"])
                note = st.text_area("Extra Notes", placeholder="e.g., minor rash, heavy wet...")
                if st.form_submit_button("Save Diaper"):
                    final_note = f"Diaper: {status} - {note}" if note else f"Diaper: {status}"
                    save_log("Diaper", final_note, cg)

        elif action == "Note":
            with st.form("note_form", clear_on_submit=True):
                cg = st.selectbox("Caregiver", caregiver_options)
                note = st.text_area("Details", placeholder="Enter milestone, mood, or health note...")
                if st.form_submit_button("Save Note"):
                    save_log("Note", note, cg)

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
