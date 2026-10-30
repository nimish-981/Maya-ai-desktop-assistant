"""
skills/calendar_scheduling_skills.py

Module 6: Productivity & Scheduling
Implements calendar event management, meeting agendas, daily schedules,
habit tracking, and goal/deadline tracking.
Auto-registered via engine.py.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "maya_history.db"


def _get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            event_date TEXT,
            event_time TEXT,
            duration_minutes INTEGER,
            description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            streak INTEGER DEFAULT 0,
            last_logged TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            deadline TEXT,
            category TEXT,
            status TEXT DEFAULT 'IN_PROGRESS'
        )
    """)
    conn.commit()
    return conn


def create_calendar_event(title: str, date: str = "", time_str: str = "", duration_minutes: str = "60", description: str = "") -> str:
    """Creates a new calendar event or meeting. date format: 'YYYY-MM-DD' or 'today'/'tomorrow'. time_str format: 'HH:MM AM/PM'."""
    try:
        conn = _get_db()
        now = datetime.now()
        target_date = date.strip().lower()

        if not target_date or target_date == "today":
            event_date = now.strftime("%Y-%m-%d")
        elif target_date == "tomorrow":
            event_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            event_date = target_date

        event_time = time_str.strip() or now.strftime("%I:%M %p")
        dur = int(''.join(filter(str.isdigit, duration_minutes)) or '60')

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO calendar_events (title, event_date, event_time, duration_minutes, description) VALUES (?, ?, ?, ?, ?)",
            (title.strip(), event_date, event_time, dur, description.strip())
        )
        conn.commit()
        return f"Calendar event created: '{title}' scheduled for {event_date} at {event_time} ({dur} mins)."
    except Exception as e:
        return f"Error creating calendar event: {e}"


def list_calendar_events(date: str = "") -> str:
    """Lists scheduled calendar events and meetings. If date is empty or 'today', shows today's events."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        now = datetime.now()
        target_date = date.strip().lower()

        if not target_date or target_date == "today":
            filter_date = now.strftime("%Y-%m-%d")
            cursor.execute("SELECT id, title, event_date, event_time, duration_minutes FROM calendar_events WHERE event_date = ? ORDER BY event_time", (filter_date,))
        elif target_date in ("all", "upcoming"):
            filter_date = now.strftime("%Y-%m-%d")
            cursor.execute("SELECT id, title, event_date, event_time, duration_minutes FROM calendar_events WHERE event_date >= ? ORDER BY event_date, event_time LIMIT 10", (filter_date,))
        else:
            cursor.execute("SELECT id, title, event_date, event_time, duration_minutes FROM calendar_events WHERE event_date = ? ORDER BY event_time", (target_date,))

        rows = cursor.fetchall()
        if not rows:
            return f"No calendar events found for {target_date or 'today'}."

        items = [f"#{r[0]} '{r[1]}' on {r[2]} at {r[3]} ({r[4]} min)" for r in rows]
        return f"Found {len(rows)} event(s): " + "; ".join(items)
    except Exception as e:
        return f"Error retrieving calendar events: {e}"


def reschedule_calendar_event(event_id_or_title: str, new_date: str, new_time: str) -> str:
    """Reschedules an existing calendar event. Example: event_id_or_title='1' or 'Team Sync', new_date='2026-10-30', new_time='03:00 PM'."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        val = event_id_or_title.strip()
        if val.isdigit():
            cursor.execute("UPDATE calendar_events SET event_date = ?, event_time = ? WHERE id = ?", (new_date, new_time, int(val)))
        else:
            cursor.execute("UPDATE calendar_events SET event_date = ?, event_time = ? WHERE title LIKE ?", (new_date, new_time, f"%{val}%"))
        conn.commit()
        if cursor.rowcount > 0:
            return f"Event '{event_id_or_title}' rescheduled to {new_date} at {new_time}."
        return f"No event found matching '{event_id_or_title}'."
    except Exception as e:
        return f"Error rescheduling event: {e}"


