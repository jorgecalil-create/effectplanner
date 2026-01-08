# app.py
import json
import uuid
import datetime as dt
from pathlib import Path

import streamlit as st
from streamlit_calendar import calendar

APP_TITLE = "EffectPlanner"
DATA_FILE = Path(__file__).with_name("events.json")
FEEDBACK_FILE = Path(__file__).with_name("feedback.json")

# -----------------------------
# Research-Based tags (your 4 evidence-backed tags)
# -----------------------------
RESEARCH_TAGS = [
    "Sleep (Timing & Health)",
    "Meal/Eating Timing (Chrononutrition)",
    "Exercise (Time-of-Day Effects)",
    "Light Exposure (Timing & Circadian Regulation)",
]

RESEARCH_PAPERS = {
    "Sleep (Timing & Health)": {
        "title": "Sleep in Adolescence: Physiology, Cognition and Mental Health",
        "authors": "L. Tarokh et al. (2016)",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5074885/",
        "default_start": dt.time(22, 0),  # bedtime anchor
        "base_tag": "Health",
        "recommended_sleep_hours": 9.0,
        "min_sleep_hours": 6.0,
        "max_sleep_hours": 11.0,
    },
    "Meal/Eating Timing (Chrononutrition)": {
        "title": "Chrononutrition and Energy Balance: How Meal Timing and Circadian Rhythms Shape Metabolism",
        "authors": "C. Reytor-González et al. (2025)",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12252119/",
        "default_start": dt.time(18, 0),
        "base_tag": "Health",
    },
    "Exercise (Time-of-Day Effects)": {
        "title": "Best Time of Day for Strength and Endurance Training: Systematic Review & Meta-Analysis",
        "authors": "F. Bruggisser et al. (2023)",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10198889/",
        "default_start": dt.time(16, 30),
        "base_tag": "Fitness",
    },
    "Light Exposure (Timing & Circadian Regulation)": {
        "title": "Effects of Light on Human Circadian Rhythms, Sleep and Mood",
        "authors": "C. Blume et al. (2019)",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6751071/",
        "default_start": dt.time(8, 0),
        "base_tag": "Health",
    },
}

# -----------------------------
# Tag options (GLOBAL) — include research tags everywhere
# -----------------------------
TAG_OPTIONS = [
    "Work",
    "School",
    "Family",
    "Fitness",
    "Health",
    "Finance",
    "Travel",
    "Personal",
] + RESEARCH_TAGS

# -----------------------------
# "Prof" sources — ONLY the 4 research tags
# -----------------------------
PROF_SOURCES = {
    "Sleep (Timing & Health)": {
        "title": RESEARCH_PAPERS["Sleep (Timing & Health)"]["title"],
        "url": RESEARCH_PAPERS["Sleep (Timing & Health)"]["url"],
        "note": "Adolescent circadian timing shifts later; sleep timing/duration affect cognition and mental health.",
        "authors": RESEARCH_PAPERS["Sleep (Timing & Health)"]["authors"],
    },
    "Meal/Eating Timing (Chrononutrition)": {
        "title": RESEARCH_PAPERS["Meal/Eating Timing (Chrononutrition)"]["title"],
        "url": RESEARCH_PAPERS["Meal/Eating Timing (Chrononutrition)"]["url"],
        "note": "Meal timing interacts with circadian rhythms and can influence metabolic health.",
        "authors": RESEARCH_PAPERS["Meal/Eating Timing (Chrononutrition)"]["authors"],
    },
    "Exercise (Time-of-Day Effects)": {
        "title": RESEARCH_PAPERS["Exercise (Time-of-Day Effects)"]["title"],
        "url": RESEARCH_PAPERS["Exercise (Time-of-Day Effects)"]["url"],
        "note": "Time-of-day can affect training adaptations/performance; evidence synthesized in meta-analysis.",
        "authors": RESEARCH_PAPERS["Exercise (Time-of-Day Effects)"]["authors"],
    },
    "Light Exposure (Timing & Circadian Regulation)": {
        "title": RESEARCH_PAPERS["Light Exposure (Timing & Circadian Regulation)"]["title"],
        "url": RESEARCH_PAPERS["Light Exposure (Timing & Circadian Regulation)"]["url"],
        "note": "Morning vs evening light shifts the circadian clock, affecting melatonin, sleep, and mood.",
        "authors": RESEARCH_PAPERS["Light Exposure (Timing & Circadian Regulation)"]["authors"],
    },
}

