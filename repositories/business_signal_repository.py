import streamlit as st


def add_signal(cursor, signal_date, metric_name, value):
    try:
        cursor.execute(
            "INSERT INTO business_signals (signal_date, metric_name, value) VALUES (%s, %s, %s)",
            (signal_date, metric_name, value))
        return True
    except Exception:
        st.error("Не удалось сохранить показатель")
        return False


def get_today_signals(cursor, today):
    try:
        cursor.execute(
            "SELECT metric_name, value FROM business_signals WHERE signal_date = %s", (today,))
        return cursor.fetchall()
    except Exception:
        st.error("Не удалось получить показатели за сегодня")
        return []


def get_metric_names(cursor):
    try:
        cursor.execute("SELECT DISTINCT metric_name FROM business_signals ORDER BY metric_name")
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        st.error("Не удалось получить список показателей")
        return []


def get_metric_history(cursor, metric_name, limit=30):
    try:
        cursor.execute(
            "SELECT signal_date, value FROM business_signals WHERE metric_name = %s ORDER BY id ASC LIMIT %s",
            (metric_name, limit))
        return cursor.fetchall()
    except Exception:
        st.error("Не удалось получить историю показателя")
        return []