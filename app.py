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
    :root {
        /* Warm, modern color palette */
        --bg-primary: #FFF8F5;
        --bg-secondary: #FFF1EA;
        --bg-tertiary: #FFE8DC;
        --accent-warm: #FF9F7F;
        --accent-bold: #FF7A5C;
        --accent-soft: #FFB8A3;
        --text-primary: #3D2817;
        --text-secondary: #6B4423;
        --text-light: #8B6A52;
        --border-color: #F5D4C8;
        --success-color: #6BAA75;
        --info-color: #5B9CD6;
    }

    .stApp { 
        background-color: #FFF8F5; 
        color: #3D2817; 
    }
    
    h1, h2, h3, h4, h5, h6 { 
        color: #3D2817 !important; 
        font-weight: 700 !important;
    }
    
    p, label, span, .stMarkdown { 
        color: #6B4423 !important; 
    }

    input, textarea, .stTextInput input, .stDateInput input, .stTimeInput input {
        color: #3D2817 !important;
        background-color: #FFF1EA !important;
        border: 1.5px solid #F5D4C8 !important;
        border-radius: 8px !important;
    }
    
    input::placeholder {
        color: #A0887A !important;
    }

    .stSelectbox div[data-baseweb="select"] {
        background-color: #FFF1EA !important;
        color: #3D2817 !important;
        border-radius: 8px !important;
        border: 1.5px solid #F5D4C8 !important;
    }
    .stSelectbox span { color: #3D2817 !important; }

    div[data-baseweb="popover"] div, div[data-baseweb="menu"] div {
        background-color: #FFF1EA !important;
        color: #3D2817 !important;
    }
    div[data-baseweb="menu"] div:hover {
        background-color: #FFE8DC !important;
        color: #FF7A5C !important;
    }

    .stRadio label { 
        color: #3D2817 !important; 
        font-weight: 600 !important; 
    }
    
    .stRadio div[role="radiogroup"] {
        gap: 1.5rem !important;
    }

    .stButton>button {
        background-color: #FF7A5C;
        color: #FFFFFF;
        border-radius: 10px;
        border: none;
        font-weight: 700;
        padding: 0.6rem 1rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #FF9F7F;
        color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(255, 122, 92, 0.3);
    }

    .stFormSubmitButton>button {
        background-color: #6BAA75;
        color: #FFFFFF;
        border-radius: 10px;
        border: none;
        font-weight: 700;
        width: 100%;
        padding: 0.7rem;
    }
    .stFormSubmitButton>button:hover { 
        background-color: #5A9563;
        box-shadow: 0 4px 12px rgba(107, 170, 117, 0.3);
    }

    div[data-testid="stMetric"] {
        background-color: #FFF1EA;
        padding: 14px;
        border-radius: 10px;
        border: 1.5px solid #F5D4C8;
    }
    div[data-testid="stMetric"] label { 
        color: #8B6A52 !important; 
        font-size: 0.85rem !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { 
        color: #FF7A5C !important; 
        font-size: 1.8rem !important;
    }

    .family-code-box {
        background: linear-gradient(135deg, rgba(255, 122, 92, 0.08), rgba(255, 241, 234, 0.9));
        border: 2px solid #FF9F7F;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        margin: 18px 0;
    }
    .family-code-display {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 0.24rem;
        color: #FF7A5C;
        font-family: "SFMono-Regular", Consolas, monospace;
    }
    
    .member-card {
        background-color: #FFF1EA;
        border: 1.5px solid #F5D4C8;
        border-radius: 10px;
        padding: 12px 14px;
        margin: 8px 0;
    }
    .member-card strong {
        color: #FF7A5C !important;
    }
    
    .nav-btn > button {
        border-radius: 10px;
    }
    .danger-btn > button {
        background-color: #E74C3C !important;
        color: #FFFFFF !important;
    }
    .danger-btn > button:hover {
        background-color: #C0392B !important;
    }
    
    .stDivider {
        background-color: #F5D4C8 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #6B4423 !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #FF7A5C !important;
    }
    
    .stAlert {
        border-radius: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------------------------
# Logging & Initialization
# -------------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@st.cache_resource
def init_supabase():
    """Initialize Supabase client."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


supabase = init_supabase()


# -------------------------------------------------------------------------------------
# Validation Helpers
# -------------------------------------------------------------------------------------
def is_valid_email(email: str) -> bool:
    """Validate email format."""
    return "@" in email and "." in email.split("@")[-1]


def is_family_ready(profile: dict | None) -> bool:
    """Check if profile has a valid family_id."""
    return bool(profile and profile.get("family_id"))


# -------------------------------------------------------------------------------------
# Database Helpers
# -------------------------------------------------------------------------------------
def get_profile_by_user(user_id: str | None) -> dict | None:
    """Fetch user profile from database."""
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
    except Exception as e:
        logger.exception("Failed to fetch profile for user %s: %s", user_id, str(e))
        return None


def get_family_members(family_id: str | None) -> list[dict]:
    """Fetch all caregivers in a family."""
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
    except Exception as e:
        logger.exception("Failed to fetch family members for %s: %s", family_id, str(e))
        return []


# -------------------------------------------------------------------------------------
# Data Aggregation Helpers
# -------------------------------------------------------------------------------------
def calc_age_text(baby_dob_value: str | None) -> str:
    """Calculate a human-readable age string."""
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
    except Exception as e:
        logger.exception("Unable to calculate age for %s: %s", baby_dob_value, str(e))
        return ""


def fetch_today_logs(family_id: str | None) -> list[dict]:
    """Fetch all logs for today, scoped to family."""
    if not family_id:
        return []
    today = datetime.now().strftime("%Y-%m-%d")
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
    except Exception as e:
        logger.exception("Failed to fetch today's logs for family %s: %s", family_id, str(e))
        return []


def fetch_recent_logs(family_id: str | None, limit: int = 20) -> list[dict]:
    """Fetch recent logs, scoped to family."""
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
    except Exception as e:
        logger.exception("Failed to fetch recent logs for family %s: %s", family_id, str(e))
        return []


def fetch_history_chart(family_id: str | None) -> pd.DataFrame:
    """Fetch logs for chart visualization, scoped to family."""
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
    except Exception as e:
        logger.exception("Failed to fetch chart history for family %s: %s", family_id, str(e))
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
    feed_type: str | None = None,
    amount_ml: float | None = None,
    diaper_status: str | None = None,
) -> None:
    """Save a log entry to the database."""
    profile = st.session_state.get("profile")
    if not profile:
        st.error("Your profile is not loaded yet.")
        return

    family_id = profile.get("family_id")
    if not family_id:
        st.error("This account is not attached to a family yet.")
        return

    # Build payload with only non-None values
    payload: dict[str, Any] = {
        "type": act_type,
        "created_by_caregiver": profile.get("caregiver_name", "Caregiver"),
        "note": note_text,
        "family_id": family_id,
        "start_date_time": (start_time or datetime.now()).isoformat(),
        "source_app": "smart_baby",
    }
    
    # Add optional fields only if provided
    if end_time is not None:
        payload["end_date_time"] = end_time.isoformat()
    if duration_minutes is not None:
        payload["duration_minutes"] = int(duration_minutes)
    if feed_type is not None:
        payload["feed_type"] = feed_type
    if amount_ml is not None:
        payload["amount_ml"] = float(amount_ml)
    if diaper_status is not None:
        payload["diaper_status"] = diaper_status

    logger.info("Attempting to save log: %s for family %s", act_type, family_id)
    logger.debug("Payload: %s", payload)
    
    try:
        result = supabase.schema("public").table("baby_logs").insert(payload).execute()
        logger.info("Log saved successfully: %s", result.data)
        st.success(f"{act_type} saved successfully!")
        st.rerun()
    except Exception as e:
        error_msg = str(e)
        logger.exception("Error saving log for family %s. Error details: %s", family_id, error_msg)
        st.error(f"Failed to save this log. Error: {error_msg[:150]}")


def delete_log(log_id: str | None) -> None:
    """Delete a log entry."""
    if not log_id:
        return
    try:
        supabase.schema("public").table("baby_logs").delete().eq("id", log_id).execute()
        logger.info("Log deleted successfully: %s", log_id)
        st.rerun()
    except Exception as e:
        logger.exception("Failed to delete log %s: %s", log_id, str(e))
        st.error("Could not delete that log.")


def reset_session_after_logout() -> None:
    """Clear session state on logout."""
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
if "current_page" not in st.session_state:
    st.session_state.current_page = "tracker"

try:
    session = supabase.auth.get_session()
    if session and getattr(session, "user", None):
        st.session_state.user = session.user
        st.session_state.profile = get_profile_by_user(session.user.id)
except Exception as e:
    logger.exception("Failed to restore existing session: %s", str(e))


# -------------------------------------------------------------------------------------
# Authentication UI
# -------------------------------------------------------------------------------------
def render_auth_screen() -> None:
    """Display login and signup screens."""
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
                    except Exception as e:
                        logger.exception("Login failed: %s", str(e))
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
                    except Exception as e:
                        logger.exception("Registration failed: %s", str(e))
                        st.error("Registration failed. Please try again.")


# -------------------------------------------------------------------------------------
# Profile Setup UI
# -------------------------------------------------------------------------------------
def render_profile_setup() -> None:
    """Display profile setup screen."""
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
                except Exception as e:
                    logger.exception("Profile setup failed: %s", str(e))
                    st.error("Profile creation failed. Please try again.")


# -------------------------------------------------------------------------------------
# Settings UI
# -------------------------------------------------------------------------------------
def render_settings() -> None:
    """Display settings and family sharing page."""
    profile = st.session_state.profile
    if not profile:
        return

    st.title("⚙️ Settings")
    st.caption("Manage your family, invite your partner, and sign out securely.")

    st.subheader("👤 Profile")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Caregiver", profile.get("caregiver_name", "N/A"))
    with col2:
        st.metric("Baby", profile.get("baby_name", "N/A"))
    st.metric("Baby age", calc_age_text(profile.get("baby_dob")))
    st.divider()

    st.subheader("👨‍👩‍👧 Family")
    family_id = profile.get("family_id")
    if family_id:
        st.markdown("Share this code to invite a partner or another caregiver.")
        st.markdown(
            f"""
            <div class="family-code-box">
                <div class="family-code-display">{family_id}</div>
                <div>Invite your partner to join this family and track routines together.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.code(family_id, language="text")

        st.markdown("**Family Members**")
        family_members = get_family_members(family_id)
        if family_members:
            for member in family_members:
                st.markdown(
                    f"""
                    <div class="member-card">
                        <strong>👤 {member.get('caregiver_name', 'Caregiver')}</strong><br>
                        <small>Tracking: {member.get('baby_name', 'Baby')}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No other family members yet. Share your code above to get started.")
    else:
        st.warning("No family is linked yet. Please complete setup or ask a partner for a code.")

    st.divider()
    st.subheader("🔐 Account")
    if st.session_state.user:
        st.write(f"Email: {st.session_state.user.email}")

    st.divider()
    st.subheader("🚪 Sign Out")
    st.write("Sign out to return to the login screen.")
    if st.button("Log out", use_container_width=True, key="settings_logout"):
        try:
            supabase.auth.sign_out()
        except Exception as e:
            logger.exception("Failed to sign out: %s", str(e))
        reset_session_after_logout()
        st.session_state.current_page = "tracker"
        st.rerun()


# -------------------------------------------------------------------------------------
# Tracker UI
# -------------------------------------------------------------------------------------
def render_tracker_page(family_id: str | None) -> None:
    """Render the main tracking page."""
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
                    save_log(
                        "Feed",
                        final_note,
                        feed_type=feed_type,
                        amount_ml=amount if amount > 0 else None,
                    )

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
                    st.session_state.sleep_start_time = past_start_time or datetime.now()
                    st.rerun()
            else:
                started_at = st.session_state.sleep_start_time
                st.warning(f"🔴 Sleeping! Started at {started_at.strftime('%H:%M:%S')}")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Stop & Save"):
                        end_time = datetime.now()
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
                    save_log("Diaper", final_note, diaper_status=status)

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
                    st.markdown(f"**{log_type}** — *{caregiver}*")
                    if log.get("note"):
                        st.write(f"📝 {log.get('note')}")
                    if log.get("start_date_time"):
                        st.caption(log.get("start_date_time", "").replace("T", " ")[:16])
                with col_d:
                    if st.button("❌", key=f"del_{log_id}"):
                        delete_log(log_id)
                st.write("---")


# -------------------------------------------------------------------------------------
# Main App UI
# -------------------------------------------------------------------------------------
def render_main_app() -> None:
    """Display the main tracking app."""
    profile = st.session_state.profile
    if not profile:
        reset_session_after_logout()
        st.rerun()

    baby_name = profile.get("baby_name", "Baby")
    family_id = profile.get("family_id")
    current_caregiver = profile.get("caregiver_name", "Caregiver")
    age_text = calc_age_text(profile.get("baby_dob"))

    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([4, 1, 1, 1])
    with nav_col1:
        st.title(f"🍼 {baby_name}'s Tracker")
    with nav_col2:
        if st.button("Tracker", use_container_width=True, key="nav_tracker"):
            st.session_state.current_page = "tracker"
            st.rerun()
    with nav_col3:
        if st.button("Settings", use_container_width=True, key="nav_settings"):
            st.session_state.current_page = "settings"
            st.rerun()
    with nav_col4:
        if st.button("Log out", use_container_width=True, key="nav_logout"):
            try:
                supabase.auth.sign_out()
            except Exception as e:
                logger.exception("Failed to sign out: %s", str(e))
            reset_session_after_logout()
            st.session_state.current_page = "tracker"
            st.rerun()

    st.markdown(f"Welcome back, **{current_caregiver}**!")
    st.caption(f"{baby_name} is {age_text}")

    if st.session_state.current_page == "settings":
        render_settings()
    else:
        render_tracker_page(family_id)


# -------------------------------------------------------------------------------------
# Routing
# -------------------------------------------------------------------------------------
if st.session_state.user is None:
    render_auth_screen()
elif not st.session_state.profile:
    render_profile_setup()
else:
    render_main_app()
