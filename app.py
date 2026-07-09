import streamlit as st

st.set_page_config(
    page_title="Syntera",
    page_icon="🧭",
    layout="wide"
)
import sqlite3

conn = sqlite3.connect("syntera.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS business_context (
    id INTEGER PRIMARY KEY,
    goal TEXT,
    horizon TEXT,
    criteria TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS directions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    weight INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direction_name TEXT,
    conclusion TEXT,
    arguments TEXT,
    risks TEXT,
    decision_text TEXT,
    owner TEXT,
    deadline TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS daily_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT,
    direction_name TEXT,
    status TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS ceo_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direction_name TEXT,
    reasoning TEXT,
    challenge_date TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS business_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_date TEXT,
    metric_name TEXT,
    value TEXT
)
""")
conn.commit()

st.title("Syntera")

if "selected_direction" not in st.session_state:
    st.session_state.selected_direction = None

st.sidebar.title("🧭 Syntera")
st.sidebar.caption("Управленческий контур")
st.sidebar.divider()

page = st.sidebar.radio("Раздел", [
    "📋 Онбординг",
    "🌅 Executive Briefing",
    "🎯 Decision Board",
    "🌙 Evening Closure"
])

# Убираем эмодзи из значения page, чтобы не менять остальной код
page = page.split(" ", 1)[1]
st.sidebar.divider()

cursor.execute("SELECT COUNT(*) FROM directions")
total_directions = cursor.fetchone()[0]

if total_directions > 0:
    cursor.execute("SELECT DISTINCT direction_name FROM decisions")
    decided = [row[0] for row in cursor.fetchall()]

    overdue_count = 0
    from datetime import datetime
    for name in decided:
        cursor.execute(
            "SELECT deadline FROM decisions WHERE direction_name = ? ORDER BY id DESC LIMIT 1",
            (name,))
        deadline_row = cursor.fetchone()
        if deadline_row:
            try:
                if datetime.strptime(deadline_row[0], "%d.%m.%Y") < datetime.now():
                    overdue_count += 1
            except ValueError:
                pass

    white_spot_count = total_directions - len(decided)

    st.sidebar.write("**Состояние сейчас:**")
    st.sidebar.write(f"🟢 В порядке: {len(decided) - overdue_count}")
    if overdue_count > 0:
        st.sidebar.write(f"🟠 Требуют внимания: {overdue_count}")
    if white_spot_count > 0:
        st.sidebar.write(f"⚪ Без решения: {white_spot_count}")
# ==================== СТРАНИЦА ОНБОРДИНГА ====================
if page == "Онбординг":
    st.subheader("Онбординг: Главная цель компании")

    cursor.execute("SELECT goal, horizon, criteria FROM business_context WHERE id = 1")
    existing = cursor.fetchone()

    default_goal = existing[0] if existing else ""
    default_horizon = existing[1] if existing else "1 год"
    default_criteria = existing[2] if existing else ""

    goal = st.text_input("Формулировка Главной цели", value=default_goal)
    horizon = st.selectbox("Горизонт цели", ["1 год", "3 года", "5 лет"],
                            index=["1 год", "3 года", "5 лет"].index(default_horizon))
    criteria = st.text_area("Критерий достижения", value=default_criteria)

    st.subheader("Стратегические направления")

    cursor.execute("SELECT name, weight FROM directions")
    all_directions = cursor.fetchall()
    existing_names = [name for name, weight in all_directions]

    st.caption(f"Добавлено направлений: {len(all_directions)} из 5 максимум (минимум 3)")

    if len(all_directions) < 5:
        col1, col2 = st.columns([3, 1])
        with col1:
            new_direction = st.text_input("Название направления", key="new_dir_name")
        with col2:
            new_weight = st.number_input("Вес (1-5)", min_value=1, max_value=5, value=3, key="new_dir_weight")

        if st.button("Добавить направление"):
            if not new_direction.strip():
                st.error("Название направления не может быть пустым")
            elif new_direction.strip() in existing_names:
                st.error(f"Направление '{new_direction}' уже добавлено")
            else:
                cursor.execute("INSERT INTO directions (name, weight) VALUES (?, ?)",
                                (new_direction.strip(), new_weight))
                conn.commit()
                st.rerun()
    else:
        st.info("Достигнут максимум в 5 направлений. Удалите одно, чтобы добавить другое.")

    if all_directions:
        st.write("**Текущие направления:**")
        for name, weight in all_directions:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"- {name} (вес: {weight})")
            with col2:
                if st.button("Удалить", key=f"del_{name}"):
                    cursor.execute("DELETE FROM directions WHERE name = ?", (name,))
                    conn.commit()
                    st.rerun()

    st.divider()

    if st.button("Сохранить всю стратегию"):
        if not goal.strip():
            st.error("Сначала введите Главную цель")
        elif len(all_directions) < 3:
            st.error(f"Нужно минимум 3 направления, сейчас добавлено: {len(all_directions)}")
        else:
            cursor.execute("DELETE FROM business_context WHERE id = 1")
            cursor.execute("INSERT INTO business_context (id, goal, horizon, criteria) VALUES (1, ?, ?, ?)",
                            (goal, horizon, criteria))
            conn.commit()
            st.success(f"Стратегия сохранена: {goal}. Направлений: {len(all_directions)}")

# ==================== СТРАНИЦА BRIEFING ====================
elif page == "Executive Briefing":
    st.subheader("Executive Briefing")

    cursor.execute("SELECT goal FROM business_context WHERE id = 1")
    context = cursor.fetchone()

    if not context:
        st.warning("Сначала заполните стратегию во вкладке 'Онбординг'")
    else:
        st.write(f"**Главная цель:** {context[0]}")
        st.divider()

        cursor.execute("SELECT name, weight FROM directions")
        directions = cursor.fetchall()

        cursor.execute("SELECT direction_name FROM decisions")
        decided_directions = [row[0] for row in cursor.fetchall()]

        white_spots = [(name, weight) for name, weight in directions if name not in decided_directions]
        active = [(name, weight) for name, weight in directions if name in decided_directions]

        if not directions:
            st.info("Стратегические направления ещё не заданы")
        else:
            if not decided_directions:
                top_direction = max(directions, key=lambda d: d[1])
                st.write("Активных управленческих решений пока нет.")
                st.write(f"**Рекомендованный первый фокус:** {top_direction[0]} (вес {top_direction[1]})")
                if st.button(f"Создать первое решение по направлению '{top_direction[0]}'"):
                    st.session_state.selected_direction = top_direction[0]
                    st.info("Направление выбрано. Перейдите во вкладку 'Decision Board' слева.")
            else:
                if active:
                    st.write("**Активные решения:**")
                    for name, weight in active:
                        cursor.execute(
                            "SELECT decision_text, owner, deadline FROM decisions WHERE direction_name = ? ORDER BY id DESC LIMIT 1",
                            (name,))
                        d = cursor.fetchone()
                        status = "🟢 Нет выявленных отклонений"
                        if d:
                            decision_text, owner, deadline = d
                            try:
                                from datetime import datetime
                                deadline_date = datetime.strptime(deadline, "%d.%m.%Y")
                                if deadline_date < datetime.now():
                                    status = "🟠 Срок истёк"
                            except ValueError:
                                status = "🟡 Не удалось распознать срок"

                        with st.expander(f"{name} (вес: {weight}) — {status}"):
                            if d:
                                st.write(f"**Решение:** {decision_text}")
                                st.write(f"**Владелец:** {owner}")
                                st.write(f"**Срок:** {deadline}")

                            cursor.execute(
                                "SELECT reasoning, challenge_date FROM ceo_challenges WHERE direction_name = ? ORDER BY id DESC LIMIT 1",
                                (name,))
                            challenge = cursor.fetchone()
                            if challenge:
                                st.warning(f"**Возражение CEO от {challenge[1]}:** {challenge[0]}")

                            st.write("**Не согласны с этой оценкой?**")
                            reasoning = st.text_area("Объясните, почему статус кажется неверным",
                                                       key=f"challenge_{name}")
                            if st.button("Отправить возражение", key=f"challenge_btn_{name}"):
                                if reasoning.strip():
                                    from datetime import datetime
                                    today = datetime.now().strftime("%d.%m.%Y")
                                    cursor.execute(
                                        "INSERT INTO ceo_challenges (direction_name, reasoning, challenge_date) VALUES (?, ?, ?)",
                                        (name, reasoning.strip(), today))
                                    conn.commit()
                                    st.success("Возражение зафиксировано. Статус останется прежним до пересмотра решения.")
                                    st.rerun()
                                else:
                                    st.error("Опишите причину возражения")

                            st.divider()
                            st.write("**Пересмотреть решение**")
                            new_decision_text = st.text_area("Новая формулировка решения",
                                                               value=decision_text if d else "",
                                                               key=f"review_text_{name}")
                            new_owner = st.text_input("Новый владелец",
                                                        value=owner if d else "",
                                                        key=f"review_owner_{name}")
                            new_deadline = st.date_input("Новый срок", key=f"review_deadline_{name}")

                            if st.button("Сохранить пересмотренное решение", key=f"review_btn_{name}"):
                                if new_decision_text.strip() and new_owner.strip():
                                    new_deadline_str = new_deadline.strftime("%d.%m.%Y")
                                    cursor.execute("""
                                        INSERT INTO decisions (direction_name, conclusion, arguments, risks, decision_text, owner, deadline)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (name, "Пересмотр решения", "", "", new_decision_text.strip(),
                                          new_owner.strip(), new_deadline_str))
                                    conn.commit()
                                    st.success("Решение пересмотрено и обновлено.")
                                    st.rerun()
                                else:
                                    st.error("Заполните формулировку решения и владельца")

