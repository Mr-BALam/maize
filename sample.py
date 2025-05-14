import streamlit as st
import mysql.connector
import bcrypt
import random
import smtplib
from email.message import EmailMessage

# ---------------- DATABASE CONFIG ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",       # adjust if you've changed default
    password="",       # your MySQL password
    database="agri_users"
)
cursor = db.cursor(dictionary=True)

# ---------------- EMAIL SENDER CONFIG ----------------
EMAIL_ADDRESS = "your_email@example.com"
EMAIL_PASSWORD = "your_email_password"

def send_confirmation_email(recipient, code):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Confirm your AgriPrice account"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient
        msg.set_content(f"Your confirmation code is: {code}")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email sending failed: {e}")
        return False

# ---------------- AUTH FUNCTIONS ----------------
def register_user(email, password):
    code = str(random.randint(100000, 999999))
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute("INSERT INTO users (email, password_hash, confirmation_code) VALUES (%s, %s, %s)",
                       (email, password_hash, code))
        db.commit()
        send_confirmation_email(email, code)
        return True
    except mysql.connector.errors.IntegrityError:
        st.warning("Email already registered.")
        return False

def confirm_user(email, code):
    cursor.execute("SELECT * FROM users WHERE email = %s AND confirmation_code = %s", (email, code))
    if cursor.fetchone():
        cursor.execute("UPDATE users SET confirmed = TRUE WHERE email = %s", (email,))
        db.commit()
        return True
    return False

def authenticate_user(email, password):
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        if user["confirmed"]:
            return True
        else:
            st.warning("Account not confirmed. Check your email.")
    return False

# ---------------- STREAMLIT AUTH INTERFACE ----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "registration_email" not in st.session_state:
    st.session_state.registration_email = ""

if not st.session_state.authenticated:
    menu = st.sidebar.selectbox("Login / Register", ["Login", "Register"])

    if menu == "Register":
        st.title("🔐 Register")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(email, password):
                st.success("Check your email for confirmation code.")
                st.session_state.registration_email = email

        if st.session_state.registration_email:
            code = st.text_input("Enter confirmation code sent to email")
            if st.button("Confirm"):
                if confirm_user(st.session_state.registration_email, code):
                    st.success("Account confirmed. Please login.")
                    st.session_state.registration_email = ""
                else:
                    st.error("Invalid confirmation code.")

    elif menu == "Login":
        st.title("🔑 Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_user(email, password):
                st.session_state.authenticated = True
                st.session_state.user_email = email
            else:
                st.error("Login failed.")

# ---------------- MAIN APP ----------------
import datetime

# ---------------- MAIN APP ----------------
if st.session_state.authenticated:
    # Get the current hour for a time-based greeting
    current_hour = datetime.datetime.now().hour
    
    if current_hour < 12:
        greeting = "Good Morning"
    elif current_hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"
    
    # Display an enhanced greeting message
    st.success(f"{greeting} {st.session_state.user_email} 👋 We're happy to have you back!")

    # Add some friendly encouragement
    st.write("Feel free to explore your dashboard or use the options in the sidebar to navigate.")

    # Option for logout
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
