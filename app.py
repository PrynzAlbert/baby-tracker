# --- ACTIVITY TIMELINE VIEW (DIAGNOSTIC FETCH) ---
st.divider()
st.subheader("Recent Activity")

try:
  # Explicitly query using the REST endpoint configuration
  response = (
      supabase.table("baby_logs")
      .select("*")
      .order("id", desc=True)
      .limit(25)
      .execute()
  )
  logs = response.data
  
  if logs:
    for log in logs:
      log_id = log.get("id")
      act_type = log.get("type", "Activity")
      caregiver = log.get("created_by_caregiver", "Unknown")
      note_text = log.get("note", "")
      time_str = str(log.get("start_date_time", "Unknown time"))

      with st.container():
        col_info, col_del = st.columns([5, 1])

        with col_info:
          st.markdown(f"**{str(act_type).upper()}** — *{caregiver}*")
          if note_text:
            st.write(f"📝 {note_text}")
          st.caption(f"Logged at {time_str}")

        with col_del:
          if st.button("Delete", key=f"del_{log_id}"):
            supabase.table("baby_logs").delete().eq("id", log_id).execute()
            st.success("Deleted!")
            st.rerun()

        st.write("---")
  else:
    st.info("No activities logged in the database yet. Record your first entry above!")

except Exception as e:
  st.error(f"Diagnostic Error: {e}")
