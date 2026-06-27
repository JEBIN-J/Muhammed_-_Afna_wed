from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app) # Allow cross-origin requests

# Configuration
# Configuration
GMAIL_USER = "jebinstar1@gmail.com"
GMAIL_PASS = "dleb xrkr mdbg osmb"
TARGET_EMAILS = ["jebin6884@gmail.com", "afnafathimah@gmail.com", "jazzjasmineh@gmail.com"]

# File-based Tracking Initialization
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FILE = os.path.join(BASE_DIR, 'stats.json')

def init_stats():
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'w') as f:
            json.dump({"Muhammed side": 0, "Afna side": 0}, f)

def get_stats():
    with open(STATS_FILE, 'r') as f:
        return json.load(f)

def update_stats(side, count):
    stats = get_stats()
    if side in stats:
        stats[side] += count
    else:
        stats[side] = count
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f)
    return stats

init_stats()

def send_mail(subject, body):
    try:
        print(f"Attempting to send email to {', '.join(TARGET_EMAILS)}...")
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = ", ".join(TARGET_EMAILS)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1) # Enable SMTP debug output
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"CRITICAL SMTP Error: {e}")
        return False

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/send-email', methods=['POST'])
def handle_email():
    data = request.json
    print(f"\n--- DEBUG: Received RSVP Data ---\n{json.dumps(data, indent=2)}")
    
    subject = data.get('subject', 'New Wedding Wish/RSVP')
    content = data.get('body', '')
    
    # Tracking Counts Logic (File-based)
    name = data.get('name', 'Guest')
    guests = data.get('guests', 1)
    side = data.get('side', 'Unknown')
    attendance = data.get('attendance', 'No')

    # Parse guest count robustly
    try:
        # Convert to int, default to 1 if empty/invalid
        guests_val = int(guests) if str(guests).strip() else 1
        guests_to_add = guests_val if attendance == 'Yes' else 0
    except Exception as e:
        print(f"Error parsing guests: {e}")
        guests_to_add = 1 if attendance == 'Yes' else 0

    print(f"Guests to add: {guests_to_add} for side: {side}")

    # Update Stats in JSON file
    all_stats = update_stats(side, guests_to_add)
    
    muhammed_total = all_stats.get('Muhammed side', 0)
    afna_total = all_stats.get('Afna side', 0)

    # Append counts to email content
    count_summary = (
        f"\n\n--- RSVP TRACKING STATS ---\n"
        f"Total Guests (Muhammed Side): {muhammed_total}\n"
        f"Total Guests (Afna Side): {afna_total}\n"
        f"---------------------------\n"
        f"* This guest ({name}) selected: {side}\n"
        f"* Attendance: {attendance} ({guests_to_add} guests)"
    )
    full_content = content + count_summary
    
    if send_mail(subject, full_content):
        return jsonify({
            "status": "success", 
            "muhammed_total": muhammed_total,
            "afna_total": afna_total
        }), 200
    else:
        return jsonify({"status": "error", "message": "Failed to send email"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
