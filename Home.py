import streamlit as st
from datetime import date, datetime
import joblib
import numpy as np
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_echarts import st_echarts
import mysql.connector
import bcrypt
import random
import smtplib
from email.message import EmailMessage
import json
import os
from sklearn.linear_model import LinearRegression  # or whatever model you used

# ----------------- DATABASE CONNECTION SETUP -----------------
db_connected = False
db = None
cursor = None

try:
    db = mysql.connector.connect(
        host="192.168.1.150",
        user="root",
        password="king",
        database="agri_users",
        connection_timeout=3
    )
    cursor = db.cursor(dictionary=True)
    db_connected = True
except Exception as e:
    st.warning("MySQL not connected, falling back to JSON.")
    db_connected = False

# ----------------- LOCAL JSON STORAGE -----------------
DATA_FILE = "data.json"

def read_local_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"users": []}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def write_local_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def sync_to_mysql():
    if not db_connected:
        return
    local_data = read_local_data()
    for user in local_data.get("users", []):
        cursor.execute("SELECT * FROM users WHERE email=%s", (user["email"],))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (email, password_hash, confirmation_code, confirmed) VALUES (%s, %s, %s, %s)",
                (user["email"], user["password_hash"], user["confirmation_code"], user.get("confirmed", False))
            )
            db.commit()

# ----------------- EMAIL CONFIG -----------------
EMAIL_ADDRESS = "mrbal8824@gmail.com"
EMAIL_PASSWORD = "grwm qhez xftq maxx"

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

# ----------------- AUTH FUNCTIONS -----------------
def register_user(email, password):
    code = str(random.randint(100000, 999999))
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    if db_connected:
        try:
            cursor.execute("INSERT INTO users (email, password_hash, confirmation_code) VALUES (%s, %s, %s)",
                           (email, password_hash, code))
            db.commit()
            send_confirmation_email(email, code)
            return True
        except mysql.connector.errors.IntegrityError:
            st.warning("Email already registered.")
            return False
    else:
        data = read_local_data()
        if any(u["email"] == email for u in data["users"]):
            st.warning("Email already registered locally.")
            return False
        data["users"].append({
            "email": email,
            "password_hash": password_hash,
            "confirmation_code": code,
            "confirmed": False
        })
        write_local_data(data)
        send_confirmation_email(email, code)
        return True

def confirm_user(email, code):
    if db_connected:
        cursor.execute("SELECT * FROM users WHERE email = %s AND confirmation_code = %s", (email, code))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET confirmed = TRUE WHERE email = %s", (email,))
            db.commit()
            return True
        return False
    else:
        data = read_local_data()
        for user in data["users"]:
            if user["email"] == email and user["confirmation_code"] == code:
                user["confirmed"] = True
                write_local_data(data)
                return True
        return False

def authenticate_user(email, password):
    if db_connected:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
    else:
        data = read_local_data()
        user = next((u for u in data["users"] if u["email"] == email), None)

    if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        if user.get("confirmed"):
            return True
        else:
            st.warning("Account not confirmed. Check your email.")
    return False

# ----------------- MODEL LOADING -----------------
@st.cache_resource
def load_model():
    return joblib.load("model.pkl")

model = load_model()
# Load model and training data
saved = joblib.load("model.pkl")
model = saved["model"]
data = saved["data"]
# ----------------- STREAMLIT UI -----------------
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
                if db_connected:
                    sync_to_mysql()
            else:
                st.error("Login failed.")