# -----------------------------
# Storage
# -----------------------------
def _load_events():
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_events(events):
    DATA_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")


def _load_feedback():
    if not FEEDBACK_FILE.exists():
        return {}
    try:
        data = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_feedback(feedback: dict):
    FEEDBACK_FILE.write_text(json.dumps(feedback, indent=2), encoding="utf-8")


# -----------------------------
# Date helpers
# -----------------------------
def parse_iso_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def iso_date(d: dt.date) -> str:
    return d.isoformat()


def last_day_of_month(y: int, m: int) -> dt.date:
    if m == 12:
        return dt.date(y, 12, 31)
    return dt.date(y, m + 1, 1) - dt.timedelta(days=1)


def add_months(anchor: dt.date, delta_months: int) -> dt.date:
    y = anchor.year
    m = anchor.month + delta_months
    while m > 12:
        y += 1
        m -= 12
    while m < 1:
        y -= 1
        m += 12
    ld = last_day_of_month(y, m)
    d = min(anchor.day, ld.day)
    return dt.date(y, m, d)


def start_of_week(d: dt.date, week_starts_monday: bool = False) -> dt.date:
    wd = d.weekday()  # Mon=0 ... Sun=6
    if week_starts_monday:
        return d - dt.timedelta(days=wd)
    sunday_index = (wd + 1) % 7
    return d - dt.timedelta(days=sunday_index)


def shift_anchor(anchor: dt.date, view: str, direction: int) -> dt.date:
    if view == "month":
        return add_months(anchor, direction)
    if view == "week":
        return anchor + dt.timedelta(days=7 * direction)
    return anchor + dt.timedelta(days=direction)


def month_label(d: dt.date) -> str:
    return d.strftime("%B %Y")


def day_label(d: dt.date) -> str:
    return f"{d.strftime('%A')}, {d.strftime('%b')} {d.day}, {d.year}"


def week_label(d: dt.date) -> str:
    s = start_of_week(d, week_starts_monday=False)
    e = s + dt.timedelta(days=6)
    return f"{s.strftime('%b')} {s.day}, {s.year} – {e.strftime('%b')} {e.day}, {e.year}"


def header_label(view: str, d: dt.date) -> str:
    if view == "month":
        return month_label(d)
    if view == "week":
        return week_label(d)
    return day_label(d)


def _fmt_time(t: dt.time) -> str:
    return dt.datetime.combine(dt.date.today(), t).strftime("%I:%M %p").lstrip("0")


def _fmt_dt_range(s: dt.datetime, e: dt.datetime) -> str:
    return f"{_fmt_time(s.time())}–{_fmt_time(e.time())}"


