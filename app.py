from datetime import datetime, timedelta
import time
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Smart Baby", page_icon="🍼", layout="centered", initial_sidebar_state="collapsed"
)

# App Header
st.title("🍼 Smart Baby")
st.caption("Your lightweight daily companion for tracking baby activities.")

# Initialize session state for logs and sleep timer
if "logs" not in st.session_state:
  st.session_state.logs = []

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
      st.session_state.logs.insert(0, {
          "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
          "action": "Feed",
          "caregiver": caregiver,
          "note": note,
      })
      st.success("Feed logged successfully!")
      st.rerun()

# --- SLEEP TIMER SECTION ---
elif action == "Sleep":
  st.subheader("💤 Sleep Tracker")
  caregiver = st.selectbox("Caregiver (Handoff)", ["Albert", "Partner", "Nanny"], key="sleep_cg")

  if not st.session_state.sleep_active:
    st.info("No sleep timer currently running.")
    
    # Non-form inputs so date/time pickers interact smoothly
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
    # Active timer dashboard layout
    st.warning(f"🔴 **Baby is sleeping!** Started by **{st.session_state.sleep_caregiver}** at {st.session_state.sleep_start_time.strftime('%H:%M:%S')}")
    
    # Placeholder for live counting ticker
    timer_placeholder = st.empty()
    
    col1, col2 = st.columns(2)
    with col1:
      if st.button("Stop & Save Sleep", type="primary", use_container_width=True):
        end_time = datetime.now()
        duration_mins = int((end_time - st.session_state.sleep_start_time).total_seconds() / 60)
        
        st.session_state.logs.insert(0, {
            "timestamp": end_time.strftime("%Y-%m-%d %H:%M"),
            "action": "Sleep",
            "caregiver": caregiver,
            "note": f"Slept for {duration_mins} minutes (Started: {st.session_state.sleep_start_time.strftime('%H:%M')}, Ended: {end_time.strftime('%H:%M')})",
        })
        
        st.session_state.sleep_active = False
        st.session_state.sleep_start_time = None
        st.success("Sleep session saved to history!")
        st.rerun()
        
    with col2:
      if st.button("Cancel Timer", use_container_width=True):
        st.session_state.sleep_active = False
        st.session_state.sleep_start_time = None
        st.rerun()
        
    # Live ticker loop to update duration on screen
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
      st.session_state.logs.insert(0, {
          "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
          "action": "Diaper",
          "caregiver": caregiver,
          "note": note,
      })
      st.success("Diaper logged successfully!")
      st.rerun()

# --- NOTE FORM ---
elif action == "Note":
  with st.form("note_form", clear_on_submit=True):
    st.subheader("Log: Note")
    caregiver = st.selectbox("Caregiver", ["Albert", "Partner", "Nanny"], key="note_cg")
    note = st.text_area("Details")
    
    if st.form_submit_button("Save Note", use_container_width=True):
      st.session_state.logs.insert(0, {
          "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
          "action": "Note",
          "caregiver": caregiver,
          "note": note,
      })
      st.success("Note saved successfully!")
      st.rerun()

# --- ACTIVITY TIMELINE VIEW WITH EDIT/DELETE ---
st.divider()
st.subheader("Recent Activity")

if st.session_state.logs:
  for idx, entry in enumerate(st.session_state.logs):
    with st.container():
      col_info, col_edit, col_del = st.columns([6, 1.5, 1.5])
      
      with col_info:
        st.markdown(f"**{entry['action']}** — *{entry['caregiver']}*")
        if entry['note']:
          st.write(f"📝 {entry['note']}")
        st.caption(f"Logged at {entry['timestamp']}")
      
      with col_edit:
        if st.button("Edit", key=f"edit_{idx}ʿ"):
          st.session_state.editing_index = idx
      with col_del:
        if st.button("Delete", key=f"del_{idx}"):
          st.session_state.logs.pop(idx)
          st.rerun()
          
      # Inline Edit Form if this item is selected for editing
      if st.session_state.get("editing_index") == idx:
        with st.form(f"edit_form_{idx}"):
          st.write(f"**Editing Entry #{idx + 1}**")
          new_note = st.text_area("Update Note / Details", value=entry['note'])
          new_cg = st.selectbox("Update Caregiver", ["Albert", "Partner", "Nanny"], index=["Albert", "Partner", "Nanny"].index(entry['caregiver']) if entry['caregiver'] in ["Albert", "Partner", "Nanny"] else 0)
          
          if st.form_submit_button("Save Changes"):
            st.session_state.logs[idx]['note'] = new_note
            st.session_state.logs[idx]['caregiver'] = new_cg
            st.session_state.editing_index = None
            st.success("Updated successfully!")
            st.rerun()
            
      st.write("---")
  
  if st.button("Clear All History"):
    st.session_state.logs = []
    st.session_state.editing_index = None
    st.rerun()
else:
  st.info("No activities logged yet. Use the selectors above to record your first entry!")