def delete_calendar_event(event_id_or_title: str) -> str:
    """Deletes a calendar event by ID or title."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        val = event_id_or_title.strip()
        if val.isdigit():
            cursor.execute("DELETE FROM calendar_events WHERE id = ?", (int(val),))
        else:
            cursor.execute("DELETE FROM calendar_events WHERE title LIKE ?", (f"%{val}%",))
        conn.commit()
        if cursor.rowcount > 0:
            return f"Event '{event_id_or_title}' removed from calendar."
        return f"No event found matching '{event_id_or_title}'."
    except Exception as e:
        return f"Error deleting event: {e}"


def generate_meeting_agenda(topic: str, duration_minutes: str = "30", attendees: str = "Team") -> str:
    """Generates a structured, professional meeting agenda with time allocations and discussion goals."""
    dur = int(''.join(filter(str.isdigit, duration_minutes)) or '30')
    intro_time = max(5, int(dur * 0.15))
    review_time = int(dur * 0.50)
    action_time = dur - intro_time - review_time

    agenda = (
        f"Meeting Agenda for '{topic}' ({dur} Mins | Attendees: {attendees}):\n"
        f"1. Context & Objectives ({intro_time} mins): Align on goals and desired outcomes.\n"
        f"2. Core Discussion & Deep Dive ({review_time} mins): Review progress, roadblocks, and solutions.\n"
        f"3. Action Items & Ownership ({action_time} mins): Assign deliverables, owners, and deadlines."
    )
    return agenda


def generate_daily_schedule(tasks: str = "") -> str:
    """Creates a time-blocked productive daily schedule tailored to user's pending items and focus blocks."""
    now = datetime.now()
    schedule = [
        f"Daily Focus Schedule for {now.strftime('%A, %b %d')}:",
        "• 09:00 AM - 11:00 AM: Deep Work Block 1 (High priority technical / creative tasks)",
        "• 11:00 AM - 11:30 AM: Communication & Email triage",
        "• 11:30 AM - 01:00 PM: Deep Work Block 2 (Execution and testing)",
        "• 01:00 PM - 02:00 PM: Lunch & Rest Break",
        "• 02:00 PM - 04:00 PM: Collaborative Sessions & Project review",
        "• 04:00 PM - 05:30 PM: Wrap-up, Documentation & Daily Summary",
    ]
    if tasks:
        schedule.append(f"Focus Items Integrated: {tasks.strip()}")
    return "\n".join(schedule)


def track_goal_or_deadline(title: str, deadline_date: str, category: str = "project") -> str:
    """Records and tracks a goal, project milestone, or academic deadline. Example: title='Hackathon Demo', deadline_date='2026-11-05'."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO goals (title, deadline, category) VALUES (?, ?, ?)", (title.strip(), deadline_date.strip(), category.strip()))
        conn.commit()
        return f"Goal/Deadline tracked: '{title}' due on {deadline_date} (Category: {category})."
    except Exception as e:
        return f"Error recording goal: {e}"


def track_habit(habit_name: str, action: str = "log") -> str:
    """Tracks daily habits (e.g. 'morning coding', 'hydration', 'reading'). action: 'log' (increments streak) or 'status'."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        name = habit_name.lower().strip()

        cursor.execute("SELECT id, streak, last_logged FROM habits WHERE name = ?", (name,))
        row = cursor.fetchone()

        if action.lower() == "status":
            if row:
                return f"Habit '{name.title()}': {row[1]} day streak (Last logged: {row[2]})."
            return f"Habit '{name.title()}' is not yet registered. Say 'log habit {name}' to start!"

        if row:
            hid, streak, last_logged = row
            if last_logged == today:
                return f"Habit '{name.title()}' was already logged today! Current streak: {streak} days."
            new_streak = streak + 1
            cursor.execute("UPDATE habits SET streak = ?, last_logged = ? WHERE id = ?", (new_streak, today, hid))
        else:
            new_streak = 1
            cursor.execute("INSERT INTO habits (name, streak, last_logged) VALUES (?, ?, ?)", (name, 1, today))

        conn.commit()
        return f"Awesome! Logged habit '{name.title()}'. Streak is now {new_streak} day(s) in a row! Keep going!"
    except Exception as e:
        return f"Error logging habit: {e}"
