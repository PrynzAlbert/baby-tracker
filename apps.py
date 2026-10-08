from datetime import datetime, timedelta
import time
import streamlit as st
from supabase import create_client

# Page Configuration
st.set_page_config(
    page_title="Smart Baby", page_icon="🍼", layout="centered", initial_sidebar_state="collapsed"
)


# Initialize Supabase Connection
@st.cache_resource
def init_supabase():
  return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


supabase = init_supabase()

# App Header
st.title("🍼 Smart Baby")
st.caption("Your lightweight daily companion for tracking baby activities.")

# Initialize sleep timer session state
if "sleep_active" not in st.session_state:
  st.session_state.sleep_active = False
  st.session_state.sleep_start_time = None
  st.session_state.sleep_caregiver = "Albert"

if "editing_index" not in st.session_state:
  st.session_state.editing_index = None

# Quick Action Selector
action = st.radio(
    "Select Activity",
    ["Feed", "Sleep", "Diaper", "Note"],
    horizontal=True,
)

# --- FEED FORM ---
if action == "Feed":
  with st.form("feed_form", clear_on_submit=True):
    st.subheader("Log: Feed")
    caregiver = st.selectbox("Caregiver", ["Albert", "Partner", "Nanny"], key="feed_cg")
    feed_type = st.selectbox("Feed Type", ["Breast Milk", "Formula", "Solid"])
    amount = st.number_input("Amount (ml / oz)", min_value=0.0, step=10.0)
    note = st.text_area("Extra Notes", value=f"{feed_type} - {amount}ml" if amount > 0 else feed_type)

    if st.form_submit_button("Save Feed", use_container_width=True):
      data = {
          "type": "Feed",
          "created_by_caregiver": caregiver,
          "note": note,
          "start_date_time": datetime.now().isoformat(),
      }
      try:
        supabase.schema("public").table("baby_logs").insert(data).execute()
        st.success("Feed saved to database!")
        st.rerun()
      except Exception as e:
        st.error(f"Database Error: {e}")

# --- SLEEP TIMER SECTION ---
elif action == "Sleep":
  st.subheader("💤 Sleep Tracker")
  caregiver = st.selectbox("Caregiver (Handoff)", ["Albert", "Partner", "Nanny"], key="sleep_cg")

  if not st.session_state.sleep_active:
    st.info("No sleep timer currently running.")

    mode = st.radio("Start Mode", ["Start Now", "Add Past Start Time (Forgot to start)"], horizontal=True)

    past_time = None
    if mode == "Add Past Start Time (Forgot to start)":
      col1, col2 = st.columns(2)
      with col1:
        sleep_date = st.date_input("Start Date", datetime.now().date())
      with col2:
        sleep_time = st.time_input("Start Time", (datetime.now() - timedelta(hours=1)).time())
      past_time = datetime.combine(sleep_date, sleep_time)

    if st.button("🚀 Start Sleep Timer", use_container_width=True):
      st.session_state.sleep_active = True
      st.session_state.sleep_start_time = past_time if past_time else datetime.now()
      st.session_state.sleep_caregiver = caregiver
      st.success("Sleep timer started!")
      st.rerun()
  else:
    st.warning(f"🔴 **Baby is sleeping!** Started by **{st.session_state.sleep_caregiver}** at {st.session_state.sleep_start_time.strftime('%H:%M:%S')}")
    timer_placeholder = st.empty()

    col1, col2 = st.columns(2)
    with col1:
      if st.button("Stop & Save Sleep", type="primary", use_container_width=True):
        end_time = datetime.now()
        duration_mins = int((end_time - st.session_state.sleep_start_time).total_seconds() / 60)
        note = f"Slept for {duration_mins} minutes (Started: {st.session_state.sleep_start_time.strftime('%H:%M')}, Ended: {end_time.strftime('%H:%M')})"

        data = {
            "type": "Sleep",
            "created_by_caregiver": caregiver,
            "note": note,
            "start_date_time": st.session_state.sleep_start_time.isoformat(),
        }
        try:
          supabase.schema("public").table("baby_logs").insert(data).execute()
          st.session_state.sleep_active = False
          st.session_state.sleep_start_time = None
          st.success("Sleep session saved to database!")
          st.rerun()
        except Exception as e:
          st.error(f"Database Error: {e}")

    with col2:
      if st.button("Cancel Timer", use_container_width=True):
        st.session_state.sleep_active = False
        st.session_state.sleep_start_time = None
        st.rerun()

    for _ in range(5):
      if not st.session_state.sleep_active:
        break
      elapsed_seconds = int((datetime.now() - st.session_state.sleep_start_time).total_seconds())
      hours, remainder = divmod(elapsed_seconds, 3600)
      minutes, seconds = divmod(remainder, 60)
      timer_placeholder.metric("Current Duration", f"{hours}h {minutes}m {seconds}s")
      time.sleep(1)
    st.rerun()

