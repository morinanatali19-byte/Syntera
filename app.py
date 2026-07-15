import streamlit as st
import psycopg2

st.set_page_config(
    page_title="Syntera",
    page_icon="🧭",
    layout="wide"
)
st.markdown("""
<style>
.status-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-ok { background-color: #1F3D2B; color: #6FCF97; border: 1px solid #6FCF97; }
.badge-overdue { background-color: #3D2620; color: #E0956B; border: 1px solid #E0956B; }
.badge-white { background-color: #2A2D34; color: #9AA0A6; border: 1px solid #9AA0A6; }

div[data-testid="stExpander"] {
    border: 1px solid #2A2D34;
    border-radius: 10px;
}
.info-card {
    background-color: #1A1D24;
    border: 1px solid #2A2D34;
    border-left: 3px solid #C9A227;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

conn = psycopg2.connect(st.secrets["DATABASE_URL"])
conn.autocommit = True
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
    id SERIAL PRIMARY KEY,
    name TEXT,
    weight INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    direction_name TEXT,
    conclusion TEXT,
    arguments TEXT,
    risks TEXT,
    decision_text TEXT,
    owner TEXT,
    deadline TEXT
)
""")
cursor.execute("ALTER TABLE decisions ADD COLUMN IF NOT EXISTS target_metric TEXT")
cursor.execute("""
CREATE TABLE IF NOT EXISTS ceo_challenges (
    id SERIAL PRIMARY KEY,
    direction_name TEXT,
    reasoning TEXT,
    challenge_date TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS daily_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date TEXT,
    direction_name TEXT,
    status TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS business_signals (
    id SERIAL PRIMARY KEY,
    signal_date TEXT,
    metric_name TEXT,
    value TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS business_signals (
    id SERIAL PRIMARY KEY,
    signal_date TEXT,
    metric_name TEXT,
    value TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS decision_attributions (
    id SERIAL PRIMARY KEY,
    decision_id INTEGER,
    confidence TEXT,
    note TEXT,
    assessed_date TEXT
)
""")

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
            "SELECT deadline FROM decisions WHERE direction_name = %s ORDER BY id DESC LIMIT 1",
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
    st.sidebar.markdown(
        f'<span class="status-badge badge-ok">В порядке: {len(decided) - overdue_count}</span>',
        unsafe_allow_html=True)
    if overdue_count > 0:
        st.sidebar.markdown(
            f'<span class="status-badge badge-overdue">Требуют внимания: {overdue_count}</span>',
            unsafe_allow_html=True)
    if white_spot_count > 0:
        st.sidebar.markdown(
            f'<span class="status-badge badge-white">Без решения: {white_spot_count}</span>',
            unsafe_allow_html=True)

