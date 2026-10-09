from datetime import datetime, timedelta
import time
import pandas as pd
import streamlit as st
from supabase import create_client

# Page Configuration
st.set_page_config(
    page_title="Smart Baby", page_icon="🍼", layout="centered", initial_sidebar_state="collapsed"
)

# --- HIGH-CONTRAST DARK MOBILE THEME CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    h1, h2, h3, h4, h5, h6 { color: #F1F5F9 !important; }
    p, label, span, .stMarkdown { color: #E2E8F0 !important; }
    
    input, textarea { color: #FFFFFF !important; background-color: #1E293B !important; border: 1px solid #475569 !important; border-radius: 8px !important; }
    
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #475569 !important;
    }
    .stSelectbox span { color: #FFFFFF !important; }
    
    div[data-baseweb="popover"] div, div[data-baseweb="menu"] div {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="menu"] div:hover {
        background-color: #334155 !important;
        color: #38BDF8 !important;
    }

    .stRadio label { color: #F8FAFC !important; font-weight: 600 !important; }

    .stButton>button { background-color: #38BDF8; color: #0F172A; border-radius: 12px; border: none; font-weight: 700; padding: 0.5rem 1rem; width: 100%; }
    .stButton>button:hover { background-color: #0EA5E9; color: #FFFFFF; }
    
    .stFormSubmitButton>button { background-color: #22C55E; color: #FFFFFF; border-radius: 12px; border: none; font-weight: 700; width: 100%; padding: 0.6rem; }
    .stFormSubmitButton>button:hover { background-color: #16A34A; }
    
    div[data-testid="stMetric"] { background-color: #1E293B; padding: 12px; border-radius: 12px; border: 1px solid #334155; }
    div[data-testid="stMetric"] label { color: #94A3B8 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #38BDF8 !important; }
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

# --- AUTHENTICATION & MULTI-STEP PROFILE SETUP GATE ---
if not st.session_state.user:
    st.title("🍼 Smart Baby")
    st.caption("Sign in or create your account to begin.")
    
    tab_login, tab_signup = st.tabs(["Sign In", "Register Email"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.user = res.user
                        p_res = supabase.schema("public").table("profiles").select("*").eq("id", res.user.id).execute()
                        if p_res.data:
                            st.session_state.profile = p_res.data[0]
                        st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

    with tab_signup:
        with st.form("signup_form"):
            reg_email = st.text_input("Email", key="su_email")
            reg_password = st.text_input("Password", type="password", key="su_pass")
            if st.form_submit_button("Continue to Profile Setup"):
                if not reg_email or not reg_password:
                    st.error("Please enter email and password.")
                else:
                    try:
                        auth_res = supabase.auth.sign_up({"email": reg_email, "password": reg_password})
                        if auth_res.user:
                            st.session_state.user = auth_res.user
                            st.success("Account created! Please complete your profile below.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Registration failed: {e}")

elif not st.session_state.profile:
    st.title("👶 Setup Baby Profile")
    st.caption("Almost done! Tell us a bit about your family.")
    
    with st.form("profile_setup_form"):
        caregiver_name = st.text_input("Your Caregiver Username", placeholder="e.g. Albert, Sarah...")
        setup_mode = st.radio("Family Setup", ["Create New Baby Profile", "Join Existing Family (Partner Code)"])
        
        baby_name = ""
        baby_dob = datetime.now().date()
        family_code = ""

        if setup_mode == "Create New Baby Profile":
            baby_name = st.text_input("Baby's Name", placeholder="e.g. Leo")
            baby_dob = st.date_input("Baby's Date of Birth", datetime.now().date())
        else:
            family_code = st.text_input("Family Invite Code", placeholder="Paste partner's family code here...")

        if st.form_submit_button("Complete Setup"):
            if not caregiver_name or (setup_mode == "Create New Baby Profile" and not baby_name) or (setup_mode == "Join Existing Family (Partner Code)" and not family_code):
                st.error("Please fill in all required details.")
            else:
                try:
                    user_id = st.session_state.user.id
                    assigned_family_id = None
                    
                    if setup_mode == "Join Existing Family (Partner Code)":
                        match_res = supabase.schema("public").table("profiles").select("family_id, baby_name, baby_dob").eq("family_id", family_code).limit(1).execute()
                        if match_res.data:
                            assigned_family_id = match_res.data[0]["family_id"]
                            baby_name = match_res.data[0]["baby_name"]
                            baby_dob = match_res.data[0]["baby_dob"]
                        else:
                            st.error("Invalid family invite code. Please check with your partner.")
                            st.stop()

                    profile_data = {
                        "id": user_id,
                        "caregiver_name": caregiver_name,
                        "baby_name": baby_name,
                        "baby_dob": str(baby_dob)
                    }
                    if assigned_family_id:
                        profile_data["family_id"] = assigned_family_id

                    supabase.schema("public").table("profiles").insert(profile_data).execute()
                    
                    p_res = supabase.schema("public").table("profiles").select("*").eq("id", user_id).execute()
                    if p_res.data:
                        st.session_state.profile = p_res.data[0]
                        st.rerun()
                except Exception as e:
                    st.error(f"Profile creation failed: {e}")

else:
    # --- MAIN APP (Authenticated & Profile Loaded) ---
    profile = st.session_state.profile
    current_caregiver = profile.get("caregiver_name", "Caregiver")
    baby_name = profile.get("baby_name", "Baby")
    baby_dob_str = profile.get("baby_dob")
    family_id = profile.get("family_id")

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
        
        if family_id:
            st.divider()
            st.markdown("**Family Sharing Code:**")
            st.code(family_id, language="text")
        
        st.divider()
        if st.button("Log Out"):
            try: supabase.auth.sign_out()
            except: pass
            st.session_state.user = None
            st.session_state.profile = None
            st.rerun()

    st.title(f"🍼 {baby_name}'s Tracker")
    st.caption(f"Welcome back, **{current_caregiver}**!")

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
                st.success(f"{act_type} saved successfully!")
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

                if st.button("🚀 Start Sleep Timer"):
                    st.session_state.sleep_active = True
                    st.session_state.sleep_start_time = past_t or datetime.now()
                    st.rerun()
            else:
                st.warning(f"🔴 Sleeping! Started at {st.session_state.sleep_start_time.strftime('%H:%M:%S')}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Stop & Save"):
                        end_t = datetime.now()
                        mins = int((end_t - st.session_state.sleep_start_time).total_seconds() / 60)
                        note = f"Slept for {mins} minutes ({st.session_state.sleep_start_time.strftime('%H:%M')} - {end_t.strftime('%H:%M')})"
                        save_log("Sleep", note, st.session_state.sleep_start_time)
                        st.session_state.sleep_active = False
                with col2:
                    if st.button("Cancel"):
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
            