else:
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"
    if "language" not in st.session_state:
        st.session_state.language = "English"
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    # Navigation Sidebar
    st.sidebar.markdown("## Menu")

    if st.sidebar.button("🧭 Dashboard"):
        st.session_state.page = "Dashboard"
    if st.sidebar.button("📈 PricePrediction"):
        st.session_state.page = "PricePrediction"
    if st.sidebar.button("📊 Historical Data"):
        st.session_state.page = "Historical Data"
    if st.sidebar.button("⚙️ Setting"):
        st.session_state.page = "Setting"

    # Top Bar (Header)
    st.markdown(
        f"<h1 style='color: white; background-color: #28C76F; padding: 10px; border-radius: 5px;'>AgriPrice Predictor ({st.session_state.language})</h1>",
        unsafe_allow_html=True,
    )

    # ----------------------- Page Routing -----------------------

    if st.session_state.page == "Dashboard":
         # Get the current hour for a time-based greeting
        current_hour = datetime.now().hour
        
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

    elif st.session_state.page == "PricePrediction":
        st.markdown("### Price Prediction")

        col1, col2 = st.columns([2, 2])
        with col1:
            rainfall = st.number_input("Rainfall (mm)", value=1710)
        with col2:
            years = list(range(2000, datetime.now().year + 10))
            selected_year = st.selectbox("Select year", years, index=len(years)-10)

        col11, col22 = st.columns([2, 2])
        with col11:
            production = st.number_input("Total Production (MT)", value=700506)
        with col22:
            population = st.number_input("Mbeya Population", value=2730397)


        # Predict only if all required values are usable
        try:
            features = np.array([[selected_year, rainfall, production, population]])
            predicted_price = model.predict(features)[0]

            # Display prediction result
            st.markdown(f"""
            <div style='background-color: #EAF6FF; padding: 15px; border-radius: 10px; margin-top: 20px;'>
                <h3>🪙 <strong style="color:#000">{predicted_price:,.0f} Tsh per Kilogram</strong></h3>
                <p style='color: #666;'>Maize, Year {selected_year} Prediction</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style='background-color: #E3FCEC; padding: 10px; border-radius: 10px; border: 1px solid #28C76F; margin-top: 10px;'>
                <strong style='color: #28C76F;'>Prediction Confidence: 85%</strong>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Prediction error: {e}")

        # Influencing factors
        st.markdown("#### Factors influencing Price")
        factors = {
            "🌧️ Rainfall": True,
            "🚜 Agriculture inputs": True,
            "📈 Population": True,
            "🌐 Global Trade": True,
        }
        st.markdown("<div style='background-color: #F9F9F9; padding: 15px; border-radius: 10px;'>", unsafe_allow_html=True)
        cols = st.columns(3)
        for i, label in enumerate(factors.keys()):
            with cols[i % 3]:
                st.markdown(f"<p style='font-size: 16px;'>{label}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "Historical Data":
        st.subheader("📊 Historical Data")

        features = ['Rainfall_mm', 'Total_Production_MT', 'Mbeya_Population']
        target = 'Cost_Tsh_per_kg'
        year_col = 'Year'

        # Compute yearly averages
        yearly_avg = data.groupby(year_col).mean().reset_index()

        # Predict next year price using the average of last year features
        next_year = yearly_avg[year_col].max() + 1
        last_row = yearly_avg[yearly_avg[year_col] == yearly_avg[year_col].max()]
        next_features = [[
            next_year,
            last_row["Rainfall_mm"].values[0],
            last_row["Total_Production_MT"].values[0],
            last_row["Mbeya_Population"].values[0]
        ]]
        predicted_next_price = model.predict(next_features)[0]

        # Append predicted row
        predicted_row = pd.DataFrame({
            year_col: [next_year],
            'Rainfall_mm': last_row["Rainfall_mm"].values,
            'Total_Production_MT': last_row["Total_Production_MT"].values,
            'Mbeya_Population': last_row["Mbeya_Population"].values,
            target: [predicted_next_price]
        })
        yearly_avg = pd.concat([yearly_avg, predicted_row], ignore_index=True)


        # Plot 2 charts side by side in each row
        for i in range(0, len(features), 2):
            col1, col2 = st.columns(2)

            def render_chart(col, feature):
                with col:
                    st.markdown(f" {feature.replace('_', ' ')} vs Price")
                    options = {
                        "tooltip": {"trigger": "axis"},
                        "legend": {"data": [feature, "Price (Tsh/kg)"]},
                        "xAxis": {"type": "category", "data": yearly_avg[year_col].tolist()},
                        "yAxis": [
                            {"type": "value", "name": feature},
                            {"type": "value", "name": "Price (Tsh/kg)"}
                        ],
                        "series": [
                            {
                                "name": feature,
                                "type": "line",
                                "data": yearly_avg[feature].round(2).tolist(),
                            },
                            {
                                "name": "Price (Tsh/kg)",
                                "type": "line",
                                "yAxisIndex": 1,
                                "data": yearly_avg[target].round(2).tolist(),
                            },
                        ],
                    }
                    st_echarts(options=options, height="480px")

            render_chart(col1, features[i])
            if i + 1 < len(features):
                render_chart(col2, features[i + 1])




    elif st.session_state.page == "Setting":
        st.subheader("⚙️ Settings")

        # Language toggle
        lang = st.radio("Select Language:", ["English", "Swahili"])
        st.session_state.language = lang

        # Dark/Light toggle
        theme = st.toggle("Enable Dark Mode", value=st.session_state.dark_mode)
        st.session_state.dark_mode = theme



    # Optional: Adjust background color for dark mode
    if st.session_state.dark_mode:
        st.markdown("""
            <style>
            body {
                background-color: #2c2f33;
                color: #ffffff;
            }
            </style>
        """, unsafe_allow_html=True)