st.title("Syntera")

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

    st.divider()
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
                cursor.execute("INSERT INTO directions (name, weight) VALUES (%s, %s)",
                                (new_direction.strip(), new_weight))
                st.rerun()
    else:
        st.info("Достигнут максимум в 5 направлений. Удалите одно, чтобы добавить другое.")

    if all_directions:
        st.write("**Текущие направления:**")
        for name, weight in all_directions:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f'<div class="info-card"><b>{name}</b> &nbsp; '
                    f'<span class="status-badge badge-white">вес {weight}</span></div>',
                    unsafe_allow_html=True)
            with col2:
                if st.button("Удалить", key=f"del_{name}"):
                    cursor.execute("DELETE FROM directions WHERE name = %s", (name,))
                    st.rerun()

    st.divider()

    if st.button("Сохранить всю стратегию"):
        if not goal.strip():
            st.error("Сначала введите Главную цель")
        elif len(all_directions) < 3:
            st.error(f"Нужно минимум 3 направления, сейчас добавлено: {len(all_directions)}")
        else:
            cursor.execute("DELETE FROM business_context WHERE id = 1")
            cursor.execute("INSERT INTO business_context (id, goal, horizon, criteria) VALUES (1, %s, %s, %s)",
                            (goal, horizon, criteria))
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

        # ---- Фокус дня (CEO Focus) ----
        cursor.execute("SELECT name, weight FROM directions")
        focus_directions = cursor.fetchall()
        cursor.execute("SELECT direction_name FROM decisions")
        focus_decided = [row[0] for row in cursor.fetchall()]

        focus_candidates = []
        for f_name, f_weight in focus_directions:
            if f_name not in focus_decided:
                focus_candidates.append((f_name, f_weight, "white_spot"))
            else:
                cursor.execute(
                    "SELECT deadline FROM decisions WHERE direction_name = %s ORDER BY id DESC LIMIT 1",
                    (f_name,))
                f_deadline_row = cursor.fetchone()
                if f_deadline_row:
                    try:
                        if datetime.strptime(f_deadline_row[0], "%d.%m.%Y") < datetime.now():
                            focus_candidates.append((f_name, f_weight, "overdue"))
                    except ValueError:
                        pass

        if focus_candidates:
            def focus_score(item):
                _, w, kind = item
                return w + (10 if kind == "overdue" else 0)

            focus_candidates.sort(key=focus_score, reverse=True)
            top_name, top_weight, top_kind = focus_candidates[0]
            top_reason = "просрочен срок решения" if top_kind == "overdue" else "нет решения (White Spot)"

            st.markdown(
                f'<div class="info-card">'
                f'<span class="status-badge badge-overdue">Фокус дня</span> &nbsp; '
                f'<b>{top_name}</b> (вес {top_weight}) — {top_reason}'
                f'</div>',
                unsafe_allow_html=True)

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
                            "SELECT decision_text, owner, deadline FROM decisions WHERE direction_name = %s ORDER BY id DESC LIMIT 1",
                            (name,))
                        d = cursor.fetchone()
                        status_label = "Нет выявленных отклонений"
                        badge_class = "badge-ok"
                        if d:
                            decision_text, owner, deadline = d
                            try:
                                deadline_date = datetime.strptime(deadline, "%d.%m.%Y")
                                if deadline_date < datetime.now():
                                    status_label = "Срок истёк"
                                    badge_class = "badge-overdue"
                            except ValueError:
                                status_label = "Не удалось распознать срок"
                                badge_class = "badge-white"

                        with st.expander(f"{name} (вес: {weight}) — {status_label}"):
                            st.markdown(
                                f'<span class="status-badge {badge_class}">{status_label}</span>',
                                unsafe_allow_html=True)
                            if d:
                                st.write(f"**Решение:** {decision_text}")
                                st.write(f"**Владелец:** {owner}")
                                st.write(f"**Срок:** {deadline}")
                                cursor.execute(
                                "SELECT decision_text, owner, deadline FROM decisions WHERE direction_name = %s ORDER BY id DESC",
                                (name,))
                            all_versions = cursor.fetchall()                       
                            if len(all_versions) > 1:
                                with st.expander(f"История решений по направлению ({len(all_versions)} версий)"):
                                    for i, (v_text, v_owner, v_deadline) in enumerate(all_versions):
                                        label = "Текущее" if i == 0 else f"Версия {len(all_versions) - i}"
                                        st.write(f"**{label}:** {v_text}")
                                        st.caption(f"Владелец: {v_owner} · Срок: {v_deadline}")
                        
                            cursor.execute(
                                "SELECT reasoning, challenge_date FROM ceo_challenges WHERE direction_name = %s ORDER BY id DESC LIMIT 1",
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
                                        "INSERT INTO ceo_challenges (direction_name, reasoning, challenge_date) VALUES (%s, %s, %s)",
                                        (name, reasoning.strip(), today))
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
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    """, (name, "Пересмотр решения", "", "", new_decision_text.strip(),
                                          new_owner.strip(), new_deadline_str))
                                    st.success("Решение пересмотрено и обновлено.")
                                    st.rerun()
                                else:
                                    st.error("Заполните формулировку решения и владельца")

            if white_spots:
                st.write("**Требуют внимания (нет решения):**")
                for name, weight in sorted(white_spots, key=lambda d: -d[1]):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        priority_label = "Высокий приоритет" if weight >= 4 else ("Средний приоритет" if weight >= 2 else "Низкий приоритет")
                        priority_class = "badge-overdue" if weight >= 4 else ("badge-white" if weight >= 2 else "badge-ok")
                        st.write(
                            f"**{name}** &nbsp; <span class='status-badge badge-white'>вес {weight}</span> &nbsp; "
                            f"<span class='status-badge {priority_class}'>{priority_label}</span>",
                            unsafe_allow_html=True)
                    with col2:
                        if st.button("Решить", key=f"decide_{name}"):
                            st.session_state.selected_direction = name
                            st.info("Направление выбрано. Перейдите во вкладку 'Decision Board' слева.")

        current_direction_names = [name for name, weight in directions]
        cursor.execute("SELECT DISTINCT direction_name FROM decisions")
        all_decided_names = [row[0] for row in cursor.fetchall()]
        orphaned = [name for name in all_decided_names if name not in current_direction_names]

        if orphaned:
            st.divider()
            st.write("**⚠️ Решения, требующие пересмотра стратегии:**")
            st.caption("Направление изменено или удалено, но решение по нему всё ещё существует.")
            for o_name in orphaned:
                cursor.execute(
                    "SELECT decision_text, owner, deadline FROM decisions WHERE direction_name = %s ORDER BY id DESC LIMIT 1",
                    (o_name,))
                o_decision = cursor.fetchone()
                with st.expander(f"{o_name} — направление устарело"):
                    if o_decision:
                        st.write(f"**Решение:** {o_decision[0]}")
                        st.write(f"**Владелец:** {o_decision[1]}")
                        st.write(f"**Срок:** {o_decision[2]}")
                    st.warning("Это направление больше не входит в текущую стратегию. "
                               "Решение сохранено для истории, но не участвует в общей картине.")

# ==================== DECISION BOARD ====================
elif page == "Decision Board":
    st.subheader("Decision Board")

    if not st.session_state.selected_direction:
        st.warning("Сначала выберите направление во вкладке 'Executive Briefing'")
    else:
        direction = st.session_state.selected_direction
        cursor.execute("SELECT weight FROM directions WHERE name = %s", (direction,))
        weight_row = cursor.fetchone()
        weight = weight_row[0] if weight_row else "?"

        st.markdown(
            f'<div class="info-card"><b>Направление:</b> {direction} &nbsp; '
            f'<span class="status-badge badge-white">Strategic Weight: {weight}</span></div>',
            unsafe_allow_html=True)
        st.caption("Высокий стратегический вес + отсутствие решения")
        st.divider()

        st.write("### 1. Вывод")
        conclusion = st.text_area("Как вы видите текущую ситуацию по этому направлению?", key="db_conclusion")

        st.write("### 2. Аргументы")
        arguments = st.text_area("Почему вы считаете это правильным направлением действий?", key="db_arguments")

        st.write("### 3. Риски")
        risks = st.text_area("Что может помешать достижению результата?", key="db_risks")

        st.divider()
        st.write("### 4. Рекомендация Syntera")
        st.info("Для контроля этого решения зафиксируйте: ожидаемый результат, срок и владельца.")

        st.divider()
        st.write("### 5. Решение")
        decision_text = st.text_area("Формулировка решения", key="db_decision")
        owner = st.text_input("Владелец", key="db_owner")
        from datetime import date
        deadline_date = st.date_input("Срок", key="db_deadline")
        deadline = deadline_date.strftime("%d.%m.%Y")

        if st.button("Зафиксировать решение"):
            if not conclusion.strip() or not decision_text.strip() or not owner.strip():
                st.error("Заполните вывод, формулировку решения и владельца")
            else:
                cursor.execute("""
                    INSERT INTO decisions (direction_name, conclusion, arguments, risks, decision_text, owner, deadline)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (direction, conclusion, arguments, risks, decision_text, owner, deadline))
                st.success(f"Решение по направлению '{direction}' зафиксировано.")
                st.session_state.selected_direction = None

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
                "SELECT decision_text, owner, deadline FROM decisions WHERE direction_name = %s ORDER BY id DESC LIMIT 1",
                (name,))
            d = cursor.fetchone()

            if not d:
                status = "white_spot"
                badge_html = '<span class="status-badge badge-white">White Spot</span>'
            else:
                decision_text, owner, deadline = d
                try:
                    deadline_date = datetime.strptime(deadline, "%d.%m.%Y")
                    if deadline_date < datetime.now():
                        status = "overdue"
                        badge_html = '<span class="status-badge badge-overdue">Требует пересмотра</span>'
                    else:
                        status = "ok"
                        badge_html = '<span class="status-badge badge-ok">В порядке</span>'
                except ValueError:
                    status = "ok"
                    badge_html = '<span class="status-badge badge-white">Срок не распознан</span>'

            st.markdown(
                f'<div class="info-card"><b>{name}</b> (вес {weight}) &nbsp; {badge_html}</div>',
                unsafe_allow_html=True)
            today_statuses[name] = status

        st.divider()

        st.write("**Бизнес-показатели дня:**")
        col1, col2 = st.columns(2)
        with col1:
            metric_name = st.text_input("Название показателя (например: Выручка)", key="signal_name")
        with col2:
            metric_value = st.text_input("Значение", key="signal_value")

        if st.button("Добавить показатель"):
            if metric_name.strip() and metric_value.strip():
                cursor.execute(
                    "INSERT INTO business_signals (signal_date, metric_name, value) VALUES (%s, %s, %s)",
                    (today, metric_name.strip(), metric_value.strip()))
                st.rerun()

        cursor.execute("SELECT metric_name, value FROM business_signals WHERE signal_date = %s", (today,))
        today_signals = cursor.fetchall()
        if today_signals:
            st.write("**Сегодня:**")
            for m_name, m_value in today_signals:
                st.write(f"- {m_name}: **{m_value}**")

        cursor.execute("SELECT DISTINCT metric_name FROM business_signals ORDER BY metric_name")
        all_metric_names = [row[0] for row in cursor.fetchall()]

        if all_metric_names:
            st.write("**История по показателям:**")
            selected_metric = st.selectbox("Выберите показатель для просмотра истории",
                                             all_metric_names, key="metric_history_select")

            cursor.execute(
                "SELECT signal_date, value FROM business_signals WHERE metric_name = %s ORDER BY id ASC LIMIT 30",
                (selected_metric,))
            history = cursor.fetchall()

            if history:
                import pandas as pd
                import re

                numeric_values = []
                valid_dates = []
                has_non_numeric = False

                for h_date, h_value in history:
                    try:
                        cleaned = re.sub(r"[^\d.,\-]", "", h_value).replace(",", ".")
                        numeric_values.append(float(cleaned))
                        valid_dates.append(h_date)
                    except ValueError:
                        has_non_numeric = True

                if numeric_values:
                    chart_data = pd.DataFrame({
                        "Дата": valid_dates,
                        selected_metric: numeric_values
                    }).set_index("Дата")
                    st.line_chart(chart_data)

                if has_non_numeric:
                    st.caption("Некоторые значения не являются числами и не показаны на графике.")

                st.write("**Подробно:**")
                for h_date, h_value in reversed(history):
                    st.write(f"- {h_date}: **{h_value}**")

        st.divider()

        cursor.execute("SELECT direction_name, status FROM daily_snapshots WHERE snapshot_date = %s",
                        (today,))
        already_saved_today = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT snapshot_date FROM daily_snapshots WHERE snapshot_date != %s ORDER BY id DESC LIMIT 1", (today,))
        prev_date_row = cursor.fetchone()

        if prev_date_row:
            prev_date = prev_date_row[0]
            cursor.execute("SELECT direction_name, status FROM daily_snapshots WHERE snapshot_date = %s", (prev_date,))
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
                        st.markdown(
                            f'<span class="status-badge badge-ok">Улучшение</span> &nbsp; **{name}**: {old} → {new}',
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f'<span class="status-badge badge-overdue">Ухудшение</span> &nbsp; **{name}**: {old} → {new}',
                            unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<span class="status-badge badge-white">Новое</span> &nbsp; **{name}**',
                        unsafe_allow_html=True)
        else:
            st.caption("Это первый день наблюдения — сравнивать пока не с чем.")

        if st.button("Сохранить сегодняшний снимок"):
            for name, status in today_statuses.items():
                if name in already_saved_today:
                    cursor.execute(
                        "UPDATE daily_snapshots SET status = %s WHERE snapshot_date = %s AND direction_name = %s",
                        (status, today, name))
                else:
                    cursor.execute(
                        "INSERT INTO daily_snapshots (snapshot_date, direction_name, status) VALUES (%s, %s, %s)",
                        (today, name, status))
            st.success(f"Снимок за {today} сохранён")