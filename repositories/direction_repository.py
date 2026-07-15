import streamlit as st


def get_directions(cursor):
    try:
        cursor.execute("SELECT name, weight FROM directions")
        return cursor.fetchall()
    except Exception:
        st.error("Не удалось получить список направлений")
        return []


def add_direction(cursor, name, weight):
    try:
        cursor.execute("INSERT INTO directions (name, weight) VALUES (%s, %s)", (name, weight))
        return True
    except Exception:
        st.error("Не удалось добавить направление")
        return False


def delete_direction(cursor, name):
    try:
        cursor.execute("DELETE FROM directions WHERE name = %s", (name,))
        return True
    except Exception:
        st.error("Не удалось удалить направление")
        return False