from datetime import datetime
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Smart Baby", page_icon="🍼", layout="centered", initial_sidebar_state="collapsed"
)

# App Header
st.title("🍼 Smart Baby")
st.caption("Your lightweight daily companion for tracking baby activities.")

# Session state initialization for mock logs (until we reconnect the database)
if "logs" not in st.session_state:
  st.session_state.logs = []

# Quick Action Selector
action = st.radio(
    "Select Activity",
    ["Feed", "Sleep", "Diaper", "Note"],
    horizontal=True,
)

# Input Form based on selected action
with st.form("smart_baby_form", clear_on_submit=True):
  st.subheader(f"Log: {action}")
  
  caregiver = st.selectbox("Caregiver", ["Albert", "Partner", "Nanny"])
  
  # Dynamic fields based on action type
  if action == "Feed":
    feed_type = st.selectbox("Feed Type", ["Breast Milk", "Formula", "Solid"])
    amount = st.number_input("Amount (ml / oz)", min_value=0.0, step=10.0)
    details = f"{feed_type} - {amount}ml" if amount > 0 else f"{feed_type}"
  elif action == "Sleep":
    duration = st.number_input("Duration (minutes)", min_value=1, value=60)
    details = f"Slept for {duration} mins"
  elif action == "Diaper":
    diaper_status = st.selectbox("Type", ["Wet", "Dirty", "Both"])
    details = f"Diaper: {diaper_status}"
  else:
    details = ""

  note = st.text_area("Extra Notes", value=details)
  submitted = st.form_submit_button("Save Activity", use_container_width=True)

  if submitted:
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "action": action,
        "caregiver": caregiver,
        "note": note,
    }
    st.session_state.logs.insert(0, new_entry)
    st.success("Activity logged successfully!")
    st.rerun()

# Activity Timeline View
st.divider()
st.subheader("Recent Activity")

if st.session_state.logs:
  for entry in st.session_state.logs:
    with st.container():
      st.markdown(f"**{entry['action']}** — *{entry['caregiver']}*")
      if entry['note']:
        st.write(f"📝 {entry['note']}")
      st.caption(f"Logged at {entry['timestamp']}")
      st.write("---")
  
  if st.button("Clear History"):
    st.session_state.logs = []
    st.rerun()
else:
  st.info("No activities logged yet. Use the form above to record your first entry!")
