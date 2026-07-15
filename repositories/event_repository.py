import streamlit as st


def create_event(cursor, event_date, event_type, direction_name, description):
    try:
        cursor.execute("""
            INSERT INTO events (event_date, event_type, direction_name, description)
            VALUES (%s, %s, %s, %s)
        """, (event_date, event_type, direction_name, description))
        return True
    except Exception:
        st.error("Не удалось записать событие в журнал")
        return False


def get_events(cursor, limit=100):
    try:
        cursor.execute(
            "SELECT event_date, event_type, direction_name, description FROM events ORDER BY id DESC LIMIT %s",
            (limit,))
        return cursor.fetchall()
    except Exception:
        st.error("Не удалось получить журнал событий")
        return []