# -----------------------------
# AI time helpers
# -----------------------------
def _time_from_minutes(m: int) -> dt.time:
    m = max(0, min(23 * 60 + 59, int(m)))
    return dt.time(m // 60, m % 60)


def suggest_research_time(tag: str) -> dt.time:
    defaults = {
        "School": dt.time(17, 0),
        "Work": dt.time(16, 0),
        "Family": dt.time(18, 30),
        "Fitness": dt.time(16, 30),
        "Health": dt.time(20, 0),
        "Finance": dt.time(19, 0),
        "Travel": dt.time(10, 0),
        "Personal": dt.time(20, 30),
    }
    return defaults.get(tag, dt.time(17, 0))


def suggest_best_time_from_history(events: list, tag: str) -> dt.time:
    mins = []
    for ev in events:
        if ev.get("kind") != "event":
            continue
        tags = ev.get("tags") or []
        if tag not in tags:
            continue
        start = ev.get("start", "")
        if isinstance(start, str) and "T" in start and len(start) >= 16:
            try:
                hh = int(start[11:13])
                mm = int(start[14:16])
                mins.append(hh * 60 + mm)
            except Exception:
                pass
    if not mins:
        return suggest_research_time(tag)
    return _time_from_minutes(sum(mins) / len(mins))


# -----------------------------
# Overlap-avoidance for AI scheduling
# -----------------------------
def _parse_iso_dt(s: str):
    if not isinstance(s, str) or "T" not in s:
        return None
    try:
        return dt.datetime.fromisoformat(s)
    except Exception:
        return None


def _busy_intervals_for_date(events: list, day: dt.date):
    intervals = []
    for ev in events:
        if ev.get("kind") != "event":
            continue
        if ev.get("allDay"):
            continue
        s = _parse_iso_dt(ev.get("start", ""))
        e = _parse_iso_dt(ev.get("end", ""))
        if not s or not e:
            continue
        if s.date() != day:
            continue
        if e <= s:
            continue
        intervals.append((s, e))
    intervals.sort(key=lambda x: x[0])
    return intervals


def _overlaps(a_start: dt.datetime, a_end: dt.datetime, b_start: dt.datetime, b_end: dt.datetime) -> bool:
    return a_start < b_end and a_end > b_start


def find_next_free_slot(events: list, day: dt.date, proposed_start: dt.datetime, duration_min: int):
    duration = dt.timedelta(minutes=int(duration_min))
    day_start = dt.datetime.combine(day, dt.time(0, 0))
    day_end = dt.datetime.combine(day, dt.time(23, 59))
    latest_start = day_end - duration
    if latest_start < day_start:
        latest_start = day_start

    start = max(day_start, proposed_start)
    if start > latest_start:
        start = latest_start
    end = start + duration

    intervals = _busy_intervals_for_date(events, day)
    if not intervals:
        return start, end

    for _ in range(200):
        conflict = None
        for bs, be in intervals:
            if _overlaps(start, end, bs, be):
                conflict = (bs, be)
                break
        if conflict is None:
            return start, end

        start = conflict[1]
        if start > latest_start:
            start = latest_start
        end = start + duration

        if start == latest_start:
            return start, end

    return start, end


# -----------------------------
# Manual time parsing (American typing) — DO NOT CHANGE
# -----------------------------
def _parse_time_12h(s: str, fallback: dt.time) -> dt.time:
    if not isinstance(s, str):
        return fallback
    text = s.strip().upper().replace(".", "")
    if not text:
        return fallback

    candidates = [
        "%I %p",
        "%I:%M %p",
        "%I%p",
        "%I:%M%p",
        "%H:%M",
    ]
    for fmt in candidates:
        try:
            t = dt.datetime.strptime(text, fmt).time()
            return dt.time(t.hour, t.minute)
        except Exception:
            pass
    return fallback


# -----------------------------
# Feedback helpers
# -----------------------------
EMOJI_CHOICES = [
    ("😡", 1),
    ("😕", 2),
    ("😐", 3),
    ("🙂", 4),
    ("😄", 5),
]


def _occurrence_key(event_id: str, day: dt.date) -> str:
    return f"{event_id}::{day.isoformat()}"


def _event_occurs_on_day(ev: dict, day: dt.date) -> bool:
    if ev.get("kind") != "event":
        return False
    s = _parse_iso_dt(ev.get("start", ""))
    e = _parse_iso_dt(ev.get("end", ""))
    if not s or not e:
        return False
    return s.date() == day


def _event_label(ev: dict) -> str:
    title = (ev.get("title") or "(No title)").strip()
    s = _parse_iso_dt(ev.get("start", ""))
    e = _parse_iso_dt(ev.get("end", ""))
    if s and e:
        return f"{title} ({_fmt_dt_range(s, e)})"
    return title


# -----------------------------
# Streamlit setup/state
# -----------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")

if "events" not in st.session_state:
    st.session_state.events = _load_events()

if "feedback" not in st.session_state:
    st.session_state.feedback = _load_feedback()

if "view" not in st.session_state:
    st.session_state.view = "month"  # month | week | day

if "selected_date" not in st.session_state:
    st.session_state.selected_date = iso_date(dt.date.today())

if "anchor_date" not in st.session_state:
    st.session_state.anchor_date = st.session_state.selected_date

if "selected_event_id" not in st.session_state:
    st.session_state.selected_event_id = None

if "cal_key" not in st.session_state:
    st.session_state.cal_key = 0

if "tag_filter" not in st.session_state:
    st.session_state.tag_filter = "All"

if "page" not in st.session_state:
    st.session_state.page = "Calendar"  # Calendar | Feedback


def _clear_selection():
    st.session_state.selected_event_id = None


# -----------------------------
# Sidebar: Navigation
# -----------------------------
st.sidebar.header("Navigate")
st.session_state.page = st.sidebar.radio(
    "Page",
    ["Calendar", "Feedback"],
    index=0 if st.session_state.page == "Calendar" else 1,
    key="nav_page",
)

st.sidebar.divider()

# -----------------------------
# FEEDBACK PAGE (full screen takeover)
# -----------------------------
if st.session_state.page == "Feedback":
    st.title("Feedback")

    day = parse_iso_date(st.session_state.selected_date)

    items = []
    for ev in st.session_state.events:
        if not _event_occurs_on_day(ev, day):
            continue
        occ_key = _occurrence_key(ev.get("id", ""), day)
        fb = st.session_state.feedback.get(occ_key, {})
        if fb.get("done") is True:
            continue
        items.append(ev)

    if not items:
        st.info("No items need feedback for this day.")
        st.caption("Tip: click a date on the calendar page to change the selected day.")
    else:
        labels = [_event_label(ev) for ev in items]
        pick = st.selectbox("Pick an item", labels, key="feedback_pick_item")

        selected_ev = items[labels.index(pick)]
        event_id = selected_ev.get("id")
        occ_key = _occurrence_key(event_id, day)

        st.subheader(selected_ev.get("title", "(No title)"))
        s = _parse_iso_dt(selected_ev.get("start", ""))
        e = _parse_iso_dt(selected_ev.get("end", ""))
        if s and e:
            st.write(f"Time: **{_fmt_dt_range(s, e)}**")
        tags = selected_ev.get("tags") or []
        if tags:
            st.write(f"Tags: **{', '.join(tags)}**")

        desc = (selected_ev.get("description") or "").strip()
        if desc:
            st.write(desc)

        st.divider()
        st.subheader("How was it?")

        st.markdown(
            """
            <style>
            div[data-testid="column"] button {
                height: 78px !important;
                font-size: 46px !important;
                line-height: 1 !important;
                padding: 0 !important;
                width: 100% !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        if "feedback_rating" not in st.session_state:
            st.session_state.feedback_rating = None

        cols = st.columns(5)
        for i, (emo, score) in enumerate(EMOJI_CHOICES):
            if cols[i].button(emo, key=f"fb_emo_{score}", use_container_width=True):
                st.session_state.feedback_rating = score

        if st.session_state.feedback_rating is not None:
            st.caption(f"Selected: {EMOJI_CHOICES[st.session_state.feedback_rating - 1][0]}")

        notes = st.text_area("Notes (optional)", height=120, key="fb_notes")

        if st.button("Done", use_container_width=True):
            if st.session_state.feedback_rating is None:
                st.error("Pick an emoji first.")
            else:
                st.session_state.feedback[occ_key] = {
                    "event_id": event_id,
                    "date": day.isoformat(),
                    "rating": int(st.session_state.feedback_rating),
                    "notes": (notes or "").strip(),
                    "done": True,
                    "saved_at": dt.datetime.now().isoformat(timespec="seconds"),
                }
                _save_feedback(st.session_state.feedback)

                st.session_state.feedback_rating = None
                if "fb_notes" in st.session_state:
                    del st.session_state["fb_notes"]
                if "feedback_pick_item" in st.session_state:
                    del st.session_state["feedback_pick_item"]

                st.rerun()

    st.stop()

# -----------------------------
# CALENDAR PAGE
# -----------------------------
left, mid, right = st.columns([1.4, 2.2, 1.4])

with left:
    if st.button("Today", use_container_width=True):
        today = dt.date.today()
        st.session_state.selected_date = iso_date(today)
        st.session_state.anchor_date = st.session_state.selected_date
        _clear_selection()
        st.session_state.cal_key += 1
        st.rerun()

with mid:
    c1, c2, c3 = st.columns([0.6, 1.8, 0.6])
    with c1:
        if st.button("◀", use_container_width=True):
            a = parse_iso_date(st.session_state.anchor_date)
            a2 = shift_anchor(a, st.session_state.view, -1)
            st.session_state.anchor_date = iso_date(a2)
            st.session_state.selected_date = iso_date(a2)
            _clear_selection()
            st.session_state.cal_key += 1
            st.rerun()

    with c2:
        a = parse_iso_date(st.session_state.anchor_date)
        st.markdown(
            f"<h2 style='text-align:center; margin:0;'>{header_label(st.session_state.view, a)}</h2>",
            unsafe_allow_html=True,
        )

    with c3:
        if st.button("▶", use_container_width=True):
            a = parse_iso_date(st.session_state.anchor_date)
            a2 = shift_anchor(a, st.session_state.view, +1)
            st.session_state.anchor_date = iso_date(a2)
            st.session_state.selected_date = iso_date(a2)
            _clear_selection()
            st.session_state.cal_key += 1
            st.rerun()

with right:
    v1, v2, v3 = st.columns(3)
    new_view = st.session_state.view
    with v1:
        if st.button("Month", use_container_width=True):
            new_view = "month"
    with v2:
        if st.button("Week", use_container_width=True):
            new_view = "week"
    with v3:
        if st.button("Day", use_container_width=True):
            new_view = "day"

    if new_view != st.session_state.view:
        st.session_state.view = new_view
        _clear_selection()
        st.session_state.cal_key += 1
        st.rerun()

st.divider()
default_date = parse_iso_date(st.session_state.selected_date)

# Sidebar: Filter by tag
st.sidebar.header("Filter")
tag_filter = st.sidebar.selectbox(
    "Tag",
    ["All"] + TAG_OPTIONS,
    index=(["All"] + TAG_OPTIONS).index(st.session_state.tag_filter)
    if st.session_state.tag_filter in (["All"] + TAG_OPTIONS)
    else 0,
    key="filter_tag_select",
)
st.session_state.tag_filter = tag_filter


def passes_filter(ev: dict) -> bool:
    if st.session_state.tag_filter == "All":
        return True
    tags = ev.get("tags") or []
    return st.session_state.tag_filter in tags


display_events = [ev for ev in st.session_state.events if passes_filter(ev)]
st.sidebar.divider()

# Sidebar: PROF (only the 4 research tags)
with st.sidebar.expander("Prof", expanded=False):
    prof_tag = st.selectbox("Choose a tag", RESEARCH_TAGS, key="prof_tag_select")
    src = PROF_SOURCES.get(prof_tag, {})
    if src:
        st.markdown(f"**{prof_tag}**")
        authors = (src.get("authors") or "").strip()
        if authors:
            st.markdown(f"- Authors: {authors}")
        st.markdown(f"- Paper: [{src.get('title','Open')}]({src.get('url','')})")
        note = (src.get("note") or "").strip()
        if note:
            st.caption(note)

st.sidebar.divider()

# Sidebar: Create
st.sidebar.header("Create")

# ====== CREATE EVENT ======
with st.sidebar.expander("Create Event", expanded=True):
    if "_force_ui_rerun" not in st.session_state:
        st.session_state._force_ui_rerun = False

    def _mark_ui_rerun():
        st.session_state._force_ui_rerun = True

    sched_mode = st.selectbox(
        "Scheduling mode",
        ["Manual (pick times)", "Research-Based", "Your best time"],
        index=0,
        key="create_event_sched_mode",
        on_change=_mark_ui_rerun,
    )

    research_tag = None
    if sched_mode == "Research-Based":
        research_tag = st.selectbox(
            "Research Tag",
            RESEARCH_TAGS,
            key="create_event_research_tag",
            on_change=_mark_ui_rerun,
        )

    if st.session_state._force_ui_rerun:
        st.session_state._force_ui_rerun = False
        st.rerun()

    with st.form("create_event_form", clear_on_submit=True):
        moveable = False
        duration_min = 60

        if sched_mode == "Research-Based":
            paper = RESEARCH_PAPERS.get(research_tag, {})

            ev_title = st.text_input("Title", key="create_event_title")
            ev_desc = st.text_area("Description", height=80, key="create_event_desc")

            if research_tag == "Sleep (Timing & Health)":
                rec_hours = float(paper.get("recommended_sleep_hours", 9.0))
                min_h = float(paper.get("min_sleep_hours", 6.0))
                max_h = float(paper.get("max_sleep_hours", 11.0))

                st.caption(f"Recommended sleep duration: **{rec_hours:.1f} hours** (adjust below)")
                sleep_hours = st.slider(
                    "How many hours do you want to sleep?",
                    min_value=min_h,
                    max_value=max_h,
                    value=rec_hours,
                    step=0.5,
                    key="create_event_sleep_hours",
                )
                duration_min = int(round(float(sleep_hours) * 60))
            else:
                duration_min = st.number_input(
                    "How long should it last? (minutes)",
                    min_value=5,
                    max_value=8 * 60,
                    value=60,
                    step=5,
                    key="create_event_duration",
                )

            moveable = st.checkbox(
                "AI can move this event around in the future (flexible)",
                value=True,
                key="create_event_moveable",
            )
            ev_date = st.date_input("Date", value=default_date, key="create_event_date")

        elif sched_mode == "Manual (pick times)":
            ev_title = st.text_input("Title", key="create_event_title")
            ev_desc = st.text_area("Description", height=80, key="create_event_desc")
            ev_date = st.date_input("Date", value=default_date, key="create_event_date")
            ev_tag = st.selectbox("Tag", TAG_OPTIONS, index=0, key="create_event_tag")

            c1, c2 = st.columns(2)
            with c1:
                start_text = st.text_input("Start (type, e.g., 9:15 AM)", value="9:00 AM", key="create_event_start_text")
            with c2:
                end_text = st.text_input("End (type, e.g., 10:45 AM)", value="10:00 AM", key="create_event_end_text")

            moveable = st.checkbox(
                "AI can move this event around (flexible)",
                value=True,
                key="create_event_moveable",
            )

        else:  # "Your best time"
            ev_title = st.text_input("Title", key="create_event_title")
            ev_desc = st.text_area("Description", height=80, key="create_event_desc")
            ev_date = st.date_input("Date", value=default_date, key="create_event_date")
            ev_tag = st.selectbox("Tag", TAG_OPTIONS, index=0, key="create_event_tag")

            duration_min = st.number_input(
                "How long should it last? (minutes)",
                min_value=5,
                max_value=8 * 60,
                value=60,
                step=5,
                key="create_event_duration",
            )

            moveable = st.checkbox(
                "AI can move this event around in the future (flexible)",
                value=True,
                key="create_event_moveable",
            )

        add_event = st.form_submit_button("Add Event", use_container_width=True)

    if add_event:
        new_id = uuid.uuid4().hex[:10]

        if sched_mode == "Research-Based":
            paper = RESEARCH_PAPERS.get(research_tag, {})
            base_tag = paper.get("base_tag", "Health")
            start_t = paper.get("default_start", dt.time(17, 0))

            proposed = dt.datetime.combine(ev_date, start_t)
            sdt, edt = find_next_free_slot(st.session_state.events, ev_date, proposed, int(duration_min))

            tags_to_store = [research_tag, base_tag] if research_tag else [base_tag]

            extended = {
                "description": (ev_desc or "").strip(),
                "scheduling_mode": "Research-Based",
                "moveable": bool(moveable),
                "duration_min": int((edt - sdt).total_seconds() // 60),
                "research_tag": research_tag,
                "research_paper_title": paper.get("title", ""),
                "research_paper_authors": paper.get("authors", ""),
                "research_paper_url": paper.get("url", ""),
            }
            if research_tag == "Sleep (Timing & Health)":
                extended["sleep_hours"] = round(int(duration_min) / 60.0, 2)
                extended["recommended_sleep_hours"] = float(paper.get("recommended_sleep_hours", 9.0))

        elif sched_mode == "Manual (pick times)":
            start_t = _parse_time_12h(start_text, dt.time(9, 0))
            end_t = _parse_time_12h(end_text, dt.time(10, 0))

            sdt = dt.datetime.combine(ev_date, start_t)
            edt = dt.datetime.combine(ev_date, end_t)
            if edt <= sdt:
                edt = sdt + dt.timedelta(minutes=30)

            tags_to_store = [ev_tag]
            extended = {
                "description": (ev_desc or "").strip(),
                "scheduling_mode": "Manual (pick times)",
                "moveable": bool(moveable),
                "duration_min": int((edt - sdt).total_seconds() // 60),
            }

        else:  # "Your best time"
            start_t = suggest_best_time_from_history(st.session_state.events, ev_tag)
            proposed = dt.datetime.combine(ev_date, start_t)
            sdt, edt = find_next_free_slot(st.session_state.events, ev_date, proposed, int(duration_min))

            tags_to_store = [ev_tag]
            extended = {
                "description": (ev_desc or "").strip(),
                "scheduling_mode": "Your best time",
                "moveable": bool(moveable),
                "duration_min": int((edt - sdt).total_seconds() // 60),
            }

        new_ev = {
            "id": new_id,
            "kind": "event",
            "title": (ev_title.strip() if isinstance(ev_title, str) else "") or "(No title)",
            "tags": tags_to_store,
            "description": (ev_desc or "").strip(),
            "extendedProps": extended,
            "allDay": False,
            "start": sdt.isoformat(),
            "end": edt.isoformat(),
        }

        st.session_state.events.append(new_ev)
        _save_events(st.session_state.events)
        st.session_state.cal_key += 1
        st.rerun()
# ====== END CREATE EVENT ======

with st.sidebar.expander("Create Task", expanded=False):
    with st.form("create_task_form", clear_on_submit=True):
        t_title = st.text_input("Title", key="create_task_title")
        t_desc = st.text_area("Description", height=80, key="create_task_desc")
        t_date = st.date_input("Date", value=default_date, key="create_task_date")
        t_tag = st.selectbox("Tag", TAG_OPTIONS, index=0, key="create_task_tag")
        t_done = st.checkbox("Completed", value=False, key="create_task_done")

        add_task = st.form_submit_button("Add Task", use_container_width=True)

    if add_task:
        new_id = uuid.uuid4().hex[:10]
        new_task = {
            "id": new_id,
            "kind": "task",
            "title": t_title.strip() or "(No title)",
            "tags": [t_tag],
            "description": (t_desc or "").strip(),
            "extendedProps": {"description": (t_desc or "").strip()},
            "allDay": True,
            "start": iso_date(t_date),
            "done": bool(t_done),
        }
        st.session_state.events.append(new_task)
        _save_events(st.session_state.events)
        st.session_state.cal_key += 1
        st.rerun()

st.sidebar.divider()

# -----------------------------
# Sidebar: Edit/Delete  (CHANGED BACK to the previous style)
# -----------------------------
st.sidebar.header("Edit / Delete")

selected_event = None
if st.session_state.selected_event_id:
    for ev in st.session_state.events:
        if ev.get("id") == st.session_state.selected_event_id:
            selected_event = ev
            break

if not selected_event:
    st.sidebar.caption("Click an item on the calendar to edit/delete.")
else:
    st.sidebar.caption("Selected item")

    ed_kind = selected_event.get("kind", "event")

    with st.form("edit_form", clear_on_submit=False):
        ed_title = st.text_input("Title", value=selected_event.get("title", ""))
        ed_desc = st.text_area(
            "Description",
            value=selected_event.get("description", selected_event.get("extendedProps", {}).get("description", "")) or "",
            height=110,
        )

        current_tag = (selected_event.get("tags") or [TAG_OPTIONS[0]])[0]
        ed_tag = st.selectbox(
            "Tag",
            TAG_OPTIONS,
            index=TAG_OPTIONS.index(current_tag) if current_tag in TAG_OPTIONS else 0,
        )

        start_str = (selected_event.get("start") or "")[:10] or st.session_state.selected_date
        ed_date = st.date_input("Date", value=parse_iso_date(start_str))

        if ed_kind == "event":
            ed_all_day = st.checkbox("All-day", value=bool(selected_event.get("allDay", True)))

            def _safe_time_from_iso(value: str, fallback: dt.time) -> dt.time:
                if isinstance(value, str) and "T" in value and len(value) >= 19:
                    try:
                        return dt.time.fromisoformat(value[11:19])
                    except Exception:
                        return fallback
                return fallback

            if not ed_all_day:
                ed_start = st.time_input(
                    "Start",
                    value=_safe_time_from_iso(selected_event.get("start", ""), dt.time(9, 0)),
                )
                ed_end = st.time_input(
                    "End",
                    value=_safe_time_from_iso(selected_event.get("end", ""), dt.time(10, 0)),
                )
        else:
            ed_all_day = True
            ed_done = st.checkbox("Completed", value=bool(selected_event.get("done", False)))

        c1, c2 = st.columns(2)
        save_btn = c1.form_submit_button("Save", use_container_width=True)
        delete_btn = c2.form_submit_button("Delete", use_container_width=True)

    if save_btn:
        for ev in st.session_state.events:
            if ev.get("id") == selected_event.get("id"):
                ev["title"] = ed_title.strip() or "(No title)"

                existing_tags = ev.get("tags") or []
                if existing_tags:
                    existing_tags[0] = ed_tag
                    ev["tags"] = existing_tags
                else:
                    ev["tags"] = [ed_tag]

                ev["kind"] = ed_kind
                ev["description"] = (ed_desc or "").strip()
                ev["extendedProps"] = ev.get("extendedProps") or {}
                ev["extendedProps"]["description"] = (ed_desc or "").strip()

                if ed_kind == "task":
                    ev["allDay"] = True
                    ev["start"] = iso_date(ed_date)
                    ev["done"] = bool(ed_done)
                    ev.pop("end", None)
                else:
                    if ed_all_day:
                        ev["allDay"] = True
                        ev["start"] = iso_date(ed_date)
                        ev.pop("end", None)
                    else:
                        sdt = dt.datetime.combine(ed_date, ed_start)
                        edt = dt.datetime.combine(ed_date, ed_end)
                        if edt <= sdt:
                            edt = sdt + dt.timedelta(minutes=30)
                        ev["allDay"] = False
                        ev["start"] = sdt.isoformat()
                        ev["end"] = edt.isoformat()
                break

        _save_events(st.session_state.events)
        _clear_selection()
        st.session_state.cal_key += 1
        st.rerun()

    if delete_btn:
        st.session_state.events = [ev for ev in st.session_state.events if ev.get("id") != selected_event.get("id")]
        _save_events(st.session_state.events)
        _clear_selection()
        st.session_state.cal_key += 1
        st.rerun()

# -----------------------------
# Calendar options + highlighting rules
# -----------------------------
view_map = {"month": "dayGridMonth", "week": "timeGridWeek", "day": "timeGridDay"}
options = {
    "initialView": view_map[st.session_state.view],
    "initialDate": st.session_state.selected_date,
    "headerToolbar": False,
    "height": 740 if st.session_state.view in ("week", "day") else 760,
    "expandRows": True,
    "editable": False,
    "selectable": True,
    "dayMaxEvents": True,
    "firstDay": 0,
    "nowIndicator": True,
    "timeZone": "local",
    "slotMinTime": "00:00:00",
    "slotMaxTime": "24:00:00",
    "scrollTime": "08:00:00",
    "eventTimeFormat": {"hour": "numeric", "minute": "2-digit", "meridiem": "short"},
}

sel = st.session_state.selected_date
css = []

css.append(
    f"""
.fc .fc-daygrid-day[data-date="{sel}"] {{
  background: rgba(66, 133, 244, 0.12);
}}
.fc .fc-daygrid-day[data-date="{sel}"] .fc-daygrid-day-number {{
  background: rgba(66, 133, 244, 0.90);
  color: white !important;
  border-radius: 999px;
  padding: 2px 8px;
  display: inline-block;
}}
"""
)

if st.session_state.view == "week":
    css.append(
        f"""
.fc .fc-timegrid-col[data-date="{sel}"] {{
  background: rgba(66, 133, 244, 0.08);
}}
"""
    )

css.append(
    """
.fc .fc-scroller { overflow-y: auto !important; }
.fc .fc-now-indicator-line { border-width: 2px !important; }

/* Past events -> green */
.fc .fc-event-past,
.fc .fc-daygrid-event.fc-event-past,
.fc .fc-timegrid-event.fc-event-past {
  background-color: #2e7d32 !important;
  border-color: #2e7d32 !important;
}
"""
)

st.markdown(f"<style>{''.join(css)}</style>", unsafe_allow_html=True)

cal_state = calendar(
    events=display_events,
    options=options,
    key=f"calendar_{st.session_state.cal_key}",
)

# -----------------------------
# Click handling
# -----------------------------
if cal_state:
    if cal_state.get("eventClick"):
        ev = cal_state["eventClick"].get("event", {})
        ev_id = ev.get("id")
        if ev_id:
            st.session_state.selected_event_id = ev_id
            start10 = (ev.get("start") or "")[:10]
            if start10:
                st.session_state.selected_date = start10
                st.session_state.anchor_date = start10
            st.session_state.cal_key += 1
            st.rerun()

    if cal_state.get("dateClick"):
        dstr = cal_state["dateClick"].get("date", "")[:10]
        if dstr:
            st.session_state.selected_date = dstr
            st.session_state.anchor_date = dstr
            _clear_selection()
            st.session_state.cal_key += 1
            st.rerun()
