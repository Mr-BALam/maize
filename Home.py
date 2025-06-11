import streamlit as st
import hashlib
import sqlite3
import random
import string
import os

DB_FILE = "maize.db"

# --- DATABASE SETUP ---
def create_users_table():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT ,
            password_hash TEXT NOT NULL,
            confirmed BOOLEAN NOT NULL DEFAULT 0,
            confirmation_code TEXT
        )
        """)

        # Logs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(email) REFERENCES users(email)
        )
        """)
        conn.commit()

# --- HASHING PASSWORD ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- GENERATE CONFIRMATION CODE ---
def generate_confirmation_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- SEND EMAIL (SIMULATION) ---
def send_confirmation_email(email, code):
    st.info(f"Confirmation code for {email}: {code}")  # For testing purposes

# --- LOG USER ACTION ---
def log_user_action(email, action):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (email, action) VALUES (?, ?)", (email, action))
        conn.commit()

# --- REGISTER USER ---
def register_user(email, password):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            st.warning("Email already registered.")
            return False

        password_hash = hash_password(password)
        code = generate_confirmation_code()
        cursor.execute("INSERT INTO users (email, password_hash, confirmed, confirmation_code) VALUES (?, ?, 0, ?)",
                       (email, password_hash, code))
        conn.commit()
        send_confirmation_email(email, code)
        log_user_action(email, "Registered")
        return True

# --- CONFIRM USER ---
def confirm_user(email, code):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT confirmation_code FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row and row[0] == code:
            cursor.execute("UPDATE users SET confirmed = 1 WHERE email = ?", (email,))
            conn.commit()
            log_user_action(email, "Confirmed Email")
            return True
    return False

# --- AUTHENTICATE USER ---
def authenticate_user(email, password):
    hashed = hash_password(password)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, confirmed FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row and row[0] == hashed and row[1]:
            log_user_action(email, "Logged In")
            return True
    return False

# --- RESET PASSWORD ---
def update_user_password(email, new_password):
    hashed = hash_password(new_password)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed, email))
            conn.commit()
            log_user_action(email, "Password Reset")
            return True
    return False

# --- VIEW LOGS ---
def view_logs():
    st.subheader("User Action Logs")
    with sqlite3.connect(DB_FILE) as conn:
        logs = conn.execute("SELECT * FROM logs ORDER BY timestamp DESC").fetchall()
        if logs:
            for log in logs:
                st.text(f"[{log[3]}] {log[1]} - {log[2]}")
        else:
            st.info("No logs found.")

# --- MAIN STREAMLIT PAGE ---
def login_page():
    create_users_table()

    st.title("User Login System")
    menu = ["Login", "Register", "Confirm", "Forgot Password", "View Logs"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_user(email, password):
                st.success(f"Logged in as {email}")
                st.session_state["logged_in"] = True
                st.session_state["email"] = email
            else:
                st.error("Invalid email, password, or unconfirmed account.")

    elif choice == "Register":
        st.subheader("Create New Account")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(email, password):
                st.success("Registered successfully! Check your email for confirmation code.")

    elif choice == "Confirm":
        st.subheader("Confirm Email")
        email = st.text_input("Email")
        code = st.text_input("Confirmation Code")
        if st.button("Confirm"):
            if confirm_user(email, code):
                st.success("Account confirmed! You can now login.")
            else:
                st.error("Invalid email or confirmation code.")

    elif choice == "Forgot Password":
        st.subheader("Reset Password")
        email = st.text_input("Email")
        new_password = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            if update_user_password(email, new_password):
                st.success("Password updated. You can now login.")
            else:
                st.error("Email not found.")

    elif choice == "View Logs":
        view_logs()

# Run the app
if __name__ == "__main__":
    login_page()
