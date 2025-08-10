from flask import Flask, render_template, request, redirect, flash
import sqlite3
import re
import os
from werkzeug.utils import secure_filename

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secret key

EMAIL_ADDRESS = "shyamsonu13@gmail.com"
EMAIL_PASSWORD = "kart hieh sadk cmgb"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

DB_PATH = 'leads.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Old database deleted, creating new one.")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            resume_filename TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized with new schema.")

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "").strip()
        message = request.form.get("message", "").strip()
        resume = request.files.get("resume")

        if not (name and email and phone and role and message and resume):
            flash("Please fill in all fields and upload your resume.", "danger")
            return redirect("/")

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return redirect("/")

        if not allowed_file(resume.filename):
            flash("Resume file must be PDF or DOC/DOCX format.", "danger")
            return redirect("/")

        filename = secure_filename(resume.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        resume.save(save_path)

        # Save to DB
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''
                INSERT INTO leads (name, email, phone, role, message, resume_filename)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, phone, role, message, filename))
            conn.commit()
            conn.close()
        except Exception as e:
            flash(f"Failed to save inquiry: {e}", "danger")
            return redirect("/")

        # Prepare and send email with attachment
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = EMAIL_ADDRESS
            msg['Subject'] = "New Contact Form Submission with Resume"

            # Email body text
            body = f"""
Name: {name}
Email: {email}
Phone: {phone}
Role Seeking: {role}
Message:
{message}
"""
            msg.attach(MIMEText(body, 'plain'))

            # Attach resume file
            with open(save_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=filename)
            part['Content-Disposition'] = f'attachment; filename="{filename}"'
            msg.attach(part)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)

            flash("Message and resume sent successfully! We will get back to you soon.", "success")
        except Exception as e:
            flash(f"Failed to send email: {e}", "danger")

        return redirect("/")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
