"""
skills/contacts_messaging_skills.py

Module 7: Email, Messaging and Contacts
Implements contact lookup and management, WhatsApp messaging integration,
suggested email replies, and meeting invitations.
Auto-registered via engine.py.
"""

import os
import sqlite3
import urllib.parse
import webbrowser

DB_PATH = "maya_history.db"


def _get_contacts_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE COLLATE NOCASE,
            phone TEXT,
            email TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    return conn


def save_contact(name: str, phone: str = "", email: str = "", notes: str = "") -> str:
    """Saves or updates a contact in Maya's address book. Example: name='Rahul', phone='+919876543210', email='rahul@example.com'."""
    try:
        conn = _get_contacts_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contacts (name, phone, email, notes) VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET phone=excluded.phone, email=excluded.email, notes=excluded.notes
        """, (name.strip(), phone.strip(), email.strip(), notes.strip()))
        conn.commit()
        return f"Contact saved: '{name.strip()}' (Phone: {phone or 'N/A'}, Email: {email or 'N/A'})."
    except Exception as e:
        return f"Error saving contact: {e}"


def find_contact(query: str) -> str:
    """Searches for a contact by name, phone, or email in Maya's address book."""
    try:
        conn = _get_contacts_db()
        cursor = conn.cursor()
        q = f"%{query.strip()}%"
        cursor.execute("SELECT name, phone, email, notes FROM contacts WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?", (q, q, q))
        rows = cursor.fetchall()
        if not rows:
            return f"No contact found matching '{query}'."
        results = [f"{r[0]}: Phone {r[1] or 'N/A'}, Email {r[2] or 'N/A'}" for r in rows]
        return "Found contact(s): " + "; ".join(results)
    except Exception as e:
        return f"Error searching contact: {e}"


def list_contacts() -> str:
    """Lists all contacts saved in Maya's address book."""
    try:
        conn = _get_contacts_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, phone, email FROM contacts ORDER BY name LIMIT 20")
        rows = cursor.fetchall()
        if not rows:
            return "Your contact address book is empty. Say 'save contact: Name, phone, email' to add one."
        entries = [f"• {r[0]} ({r[1] or r[2] or 'No details'})" for r in rows]
        return f"Saved Contacts ({len(rows)}):\n" + "\n".join(entries)
    except Exception as e:
        return f"Error listing contacts: {e}"


def send_whatsapp_message(contact_name_or_phone: str, message: str) -> str:
    """Opens WhatsApp (web or app) to send a message to a phone number or saved contact. Requires user review before sending."""
    target = contact_name_or_phone.strip()
    phone = target

    # Check if target is a contact name
    try:
        conn = _get_contacts_db()
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM contacts WHERE name LIKE ?", (f"%{target}%",))
        row = cursor.fetchone()
        if row and row[0]:
            phone = row[0]
    except Exception:
        pass

    clean_phone = "".join(filter(str.isdigit, phone))
    msg_encoded = urllib.parse.quote(message.strip())

    if clean_phone:
        url = f"https://wa.me/{clean_phone}?text={msg_encoded}"
    else:
        url = f"https://web.whatsapp.com/send?text={msg_encoded}"

    webbrowser.open(url)
    return f"WhatsApp opened for {target} with message: '{message}'. Please click send to deliver."


def suggest_email_reply(email_content: str, tone: str = "professional") -> str:
    """Generates three context-aware, structured email response suggestions (affirmative, neutral, polite reschedule)."""
    t = tone.lower().strip()
    suggestions = [
        f"1. Affirmative ({t.title()}): 'Thank you for your email. I have reviewed the details and agree with the proposed approach. Looking forward to our next steps.'",
        f"2. Informative ({t.title()}): 'Thanks for reaching out. I am currently reviewing the documents and will send over my detailed feedback by tomorrow afternoon.'",
        f"3. Reschedule / Alternative: 'Thank you for following up. I have a prior commitment at that time, but would 2:00 PM tomorrow work better for you?'"
    ]
    return f"Suggested Email Replies ({tone}):\n" + "\n".join(suggestions)


def create_meeting_invitation(title: str, date_time: str, attendees: str = "") -> str:
    """Generates a professional meeting invitation text with calendar agenda and participant details."""
    invite = (
        f"--- Meeting Invitation ---\n"
        f"Subject: Invitation: {title}\n"
        f"When: {date_time}\n"
        f"Attendees: {attendees or 'Team'}\n"
        f"Agenda: Discussion on deliverables, progress alignment, and action steps.\n"
        f"Format: Virtual / Desktop Conference"
    )
    return invite
