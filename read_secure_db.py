import sqlite3
import sys
from cryptography.fernet import Fernet

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Secret Key Load karo
with open("maya_secret.key", "rb") as key_file:
    key = key_file.read()
cipher_suite = Fernet(key)

# Database connect karo
conn = sqlite3.connect('maya_history.db')
cursor = conn.cursor()

print("🔒 --- SECURE MAYA DATABASE LOGS --- 🔓\n")

try:
    cursor.execute("SELECT timestamp, role, message FROM chats")
    rows = cursor.fetchall()
    
    for row in rows:
        timestamp = row[0]
        # Decrypt karo
        role = cipher_suite.decrypt(row[1].encode()).decode()
        message = cipher_suite.decrypt(row[2].encode()).decode()
        
        print(f"[{timestamp}] {role}: {message}")
        
except Exception as e:
    print("Error reading database. Make sure data is encrypted.")

conn.close()