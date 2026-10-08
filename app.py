from datetime import datetime
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Baby Tracker", page_icon="👶", layout="centered"
)


@st.cache_resource
def init_supabase():
  return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


supabase = init_supabase()

st.title("👶 Nara-Synced Baby Tracker")

# Input Form
with st.form("activity_form", clear_on_submit=True):
  st.subheader("Log New Event")

  activity_type = st.selectbox(
      "Activity Type", ["bottle_feed", "sleep", "diaper", "solid_feed", "note"]
  )
  profile_name = st.selectbox("Baby Profile", ["Baby"])
  caregiver = st.selectbox("Caregiver", ["Albert", "Partner", "Nanny"])
  note = st.text_area("Note / Details")

  submitted = st.form_submit_button("Save Entry")

  if submitted:
    now_utc = datetime.now()
    data = {
        "type": activity_type,
        "created_by_caregiver": caregiver,
        "note": note,
        "start_date_time": now_utc.isoformat(),
    }

    try:
      response = supabase.table("baby_logs").insert(data).execute()
      st.success("Saved successfully!")
      st.rerun()
    except Exception as e:
      st.error(f"Detailed Database Error: {e}")

# Timeline View
st.divider()
st.subheader("Activity Timeline")

try:
  response = (
      supabase.table("baby_logs")
      .select("id, type, created_by_caregiver, note, start_date_time")
      .execute()
  )
  logs = response.data

  if logs:
    for log in logs:
      time_raw = log.get("start_date_time")
      time_str = (
          time_raw.replace("T", " ")[:16] if time_raw else "Unknown time"
      )

      act_type = log.get("type", "unknown")
      caregiver = log.get("created_by_caregiver", "Unknown")
      note_text = log.get("note")

      st.markdown(f"**{act_type.upper()}** — *{caregiver}* ({time_str})")
      if note_text:
        st.caption(f"📝 {note_text}")
      st.write("---")
  else:
    st.info("No logs found yet.")
except Exception as e:
  st.error(f"Detailed Timeline Error: {e}")
