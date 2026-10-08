if submitted:
    now_utc = datetime.now()
    data = {
        "type": activity_type,
        "created_by_caregiver": caregiver,
        "note": note,
        "start_date_time": now_utc.isoformat(),
    }

    try:
      # Explicitly targeting the public schema
      response = (
          supabase.schema("public")
          .table("baby_logs")
          .insert(data)
          .execute()
      )
      st.success("Saved successfully!")
      st.rerun()
    except Exception as e:
      st.error(f"Detailed Database Error: {e}")

# Timeline View
st.divider()
st.subheader("Activity Timeline")

try:
  # Explicitly targeting the public schema here too
  response = (
      supabase.schema("public")
      .table("baby_logs")
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
