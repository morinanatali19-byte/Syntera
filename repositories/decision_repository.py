import streamlit as st


def get_decided_direction_names(cursor):
    try:
        cursor.execute("SELECT DISTINCT direction_name FROM decisions")
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        st.error("Не удалось получить список направлений с решениями")
        return []


def get_latest_decision(cursor, direction_name):
    try:
        cursor.execute(
            "SELECT id, decision_text, owner, deadline, target_metric FROM decisions "
            "WHERE direction_name = %s ORDER BY id DESC LIMIT 1",
            (direction_name,))
        return cursor.fetchone()
    except Exception:
        st.error("Не удалось получить решение по направлению")
        return None


def get_decision_history(cursor, direction_name):
    try:
        cursor.execute(
            "SELECT decision_text, owner, deadline FROM decisions "
            "WHERE direction_name = %s ORDER BY id DESC",
            (direction_name,))
        return cursor.fetchall()
    except Exception:
        st.error("Не удалось получить историю решений")
        return []


def create_decision(cursor, direction_name, conclusion, arguments, risks,
                     decision_text, owner, deadline, target_metric=None):
    try:
        cursor.execute("""
            INSERT INTO decisions (direction_name, conclusion, arguments, risks, decision_text, owner, deadline, target_metric)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (direction_name, conclusion, arguments, risks, decision_text, owner, deadline, target_metric))
        return True
    except Exception:
        st.error("Не удалось сохранить решение")
        return False


def update_target_metric(cursor, decision_id, target_metric):
    try:
        cursor.execute("UPDATE decisions SET target_metric = %s WHERE id = %s",
                        (target_metric, decision_id))
        return True
    except Exception:
        st.error("Не удалось обновить целевой показатель")
        return False