# --- DIAPER FORM ---
elif action == "Diaper":
  with st.form("diaper_form", clear_on_submit=True):
    st.subheader("Log: Diaper")
    caregiver = st.selectbox("Caregiver", ["Albert", "Partner", "Nanny"], key="diaper_cg")
    diaper_status = st.selectbox("Type", ["Wet", "Dirty", "Both"])
    note = st.text_area("Extra Notes", value=f"Diaper: {diaper_status}")

    if st.form_submit_button("Save Diaper", use_container_width=True):
      data = {
          "type": "Diaper",
          "created_by_caregiver": caregiver,
          "note": note,
          "start_date_time": datetime.now().isoformat(),
      }
      try:
        supabase.schema("public").table("baby_logs").insert(data).execute()
        st.success("Diaper logged to database!")
        st.rerun()
      except Exception as e:
        st.error(f"Database Error: {e}")

# --- NOTE FORM ---
elif action == "Note":
  with st.form("note_form", clear_on_submit=True):
    st.subheader("Log: Note")
    caregiver = st.selectbox("Caregiver", ["Albert", "Partner", "Nanny"], key="note_cg")
    note = st.text_area("Details")

    if st.form_submit_button("Save Note", use_container_width=True):
      data = {
          "type": "Note",
          "created_by_caregiver": caregiver,
          "note": note,
          "start_date_time": datetime.now().isoformat(),
      }
      try:
        supabase.schema("public").table("baby_logs").insert(data).execute()
        st.success("Note saved to database!")
        st.rerun()
      except Exception as e:
        st.error(f"Database Error: {e}")

# --- ACTIVITY TIMELINE VIEW (FETCHED FROM SUPABASE) ---
st.divider()
st.subheader("Recent Activity")

try:
  response = (
      supabase.schema("public")
      .table("baby_logs")
      .select("id, type, created_by_caregiver, note, start_date_time")
      .order("start_date_time", desc=True)
      .limit(25)
      .execute()
  )
  logs = response.data

  if logs:
    for idx, log in enumerate(logs):
      log_id = log.get("id")
      act_type = log.get("type", "Activity")
      caregiver = log.get("created_by_caregiver", "Unknown")
      note_text = log.get("note", "")
      time_raw = log.get("start_date_time")
      
      # Clean up timestamp format for readable display
      time_str = time_raw.replace("T", " ")[:16] if time_raw else "Unknown time"

      with st.container():
        col_info, col_del = st.columns([5, 1])

        with col_info:
          st.markdown(f"**{act_type.upper()}** — *{caregiver}*")
          if note_text:
            st.write(f"📝 {note_text}")
          st.caption(f"Logged at {time_str}")

        with col_del:
          if st.button("Delete", key=f"del_{log_id}"):
            supabase.schema("public").table("baby_logs").delete().eq("id", log_id).execute()
            st.success("Deleted!")
            st.rerun()

        st.write("---")
  else:
    st.info("No activities logged in the database yet. Record your first entry above!")

except Exception as e:
  st.error(f"Timeline Loading Error: {e}")