# ==================== DECISION BOARD ====================
elif page == "Decision Board":
    st.subheader("Decision Board")

    if not st.session_state.selected_direction:
        st.warning("Сначала выберите направление во вкладке 'Executive Briefing'")
    else:
        direction = st.session_state.selected_direction
        cursor.execute("SELECT weight FROM directions WHERE name = ?", (direction,))
        weight_row = cursor.fetchone()
        weight = weight_row[0] if weight_row else "?"

        st.write(f"**Направление:** {direction}")
        st.write(f"**Strategic Weight:** {weight}")
        st.caption("Высокий стратегический вес + отсутствие решения")
        st.divider()

        st.write("### 1. Вывод")
        conclusion = st.text_area("Как вы видите текущую ситуацию по этому направлению?", key="db_conclusion")

        st.write("### 2. Аргументы")
        arguments = st.text_area("Почему вы считаете это правильным направлением действий?", key="db_arguments")

        st.write("### 3. Риски")
        risks = st.text_area("Что может помешать достижению результата?", key="db_risks")

        st.write("### 4. Рекомендация Syntera")
        st.info("Для контроля этого решения зафиксируйте: ожидаемый результат, срок и владельца.")

        st.write("### 5. Решение")
        decision_text = st.text_area("Формулировка решения", key="db_decision")
        owner = st.text_input("Владелец", key="db_owner")
        from datetime import date
        deadline_date = st.date_input("Срок", key="db_deadline")
        deadline = deadline_date.strftime("%d.%m.%Y")
        if st.button("Зафиксировать решение"):
            if not conclusion.strip() or not decision_text.strip() or not owner.strip() or not deadline.strip():
                st.error("Заполните вывод, формулировку решения, владельца и срок")
            else:
                cursor.execute("""
                    INSERT INTO decisions (direction_name, conclusion, arguments, risks, decision_text, owner, deadline)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (direction, conclusion, arguments, risks, decision_text, owner, deadline))
                conn.commit()
                st.success(f"Решение по направлению '{direction}' зафиксировано.")
                st.session_state.selected_direction = None
                # ==================== EVENING CLOSURE ====================
# ==================== EVENING CLOSURE ====================
elif page == "Evening Closure":
    st.subheader("Evening Closure")

    cursor.execute("SELECT name, weight FROM directions")
    directions = cursor.fetchall()

    if not directions:
        st.info("Стратегические направления ещё не заданы")
    else:
        from datetime import datetime

        today = datetime.now().strftime("%d.%m.%Y")

        st.write("**Состояние решений на сегодня:**")

        today_statuses = {}

        for name, weight in directions:
            cursor.execute(
                "SELECT decision_text, owner, deadline FROM decisions WHERE direction_name = ? ORDER BY id DESC LIMIT 1",
                (name,))
            d = cursor.fetchone()

            if not d:
                status = "white_spot"
                st.write(f"- **{name}** (вес {weight}): решения нет — White Spot")
            else:
                decision_text, owner, deadline = d
                try:
                    deadline_date = datetime.strptime(deadline, "%d.%m.%Y")
                    if deadline_date < datetime.now():
                        status = "overdue"
                        st.write(f"- **{name}** (вес {weight}): 🟠 срок истёк — требует пересмотра")
                    else:
                        status = "ok"
                        st.write(f"- **{name}** (вес {weight}): 🟢 в порядке, решение принято")
                except ValueError:
                    status = "ok"
                    st.write(f"- **{name}** (вес {weight}): решение принято, срок не распознан")

            today_statuses[name] = status

        st.write("**Бизнес-показатели дня:**")
        col1, col2 = st.columns(2)
        with col1:
            metric_name = st.text_input("Название показателя (например: Выручка)", key="signal_name")
        with col2:
            metric_value = st.text_input("Значение", key="signal_value")

        if st.button("Добавить показатель"):
            if metric_name.strip() and metric_value.strip():
                cursor.execute(
                    "INSERT INTO business_signals (signal_date, metric_name, value) VALUES (?, ?, ?)",
                    (today, metric_name.strip(), metric_value.strip()))
                conn.commit()
                st.rerun()

        cursor.execute("SELECT metric_name, value FROM business_signals WHERE signal_date = ?", (today,))
        today_signals = cursor.fetchall()
        if today_signals:
            for m_name, m_value in today_signals:
                st.write(f"- {m_name}: **{m_value}**")

        st.divider()

        cursor.execute("SELECT direction_name, status FROM daily_snapshots WHERE snapshot_date = ?",
                        (today,))
        already_saved_today = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT DISTINCT snapshot_date FROM daily_snapshots WHERE snapshot_date != ? ORDER BY id DESC LIMIT 1", (today,))
        prev_date_row = cursor.fetchone()

        if prev_date_row:
            prev_date = prev_date_row[0]
            cursor.execute("SELECT direction_name, status FROM daily_snapshots WHERE snapshot_date = ?", (prev_date,))
            prev_statuses = {row[0]: row[1] for row in cursor.fetchall()}

            st.write(f"**Изменения с {prev_date}:**")

            status_rank = {"white_spot": 0, "overdue": 1, "ok": 2}

            for name in today_statuses:
                if name in prev_statuses:
                    old = prev_statuses[name]
                    new = today_statuses[name]
                    if old == new:
                        continue
                    elif status_rank[new] > status_rank[old]:
                        st.write(f"- 🟢 **{name}**: улучшение ({old} → {new})")
                    else:
                        st.write(f"- 🔴 **{name}**: ухудшение ({old} → {new})")
                else:
                    st.write(f"- ⚪ **{name}**: новое направление")
        else:
            st.caption("Это первый день наблюдения — сравнивать пока не с чем.")

        if st.button("Сохранить сегодняшний снимок"):
            for name, status in today_statuses.items():
                if name in already_saved_today:
                    cursor.execute(
                        "UPDATE daily_snapshots SET status = ? WHERE snapshot_date = ? AND direction_name = ?",
                        (status, today, name))
                else:
                    cursor.execute(
                        "INSERT INTO daily_snapshots (snapshot_date, direction_name, status) VALUES (?, ?, ?)",
                        (today, name, status))
            conn.commit()
            st.success(f"Снимок за {today} сохранён")