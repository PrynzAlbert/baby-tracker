from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import pandas as pd
import streamlit as st
from supabase import create_client

# -------------------------------------------------------------------------------------
# App Configuration
# -------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Smart Baby",
    page_icon="🍼",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    h1, h2, h3, h4, h5, h6 { color: #F1F5F9 !important; }
    p, label, span, .stMarkdown { color: #E2E8F0 !important; }

    input, textarea, .stTextInput input, .stDateInput input, .stTimeInput input {
        color: #FFFFFF !important;
        background-color: #1E293B !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }

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

    .stButton>button {
        background-color: #38BDF8;
        color: #0F172A;
        border-radius: 12px;
        border: none;
        font-weight: 700;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #0EA5E9;
        color: #FFFFFF;
    }

    .stFormSubmitButton>button {
        background-color: #22C55E;
        color: #FFFFFF;
        border-radius: 12px;
        border: none;
        font-weight: 700;
        width: 100%;
        padding: 0.6rem;
    }
    .stFormSubmitButton>button:hover { background-color: #16A34A; }

    div[data-testid="stMetric"] {
        background-color: #1E293B;
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #334155;
    }
    div[data-testid="stMetric"] label { color: #94A3B8 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #38BDF8 !important; }

    .bold-name {
        font-weight: 700;
        color: #38BDF8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------------------------
# Logging & Initialization
# -------------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)


@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


supabase = init_supabase()


# -------------------------------------------------------------------------------------
# Validation Helpers
# -------------------------------------------------------------------------------------
def is_valid_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1]


def is_family_ready(profile: dict | None) -> bool:
    return bool(profile and profile.get("family_id"))


# -------------------------------------------------------------------------------------
# Database Helpers
# -------------------------------------------------------------------------------------
def get_profile_by_user(user_id: str | None) -> dict | None:
    if not user_id:
        return None
    try:
        response = (
            supabase.schema("public")
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        return (response.data or [None])[0]
    except Exception:
        logging.exception("Failed to fetch profile for user %s", user_id)
        return None


def get_family_members(family_id: str | None) -> list[dict]:
    if not family_id:
        return []
    try:
        response = (
            supabase.schema("public")
            .table("profiles")
            .select("id, caregiver_name, baby_name")
            .eq("family_id", family_id)
            .execute()
        )
        return response.data or []
    except Exception:
        logging.exception("Failed to fetch family members for %s", family_id)
        return []


def update_caregiver_name(user_id: str, new_name: str) -> bool:
    try:
        supabase.schema("public").table("profiles").update({"caregiver_name": new_name}).eq("id", user_id).execute()
        return True
    except Exception:
        logging.exception("Failed to update caregiver name")
        return False


def get_local_now() -> datetime:
    """Return current local time based on the browser's timezone.
    Streamlit does not provide timezone offset directly, so we use the browser's local
    time for front-end interaction and store it in UTC for server values only when needed.
    """
    return datetime.now()


# -------------------------------------------------------------------------------------
# Data Aggregation Helpers
# -------------------------------------------------------------------------------------
def calc_age_text(baby_dob_value: str | None) -> str:
    if not baby_dob_value:
        return ""
    try:
        dob = datetime.strptime(baby_dob_value, "%Y-%m-%d").date()
        days_old = (datetime.now().date() - dob).days
        if days_old < 30:
            return f"{days_old} days old"
        if days_old < 365:
            return f"{round(days_old / 30, 1)} months old"
        return f"{round(days_old / 365, 1)} years old"
    except Exception:
        logging.exception("Unable to calculate age for %s", baby_dob_value)
        return ""


def fetch_today_logs(family_id: str | None) -> list[dict]:
    if not family_id:
        return []
    today = get_local_now().strftime("%Y-%m-%d")
    try:
        response = (
            supabase.schema("public")
            .table("baby_logs")
            .select("*")
            .eq("family_id", family_id)
            .gte("start_date_time", f"{today}T00:00:00")
            .execute()
        )
        return response.data or []
    except Exception:
        logging.exception("Failed to fetch today's logs for family %s", family_id)
        return []


def fetch_recent_logs(family_id: str | None, limit: int = 20) -> list[dict]:
    if not family_id:
        return []
    try:
        response = (
            supabase.schema("public")
            .table("baby_logs")
            .select("*")
            .eq("family_id", family_id)
            .order("start_date_time", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception:
        logging.exception("Failed to fetch recent logs for family %s", family_id)
        return []


def fetch_history_chart(family_id: str | None) -> pd.DataFrame:
    if not family_id:
        return pd.DataFrame()
    try:
        response = (
            supabase.schema("public")
            .table("baby_logs")
            .select("type, start_date_time")
            .eq("family_id", family_id)
            .order("start_date_time", desc=False)
            .limit(100)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["start_date_time"]).dt.strftime("%Y-%m-%d")
        return df.groupby(["date", "type"]).size().unstack(fill_value=0)
    except Exception:
        logging.exception("Failed to fetch chart history for family %s", family_id)
        return pd.DataFrame()


# -------------------------------------------------------------------------------------
# Log Management
# -------------------------------------------------------------------------------------
def save_log(
    act_type: str,
    note_text: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    duration_minutes: int | None = None,
) -> None:
    profile = st.session_state.get("profile")
    if not profile:
        st.error("Your profile is not loaded yet.")
        return

    family_id = profile.get("family_id")
    if not family_id:
        st.error("This account is not attached to a family yet.")
        return

    now_value = get_local_now()
    payload: dict[str, Any] = {
        "type": act_type,
        "created_by_caregiver": profile.get("caregiver_name", "Caregiver"),
        "note": note_text,
        "family_id": family_id,
        "start_date_time": (start_time or now_value).isoformat(),
    }
    if end_time is not None:
        payload["end_date_time"] = end_time.isoformat()
    if duration_minutes is not None:
        payload["duration_minutes"] = int(duration_minutes)

    try:
        supabase.schema("public").table("baby_logs").insert(payload).execute()
        st.success(f"{act_type} saved successfully!")
        st.rerun()
    except Exception:
        logging.exception("Error saving log for family %s", family_id)
        st.error("Failed to save this log. Please try again.")


def delete_log(log_id: str | None) -> None:
    if not log_id:
        return
    try:
        supabase.schema("public").table("baby_logs").delete().eq("id", log_id).execute()
        st.rerun()
    except Exception:
        logging.exception("Failed to delete log %s", log_id)
        st.error("Could not delete that log.")


def reset_session_after_logout() -> None:
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.sleep_active = False
    st.session_state.sleep_start_time = None


# -------------------------------------------------------------------------------------
# Session Initialization
# -------------------------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "sleep_active" not in st.session_state:
    st.session_state.sleep_active = False
if "sleep_start_time" not in st.session_state:
    st.session_state.sleep_start_time = None

try:
    session = supabase.auth.get_session()
    if session and getattr(session, "user", None):
        st.session_state.user = session.user
        st.session_state.profile = get_profile_by_user(session.user.id)
except Exception:
    logging.exception("Failed to restore existing session")


# -------------------------------------------------------------------------------------
# Authentication UI
# -------------------------------------------------------------------------------------
def render_auth_screen() -> None:
    st.title("🍼 Smart Baby")
    st.caption("Sign in or create your account to begin.")

    tab_login, tab_signup = st.tabs(["Sign In", "Register Email"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if not email or not password:
                    st.error("Please enter both email and password.")
                elif not is_valid_email(email):
                    st.error("Please use a valid email address.")
                else:
                    try:
                        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        if result.user:
                            st.session_state.user = result.user
                            st.session_state.profile = get_profile_by_user(result.user.id)
                            st.rerun()
                        else:
                            st.error("Login failed. Please check your credentials.")
                    except Exception:
                        logging.exception("Login failed")
                        st.error("Login failed. Please check your credentials.")

    with tab_signup:
        with st.form("signup_form"):
            reg_email = st.text_input("Email", key="su_email")
            reg_password = st.text_input("Password", type="password", key="su_pass")
            if st.form_submit_button("Continue to Profile Setup"):
                if not reg_email or not reg_password:
                    st.error("Please enter both email and password.")
                elif not is_valid_email(reg_email):
                    st.error("Please use a valid email address.")
                elif len(reg_password) < 8:
                    st.error("Password must be at least 8 characters long.")
                else:
                    try:
                        auth_res = supabase.auth.sign_up({"email": reg_email, "password": reg_password})
                        if auth_res.user:
                            st.session_state.user = auth_res.user
                            st.session_state.profile = None
                            st.success("Account created! Please complete your profile below.")
                            st.rerun()
                        else:
                            st.error("Registration failed. Please try again.")
                    except Exception:
                        logging.exception("Registration failed")
                        st.error("Registration failed. Please try again.")


# -------------------------------------------------------------------------------------
# Profile Setup UI
# -------------------------------------------------------------------------------------
def render_profile_setup() -> None:
    st.title("👶 Setup Baby Profile")
    st.caption("Almost done! Tell us a bit about your family.")

    with st.form("profile_setup_form"):
        caregiver_name = st.text_input("Your Caregiver Username", placeholder="e.g. Albert, Audra...")
        setup_mode = st.radio(
            "Family Setup",
            ["Create New Baby Profile", "Join Existing Family (Partner Code)"]
        )

        baby_name = ""
        baby_dob = datetime.now().date()
        family_code = ""

        if setup_mode == "Create New Baby Profile":
            baby_name = st.text_input("Baby's Name", placeholder="e.g. Leo")
            baby_dob = st.date_input("Baby's Date of Birth", datetime.now().date())
        else:
            family_code = st.text_input(
                "Family Invite Code",
                placeholder="Paste partner's family code here..."
            )

        if st.form_submit_button("Complete Setup"):
            if not caregiver_name:
                st.error("Please enter your caregiver username.")
            elif setup_mode == "Create New Baby Profile" and not baby_name:
                st.error("Please enter your baby's name.")
            elif setup_mode == "Join Existing Family (Partner Code)" and not family_code:
                st.error("Please enter a family invite code.")
            else:
                try:
                    user_id = st.session_state.user.id
                    assigned_family_id = None
                    final_baby_name = baby_name
                    final_baby_dob = str(baby_dob)

                    if setup_mode == "Join Existing Family (Partner Code)":
                        match_res = (
                            supabase.schema("public")
                            .table("profiles")
                            .select("family_id, baby_name, baby_dob")
                            .eq("family_id", family_code)
                            .limit(1)
                            .execute()
                        )
                        if not match_res.data:
                            st.error("Invalid family invite code. Please check with your partner.")
                            st.stop()
                        assigned_family_id = match_res.data[0]["family_id"]
                        final_baby_name = match_res.data[0]["baby_name"]
                        final_baby_dob = match_res.data[0]["baby_dob"]
                    else:
                        assigned_family_id = uuid4().hex[:8].upper()

                    profile_data = {
                        "id": user_id,
                        "caregiver_name": caregiver_name,
                        "baby_name": final_baby_name,
                        "baby_dob": final_baby_dob,
                        "family_id": assigned_family_id,
                    }

                    existing_profile = get_profile_by_user(user_id)
                    if existing_profile:
                        supabase.schema("public").table("profiles").update(profile_data).eq("id", user_id).execute()
                    else:
                        supabase.schema("public").table("profiles").insert(profile_data).execute()

                    st.session_state.profile = get_profile_by_user(user_id)
                    st.rerun()
                except Exception:
                    logging.exception("Profile setup failed")
                    st.error("Profile creation failed. Please try again.")


# -------------------------------------------------------------------------------------
# Settings UI
# -------------------------------------------------------------------------------------
def render_settings() -> None:
    profile = st.session_state.profile
    user_id = st.session_state.user.id if st.session_state.user else None

    if not profile or not user_id:
        st.error("Profile not found.")
        return

    st.title("⚙️ Settings")

    st.subheader("👤 Profile")
    current_caregiver = profile.get("caregiver_name", "Caregiver")
    new_caregiver_name = st.text_input("Your Caregiver Name", value=current_caregiver)

    if st.button("Update Name"):
        if new_caregiver_name and new_caregiver_name != current_caregiver:
            if update_caregiver_name(user_id, new_caregiver_name):
                st.session_state.profile = get_profile_by_user(user_id)
                st.success("Name updated successfully!")
                st.rerun()
            else:
                st.error("Failed to update name.")
        else:
            st.info("No changes to save.")

    st.divider()

    st.subheader("👨‍👩‍👧‍👦 Family Management")
    family_id = profile.get("family_id")

    if family_id:
        st.markdown("#### Family Invite Code")
        st.info("Share this code with your partner to join your family:")
        st.code(family_id, language="text")
        st.caption("This code can be pasted in the 'Join Existing Family' option during registration.")

        st.divider()
        st.markdown("#### Family Members")
        family_members = get_family_members(family_id)

        if family_members:
            for member in family_members:
                member_name = member.get("caregiver_name", "Unknown")
                baby_name = member.get("baby_name", "")
                st.write(f"• <span class='bold-name'>{member_name}</span>", unsafe_allow_html=True)
                if baby_name:
                    st.caption(f"Tracking: {baby_name}")
        else:
            st.caption("No family members yet.")
    else:
        st.warning("Family ID not found. Please complete your profile setup.")

    st.divider()

    st.subheader("🔐 Account")
    st.write(f"Email: {st.session_state.user.email}")

    if st.button("Change Password"):
        st.info("Password changes can be managed through your email. Check your email for a password reset link.")


# -------------------------------------------------------------------------------------
# Main App UI
# -------------------------------------------------------------------------------------
def render_main_app() -> None:
    profile = st.session_state.profile
    if not profile:
        reset_session_after_logout()
        st.rerun()

    current_caregiver = profile.get("caregiver_name", "Caregiver")
    baby_name = profile.get("baby_name", "Baby")
    baby_dob_str = profile.get("baby_dob")
    family_id = profile.get("family_id")
    age_text = calc_age_text(baby_dob_str)

    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    if st.session_state.current_page == "settings":
        render_settings()
        return

    with st.sidebar:
        st.markdown(
            f"<div>Signed in as:<br/><span class='bold-name'>{current_caregiver}</span></div>",
            unsafe_allow_html=True,
        )
        if baby_name:
            st.caption(f"Baby: {baby_name} ({age_text})")

        st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.current_page = "home"
                st.rerun()
        with col2:
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.current_page = "settings"
                st.rerun()
        with col3:
            if st.button("🚪 Logout", use_container_width=True):
                try:
                    supabase.auth.sign_out()
                except Exception:
                    logging.exception("Failed to sign out")
                reset_session_after_logout()
                st.session_state.current_page = "home"
                st.rerun()

    st.title(f"🍼 {baby_name}'s Tracker")
    st.markdown(
        f"<div>Welcome back, <span class='bold-name'>{current_caregiver}</span>!</div>",
        unsafe_allow_html=True,
    )

    today_logs = fetch_today_logs(family_id)
    feeds = sum(1 for item in today_logs if item.get("type") == "Feed")
    diapers = sum(1 for item in today_logs if item.get("type") == "Diaper")
    sleep_mins = sum(
        int(item.get("duration_minutes") or 0)
        for item in today_logs
        if item.get("type") == "Sleep"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("💤 Sleep", f"{round(sleep_mins / 60, 1)}h")
    c2.metric("🍼 Feeds", feeds)
    c3.metric("🧷 Diapers", diapers)

    st.divider()

    tab_track, tab_analytics = st.tabs(["📝 Track & Log", "📊 History & Trends"])

    with tab_track:
        action = st.radio("Select Activity", ["Feed", "Sleep", "Diaper", "Note"], horizontal=True)

        if action == "Feed":
            with st.form("feed_form", clear_on_submit=True):
                feed_type = st.selectbox("Type", ["Breast Milk", "Formula", "Solid"])
                amount = st.number_input("Amount (ml / oz)", min_value=0.0, step=10.0)
                note = st.text_area("Extra Notes", placeholder="e.g., drank 120ml, burped well...")
                if st.form_submit_button("Save Feed"):
                    final_note = f"{feed_type} ({amount}ml) - {note}" if amount > 0 else f"{feed_type} - {note}"
                    save_log("Feed", final_note)

        elif action == "Sleep":
            st.subheader("💤 Sleep Tracker")

            if not st.session_state.sleep_active:
                mode = st.radio("Mode", ["Start Now", "Add Past Start Time"], horizontal=True)
                past_start_time = None

                if mode == "Add Past Start Time":
                    s_date = st.date_input("Date", datetime.now().date())
                    s_time = st.time_input("Time", (datetime.now() - timedelta(hours=1)).time())
                    past_start_time = datetime.combine(s_date, s_time)

                if st.button("🚀 Start Sleep Timer"):
                    st.session_state.sleep_active = True
                    st.session_state.sleep_start_time = get_local_now()
                    st.rerun()
            else:
                started_at = st.session_state.sleep_start_time
                st.warning(f"🔴 Sleeping! Started at {started_at.strftime('%H:%M:%S')}")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Stop & Save"):
                        end_time = get_local_now()
                        duration_minutes = max(int((end_time - started_at).total_seconds() / 60), 0)
                        note_text = (
                            f"Slept for {duration_minutes} minutes "
                            f"({started_at.strftime('%H:%M')} - {end_time.strftime('%H:%M')})"
                        )
                        save_log(
                            "Sleep",
                            note_text,
                            start_time=started_at,
                            end_time=end_time,
                            duration_minutes=duration_minutes,
                        )
                        st.session_state.sleep_active = False
                        st.session_state.sleep_start_time = None

                with col2:
                    if st.button("Cancel"):
                        st.session_state.sleep_active = False
                        st.session_state.sleep_start_time = None
                        st.rerun()

        elif action == "Diaper":
            with st.form("diaper_form", clear_on_submit=True):
                status = st.selectbox("Status", ["Wet", "Dirty", "Both"])
                note = st.text_area("Extra Notes", placeholder="e.g., minor rash, heavy wet...")
                if st.form_submit_button("Save Diaper"):
                    final_note = f"Diaper: {status} - {note}" if note else f"Diaper: {status}"
                    save_log("Diaper", final_note)

        elif action == "Note":
            with st.form("note_form", clear_on_submit=True):
                note = st.text_area("Details", placeholder="Enter milestone, mood, or health note...")
                if st.form_submit_button("Save Note"):
                    save_log("Note", note)

    with tab_analytics:
        st.subheader("📈 Trends & Timeline")
        chart_data = fetch_history_chart(family_id)
        if chart_data.empty:
            st.info("Analytics will appear once data is logged.")
        else:
            st.bar_chart(chart_data, use_container_width=True)

        st.divider()
        st.subheader("Recent Activity History")

        recent_logs = fetch_recent_logs(family_id, limit=20)
        if not recent_logs:
            st.info("No activity yet. Start logging your baby's routine.")
        else:
            for log in recent_logs:
                log_id = log.get("id")
                col_i, col_d = st.columns([5, 1])
                with col_i:
                    log_type = (log.get("type") or "").upper()
                    caregiver = log.get("created_by_caregiver") or "Caregiver"
                    st.markdown(
                        f"<span class='bold-name'>{log_type}</span> — *{caregiver}*",
                        unsafe_allow_html=True,
                    )
                    if log.get("note"):
                        st.write(f"📝 {log.get('note')}")
                    if log.get("start_date_time"):
                        st.caption(log.get("start_date_time", "").replace("T", " ")[:16])
                with col_d:
                    if st.button("❌", key=f"del_{log_id}"):
                        delete_log(log_id)
                st.write("---")


# -------------------------------------------------------------------------------------
# Routing
# -------------------------------------------------------------------------------------
if st.session_state.user is None:
    render_auth_screen()
elif not st.session_state.profile:
    render_profile_setup()
else:
    render_main_app()
